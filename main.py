"""
main.py  —  AcadAlliance Desktop Application
CV1014 / AY25S2 Mini Project  —  Study Group Matching System (Theme P)

HOW TO RUN:
    python main.py

DEPENDENCIES (install with: pip install pygame pandas openpyxl):
    pygame      — graphical window, event loop, drawing
    pandas      — CSV student database + Excel export
    openpyxl    — Excel (.xlsx) writer backend used by pandas

HOW engine.py IS CONNECTED:
    Line 1  — `from engine import Student, MatchingEngine`
    Every time the user clicks Submit, we build a Student object from the
    input boxes and pass it to MatchingEngine.find_best_matches().
    No changes to engine.py are required; this file is purely the UI layer.
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
MAP_IMAGE_FILE  = "campus_map.png"      # place this image in the project folder
DATABASE_FILE   = "students.csv"        # pandas CSV — persists registrations
EXPORT_FILE     = "study_groups.xlsx"   # output file written by the export function


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

        # ── Map state ────────────────────────────────────────
        self.map_image   = self._load_map_image()
        self.map_rect    = pygame.Rect(10, 50, MAP_W - 20, WINDOW_H - 60)
        self.map_click: Optional[Tuple[int, int]] = None  # last click coords

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
        Read students.csv with pandas on startup.
        If the file does not exist yet, return the built-in seed pool.

        Using pandas here satisfies the assignment's data-processing
        requirement: the DataFrame gives us searching and sorting for free.
        """
        if os.path.exists(DATABASE_FILE):
            df = pd.read_csv(DATABASE_FILE)
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

        # Seed data — used the first time the app runs (no CSV exists yet)
        return [
            Student("Alice",   "CS2040S", {"Mon 6PM", "Wed 6PM"},            {"Concept understanding"}),
            Student("Bob",     "CS2040S", {"Mon 6PM", "Wed 6PM", "Fri 6PM"}, {"Concept understanding", "Tutorial Help"}),
            Student("Charlie", "CS2040S", {"Tue 6PM", "Thu 6PM"},            {"Exam paper practice"}),
            Student("Diana",   "DSA1101", {"Mon 6PM", "Wed 6PM"},            {"Concept understanding"}),
            Student("Eve",     "CS2040S", {"Wed 6PM", "Fri 6PM"},            {"Tutorial Help", "Exam paper practice"}),
            Student("Ivan",    "CS2040S", {"Mon 6PM", "Wed 6PM"},            {"Concept understanding", "Exam paper practice"}),
            Student("Judy",    "DSA1101", {"Mon 6PM", "Wed 6PM", "Fri 6PM"}, {"Concept understanding", "Tutorial Help"}),
        ]

    def _save_to_database(self, student: Student) -> None:
        """
        Append one student record to students.csv using pandas.
        If the file doesn't exist it is created with a header row.
        """
        new_row = pd.DataFrame([{
            "name":       student.name,
            "course":     student.course,
            "time_slots": ", ".join(sorted(student.time_slots)),
            "objectives": ", ".join(sorted(student.objectives)),
        }])
        # mode="a" appends; header=False skips re-writing the column names
        write_header = not os.path.exists(DATABASE_FILE)
        new_row.to_csv(DATABASE_FILE, mode="a", header=write_header, index=False)

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

    def _load_map_image(self) -> Optional[pygame.Surface]:
        """Load campus_map.png. Returns None if the file is absent."""
        if os.path.exists(MAP_IMAGE_FILE):
            return pygame.image.load(MAP_IMAGE_FILE).convert()
        return None

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
            placeholder="e.g. Daniel Wong"
        )
        y += 80

        self.box_course = InputBox(
            cx, y + 22, w, 38,
            label="Module Code",
            placeholder="e.g. CS2040S"
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
        self.btn_submit = Button(cx,           y, half, 42, "Submit & Match",
                                  color=BLUE, hover_color=BLUE_DARK)
        self.btn_clear  = Button(cx + half + 8, y, half, 42, "Clear Fields",
                                  color=(160, 70, 70), hover_color=(130, 45, 45))
        self.btn_export = Button(cx,           y + 52, w, 38, "Export to Excel  [E]",
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

                # Map click: record (x, y) relative to the map image origin
                if self.map_rect.collidepoint(event.pos):
                    self.map_click = (
                        event.pos[0] - self.map_rect.x,
                        event.pos[1] - self.map_rect.y,
                    )

                # Button clicks
                if self.btn_submit.is_clicked(event):
                    self._on_submit()
                if self.btn_clear.is_clicked(event):
                    self._on_clear()
                if self.btn_export.is_clicked(event):
                    self._export_to_excel()

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
        self._save_to_database(new_student)
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
        self._draw_map_panel()
        self._draw_divider()
        self._draw_control_panel()
        pygame.display.flip()   # push the completed frame to the screen

    def _draw_map_panel(self) -> None:
        """
        Render the campus map on the left half of the window.

        If campus_map.png is present it is scaled to fill the panel.
        Otherwise a placeholder rectangle is drawn with instructions.
        After a click, a red dot is drawn at the clicked position and
        the (x, y) coordinates are displayed next to it.
        """
        # Panel title above the map
        title = self.font_small.render(
            "Campus Map  —  click anywhere to capture location", True, MID_GREY
        )
        self.screen.blit(title, (10, 28))

        # Map area background
        pygame.draw.rect(self.screen, MAP_BG, self.map_rect, border_radius=8)

        if self.map_image:
            # Scale the image to fit the panel (may distort — swap for aspect-ratio
            # preserving logic if your supervisor expects a clean map display)
            scaled = pygame.transform.scale(
                self.map_image,
                (self.map_rect.w, self.map_rect.h)
            )
            self.screen.blit(scaled, self.map_rect.topleft)
        else:
            # Placeholder text — remove once campus_map.png is added
            hint = self.font_body.render(
                "Add campus_map.png to the project folder", True, MID_GREY
            )
            self.screen.blit(hint, hint.get_rect(center=self.map_rect.center))

        # Map border
        pygame.draw.rect(self.screen, LIGHT_GREY, self.map_rect, 2, border_radius=8)

        # Draw the clicked-coordinate marker
        if self.map_click:
            dot_x = self.map_rect.x + self.map_click[0]
            dot_y = self.map_rect.y + self.map_click[1]
            pygame.draw.circle(self.screen, ACCENT, (dot_x, dot_y), 9)
            pygame.draw.circle(self.screen, WHITE,  (dot_x, dot_y), 5)
            label = self.font_small.render(
                f"({self.map_click[0]}, {self.map_click[1]})", True, ACCENT
            )
            self.screen.blit(label, (dot_x + 12, dot_y - 10))

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
