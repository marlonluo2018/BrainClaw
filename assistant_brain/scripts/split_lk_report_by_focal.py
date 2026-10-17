"""
Split monthly L&K Learning Report by Sub Team (focal) for Industry & Delivery team.

Sheets generated per Sub Team:
1. T2G (from Credential Priority Certs / T2G report, filtered by I&D HC mapping)
2. Industry Badge (from Industry badge report, sheet 'YL Report')
3. Language (from Language report, sheet 'final')
4. T40 (from T40 report, sheet 'HC')

Supports both direct .zip archives and extracted folder paths.
Handles encrypted Excel files automatically using msoffcrypto.

Passwords convention:
- HC excel: learningreportYYYYMM (e.g. learningreport202609)
- Other excels: learning-report

Usage:
  py -3 assistant_brain/scripts/split_lk_report_by_focal.py <zip_path_or_folder> [--t2g <path_to_t2g_file>]
Examples:
  py -3 assistant_brain/scripts/split_lk_report_by_focal.py "C:/Users/MengNingLuo/Downloads/Sep.zip"
  py -3 assistant_brain/scripts/split_lk_report_by_focal.py "C:/Users/MengNingLuo/Downloads/Sep" --t2g "C:/Users/MengNingLuo/Downloads/Credential Priority Certs publ. Report Updated on 2026-09-25.csv"
"""

import io
import os
import sys
import re
import csv
import glob
import zipfile
import argparse
from datetime import datetime
import openpyxl
from openpyxl.utils import get_column_letter

try:
    import msoffcrypto
except ImportError:
    msoffcrypto = None

TEAM_FILTER = "Industry & Delivery"

EXCEL_REPORT_PATTERNS = [
    {
        "keyword": "Industry badge",
        "sheet": "YL Report",
        "team_col": 5,
        "sub_team_col": 6,
        "output_sheet_name": "Industry Badge",
    },
    {
        "keyword": "Language",
        "sheet": "final",
        "team_col": 6,
        "sub_team_col": 7,
        "output_sheet_name": "Language",
    },
    {
        "keyword": "T40",
        "sheet": "HC",
        "team_col": 10,
        "sub_team_col": 11,
        "output_sheet_name": "T40",
    },
]

TARGET_SHEET_ORDER = ["T2G", "Industry Badge", "Language", "T40"]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_ABBR_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}


def parse_period(source_hint, file_list):
    """Detect month and year from path and filenames."""
    year = None
    month_num = None

    for f in file_list:
        if not f.endswith(".xlsx") or f.startswith("~$"):
            continue
        m1 = re.search(r"(\d{4})[_\s\.\-]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*", f, re.IGNORECASE)
        if m1:
            year = int(m1.group(1))
            month_num = MONTH_ABBR_MAP[m1.group(2)[:3].lower()]
            break
        m2 = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[_\s\.\-]+(\d{4})", f, re.IGNORECASE)
        if m2:
            month_num = MONTH_ABBR_MAP[m2.group(1)[:3].lower()]
            year = int(m2.group(2))
            break

    if not month_num or not year:
        hint_str = os.path.basename(source_hint)
        m_hint = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*", hint_str, re.IGNORECASE)
        if m_hint:
            month_num = MONTH_ABBR_MAP[m_hint.group(0)[:3].lower()]
        y_hint = re.search(r"(20\d\d)", hint_str)
        if y_hint:
            year = int(y_hint.group(1))

    if not year:
        year = datetime.now().year
    if not month_num:
        month_num = datetime.now().month

    month_name = MONTH_NAMES[month_num - 1]
    return year, month_num, month_name


def open_workbook_auto(filepath, passwords):
    """Open workbook, automatically handling encryption if msoffcrypto is available."""
    if msoffcrypto is not None:
        try:
            with open(filepath, "rb") as f:
                office_file = msoffcrypto.OfficeFile(f)
                if office_file.is_encrypted():
                    for pw in passwords:
                        try:
                            f.seek(0)
                            office_file = msoffcrypto.OfficeFile(f)
                            office_file.load_key(password=pw)
                            decrypted = io.BytesIO()
                            office_file.decrypt(decrypted)
                            decrypted.seek(0)
                            return openpyxl.load_workbook(decrypted, read_only=True, data_only=True)
                        except Exception:
                            continue
                    raise ValueError(f"Could not decrypt {os.path.basename(filepath)} with passwords: {passwords}")
        except Exception as e:
            if "Could not decrypt" in str(e):
                raise
            pass

    return openpyxl.load_workbook(filepath, read_only=True, data_only=True)


