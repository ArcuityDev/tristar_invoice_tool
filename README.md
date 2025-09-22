# Tristar Subscription Pricing Tool

Interactive subscription pricing tool for Tristar. It reads a CSV report at the repo root and populates usage/page counts for each service, preserving your existing pricing math. A timeframe variant is provided to filter/segment results.

## Live hosting options

- Netlify (recommended)
- GitHub Pages
- bolt.new (drag-and-drop for quick sharing)

## Files

Place these at the repository root:

- `index.html` — Main app (includes month dropdown and CSV loader)
- `index_timeframe.html` — Timeframe-filtered view variant
- `shirlei_report_all_data.csv` — Data source (export from your backend)
- `logo.png` — Logo displayed in the header

> If you preview locally via `file://`, browsers may block fetching the CSV. Use Netlify/GitHub Pages/bolt.new, or the built‑in file picker will appear as a fallback.

## CSV format

Expected columns (header row):

- `id`
- `date_received` — format `m/d/yyyy` or `mm/dd/yyyy`
- `Insurer`
- `RequestType` — mapped to services:
  - `Arcuity IMR` → IMR Report Generation (`imr`)
  - `Arcuity SDT Response` → SDT Response (`sdt`)
  - `Arcuity File and Serve` → File and Serve (`file`)
  - `Arcuity File Prep` / `Arcuity FIle Prep` → New File Prep (`nfp`)
  - `Arcuity On-Demand` → On-Demand (`ond`)
  - Any variant containing `QME` → QME Report Prep (`qme`)
- `PredupePageCount` (optional)
- `PostDupePageCount` (optional)

Page counts use `PostDupePageCount` if present; otherwise `PredupePageCount`; otherwise `0`.

## Data generation

- Script: `shirlei_report.py`
  - Purpose: parses source data and produces `shirlei_report_all_data.csv` at the repo root.
  - Usage:
    - Ensure Python 3 is installed.
    - From repo root:
      - `python shirlei_report.py`
    - Confirm `shirlei_report_all_data.csv` is updated/created at the root.
  - Reference sample: `sample reports/shirlei_report_20250707.csv`

## How the month filter works

- The app parses `shirlei_report_all_data.csv` client‑side and groups data by `YYYY-MM` from `date_received`.
- Selecting a month updates the numeric inputs for each service (reports/pages) and triggers the existing calculators; no pricing logic was changed.

## Deploy on Netlify

1. Push this folder to GitHub with `index.html`, `shirlei_report_all_data.csv`, and `logo.png` at the root.
2. In Netlify: New site → Import from Git.
3. Choose your repo.
4. Build settings:
   - Build command: (leave empty)
   - Publish directory: `./` (repo root)
5. Deploy. Visit the site URL.

## Deploy on GitHub Pages

1. Ensure `index.html`, `shirlei_report_all_data.csv`, and `logo.png` are in the repo root.
2. Repo Settings → Pages → Source: Deploy from a branch → select default branch and root.
3. Wait for the build, then visit the Pages URL.

## CI validation

This repository includes a lightweight validation workflow to prevent accidental removal or empty/malformed CSV submissions.

- Workflow: `.github/workflows/validate-csv.yml`
- Triggers on pull requests
- Checks:
  - CSV exists at repo root: `shirlei_report_all_data.csv`
  - CSV is non-empty
  - Header contains required columns: `date_received`, `RequestType`
  - At least 2 lines total (header + at least one data row)

## Quick local preview (optional)

Use a local web server to avoid `file://` fetch restrictions:

- Python 3

```bash
python -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080)

- Node (serve)

```bash
npx serve .
```

## Development notes

- Calculations remain the same as your original spreadsheet logic:
  - Subscription units = usage / included (with minimum base price)
  - Report fees = usage × $25
  - Page fees = pages × $0.10
  - Record Retrieval tiers and extra page calc preserved
- The month selector only sets input values; totals update via existing JS functions.
- Historical/working variants are kept under `Working Files/` and `prior_to_excel_sync/` for context/audit.
- If CSV/ZIP files become large or change frequently, consider enabling Git LFS for `*.csv` / `*.zip` to reduce repo bloat.

## License

Internal use only unless specified otherwise.
