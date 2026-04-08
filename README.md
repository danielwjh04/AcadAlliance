# AcadAlliance — Study Group Matching System
A Python desktop app that matches NTU students into compatible study groups based on shared module, availability, and learning objectives — built with Pygame and Pandas.

---

## What it does

AcadAlliance matches NTU students into compatible study groups based on:
- **Module code** — only students in the same course are compared
- **Available time slots** — weighted at 70% of the compatibility score
- **Learning objectives** — weighted at 30% of the compatibility score

---

## Project files

| File | Purpose |
|---|---|
| `main.py` | Pygame desktop application — run this to launch the app |
| `engine.py` | Matching engine — compatibility scoring logic |
| `students.csv` | Auto-generated student database (created on first Submit) |
| `study_groups.xlsx` | Excel export (generated when you press E) |
| `campus_map.png` | Place your campus map image here (optional) |
| `requirements.txt` | Python dependencies |

---

## Setup

**1. Make sure you have Python 3.8 or later**
```
python --version
```

**2. Install dependencies**
```
pip install pygame pandas openpyxl
```

**3. (Optional) Add a campus map**

Place any image named `campus_map.png` in the project folder.
The app runs fine without it — a placeholder panel is shown instead.

**4. Run the app**
```
python main.py
```

---

## How to use the app

### Registering and finding matches

1. **Fill in the four input fields** on the right panel:
   - **Full Name** — your name
   - **Module Code** — e.g. `CS2040S`, `DSA1101`
   - **Available Times** — comma-separated, e.g. `Mon 6PM, Wed 6PM, Fri 6PM`
   - **Learning Objectives** — comma-separated, e.g. `Concept understanding, Tutorial Help, Exam paper practice`

2. Click **Submit & Match**

3. Your top 3 most compatible study partners are displayed on screen, showing:
   - Compatibility score (with a visual score bar)
   - Shared available time slots
   - Shared learning objectives

4. Your registration is automatically saved to `students.csv` so you appear in future searches.

### Map panel

- Click anywhere on the campus map (left side of the screen)
- The app captures and displays the `(x, y)` pixel coordinates of your click

### Exporting data

- Press **`E`** on your keyboard, or click the **Export to Excel** button
- All registered students are saved to `study_groups.xlsx`, sorted by course then name
- Open the file in Excel or Google Sheets to view the full database

### Other controls

| Key / Button | Action |
|---|---|
| `Submit & Match` | Register and find matches |
| `Clear Fields` | Wipe all input boxes |
| `Export to Excel` or `E` | Save database to .xlsx |
| `ESC` | Quit the application |

---

## Available time slot format

Use this exact format when entering times so students match correctly:

```
Mon 6PM, Tue 6PM, Wed 6PM, Thu 6PM, Fri 6PM, Sat 10AM, Sun 10AM
```

---

## Available learning objectives

```
Concept understanding, Tutorial Help, Exam paper practice
```

---

## How the matching score is calculated

```
score = (time_overlap × 0.7) + (objective_overlap × 0.3)
```

`time_overlap` and `objective_overlap` are each calculated as:
```
shared items ÷ smaller of the two sets
```

This means a student with limited availability is not penalised for matching
fully with someone who has wider availability. A score of `0.0` is returned
immediately if the courses differ or if there is no shared time slot at all.
