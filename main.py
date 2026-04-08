"""
main.py  —  AcadAlliance Desktop Application
CV1014 / AY25S2 Mini Project  —  Study Group Matching System (Theme P)

HOW TO RUN:
    python main.py

DEPENDENCIES (install with: pip install pygame pandas openpyxl):
    pygame      — graphical window, event loop, drawing
    pandas      — Excel student database + export
    openpyxl    — Excel (.xlsx) read/write backend used by pandas

HOW engine.py IS CONNECTED:
    Line 1  — `from engine import Student, MatchingEngine`
    Every time the user clicks Submit, we build a Student object from the
    input boxes and pass it to MatchingEngine.find_best_matches().
    No changes to engine.py are required; this file is purely the UI layer.

DATABASE:
    students.xlsx is the single source of truth for all registered students.
    It is created automatically with fake seed data on first run, and is
    updated every time a new student submits their details.
    Press E (or click Export) to write a sorted copy to study_groups.xlsx.
"""

import os
import sys
import pygame
import pandas as pd

# ── Import the matching engine written by the team ──────────────────────────
# engine.py must be in the same folder as this file.
# Student  : dataclass that holds one student's data
# MatchingEngine : calculates compatibility scores and returns ranked matches
from engine import Student, MatchingEngine

# Python 3.8 compatibility — use typing module instead of built-in generics
from typing import List, Tuple, Optional


# ============================================================
#  CONSTANTS
# ============================================================

WINDOW_W, WINDOW_H = 1280, 800
FPS = 60

# ── Colour palette (R, G, B) ────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (10,  10,  10)
DARK_GREY  = (45,  45,  45)
MID_GREY   = (130, 130, 130)
LIGHT_GREY = (210, 210, 210)
PANEL_BG   = (245, 247, 250)
MAP_BG     = (215, 222, 230)
BLUE       = (50,  115, 200)
BLUE_DARK  = (30,   85, 160)
GREEN      = (55,  175,  95)
GREEN_DARK = (35,  140,  70)
RED        = (210,  60,  60)
ACCENT     = (255, 165,   0)   # orange — used for the map coordinate dot

# ── Layout: left panel = map, right panel = controls ────────
MAP_W     = 580                         # width of the map panel
CTRL_X    = MAP_W + 12                  # left edge of the control panel
CTRL_W    = WINDOW_W - CTRL_X - 12     # width of the control panel

# ── Files ───────────────────────────────────────────────────
DATABASE_FILE   = "students.xlsx"       # pandas Excel database — persists registrations
EXPORT_FILE     = "study_groups.xlsx"   # sorted export written when user presses E

# ── Table display ────────────────────────────────────────────
TABLE_COL_WIDTHS = [160, 90, 175, 175]
TABLE_HEADERS    = ["Name", "Course", "Available Times", "Objectives"]
TABLE_ROW_H      = 24   # height of each row in the table
TABLE_SCROLL_SPD = 3    # rows scrolled per mouse-wheel tick


# ============================================================
#  HELPER WIDGET: InputBox
# ============================================================

