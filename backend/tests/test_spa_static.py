from pathlib import Path

from app.main import resolve_spa_path


def test_spa_resolves_file_inside_static_root(tmp_path: Path) -> None:
    static_root = tmp_path / "static"
    static_root.mkdir()
    asset = static_root / "app.js"
    asset.write_text("console.log('ok')")

    assert resolve_spa_path(static_root.resolve(), "app.js") == asset.resolve()


def test_spa_blocks_path_traversal_outside_static_root(tmp_path: Path) -> None:
    static_root = tmp_path / "static"
    static_root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("private")

    assert resolve_spa_path(static_root.resolve(), "../secret.txt") is None


def test_spa_blocks_symlink_to_file_outside_static_root(tmp_path: Path) -> None:
    static_root = tmp_path / "static"
    static_root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("private")
    (static_root / "secret-link.txt").symlink_to(secret)

    assert resolve_spa_path(static_root.resolve(), "secret-link.txt") is None
