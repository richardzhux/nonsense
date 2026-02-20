# Media Observatory

Static analysis report for a media archive using a strict year/month folder structure.

## Structure assumptions
- Base path contains year folders named `20xx` (four digits only).
- Each year folder contains month folders named `01` through `12`.
- Only those folders are scanned; everything else is ignored.
- If EXIF time is missing and only a filename date exists, the scan borrows the file's mtime time-of-day.

## Configure
Edit `onedrive_observatory/config.py`:
- `base_folder`
- `start_date` (YYYYMMDD)
- `allowed_years` (default: 2019-2025)
- output paths in `output_dir`
- `enable_hashing` (default choice for the prompt)
- `prompt_hashing` (set false to skip the prompt)
- scanner output excludes source paths, device identifiers, and GPS metadata

## Run
```
pip install -r onedrive_observatory/requirements.txt
python -m onedrive_observatory
```

To build the report from an existing CSV without scanning media files:
```
python -m onedrive_observatory.from_csv onedrive_observatory/output/onedrive_report_data.csv
```

You can also run `onedrive_report.py` for an interactive mode prompt.

## Output
- `onedrive_observatory/output/onedrive_report.html`
- `onedrive_observatory/output/onedrive_report_data.csv`