def find_excel_folder(root_dir):
    """Locate the directory that contains the target report Excel files."""
    for root, _, files in os.walk(root_dir):
        xlsx_files = [f for f in files if f.endswith(".xlsx") and not f.startswith("~$")]
        matched_count = 0
        for f in xlsx_files:
            for p in EXCEL_REPORT_PATTERNS:
                if p["keyword"].lower() in f.lower():
                    matched_count += 1
                    break
        if matched_count >= 2:
            return root
    return root_dir


def find_t2g_file(search_dirs, explicit_path=None):
    """Find T2G / Credential Priority Certs file."""
    if explicit_path and os.path.isfile(explicit_path):
        return explicit_path

    pattern = re.compile(r"credential\s+(priority\s+certs|t2g)", re.IGNORECASE)
    candidates = []
    for d in search_dirs:
        if not d or not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if pattern.search(fname) and (fname.endswith(".csv") or fname.endswith(".xlsx")) and not fname.startswith("~$"):
                full_path = os.path.join(d, fname)
                candidates.append((os.path.getmtime(full_path), full_path))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return None


def extract_hc_mapping(excel_dir, excel_files, pw_list):
    """
    Extract email -> subteam and cnum -> subteam mapping for Industry & Delivery.
    Uses T40 sheet 'HC' or CIC Export HC report.
    """
    # Prefer T40 file
    t40_file = None
    for f in excel_files:
        if "t40" in f.lower() and f.endswith(".xlsx"):
            t40_file = f
            break
    if not t40_file:
        for f in excel_files:
            if "export hc" in f.lower() and f.endswith(".xlsx"):
                t40_file = f
                break

    if not t40_file:
        raise FileNotFoundError("Could not find T40 or Export HC Excel file to extract HC mapping.")

    filepath = os.path.join(excel_dir, t40_file)
    wb = open_workbook_auto(filepath, pw_list)
    sheet_name = "HC" if "HC" in wb.sheetnames else wb.sheetnames[0]
    ws = wb[sheet_name]

    headers = None
    email_col = 8
    cnum_col = 0
    team_col = 10
    sub_team_col = 11

    email_map = {}
    cnum_map = {}

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(h).strip().lower() if h else "" for h in row]
            for idx, h in enumerate(headers):
                if h in ["internet email", "email"]:
                    email_col = idx
                elif h in ["talentid", "cnum", "employee - id"]:
                    cnum_col = idx
                elif h == "team":
                    team_col = idx
                elif h in ["sub team", "subteam"]:
                    sub_team_col = idx
            continue

        team_val = str(row[team_col]).strip() if team_col < len(row) and row[team_col] is not None else ""
        if team_val == TEAM_FILTER:
            sub_team_val = str(row[sub_team_col]).strip() if sub_team_col < len(row) and row[sub_team_col] is not None else "Unknown"
            if email_col < len(row) and row[email_col]:
                email_map[str(row[email_col]).strip().lower()] = sub_team_val
            if cnum_col < len(row) and row[cnum_col]:
                cnum_map[str(row[cnum_col]).strip().lower()] = sub_team_val

    wb.close()
    return email_map, cnum_map


