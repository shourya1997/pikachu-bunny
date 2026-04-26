from __future__ import annotations

import re
from pathlib import Path

COMPOSE_FILES = [Path('docker-compose.yml'), Path('docker-compose.dev.yml')]
PORT_PATTERN = re.compile(r'^[\s-]*["\']?(?P<binding>(?:\d+\.\d+\.\d+\.\d+:)?\d+:\d+)["\']?\s*$')
KEY_VALUE_PATTERN = re.compile(r'^\s*(?P<key>[a-zA-Z_]+):\s*["\']?(?P<value>[^"\'\s#]+)')


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(' '))


def parse_port_entry(lines: list[str], start_index: int) -> tuple[dict[str, str], int]:
    fields: dict[str, str] = {}
    start_line = lines[start_index]
    start_indent = leading_spaces(start_line)
    first_item = start_line.lstrip()[2:].strip()
    if match := KEY_VALUE_PATTERN.match(first_item):
        fields[match.group('key')] = match.group('value')

    index = start_index + 1
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            index += 1
            continue
        indent = leading_spaces(line)
        if indent <= start_indent:
            break
        if line.lstrip().startswith('- '):
            break
        if match := KEY_VALUE_PATTERN.match(line):
            fields[match.group('key')] = match.group('value')
        index += 1

    return fields, index


def check_compose_file(compose_file: Path) -> list[str]:
    if not compose_file.exists():
        return [f'{compose_file} is required for Docker privacy checks but is missing']

    failures: list[str] = []
    lines = compose_file.read_text().splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        line_no = index + 1
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            index += 1
            continue

        match = PORT_PATTERN.match(line)
        if match:
            binding = match.group('binding')
            if not binding.startswith('127.0.0.1:'):
                failures.append(f'{compose_file}:{line_no} exposes {binding}; bind host ports to 127.0.0.1')
            index += 1
            continue

        if line.lstrip().startswith('- '):
            fields, next_index = parse_port_entry(lines, index)
            if 'published' in fields and fields.get('host_ip') != '127.0.0.1':
                failures.append(f'{compose_file}:{line_no} publishes a port without host_ip: 127.0.0.1')
            index = next_index
            continue

        index += 1

    return failures


def main() -> int:
    failures: list[str] = []
    for compose_file in COMPOSE_FILES:
        failures.extend(check_compose_file(compose_file))
    if failures:
        print('\n'.join(failures))
        return 1
    print('Docker privacy check passed: all published host ports bind to 127.0.0.1')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
