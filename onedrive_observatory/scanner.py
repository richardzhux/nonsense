import hashlib
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from PIL import Image, ExifTags

IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".heif",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
    ".webp",
    ".dng",
    ".cr2",
    ".nef",
    ".arw",
    ".rw2",
}
VIDEO_EXTS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".mts",
    ".3gp",
    ".wmv",
}

DATE_PATTERNS = [
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
    re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})"),
]

YEAR_PATTERN = re.compile(r"20\d{2}")
MONTH_PATTERN = re.compile(r"(0[1-9]|1[0-2])")


@dataclass
class MediaRecord:
    ext: str
    size_bytes: int
    mtime: datetime
    date_taken: Optional[datetime]
    date_source: str
    media_type: str
    width: Optional[int]
    height: Optional[int]
    sha1: Optional[str]
    dhash: Optional[str]


def parse_exif_date(exif: Dict) -> Optional[datetime]:
    for key in ["DateTimeOriginal", "DateTimeDigitized", "DateTime", "CreateDate"]:
        value = exif.get(key)
        if not value:
            continue
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="ignore")
            except Exception:
                continue
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
    return None


def parse_filename_date(name: str) -> Optional[datetime]:
    for pattern in DATE_PATTERNS:
        match = pattern.search(name)
        if match:
            y, m, d = match.groups()
            try:
                return datetime(int(y), int(m), int(d))
            except ValueError:
                continue
    return None


def compute_sha1(path: Path) -> str:
    sha1 = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha1.update(chunk)
    return sha1.hexdigest()


def compute_dhash(path: Path, hash_size: int = 8) -> Optional[str]:
    try:
        with Image.open(path) as img:
            img = img.convert("L")
            img = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
        rows = [pixels[i : i + hash_size + 1] for i in range(0, len(pixels), hash_size + 1)]
        diff = []
        for row in rows:
            diff.extend([row[i] > row[i + 1] for i in range(hash_size)])
        decimal_value = 0
        for idx, value in enumerate(diff):
            if value:
                decimal_value |= 1 << idx
        width = int(math.ceil(hash_size * hash_size / 4))
        return f"{decimal_value:0{width}x}"
    except Exception:
        return None


def iter_media_paths(base_path: Path, start_date: date, allowed_years: List[int]) -> Iterable[Path]:
    for year_dir in sorted(base_path.iterdir()):
        if not year_dir.is_dir():
            continue
        if not YEAR_PATTERN.fullmatch(year_dir.name):
            continue
        year = int(year_dir.name)
        if allowed_years and year not in allowed_years:
            continue
        if year < start_date.year:
            continue

        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            if not MONTH_PATTERN.fullmatch(month_dir.name):
                continue
            month = int(month_dir.name)
            if year == start_date.year and month < start_date.month:
                continue

            for path in month_dir.iterdir():
                if path.is_file():
                    yield path


def scan_media(
    base_path: Path, start_date: date, allowed_years: List[int], enable_hashing: bool
) -> List[MediaRecord]:
    records = []
    skipped = 0
    scanned = 0

    for path in iter_media_paths(base_path, start_date, allowed_years):
        ext = path.suffix.lower()
        if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
            continue

        scanned += 1
        if scanned % 1000 == 0:
            print(f"Scanned {scanned} media files...")

        try:
            stat = path.stat()
        except Exception:
            skipped += 1
            continue

        mtime = datetime.fromtimestamp(stat.st_mtime)
        date_taken = None
        date_source = "unknown"
        width = None
        height = None

        if ext in IMAGE_EXTS:
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    exif_raw = img.getexif()
                exif = {}
                if exif_raw:
                    for key, val in exif_raw.items():
                        exif_key = ExifTags.TAGS.get(key, key)
                        exif[exif_key] = val
                date_taken = parse_exif_date(exif)
                if date_taken:
                    date_source = "exif"
                else:
                    date_taken = parse_filename_date(path.name)
                    if date_taken:
                        date_source = "filename"
            except Exception:
                date_taken = parse_filename_date(path.name)
                if date_taken:
                    date_source = "filename"
        else:
            date_taken = parse_filename_date(path.name)
            if date_taken:
                date_source = "filename"

        if not date_taken:
            date_taken = mtime
            date_source = "mtime"
        elif date_source == "filename":
            # Filename dates have no time-of-day; borrow the file's mtime time.
            date_taken = datetime.combine(date_taken.date(), mtime.time())

        if date_taken and date_taken.date() < start_date:
            continue

        sha1 = compute_sha1(path) if enable_hashing else None
        dhash = compute_dhash(path) if enable_hashing and ext in IMAGE_EXTS else None

        record = MediaRecord(
            ext=ext,
            size_bytes=stat.st_size,
            mtime=mtime,
            date_taken=date_taken,
            date_source=date_source,
            media_type="photo" if ext in IMAGE_EXTS else "video",
            width=width,
            height=height,
            sha1=sha1,
            dhash=dhash,
        )
        records.append(record)

    print(f"Scan complete. {scanned} files scanned, {skipped} skipped.")
    return records
