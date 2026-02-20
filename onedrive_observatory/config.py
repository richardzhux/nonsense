from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Settings:
    base_folder: Path
    start_date: str
    output_dir: Path
    output_html: Path
    output_csv: Path
    default_csv_path: Path
    allowed_years: List[int]
    enable_hashing: bool
    prompt_hashing: bool
    near_dup_threshold: int
    near_dup_prefix_len: int


DEFAULT_SETTINGS = Settings(
    base_folder=Path("media_archive"),
    start_date="20220101",
    output_dir=Path("onedrive_observatory/output"),
    output_html=Path("onedrive_observatory/output/onedrive_report.html"),
    output_csv=Path("onedrive_observatory/output/onedrive_report_data.csv"),
    default_csv_path=Path("onedrive_observatory/output/onedrive_report_data.csv"),
    allowed_years=[2019, 2020, 2021, 2022, 2023, 2024, 2025],
    enable_hashing=False,
    prompt_hashing=True,
    near_dup_threshold=6,
    near_dup_prefix_len=4,
)