class InputBox:
    """
    A single-line text input rendered entirely with Pygame primitives.

    DECOMPOSITION — all text-entry logic is isolated here so the main
    event loop only needs to forward events; it never handles raw
    keystrokes itself.

    Usage:
        box = InputBox(x, y, width, height, label="Name", placeholder="...")
        # inside the event loop:
        box.handle_event(event)
        # inside the draw call:
        box.draw(screen)
        # to read the value:
        value = box.get_value()
    """

    # Shared font objects — created once when the first box is instantiated
    _font_label: Optional[pygame.font.Font] = None
    _font_text:  Optional[pygame.font.Font] = None

    def __init__(self, x: int, y: int, w: int, h: int,
                 label: str = "", placeholder: str = ""):
        self.rect        = pygame.Rect(x, y, w, h)
        self.label       = label
        self.placeholder = placeholder
        self.text        = ""        # the string the user has typed so far
        self.active      = False     # True when this box has keyboard focus

        # Lazy-initialise shared fonts (pygame.font must be init'd first)
        if InputBox._font_label is None:
            InputBox._font_label = pygame.font.SysFont("segoeui", 14, bold=True)
            InputBox._font_text  = pygame.font.SysFont("segoeui", 16)

    # ── Event handling ───────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Process one pygame event.

        MOUSE click  → activate this box if the click lands inside it,
                        deactivate it if the click is elsewhere.
        KEYDOWN      → only act when this box is active (has focus).
                        BACKSPACE deletes the last character.
                        RETURN / TAB are intentionally ignored so they
                        don't insert whitespace.
                        Any other key appends event.unicode to self.text.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # collidepoint returns True if the click position is inside self.rect
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                # Remove the last character (slicing to [:-1] is safe on empty str)
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                pass  # swallow these keys — they are handled at app level
            else:
                # event.unicode is the printable character for this key press,
                # already accounting for shift / caps lock / locale.
                self.text += event.unicode

    # ── Rendering ────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        """Render the label above the box, then the box itself with its text."""
        # Label sits 22 px above the box
        if self.label:
            label_surf = self._font_label.render(self.label, True, DARK_GREY)
            surface.blit(label_surf, (self.rect.x, self.rect.y - 22))

        # Fill the box background
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)

        # Border: bright blue when focused, light grey when idle
        border_col = BLUE if self.active else LIGHT_GREY
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)

        # Render typed text, or the placeholder in grey if the box is empty
        if self.text:
            txt_surf = self._font_text.render(self.text, True, DARK_GREY)
        else:
            txt_surf = self._font_text.render(self.placeholder, True, MID_GREY)

        # Vertically centre the text inside the box and add 8 px left padding
        ty = self.rect.y + (self.rect.h - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (self.rect.x + 8, ty))

    # ── Value access ─────────────────────────────────────────

    def get_value(self) -> str:
        """Return the current text with leading/trailing whitespace removed."""
        return self.text.strip()

    def clear(self) -> None:
        self.text   = ""
        self.active = False


# ============================================================
#  HELPER WIDGET: Button
# ============================================================