def load_t2g_data(t2g_path, email_map, cnum_map, pw_list):
    """Load T2G / Priority Certs rows mapped to I&D subteams."""
    grouped = {}
    headers = None

    if t2g_path.endswith(".csv"):
        with open(t2g_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            headers = next(reader)
            email_col = 0
            cnum_col = 1
            for idx, h in enumerate(headers):
                hl = h.strip().lower()
                if hl == "internet email":
                    email_col = idx
                elif hl in ["cnum", "talentid"]:
                    cnum_col = idx

            for row in reader:
                email = row[email_col].strip().lower() if email_col < len(row) and row[email_col] else ""
                cnum = row[cnum_col].strip().lower() if cnum_col < len(row) and row[cnum_col] else ""
                st = email_map.get(email) or cnum_map.get(cnum)
                if st:
                    if st not in grouped:
                        grouped[st] = []
                    grouped[st].append(row)
    else:
        wb = open_workbook_auto(t2g_path, pw_list)
        ws = wb.active
        if ws is None:
            wb.close()
            return headers, grouped
        email_col = 0
        cnum_col = 1
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = list(row)
                for idx, h in enumerate(headers):
                    hl = str(h).strip().lower() if h else ""
                    if hl == "internet email":
                        email_col = idx
                    elif hl in ["cnum", "talentid"]:
                        cnum_col = idx
                continue

            email = str(row[email_col]).strip().lower() if email_col < len(row) and row[email_col] else ""
            cnum = str(row[cnum_col]).strip().lower() if cnum_col < len(row) and row[cnum_col] else ""
            st = email_map.get(email) or cnum_map.get(cnum)
            if st:
                if st not in grouped:
                    grouped[st] = []
                grouped[st].append(list(row))
        wb.close()

    return headers, grouped


def load_filtered_data(filepath, config, passwords):
    """Load data filtered by Team = 'Industry & Delivery', grouped by Sub Team."""
    wb = open_workbook_auto(filepath, passwords)
    
    sheet_name = None
    for s in wb.sheetnames:
        if s.strip().lower() == config["sheet"].strip().lower():
            sheet_name = s
            break

    if not sheet_name:
        print(f"  WARNING: Sheet '{config['sheet']}' not found in {os.path.basename(filepath)}, skipping")
        wb.close()
        return None, {}

    ws = wb[sheet_name]
    headers = None
    grouped = {}

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = list(row)
            continue
        team = row[config["team_col"]] if config["team_col"] < len(row) else None
        sub_team = row[config["sub_team_col"]] if config["sub_team_col"] < len(row) else None
        if str(team).strip() == TEAM_FILTER:
            st_key = str(sub_team).strip() if sub_team else "Unknown"
            if st_key not in grouped:
                grouped[st_key] = []
            grouped[st_key].append(list(row))

    wb.close()
    return headers, grouped


def process_reports(source_dir, output_dir=None, t2g_path=None):
    """Core logic to process and split report files."""
    excel_dir = find_excel_folder(source_dir)
    excel_files = [f for f in os.listdir(excel_dir) if f.endswith(".xlsx") and not f.startswith("~$")]

    detected_year, detected_month_num, detected_month_name = parse_period(source_dir, excel_files)
    month_label = f"{detected_month_name} {detected_year}"

    hc_password = f"learningreport{detected_year}{detected_month_num:02d}"
    general_password = "learning-report"

    hc_passwords = [hc_password, general_password]
    general_passwords = [general_password, hc_password]

    if not output_dir:
        output_dir = os.path.join(source_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Report period: {month_label}")
    print(f"Excel source folder: {excel_dir}")
    print(f"Output folder: {output_dir}")
    print(f"HC Password: {hc_password} | General Password: {general_password}\n")

    # Locate T2G / Credential Priority Certs file
    search_dirs = [excel_dir, source_dir, os.path.dirname(source_dir)]
    t2g_file = find_t2g_file(search_dirs, explicit_path=t2g_path)
    if not t2g_file:
        print(f"ERROR: Could not locate T2G / Credential Priority Certs file in {search_dirs}")
        print("Please provide it via --t2g <path>")
        sys.exit(1)

    print(f"Found T2G source: {t2g_file}")

    # Build HC Mapping
    email_map, cnum_map = extract_hc_mapping(excel_dir, excel_files, general_passwords)
    print(f"Built I&D HC member map: {len(email_map)} emails, {len(cnum_map)} CNUMs")

    all_data = {}

    # 1. Process T2G Sheet
    print(f"\nProcessing T2G: {os.path.basename(t2g_file)}")
    t2g_headers, t2g_grouped = load_t2g_data(t2g_file, email_map, cnum_map, general_passwords)
    for sub_team, rows in t2g_grouped.items():
        if sub_team not in all_data:
            all_data[sub_team] = {}
        all_data[sub_team]["T2G"] = (t2g_headers, rows)
        print(f"  [T2G] [{sub_team}] +{len(rows)} rows")

    # 2. Process Industry Badge, Language, T40
    for config in EXCEL_REPORT_PATTERNS:
        matched_file = None
        for filename in sorted(excel_files):
            if config["keyword"].lower() in filename.lower():
                matched_file = filename
                break

        if not matched_file:
            print(f"  WARNING: No file matching keyword '{config['keyword']}' found")
            continue

        filepath = os.path.join(excel_dir, matched_file)
        is_hc = "hc" in matched_file.lower() and "export hc" in matched_file.lower()
        pw_list = hc_passwords if is_hc else general_passwords

        print(f"\nProcessing: {matched_file} -> sheet '{config['sheet']}'")
        headers, grouped = load_filtered_data(filepath, config, pw_list)

        if headers is None:
            continue

        for sub_team, rows in grouped.items():
            if sub_team not in all_data:
                all_data[sub_team] = {}
            all_data[sub_team][config["output_sheet_name"]] = (headers, rows)
            print(f"  [{config['output_sheet_name']}] [{sub_team}] +{len(rows)} rows")

    # Write output files
    print(f"\n--- Writing output files ---")
    generated_files = []
    for sub_team, sheets in sorted(all_data.items()):
        out_filename = f"{month_label} - {sub_team}.xlsx"
        out_path = os.path.join(output_dir, out_filename)

        wb_out = openpyxl.Workbook()
        if wb_out.active is not None:
            wb_out.remove(wb_out.active)

        # Write sheets in strictly specified order: T2G, Industry Badge, Language, T40
        for sheet_name in TARGET_SHEET_ORDER:
            if sheet_name not in sheets:
                continue
            headers, rows = sheets[sheet_name]
            ws = wb_out.create_sheet(title=sheet_name)
            ws.append(headers)
            for row in rows:
                ws.append(row)
            for col_idx, header in enumerate(headers, 1):
                if header:
                    ws.column_dimensions[get_column_letter(col_idx)].width = max(12, min(30, len(str(header)) + 2))

        wb_out.save(out_path)
        total_rows = sum(len(r) for _, (_, r) in sheets.items())
        print(f"  Created: {out_filename} ({len(sheets)} sheets: {list(sheets.keys())}, {total_rows} rows)")
        generated_files.append(out_path)

    print(f"\nSUCCESS: {len(all_data)} focal report files created in {output_dir}")
    return generated_files


def main():
    parser = argparse.ArgumentParser(description="Split monthly L&K Learning Report by Sub Team for I&D.")
    parser.add_argument("input_path", help="Path to .zip file or extracted directory containing the monthly reports.")
    parser.add_argument("--t2g", help="Optional path to Credential Priority Certs / T2G file.")
    parser.add_argument("--output-dir", help="Optional output directory. Defaults to <source_dir>/output.")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_path)
    if not os.path.exists(input_path):
        print(f"ERROR: Input path not found: {input_path}")
        sys.exit(1)

    t2g_path = os.path.abspath(args.t2g) if args.t2g else None

    if os.path.isfile(input_path) and input_path.lower().endswith(".zip"):
        extract_dir = os.path.splitext(input_path)[0]
        os.makedirs(extract_dir, exist_ok=True)
        print(f"Extracting zip archive: {input_path} -> {extract_dir}")
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(extract_dir)
        source_dir = extract_dir
    elif os.path.isdir(input_path):
        source_dir = input_path
    else:
        print(f"ERROR: Input must be a .zip file or a directory: {input_path}")
        sys.exit(1)

    output_dir = os.path.abspath(args.output_dir) if args.output_dir else os.path.join(source_dir, "output")
    process_reports(source_dir, output_dir, t2g_path)


if __name__ == "__main__":
    main()
