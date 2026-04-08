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
| `students.xlsx` | Student database — auto-created on first run with seed data |
| `study_groups.xlsx` | Sorted Excel export — generated when you press E |
| `requirements.txt` | Python dependencies |

---

## How to run — normal setup

**1. Make sure you have Python 3.8 or later**
```
python --version
```

**2. Install dependencies**
```
pip install pygame pandas openpyxl
```

**3. Launch the app**
```
python main.py
```

A window opens immediately. `students.xlsx` is created automatically on first run with 20 pre-loaded students so you have data to match against straight away.

---

## How to run — Spyder (lab setting)

Pygame conflicts with Spyder's IPython console. You need to tell Spyder to run the script in an external terminal instead.

**One-time setup:**
1. Open `main.py` in Spyder
2. Go to **Run → Configuration per file** (or press `F6`)
3. Under *Console*, select **Execute in an external system terminal**
4. Click **OK**

**Every time you want to run it:**
- Press **F5** — a separate terminal and Pygame window will open automatically

**Installing dependencies in the lab:**

Open **Anaconda Prompt** from the Start menu and run:
```
pip install pygame-ce pandas openpyxl
```
If Anaconda Prompt is unavailable, go to **View → Panes → Terminal** inside Spyder and run the same command there.

> Note: `pygame-ce` is a drop-in replacement for `pygame` — same import, no code changes needed. Use it if `pip install pygame` fails on your Python version.

---

## How to use the app

### Left panel — Student Pool
- Displays all registered students as a scrollable table
- **Scroll with the mouse wheel** to see more rows
- Updates live every time a new student submits their details

### Right panel — Register & Match

1. **Fill in the four input fields:**
   - **Full Name** — your name
   - **Module Code** — e.g. `CS2040S`, `DSA1101`
   - **Available Times** — comma-separated, e.g. `Mon 6PM, Wed 6PM, Fri 6PM`
   - **Learning Objectives** — comma-separated, e.g. `Concept understanding, Tutorial Help`

2. Click **Submit & Match**

3. Your top 3 most compatible study partners appear on screen, each showing:
   - Compatibility score with a visual bar
   - Shared available time slots
   - Shared learning objectives

4. Your entry is saved to `students.xlsx` automatically

### Controls

| Key / Button | Action |
|---|---|
| `Submit & Match` | Register and find matches |
| `Clear Fields` | Wipe all input boxes |
| `Export to Excel` or `E` | Save a sorted copy of the pool to `study_groups.xlsx` |
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

A score of `0.0` is returned immediately if the courses differ or if there is no shared time slot at all.
