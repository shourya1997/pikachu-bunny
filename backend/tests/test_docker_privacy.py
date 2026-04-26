from __future__ import annotations

import importlib.util
from pathlib import Path


def load_privacy_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "check-docker-privacy.py"
    spec = importlib.util.spec_from_file_location("check_docker_privacy", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("Could not load Docker privacy checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_short_port_binding_must_use_localhost(tmp_path: Path) -> None:
    module = load_privacy_module()
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """
services:
  audit-app:
    ports:
      - "8000:8000"
""",
    )

    failures = module.check_compose_file(compose_file)

    assert failures
    assert "127.0.0.1" in failures[0]


def test_localhost_short_port_binding_passes(tmp_path: Path) -> None:
    module = load_privacy_module()
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """
services:
  audit-app:
    ports:
      - "127.0.0.1:8000:8000"
""",
    )

    assert module.check_compose_file(compose_file) == []


def test_long_port_binding_must_use_localhost(tmp_path: Path) -> None:
    module = load_privacy_module()
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """
services:
  audit-app:
    ports:
      - target: 8000
        published: "8000"
        protocol: tcp
""",
    )

    failures = module.check_compose_file(compose_file)

    assert failures
    assert "host_ip: 127.0.0.1" in failures[0]


def test_localhost_long_port_binding_passes(tmp_path: Path) -> None:
    module = load_privacy_module()
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """
services:
  audit-app:
    ports:
      - target: 8000
        published: "8000"
        host_ip: 127.0.0.1
""",
    )

    assert module.check_compose_file(compose_file) == []


def test_adjacent_long_port_bindings_do_not_share_host_ip(tmp_path: Path) -> None:
    module = load_privacy_module()
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """
services:
  audit-app:
    ports:
      - target: 8000
        published: 8000
      - target: 9000
        published: 9000
        host_ip: 127.0.0.1
""",
    )

    failures = module.check_compose_file(compose_file)

    assert len(failures) == 1
    assert "8000" not in failures[0]
    assert "host_ip: 127.0.0.1" in failures[0]


def test_missing_compose_file_fails_clearly(tmp_path: Path) -> None:
    module = load_privacy_module()

    failures = module.check_compose_file(tmp_path / "missing-compose.yml")

    assert failures == ["%s is required for Docker privacy checks but is missing" % (tmp_path / "missing-compose.yml")]
