#!/usr/bin/env python3
from pathlib import Path

from onedrive_observatory.config import DEFAULT_SETTINGS
from onedrive_observatory.from_csv import run_from_csv
from onedrive_observatory.main import run as run_scan


def prompt_mode() -> str:
    print("Choose report mode:")
    print("1) Scan media folders (slower)")
    print("2) Build report from existing CSV (fast)")
    choice = input("Select [1/2] (default 2): ").strip().lower()
    if choice in {"1", "scan", "s"}:
        return "scan"
    if choice in {"2", "csv", "c", ""}:
        return "csv"
    return "csv"


def prompt_csv_path(default_path: Path) -> Path:
    choice = input(f"CSV path [{default_path}]: ").strip()
    if not choice:
        return default_path
    return Path(choice)


def main() -> None:
    mode = prompt_mode()
    if mode == "scan":
        run_scan()
        return
    csv_path = prompt_csv_path(DEFAULT_SETTINGS.default_csv_path)
    run_from_csv(csv_path)


if __name__ == "__main__":
    main()
