# AcadAlliance
AcadAlliance is a Python desktop app for matching NTU students into study groups based on module code, a shared day/start-time slot, and learning objectives. The UI is built with Pygame and the matching/export flow uses Pandas.

## Project files

| File | Purpose |
|---|---|
| `main.py` | App entrypoint and application coordinator |
| `ui_widgets.py` | Reusable Pygame widgets such as input boxes, checkboxes, dropdowns, and buttons |
| `ui_panels.py` | OOP panel/view classes for the form, student pool, and match results |
| `engine.py` | Matching engine and `Student` data model |
| `requirements.txt` | Python dependencies |

## Setup

1. Check Python:
```powershell
python --version
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Launch the app:
```powershell
python main.py
```

## How to use

Fill in:
- `First Name`
- `Last Name`
- `Module Code`
- `Telehandle`
- `Day`
- `Start Time`
- `End Time`
- one or more learning objectives

Click `Submit` to find matches.

The app:
- combines first and last name into one student record
- uses `"{Day} {Start Time}"` as the exact key passed into `MatchingEngine`
- keeps the full display range like `Mon 6PM-8PM` for the UI and Excel export
- shows match cards with the student name, Telegram handle, module, slot, and shared objectives

## Matching rules

The engine compares:
- module code
- exact matching slot in the form `Day + Start Time`
- objective overlap

The engine still ranks internally with:
```text
score = (time_overlap * 0.7) + (objective_overlap * 0.3)
```

But the UI does not display the score anymore. It displays the matched student's Telegram handle instead.

## Student Pool

Before submission, the right panel shows the `Student Pool`.

It includes:
- Name
- Module
- Slot
- Telehandle

The pool supports mouse-wheel scrolling when there are more rows than fit on screen.

## Excel export

Click `Export to Excel` or press `E` to export the pool.

Export details:
- Workbook filename: `student_data.xlsx`
- Worksheet name: `student_data`
- If `student_data.xlsx` is open in Excel and locked, the app saves a fallback file like `student_data_YYYYMMDD_HHMMSS.xlsx`

## Seed data

The mock pool uses NTU-style modules only:
- `CV1014`
- `MH1811`
- `CV2020`
- `CV1011`
- `CV2002`
