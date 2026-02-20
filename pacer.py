"""
Extract NDIL criminal cases (2020–2023) from a PACER 'Criminal Cases Report' PDF
and export to CSV in the format requested by the AO:

Case Number | Case Name | Location

Requirements:
    pip install pdfplumber
"""

import re
import csv
import datetime as dt
from pathlib import Path

import pdfplumber

PDF_PATH = Path("CMECF.pdf")  # change to your input PDF
OUTPUT_CSV = Path("PACER.csv")

YEAR_MIN = 2020
YEAR_MAX = 2023
LOCATION_STR = "N.D. Ill."


def extract_cases(pdf_path: Path):
    cases = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            # drop empty lines, trim whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            i = 0
            while i < len(lines):
                line = lines[i]

                # case number is at the start of the line, e.g. "1:20-cr-00002 Case filed: ..."
                m = re.match(r"^(\d+:\d{2}-[A-Za-z]{2}-\d{5})\b", line)
                if not m:
                    i += 1
                    continue

                case_number = m.group(1)

                # only keep criminal cases
                if "-cr-" not in case_number.lower():
                    i += 1
                    continue

                # ---- find filed date (for 2020–2023 filter) ----
                filed_date_str = None
                # first, try same line
                m_date = re.search(r"Case filed:\s*(\d{2}/\d{2}/\d{4})", line)
                if m_date:
                    filed_date_str = m_date.group(1)
                else:
                    # if not on same line, check next few lines
                    for off in range(1, 4):
                        if i + off >= len(lines):
                            break
                        m_date = re.search(
                            r"Case filed:\s*(\d{2}/\d{2}/\d{4})",
                            lines[i + off],
                        )
                        if m_date:
                            filed_date_str = m_date.group(1)
                            break

                # if we can't parse a valid date, skip this case
                if not filed_date_str:
                    i += 1
                    continue

                try:
                    filed_year = dt.datetime.strptime(
                        filed_date_str, "%m/%d/%Y"
                    ).year
                except ValueError:
                    i += 1
                    continue

                if not (YEAR_MIN <= filed_year <= YEAR_MAX):
                    i += 1
                    continue

                # ---- extract case name from following line ----
                case_name = ""
                if i + 1 < len(lines):
                    title_line = lines[i + 1]
                    # strip trailing "Case closed: ...", "Added:", "Office:", "Presider:" etc.
                    m_title = re.match(
                        r"^(.*?)(?:\s+Case closed:|\s+Added:|\s+Office:|\s+Presider:|$)",
                        title_line,
                    )
                    if m_title:
                        case_name = m_title.group(1).strip()

                cases.append(
                    {
                        "Case Number": case_number,
                        "Case Name": case_name,
                        "Location": LOCATION_STR,
                    }
                )

                i += 1

    # de-duplicate by case number just in case any appear twice
    deduped = {}
    for c in cases:
        deduped[c["Case Number"]] = c

    return list(deduped.values())


def main():
    cases = extract_cases(PDF_PATH)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Case Number", "Case Name", "Location"]
        )
        writer.writeheader()
        writer.writerows(cases)

    print(f"Wrote {len(cases)} cases to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
