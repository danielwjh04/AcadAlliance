# AcadAlliance

## Study Group Matching System

AcadAlliance is a desktop study group matching application built with Python, Pygame, and Pandas. It provides a custom GUI for entering learner profiles, comparing compatible study preferences, and exporting the active student pool to Excel.

## Features

- Custom Pygame interface with form inputs, checkboxes, dropdowns, and result panels
- Scrollable 24-hour time selectors covering `12AM` through `11PM`
- Pandas-powered export pipeline for saving student data to Excel
- Matching engine that ranks compatible students by shared availability and learning objectives
- Dynamic right-side panel that switches between the student pool and match results
- Telegram handle support for contact-friendly match results

## Requirements

- Python 3.10 or newer recommended
- `pygame`
- `pandas`
- `openpyxl`

## Installation

### VS Code Setup

1. Open a terminal in the folder where you want the project.
2. Clone the repository:

```powershell
git clone https://github.com/danielwjh04/AcadAlliance.git
cd AcadAlliance
```

3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:

```powershell
pip install pygame pandas openpyxl
```

If you prefer the project dependency file, you can use:

```powershell
pip install -r requirements.txt
```

5. Run the application:

```powershell
python main.py
```

### Spyder (Anaconda) Setup

1. Open Anaconda Prompt.
2. Clone the repository and move into the project folder:

```powershell
git clone https://github.com/danielwjh04/AcadAlliance.git
cd AcadAlliance
```

3. Install the required packages into the environment used by Spyder:

```powershell
pip install pygame pandas openpyxl
```

You can also install from the dependency file:

```powershell
pip install -r requirements.txt
```

4. Launch Spyder from the same environment:

```powershell
spyder
```

5. In Spyder, open `main.py`.
6. Go to `Run -> Configuration per file`.
7. Set the file to run in an external system terminal for best Pygame compatibility.
8. Run the file with `F5`.

## How To Use

1. Enter `First Name`, `Last Name`, `Module Code`, and `Telehandle`.
2. Choose a `Day`, `Start Time`, and `End Time`.
3. Select one or more learning objectives.
4. Click `Submit` to add the profile and view the best matches.
5. Review matches on the right panel, including Telegram handles for quick contact.
6. Click `Export to Excel` or press `E` to save the current student pool to `student_data.xlsx`.
7. Click `Clear` to reset the form and start a new submission.

## Controls

| Control | Action |
| --- | --- |
| `Submit` button | Validates the form, adds the student to the pool, and shows the best matches |
| `Clear` button | Resets all form fields and returns the app to a fresh entry state |
| `Export to Excel` button | Exports the current student pool to `student_data.xlsx` |
| `E` key | Triggers Excel export when a text input field is not active |
| Mouse wheel on open dropdown | Scrolls through time options in the 24-hour dropdown list |
| Mouse wheel on Student Pool | Scrolls the student table when there are more rows than fit on screen |

## File Overview

- `main.py`: Starts the application, manages the seeded student pool, handles submission and export actions, and coordinates the GUI state.
- `engine.py`: Defines the `Student` model and the matching engine that calculates compatibility scores and returns ranked matches.

## Export Output

- Excel filename: `student_data.xlsx`
- Worksheet name: `student_data`

If the Excel file is already open in another program, the application automatically saves a timestamped fallback copy instead.