class Button:
    """
    A clickable rectangle with a text label and a hover colour change.

    Usage:
        btn = Button(x, y, w, h, "Label")
        btn.draw(screen)
        if btn.is_clicked(event):
            do_something()
    """

    _font: Optional[pygame.font.Font] = None

    def __init__(self, x: int, y: int, w: int, h: int, text: str,
                 color: tuple = BLUE, hover_color: tuple = BLUE_DARK):
        self.rect        = pygame.Rect(x, y, w, h)
        self.text        = text
        self.color       = color
        self.hover_color = hover_color

        if Button._font is None:
            Button._font = pygame.font.SysFont("segoeui", 16, bold=True)

    def draw(self, surface: pygame.Surface) -> None:
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        fill    = self.hover_color if hovered else self.color
        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        txt  = self._font.render(self.text, True, WHITE)
        pos  = txt.get_rect(center=self.rect.center)
        surface.blit(txt, pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Return True only on a left-button-down event inside the button."""
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# ============================================================
#  MAIN APPLICATION
# ============================================================

class StudyGroupApp:
    """
    Top-level application class.

    ABSTRACTION — the outside world (main()) only calls app.run().
    All Pygame lifecycle details (init, event loop, render, quit) are
    hidden inside this class.

    DECOMPOSITION — each responsibility lives in its own method:
        _build_ui()          creates all widgets
        handle_events()      routes pygame events to the right handler
        _on_submit()         validates input → builds Student → runs engine
        _export_to_excel()   pandas export
        draw()               master render, delegates to sub-draw methods
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("AcadAlliance — Study Group Matcher  |  CV1014")
        self.clock  = pygame.time.Clock()

        # ── Fonts ───────────────────────────────────────────
        self.font_title  = pygame.font.SysFont("segoeui", 24, bold=True)
        self.font_body   = pygame.font.SysFont("segoeui", 15)
        self.font_small  = pygame.font.SysFont("segoeui", 13)
        self.font_mono   = pygame.font.SysFont("consolas", 13)

        # ── Matching engine (imported from engine.py) ────────
        # MatchingEngine is instantiated once and reused for every submission.
        # Weights: time overlap counts for 70%, objective overlap for 30%.
        self.engine = MatchingEngine(time_weight=0.7, objective_weight=0.3)

        # ── Student pool ─────────────────────────────────────
        # PATTERN RECOGNITION — the pool grows with every new submission,
        # so each new student is automatically visible to future searchers.
        # We seed it from a CSV file so data persists between app sessions.
        self.student_pool: List[Student] = self._load_database()

        # ── Match results (populated after Submit) ───────────
        self.match_results: List[Tuple[Student, float]] = []
        self.last_student: Optional[Student] = None

        # ── Database table view state ─────────────────────────
        self.table_scroll = 0   # how many rows have been scrolled down

        # ── Status bar ───────────────────────────────────────
        self.status_msg   = "Enter your details and click Submit to find study partners."
        self.status_color = MID_GREY

        # Build all widgets
        self._build_ui()

    # ──────────────────────────────────────────────────────────
    #  DATABASE (pandas)
    # ──────────────────────────────────────────────────────────

    def _load_database(self) -> List[Student]:
        """
        Read students.xlsx with pandas on startup.
        If the file does not exist, create it with fake seed data and save it
        so the Excel file is always present and viewable from the first run.

        Using pandas here satisfies the assignment's data-processing requirement:
        the DataFrame gives us searching and sorting for free.
        """
        if os.path.exists(DATABASE_FILE):
            df = pd.read_excel(DATABASE_FILE)
            pool = []
            for _, row in df.iterrows():
                # Split the stored comma-separated strings back into sets
                times = {t.strip() for t in str(row["time_slots"]).split(",") if t.strip()}
                objs  = {o.strip() for o in str(row["objectives"]).split(",")  if o.strip()}
                pool.append(Student(
                    name=str(row["name"]),
                    course=str(row["course"]),
                    time_slots=times,
                    objectives=objs,
                ))
            return pool

        # ── Seed data ────────────────────────────────────────────────────────
        # Used the first time the app runs (no Excel file exists yet).
        # 20 fake students across 5 NTU courses with varied times and objectives
        # so the matching engine has enough data to produce meaningful results.
        seed = [
            # CV1014 — Introduction to Computational Thinking
            Student("Alice Tan",     "CV1014",  {"Mon 6PM", "Wed 6PM"},              {"Concept understanding"}),
            Student("Bob Lim",       "CV1014",  {"Mon 6PM", "Wed 6PM", "Fri 6PM"},   {"Concept understanding", "Tutorial Help"}),
            Student("Charlie Ng",    "CV1014",  {"Tue 6PM", "Thu 6PM"},              {"Exam paper practice"}),
            Student("Eve Wong",      "CV1014",  {"Wed 6PM", "Fri 6PM"},              {"Tutorial Help", "Exam paper practice"}),
            Student("Ivan Goh",      "CV1014",  {"Mon 6PM", "Wed 6PM"},              {"Concept understanding", "Exam paper practice"}),
            Student("Karen Yeo",     "CV1014",  {"Tue 6PM", "Thu 6PM"},              {"Concept understanding", "Tutorial Help"}),
            Student("Marcus Lee",    "CV1014",  {"Mon 6PM", "Fri 6PM"},              {"Exam paper practice"}),
            Student("Nina Chua",     "CV1014",  {"Wed 6PM", "Thu 6PM"},              {"Concept understanding"}),
            # MH1811 — Calculus
            Student("Diana Ho",      "MH1811",  {"Mon 6PM", "Wed 6PM"},              {"Concept understanding"}),
            Student("Judy Koh",      "MH1811",  {"Mon 6PM", "Wed 6PM", "Fri 6PM"},   {"Concept understanding", "Tutorial Help"}),
            Student("Omar Rashid",   "MH1811",  {"Tue 6PM", "Sat 10AM"},             {"Tutorial Help", "Exam paper practice"}),
            Student("Priya Nair",    "MH1811",  {"Wed 6PM", "Fri 6PM"},              {"Concept understanding", "Exam paper practice"}),
            # CV2020 — Engineering Mechanics
            Student("Frank Ong",     "CV2020",  {"Mon 6PM"},                         {"Concept understanding"}),
            Student("Grace Tan",     "CV2020",  {"Mon 6PM", "Wed 6PM"},              {"Tutorial Help"}),
            Student("Henry Sim",     "CV2020",  {"Tue 6PM", "Thu 6PM"},              {"Concept understanding", "Exam paper practice"}),
            # MH1812 — Discrete Mathematics
            Student("Heidi Chan",    "MH1812",  {"Mon 6PM", "Tue 6PM"},              {"Exam paper practice"}),
            Student("Leo Tay",       "MH1812",  {"Mon 6PM", "Wed 6PM"},              {"Concept understanding", "Tutorial Help"}),
            Student("Megan Foo",     "MH1812",  {"Tue 6PM", "Thu 6PM"},              {"Tutorial Help"}),
            # CV1011 — Fundamentals of Civil and Environmental Engineering
            Student("Samuel Liew",   "CV1011",  {"Tue 6PM", "Thu 6PM"},              {"Concept understanding", "Exam paper practice"}),
            Student("Rachel Koh",    "CV1011",  {"Tue 6PM"},                         {"Tutorial Help"}),
        ]
        # Write seed data to Excel immediately so the file exists from first run
        self._write_pool_to_excel(seed)
        return seed

    def _write_pool_to_excel(self, pool: List[Student]) -> None:
        """
        Overwrite students.xlsx with the entire pool.
        Called both when seeding on first run and after each new registration.
        Excel does not support row-level appending, so we rewrite the whole file.
        """
        rows = [{
            "name":       s.name,
            "course":     s.course,
            "time_slots": ", ".join(sorted(s.time_slots)),
            "objectives": ", ".join(sorted(s.objectives)),
        } for s in pool]
        pd.DataFrame(rows).to_excel(DATABASE_FILE, index=False)

    def _save_to_database(self) -> None:
        """
        Persist the current student pool to students.xlsx.
        We rewrite the entire file because Excel does not support append mode.
        """
        self._write_pool_to_excel(self.student_pool)

    def _export_to_excel(self) -> None:
        """
        Write the entire student pool to study_groups.xlsx with pandas.

        ALGORITHM DESIGN — before exporting we sort the pool by course then
        name using DataFrame.sort_values(), producing a neatly ordered sheet.

        Keyboard shortcut: press E at any time to trigger this.
        """
        if not self.student_pool:
            self._set_status("Nothing to export — no students registered yet.", RED)
            return

        rows = []
        for s in self.student_pool:
            rows.append({
                "Name":            s.name,
                "Course":          s.course,
                "Available Times": ", ".join(sorted(s.time_slots)),
                "Objectives":      ", ".join(sorted(s.objectives)),
            })

        df = pd.DataFrame(rows)
        # Sort by course first, then alphabetically by name — demonstrates sorting
        df = df.sort_values(by=["Course", "Name"]).reset_index(drop=True)
        df.to_excel(EXPORT_FILE, index=False)
        self._set_status(
            f"Exported {len(rows)} student(s) to {EXPORT_FILE}  (press E to refresh)",
            GREEN
        )

    # ──────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """
        Instantiate every widget and calculate its screen position.

        DECOMPOSITION — widget creation is separated from the event loop
        and the render loop.  Each widget knows how to draw and handle
        its own events; this method is the wiring.
        """
        cx = CTRL_X        # left edge of the control panel
        w  = CTRL_W - 4    # usable width inside the panel
        y  = 90            # running vertical cursor (starts below the title)

        # ── Four input boxes ─────────────────────────────────
        # Each box is 38 px tall; label sits 22 px above it.
        # Vertical gap between boxes: 30 px after the box itself.

        self.box_name = InputBox(
            cx, y + 22, w, 38,
            label="Full Name",
            placeholder="e.g. John Tan"
        )
        y += 80

        self.box_course = InputBox(
            cx, y + 22, w, 38,
            label="Module Code",
            placeholder="e.g. CV1014"
        )
        y += 80

        self.box_times = InputBox(
            cx, y + 22, w, 38,
            label="Available Times  (comma-separated)",
            placeholder="Mon 6PM, Wed 6PM, Fri 6PM"
        )
        y += 80

        self.box_objectives = InputBox(
            cx, y + 22, w, 38,
            label="Learning Objectives  (comma-separated)",
            placeholder="Concept understanding, Tutorial Help"
        )
        y += 80

        # Keep all boxes in a list so we can forward events with one loop
        self.all_boxes = [
            self.box_name,
            self.box_course,
            self.box_times,
            self.box_objectives,
        ]

        # ── Buttons ──────────────────────────────────────────
        half = (w - 8) // 2
        self.btn_submit = Button(cx,            y, half, 42, "Submit & Match",
                                  color=BLUE, hover_color=BLUE_DARK)
        self.btn_clear  = Button(cx + half + 8, y, half, 42, "Clear Fields",
                                  color=(160, 70, 70), hover_color=(130, 45, 45))
        self.btn_export = Button(cx,            y + 52, w, 38, "Export to Excel  [E]",
                                  color=GREEN, hover_color=GREEN_DARK)

        # y position where the status line and results begin
        self.status_y  = y + 102
        self.results_y = y + 128

    # ──────────────────────────────────────────────────────────
    #  EVENT LOOP
    # ──────────────────────────────────────────────────────────

    def handle_events(self) -> None:
        """
        Drain the pygame event queue and dispatch each event.

        THE EVENT LOOP EXPLAINED:
        pygame.event.get() returns every event that occurred since the
        last call (mouse moves, key presses, window close, etc.).
        We iterate over them one by one:

          1. QUIT           → clean shutdown
          2. KEYDOWN        → global hotkeys (E = export, ESC = quit),
                              then each InputBox gets the same event so
                              the focused one can consume the keystroke.
          3. MOUSEBUTTONDOWN→ check whether the click hit the map area,
                              then let InputBox widgets toggle focus,
                              then check Submit / Clear / Export buttons.

        Importantly, we pass EVERY event to EVERY input box.
        Each box internally checks whether it is active before acting,
        so there is no risk of two boxes receiving the same keystroke.
        """
        for event in pygame.event.get():

            # ── 1. Window close ──────────────────────────────
            if event.type == pygame.QUIT:
                self._quit()

            # ── 2. Keyboard ──────────────────────────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    # 'E' triggers the pandas Excel export from anywhere
                    self._export_to_excel()
                elif event.key == pygame.K_ESCAPE:
                    self._quit()

            # Forward every event to every input box.
            # Each box's handle_event() checks internally whether it is
            # active before processing keystrokes.
            for box in self.all_boxes:
                box.handle_event(event)

            # ── 3. Mouse clicks ──────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_submit.is_clicked(event):
                    self._on_submit()
                if self.btn_clear.is_clicked(event):
                    self._on_clear()
                if self.btn_export.is_clicked(event):
                    self._export_to_excel()

            # ── 4. Mouse wheel: scroll the database table ─────
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self.student_pool) - 1)
                self.table_scroll = max(0, min(
                    self.table_scroll - event.y * TABLE_SCROLL_SPD,
                    max_scroll
                ))

    # ──────────────────────────────────────────────────────────
    #  SUBMIT HANDLER  (UI → engine bridge)
    # ──────────────────────────────────────────────────────────

    def _on_submit(self) -> None:
        """
        Read all input boxes, validate, build a Student, run the engine.

        THIS IS WHERE engine.py IS HOOKED UP:
            1. We parse the raw strings from the input boxes.
            2. We construct a Student dataclass (defined in engine.py).
            3. We call engine.find_best_matches(student, pool) — this
               returns List[Tuple[Student, float]] sorted best-first.
            4. We store the results; the draw() call renders them.

        ALGORITHM DESIGN — validation before computation:
            - name and course must be non-empty (hard requirement).
            - at least one time slot must be provided, because the engine
              immediately returns 0.0 for any pair with no shared slots.
        """
        name      = self.box_name.get_value()
        course    = self.box_course.get_value().upper()
        times_raw = self.box_times.get_value()
        objs_raw  = self.box_objectives.get_value()

        # ── Validation ───────────────────────────────────────
        if not name:
            self._set_status("Please enter your name.", RED); return
        if not course:
            self._set_status("Please enter your module code.", RED); return
        if not times_raw:
            self._set_status("Please enter at least one available time slot.", RED); return

        # ── Parse comma-separated strings into sets ──────────
        # The engine expects Set[str], e.g. {"Mon 6PM", "Wed 6PM"}
        time_slots = {t.strip() for t in times_raw.split(",") if t.strip()}
        objectives = {o.strip() for o in objs_raw.split(",")  if o.strip()}

        # ── Build Student (from engine.py) ───────────────────
        new_student = Student(
            name=name,
            course=course,
            time_slots=time_slots,
            objectives=objectives,
        )

        # ── Add to pool & persist ────────────────────────────
        self.student_pool.append(new_student)
        self._save_to_database()
        self.last_student = new_student

        # ── Run the matching engine ──────────────────────────
        # find_best_matches() skips the student themselves (name equality check)
        # and only returns pairs with score > 0 (same course + shared time).
        self.match_results = self.engine.find_best_matches(
            new_student, self.student_pool, top_n=3
        )

        if self.match_results:
            self._set_status(
                f"Found {len(self.match_results)} match(es) for {name}!",
                GREEN
            )
        else:
            self._set_status(
                f"{name} added to pool. No matches yet — be the first in your course!",
                ACCENT
            )

    def _on_clear(self) -> None:
        """Reset all input boxes and clear the results panel."""
        for box in self.all_boxes:
            box.clear()
        self.match_results = []
        self.last_student  = None
        self._set_status("Fields cleared.", MID_GREY)

    def _set_status(self, msg: str, color: tuple) -> None:
        self.status_msg   = msg
        self.status_color = color

    # ──────────────────────────────────────────────────────────
    #  RENDER
    # ──────────────────────────────────────────────────────────

    def draw(self) -> None:
        """Master render — called once every frame. Delegates to sub-methods."""
        self.screen.fill(PANEL_BG)
        self._draw_database_table()
        self._draw_divider()
        self._draw_control_panel()
        pygame.display.flip()   # push the completed frame to the screen

    def _draw_database_table(self) -> None:
        """
        Render the student pool as a scrollable table in the left panel.

        ALGORITHM DESIGN — we compute a visible slice of self.student_pool
        using the scroll offset, then draw each row with alternating shading
        so the table is easy to read.

        Scroll with the mouse wheel when the table is visible.
        """
        panel = pygame.Rect(10, 80, MAP_W - 20, WINDOW_H - 90)
        pygame.draw.rect(self.screen, WHITE, panel, border_radius=8)
        pygame.draw.rect(self.screen, LIGHT_GREY, panel, 2, border_radius=8)

        # ── Header row ───────────────────────────────────────
        header_rect = pygame.Rect(panel.x, panel.y, panel.w, TABLE_ROW_H)
        pygame.draw.rect(self.screen, BLUE, header_rect,
                         border_top_left_radius=8, border_top_right_radius=8)

        x = panel.x + 6
        for header, col_w in zip(TABLE_HEADERS, TABLE_COL_WIDTHS):
            hdr_surf = self.font_small.render(header, True, WHITE)
            self.screen.blit(hdr_surf, (x, panel.y + 5))
            x += col_w

        # ── Data rows ────────────────────────────────────────
        # How many rows fit in the visible panel area
        visible_rows = (panel.h - TABLE_ROW_H) // TABLE_ROW_H
        start = int(self.table_scroll)
        end   = min(start + visible_rows, len(self.student_pool))

        for i, student in enumerate(self.student_pool[start:end]):
            row_y    = panel.y + TABLE_ROW_H + i * TABLE_ROW_H
            row_rect = pygame.Rect(panel.x, row_y, panel.w, TABLE_ROW_H)

            # Alternate row background colour for readability
            bg = (235, 240, 250) if i % 2 == 0 else WHITE
            pygame.draw.rect(self.screen, bg, row_rect)

            # Draw each cell, truncating text that is too wide for the column
            cells = [
                student.name,
                student.course,
                ", ".join(sorted(student.time_slots)),
                ", ".join(sorted(student.objectives)),
            ]
            x = panel.x + 6
            for cell, col_w in zip(cells, TABLE_COL_WIDTHS):
                txt  = cell if len(cell) <= 22 else cell[:20] + "\u2026"
                surf = self.font_small.render(txt, True, DARK_GREY)
                self.screen.blit(surf, (x, row_y + 5))
                x += col_w

        # ── Footer ───────────────────────────────────────────
        footer = self.font_small.render(
            f"Showing {start + 1}\u2013{end} of {len(self.student_pool)} students"
            "  |  scroll to see more",
            True, MID_GREY
        )
        self.screen.blit(footer, (panel.x + 6, panel.bottom - 20))

    def _draw_divider(self) -> None:
        """Vertical separator line between the two panels."""
        x = MAP_W + 6
        pygame.draw.line(self.screen, LIGHT_GREY, (x, 10), (x, WINDOW_H - 10), 2)

    def _draw_control_panel(self) -> None:
        """Render everything on the right: title, input boxes, buttons, results."""
        cx = CTRL_X

        # ── Title ────────────────────────────────────────────
        title = self.font_title.render("AcadAlliance", True, BLUE)
        self.screen.blit(title, (cx, 12))

        pool_count = self.font_small.render(
            f"Study Group Matching System  |  {len(self.student_pool)} student(s) in pool",
            True, MID_GREY
        )
        self.screen.blit(pool_count, (cx, 44))

        # ── Input boxes ──────────────────────────────────────
        for box in self.all_boxes:
            box.draw(self.screen)

        # ── Buttons ──────────────────────────────────────────
        self.btn_submit.draw(self.screen)
        self.btn_clear.draw(self.screen)
        self.btn_export.draw(self.screen)

        # ── Status message ───────────────────────────────────
        status_surf = self.font_small.render(self.status_msg, True, self.status_color)
        self.screen.blit(status_surf, (cx, self.status_y))

        # ── Match results ────────────────────────────────────
        if self.match_results and self.last_student:
            self._draw_results(cx)
        elif not self.match_results and self.last_student:
            hint = self.font_small.render(
                "No matches yet. More students need to register with the same course.",
                True, MID_GREY
            )
            self.screen.blit(hint, (cx, self.results_y))

    def _draw_results(self, cx: int) -> None:
        """
        Render the top-N match results as formatted text with score bars.

        PATTERN RECOGNITION — the same rendering pattern (header, bar, details)
        repeats for each match, so it is factored into one loop.
        """
        y = self.results_y
        s = self.last_student

        # Section header
        hdr = self.font_body.render(
            f"Top matches for {s.name}  ({s.course})", True, DARK_GREY
        )
        self.screen.blit(hdr, (cx, y))
        y += 22

        # Thin separator line
        pygame.draw.line(
            self.screen, LIGHT_GREY,
            (cx, y), (cx + CTRL_W - 4, y), 1
        )
        y += 8

        for rank, (match, score) in enumerate(self.match_results, start=1):
            shared_times = sorted(s.time_slots  & match.time_slots)
            shared_goals = sorted(s.objectives  & match.objectives)
            pct          = int(score * 100)

            # ── Rank line ────────────────────────────────────
            name_txt = self.font_mono.render(
                f"#{rank}  {match.name:<18}  {pct}%  compatible  |  {match.course}",
                True, BLUE
            )
            self.screen.blit(name_txt, (cx, y))
            y += 20

            # ── Score bar ────────────────────────────────────
            bar_total  = CTRL_W - 4
            bar_filled = int(bar_total * score)
            pygame.draw.rect(
                self.screen, LIGHT_GREY,
                pygame.Rect(cx, y, bar_total, 7), border_radius=3
            )
            pygame.draw.rect(
                self.screen, GREEN,
                pygame.Rect(cx, y, bar_filled, 7), border_radius=3
            )
            y += 14

            # ── Detail lines ─────────────────────────────────
            times_txt = self.font_small.render(
                f"  Shared slots : {', '.join(shared_times) or 'none'}",
                True, DARK_GREY
            )
            self.screen.blit(times_txt, (cx, y)); y += 18

            goals_txt = self.font_small.render(
                f"  Shared goals : {', '.join(shared_goals) or 'none'}",
                True, DARK_GREY
            )
            self.screen.blit(goals_txt, (cx, y)); y += 26

    # ──────────────────────────────────────────────────────────
    #  MAIN LOOP
    # ──────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        The application's main loop — runs until the user closes the window.

        Each iteration:
          1. handle_events() — process all queued input
          2. draw()          — render the current state to screen
          3. clock.tick(FPS) — cap the frame rate to avoid burning CPU
        """
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

    def _quit(self) -> None:
        pygame.quit()
        sys.exit()


# ============================================================
#  ENTRY POINT
# ============================================================

def main() -> None:
    app = StudyGroupApp()
    app.run()


if __name__ == "__main__":
    main()
