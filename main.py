"""
Refactored Pygame frontend for the study group matching system.

Run with:
    python main.py
"""

import sys
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import pygame

from engine import MatchingEngine, Student


WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 820
FPS = 60
EXPORT_FILE = "study_group_matches.xlsx"

FONT_NAME = "segoeui"

DAY_OPTIONS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
OBJECTIVE_OPTIONS = [
    "Concept understanding",
    "Tutorial Help",
    "Exam paper practice",
]


def build_time_options() -> List[str]:
    options: List[str] = []
    for hour in range(6, 23):
        suffix = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        options.append(f"{display_hour}{suffix}")
    return options


TIME_OPTIONS = build_time_options()
TIME_TO_ORDER = {label: index for index, label in enumerate(TIME_OPTIONS)}
DAY_TO_ORDER = {label: index for index, label in enumerate(DAY_OPTIONS)}


BACKGROUND = (243, 246, 251)
PANEL = (255, 255, 255)
PANEL_ALT = (248, 250, 253)
TEXT = (31, 41, 55)
TEXT_MUTED = (99, 115, 129)
BORDER = (207, 216, 228)
ACCENT = (46, 117, 184)
ACCENT_DARK = (31, 90, 145)
SUCCESS = (46, 125, 95)
WARNING = (209, 140, 59)
ERROR = (198, 70, 70)
BUTTON_NEUTRAL = (109, 122, 138)
CHECK_FILL = (66, 135, 245)
HOVER = (230, 239, 251)
OVERLAY_SHADOW = (218, 225, 236)


def parse_time_label(label: str) -> int:
    suffix = label[-2:]
    hour = int(label[:-2])
    if suffix == "AM":
        return 0 if hour == 12 else hour
    return 12 if hour == 12 else hour + 12


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    if not text:
        return []

    words = text.split()
    lines: List[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def build_record(
    name: str,
    course: str,
    day: str,
    start_time: str,
    end_time: str,
    objectives: Sequence[str],
) -> Dict[str, object]:
    return {
        "name": name,
        "course": course.upper(),
        "day": day,
        "start_time": start_time,
        "end_time": end_time,
        "matching_slot": f"{day} {start_time}",
        "objectives": list(objectives),
    }


def seed_records() -> List[Dict[str, object]]:
    return [
        build_record("Alice Tan", "CV1014", "Mon", "6PM", "8PM", ["Concept understanding"]),
        build_record(
            "Benjamin Lee",
            "CV1014",
            "Mon",
            "6PM",
            "9PM",
            ["Concept understanding", "Tutorial Help"],
        ),
        build_record("Chloe Goh", "CV1014", "Wed", "7PM", "9PM", ["Exam paper practice"]),
        build_record(
            "Darren Koh",
            "CV1014",
            "Mon",
            "6PM",
            "7PM",
            ["Tutorial Help", "Exam paper practice"],
        ),
        build_record("Eunice Lim", "CV1014", "Tue", "10AM", "12PM", ["Concept understanding"]),
        build_record(
            "Farah Noor",
            "CV2020",
            "Thu",
            "2PM",
            "4PM",
            ["Concept understanding", "Tutorial Help"],
        ),
        build_record("Gabriel Ong", "CV2020", "Thu", "2PM", "5PM", ["Tutorial Help"]),
        build_record("Hannah Teo", "CV2020", "Fri", "10AM", "12PM", ["Exam paper practice"]),
        build_record("Isaac Chua", "DSA1101", "Tue", "6PM", "8PM", ["Concept understanding"]),
        build_record(
            "Joanna Sim",
            "DSA1101",
            "Tue",
            "6PM",
            "9PM",
            ["Concept understanding", "Exam paper practice"],
        ),
        build_record("Kumar Raj", "MH1811", "Sat", "9AM", "11AM", ["Tutorial Help"]),
        build_record(
            "Li Wen",
            "MH1811",
            "Sat",
            "9AM",
            "12PM",
            ["Concept understanding", "Tutorial Help"],
        ),
    ]


class InputBox:
    label_font: Optional[pygame.font.Font] = None
    text_font: Optional[pygame.font.Font] = None

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        placeholder: str = "",
        max_length: int = 32,
    ) -> None:
        if InputBox.label_font is None:
            InputBox.label_font = pygame.font.SysFont(FONT_NAME, 14, bold=True)
            InputBox.text_font = pygame.font.SysFont(FONT_NAME, 18)

        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.active = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                return
            elif event.unicode and event.unicode.isprintable():
                if len(self.text) < self.max_length:
                    self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        label = self.label_font.render(self.label, True, TEXT)
        surface.blit(label, (self.rect.x, self.rect.y - 24))

        pygame.draw.rect(surface, PANEL, self.rect, border_radius=12)
        border_color = ACCENT if self.active else BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=12)

        value = self.text or self.placeholder
        color = TEXT if self.text else TEXT_MUTED
        text_surface = self.text_font.render(value, True, color)
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (self.rect.x + 14, text_y))

        if self.active:
            caret_x = self.rect.x + 14 + text_surface.get_width() + 2
            caret_top = self.rect.y + 11
            caret_bottom = self.rect.bottom - 11
            pygame.draw.line(surface, ACCENT, (caret_x, caret_top), (caret_x, caret_bottom), 2)

    def get_value(self) -> str:
        return self.text.strip()

    def clear(self) -> None:
        self.text = ""
        self.active = False


class Checkbox:
    label_font: Optional[pygame.font.Font] = None

    def __init__(self, x: int, y: int, label: str) -> None:
        if Checkbox.label_font is None:
            Checkbox.label_font = pygame.font.SysFont(FONT_NAME, 17)

        self.box_rect = pygame.Rect(x, y, 20, 20)
        self.label = label
        self.checked = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        click_rect = pygame.Rect(
            self.box_rect.x,
            self.box_rect.y,
            self.box_rect.width + 10 + self.label_font.size(self.label)[0],
            self.box_rect.height,
        )
        if click_rect.collidepoint(event.pos):
            self.checked = not self.checked
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PANEL, self.box_rect, border_radius=4)
        pygame.draw.rect(surface, BORDER, self.box_rect, 2, border_radius=4)

        if self.checked:
            inset = self.box_rect.inflate(-6, -6)
            pygame.draw.rect(surface, CHECK_FILL, inset, border_radius=3)
            pygame.draw.line(
                surface,
                PANEL,
                (inset.x + 3, inset.y + inset.height // 2),
                (inset.x + inset.width // 2, inset.bottom - 4),
                2,
            )
            pygame.draw.line(
                surface,
                PANEL,
                (inset.x + inset.width // 2, inset.bottom - 4),
                (inset.right - 3, inset.y + 3),
                2,
            )

        label_surface = self.label_font.render(self.label, True, TEXT)
        surface.blit(label_surface, (self.box_rect.right + 10, self.box_rect.y - 1))

    def clear(self) -> None:
        self.checked = False


class Dropdown:
    label_font: Optional[pygame.font.Font] = None
    text_font: Optional[pygame.font.Font] = None

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        options: Sequence[str],
        placeholder: str,
    ) -> None:
        if Dropdown.label_font is None:
            Dropdown.label_font = pygame.font.SysFont(FONT_NAME, 14, bold=True)
            Dropdown.text_font = pygame.font.SysFont(FONT_NAME, 17)

        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.options = list(options)
        self.placeholder = placeholder
        self.selected: Optional[str] = None
        self.is_open = False
        self.option_height = 26
        self.hovered_index = -1

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION and self.is_open:
            self.hovered_index = -1
            for index, option_rect in enumerate(self.option_rects()):
                if option_rect.collidepoint(event.pos):
                    self.hovered_index = index
                    break

    def handle_click(self, position: Tuple[int, int]) -> bool:
        if self.rect.collidepoint(position):
            self.is_open = not self.is_open
            self.hovered_index = -1
            return True

        if self.is_open:
            for index, option_rect in enumerate(self.option_rects()):
                if option_rect.collidepoint(position):
                    self.selected = self.options[index]
                    self.is_open = False
                    self.hovered_index = -1
                    return True
            self.close()

        return False

    def option_rects(self) -> List[pygame.Rect]:
        return [
            pygame.Rect(
                self.rect.x,
                self.rect.bottom + 4 + index * self.option_height,
                self.rect.width,
                self.option_height,
            )
            for index, _ in enumerate(self.options)
        ]

    def draw(self, surface: pygame.Surface) -> None:
        label = self.label_font.render(self.label, True, TEXT)
        surface.blit(label, (self.rect.x, self.rect.y - 24))

        pygame.draw.rect(surface, PANEL, self.rect, border_radius=12)
        border_color = ACCENT if self.is_open else BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=12)

        value = self.selected or self.placeholder
        color = TEXT if self.selected else TEXT_MUTED
        text_surface = self.text_font.render(value, True, color)
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (self.rect.x + 14, text_y))

        arrow_center_x = self.rect.right - 18
        arrow_center_y = self.rect.y + self.rect.height // 2
        points = [
            (arrow_center_x - 6, arrow_center_y - 3),
            (arrow_center_x + 6, arrow_center_y - 3),
            (arrow_center_x, arrow_center_y + 4),
        ]
        pygame.draw.polygon(surface, TEXT_MUTED, points)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        if not self.is_open:
            return

        option_rects = self.option_rects()
        if not option_rects:
            return

        overlay_rect = pygame.Rect(
            self.rect.x,
            self.rect.bottom + 4,
            self.rect.width,
            self.option_height * len(self.options),
        )
        shadow_rect = overlay_rect.move(0, 4)
        pygame.draw.rect(surface, OVERLAY_SHADOW, shadow_rect, border_radius=12)
        pygame.draw.rect(surface, PANEL, overlay_rect, border_radius=12)
        pygame.draw.rect(surface, BORDER, overlay_rect, 2, border_radius=12)

        for index, option_rect in enumerate(option_rects):
            fill = HOVER if index == self.hovered_index or self.options[index] == self.selected else PANEL
            pygame.draw.rect(surface, fill, option_rect)
            option_text = self.text_font.render(self.options[index], True, TEXT)
            surface.blit(option_text, (option_rect.x + 14, option_rect.y + 4))

        pygame.draw.rect(surface, BORDER, overlay_rect, 2, border_radius=12)

    def get_value(self) -> str:
        return self.selected or ""

    def close(self) -> None:
        self.is_open = False
        self.hovered_index = -1

    def clear(self) -> None:
        self.selected = None
        self.close()


class Button:
    font: Optional[pygame.font.Font] = None

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        color: Tuple[int, int, int],
        hover_color: Tuple[int, int, int],
    ) -> None:
        if Button.font is None:
            Button.font = pygame.font.SysFont(FONT_NAME, 17, bold=True)

        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.hover_color = hover_color

    def draw(self, surface: pygame.Surface) -> None:
        fill = self.hover_color if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color
        pygame.draw.rect(surface, fill, self.rect, border_radius=12)
        label_surface = self.font.render(self.label, True, PANEL)
        label_rect = label_surface.get_rect(center=self.rect.center)
        surface.blit(label_surface, label_rect)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class StudyGroupApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Study Group Matching System")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.subtitle_font = pygame.font.SysFont(FONT_NAME, 18)
        self.section_font = pygame.font.SysFont(FONT_NAME, 20, bold=True)
        self.body_font = pygame.font.SysFont(FONT_NAME, 17)
        self.small_font = pygame.font.SysFont(FONT_NAME, 14)

        self.engine = MatchingEngine()
        self.student_records = seed_records()
        self.student_pool = [self.record_to_student(record) for record in self.student_records]
        self.match_results: List[Tuple[Student, float]] = []
        self.last_submission: Optional[Dict[str, object]] = None
        self.status_message = "Fill in the form and click Submit to find compatible study partners."
        self.status_color = TEXT_MUTED

        self.form_panel = pygame.Rect(36, 92, 520, 692)
        self.results_panel = pygame.Rect(584, 92, 620, 692)
        self._build_ui()

    def _build_ui(self) -> None:
        left = self.form_panel.x + 24
        top = self.form_panel.y + 118
        full_width = self.form_panel.width - 48
        field_height = 46

        self.first_name_box = InputBox(
            left,
            top,
            220,
            field_height,
            "First Name",
            "Alicia",
            max_length=24,
        )
        self.last_name_box = InputBox(
            left + 240,
            top,
            220,
            field_height,
            "Last Name",
            "Tan",
            max_length=24,
        )
        self.course_box = InputBox(
            left,
            top + 90,
            full_width,
            field_height,
            "Module Code",
            "CV1014",
            max_length=12,
        )

        dropdown_y = top + 180
        dropdown_width = 141
        dropdown_gap = 18
        self.day_dropdown = Dropdown(
            left,
            dropdown_y,
            dropdown_width,
            field_height,
            "Day",
            DAY_OPTIONS,
            "Select day",
        )
        self.start_dropdown = Dropdown(
            left + dropdown_width + dropdown_gap,
            dropdown_y,
            dropdown_width,
            field_height,
            "Start Time",
            TIME_OPTIONS,
            "Select start",
        )
        self.end_dropdown = Dropdown(
            left + (dropdown_width + dropdown_gap) * 2,
            dropdown_y,
            dropdown_width,
            field_height,
            "End Time",
            TIME_OPTIONS,
            "Select end",
        )

        checkbox_y = dropdown_y + 124
        checkbox_gap = 36
        self.checkboxes = [
            Checkbox(left, checkbox_y, OBJECTIVE_OPTIONS[0]),
            Checkbox(left, checkbox_y + checkbox_gap, OBJECTIVE_OPTIONS[1]),
            Checkbox(left, checkbox_y + checkbox_gap * 2, OBJECTIVE_OPTIONS[2]),
        ]

        button_y = checkbox_y + checkbox_gap * 3 + 18
        self.submit_button = Button(left, button_y, 132, 46, "Submit", ACCENT, ACCENT_DARK)
        self.clear_button = Button(
            left + 146,
            button_y,
            108,
            46,
            "Clear",
            BUTTON_NEUTRAL,
            TEXT_MUTED,
        )
        self.export_button = Button(
            left + 268,
            button_y,
            192,
            46,
            "Export to Excel",
            SUCCESS,
            (38, 107, 80),
        )

        self.input_boxes = [self.first_name_box, self.last_name_box, self.course_box]
        self.dropdowns = [self.day_dropdown, self.start_dropdown, self.end_dropdown]

    def record_to_student(self, record: Dict[str, object]) -> Student:
        return Student(
            name=str(record["name"]),
            course=str(record["course"]),
            time_slots={str(record["matching_slot"])},
            objectives=set(record["objectives"]),
        )

    def build_export_frame(self) -> pd.DataFrame:
        rows = []
        for record in self.student_records:
            rows.append(
                {
                    "Name": record["name"],
                    "Module Code": record["course"],
                    "Day": record["day"],
                    "Start Time": record["start_time"],
                    "End Time": record["end_time"],
                    "Matching Slot": record["matching_slot"],
                    "Objectives": ", ".join(record["objectives"]),
                }
            )

        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame

        frame["_day_order"] = frame["Day"].map(DAY_TO_ORDER)
        frame["_start_order"] = frame["Start Time"].map(TIME_TO_ORDER)
        frame = frame.sort_values(
            by=["Module Code", "_day_order", "_start_order", "Name"]
        ).drop(columns=["_day_order", "_start_order"])
        return frame

    def set_status(self, message: str, color: Tuple[int, int, int]) -> None:
        self.status_message = message
        self.status_color = color

    def close_other_dropdowns(self, keep_open: Dropdown) -> None:
        for dropdown in self.dropdowns:
            if dropdown is not keep_open:
                dropdown.close()

    def close_all_dropdowns(self) -> None:
        for dropdown in self.dropdowns:
            dropdown.close()

    def deactivate_inputs(self) -> None:
        for box in self.input_boxes:
            box.active = False

    def any_input_active(self) -> bool:
        return any(box.active for box in self.input_boxes)

    def handle_submit(self) -> None:
        first_name = self.first_name_box.get_value()
        last_name = self.last_name_box.get_value()
        course = self.course_box.get_value().upper()
        day = self.day_dropdown.get_value()
        start_time = self.start_dropdown.get_value()
        end_time = self.end_dropdown.get_value()
        objectives = [checkbox.label for checkbox in self.checkboxes if checkbox.checked]

        if not first_name:
            self.set_status("Please enter a first name.", ERROR)
            return
        if not last_name:
            self.set_status("Please enter a last name.", ERROR)
            return
        if not course:
            self.set_status("Please enter a module code.", ERROR)
            return
        if not day or not start_time or not end_time:
            self.set_status("Please select day, start time, and end time.", ERROR)
            return
        if parse_time_label(end_time) <= parse_time_label(start_time):
            self.set_status("End time must be later than the start time.", ERROR)
            return
        if not objectives:
            self.set_status("Please choose at least one learning objective.", ERROR)
            return

        full_name = f"{first_name} {last_name}".strip()
        record = build_record(full_name, course, day, start_time, end_time, objectives)
        student = self.record_to_student(record)

        self.match_results = self.engine.find_best_matches(student, self.student_pool, top_n=3)
        self.student_records.append(record)
        self.student_pool.append(student)
        self.last_submission = record

        if self.match_results:
            self.set_status(
                f"Found {len(self.match_results)} match(es) for {full_name}.",
                SUCCESS,
            )
        else:
            self.set_status(
                f"{full_name} was added to the pool. No compatible matches yet.",
                WARNING,
            )

    def clear_form(self) -> None:
        for box in self.input_boxes:
            box.clear()
        for dropdown in self.dropdowns:
            dropdown.clear()
        for checkbox in self.checkboxes:
            checkbox.clear()

        self.match_results = []
        self.last_submission = None
        self.set_status("Form cleared. Ready for a new submission.", TEXT_MUTED)

    def export_to_excel(self) -> None:
        frame = self.build_export_frame()
        frame.to_excel(EXPORT_FILE, index=False)
        self.set_status(
            f"Exported {len(frame)} student records to {EXPORT_FILE}.",
            SUCCESS,
        )

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            for dropdown in self.dropdowns:
                dropdown.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if event.key == pygame.K_e and not self.any_input_active():
                    self.export_to_excel()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handled_by_dropdown = False
                for dropdown in reversed(self.dropdowns):
                    if dropdown.handle_click(event.pos):
                        handled_by_dropdown = True
                        self.close_other_dropdowns(dropdown)
                        self.deactivate_inputs()
                        break

                if handled_by_dropdown:
                    continue

                self.close_all_dropdowns()

            for box in self.input_boxes:
                box.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for checkbox in self.checkboxes:
                    checkbox.handle_event(event)

                if self.submit_button.is_clicked(event):
                    self.handle_submit()
                elif self.clear_button.is_clicked(event):
                    self.clear_form()
                elif self.export_button.is_clicked(event):
                    self.export_to_excel()

    def draw_background(self) -> None:
        self.screen.fill(BACKGROUND)
        pygame.draw.circle(self.screen, (230, 238, 248), (90, 70), 90)
        pygame.draw.circle(self.screen, (233, 241, 250), (1140, 120), 120)
        pygame.draw.rect(self.screen, (236, 242, 249), pygame.Rect(0, 0, WINDOW_WIDTH, 74))

    def draw_panel(self, rect: pygame.Rect) -> None:
        shadow = rect.move(0, 8)
        pygame.draw.rect(self.screen, OVERLAY_SHADOW, shadow, border_radius=24)
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=24)
        pygame.draw.rect(self.screen, BORDER, rect, 2, border_radius=24)

    def draw_form_panel(self) -> None:
        self.draw_panel(self.form_panel)

        title = self.section_font.render("Student Details", True, TEXT)
        self.screen.blit(title, (self.form_panel.x + 24, self.form_panel.y + 22))

        note_lines = wrap_text(
            "Matching uses Day + Start Time only. End Time is still collected for display and Excel export.",
            self.small_font,
            self.form_panel.width - 48,
        )
        for index, line in enumerate(note_lines):
            line_surface = self.small_font.render(line, True, TEXT_MUTED)
            self.screen.blit(
                line_surface,
                (self.form_panel.x + 24, self.form_panel.y + 52 + index * 18),
            )

        for box in self.input_boxes:
            box.draw(self.screen)
        for dropdown in self.dropdowns:
            dropdown.draw(self.screen)

        objective_label = self.section_font.render("Learning Objectives", True, TEXT)
        self.screen.blit(objective_label, (self.form_panel.x + 24, self.form_panel.y + 446))
        objective_hint = self.small_font.render(
            "Tick every reason you want a study partner for.",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(objective_hint, (self.form_panel.x + 24, self.form_panel.y + 472))

        for checkbox in self.checkboxes:
            checkbox.draw(self.screen)

        self.submit_button.draw(self.screen)
        self.clear_button.draw(self.screen)
        self.export_button.draw(self.screen)

        status_title = self.section_font.render("Status", True, TEXT)
        self.screen.blit(status_title, (self.form_panel.x + 24, self.form_panel.y + 606))
        status_lines = wrap_text(
            self.status_message,
            self.small_font,
            self.form_panel.width - 48,
        )
        for index, line in enumerate(status_lines):
            status_surface = self.small_font.render(line, True, self.status_color)
            self.screen.blit(
                status_surface,
                (self.form_panel.x + 24, self.form_panel.y + 636 + index * 20),
            )

        hotkey_note = self.small_font.render(
            "Hotkey: press E outside a text field to export to Excel.",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(hotkey_note, (self.form_panel.x + 24, self.form_panel.bottom - 24))

    def draw_match_section(self) -> None:
        section_rect = pygame.Rect(
            self.results_panel.x + 20,
            self.results_panel.y + 78,
            self.results_panel.width - 40,
            354,
        )
        pygame.draw.rect(self.screen, PANEL_ALT, section_rect, border_radius=20)
        pygame.draw.rect(self.screen, BORDER, section_rect, 2, border_radius=20)

        title = self.section_font.render("Match Results", True, TEXT)
        self.screen.blit(title, (section_rect.x + 20, section_rect.y + 18))

        if not self.last_submission:
            info_lines = wrap_text(
                "Submit a student profile to see the top matches from the current pool. "
                "The engine compares module code, the exact Day + Start Time string, and the selected objectives.",
                self.body_font,
                section_rect.width - 40,
            )
            for index, line in enumerate(info_lines):
                line_surface = self.body_font.render(line, True, TEXT_MUTED)
                self.screen.blit(line_surface, (section_rect.x + 20, section_rect.y + 68 + index * 26))
            return

        submission_lines = [
            f"Submitted: {self.last_submission['name']} ({self.last_submission['course']})",
            f"Matching slot: {self.last_submission['matching_slot']}",
            f"Selected range: {self.last_submission['day']} {self.last_submission['start_time']} - {self.last_submission['end_time']}",
            "Objectives: " + ", ".join(self.last_submission["objectives"]),
        ]
        for index, line in enumerate(submission_lines):
            line_surface = self.small_font.render(line, True, TEXT_MUTED)
            self.screen.blit(line_surface, (section_rect.x + 20, section_rect.y + 58 + index * 18))

        if not self.match_results:
            empty_surface = self.body_font.render(
                "No compatible matches yet. Try another module or time slot.",
                True,
                WARNING,
            )
            self.screen.blit(empty_surface, (section_rect.x + 20, section_rect.y + 146))
            return

        user_objectives = set(self.last_submission["objectives"])
        card_y = section_rect.y + 142

        for index, (match, score) in enumerate(self.match_results, start=1):
            card_rect = pygame.Rect(section_rect.x + 16, card_y, section_rect.width - 32, 62)
            pygame.draw.rect(self.screen, PANEL, card_rect, border_radius=16)
            pygame.draw.rect(self.screen, BORDER, card_rect, 2, border_radius=16)

            shared_objectives = sorted(user_objectives.intersection(match.objectives))
            slot = ", ".join(sorted(match.time_slots))

            headline = self.body_font.render(
                f"{index}. {match.name}  |  Score: {score:.2f}",
                True,
                TEXT,
            )
            self.screen.blit(headline, (card_rect.x + 16, card_rect.y + 10))

            detail = self.small_font.render(
                f"Module: {match.course}   Slot: {slot}",
                True,
                TEXT_MUTED,
            )
            self.screen.blit(detail, (card_rect.x + 16, card_rect.y + 34))

            objective_text = ", ".join(shared_objectives) if shared_objectives else "No shared objectives"
            objective_surface = self.small_font.render(
                f"Shared objectives: {objective_text}",
                True,
                TEXT_MUTED,
            )
            self.screen.blit(objective_surface, (card_rect.x + 270, card_rect.y + 34))

            card_y += 74

    def draw_pool_section(self) -> None:
        section_rect = pygame.Rect(
            self.results_panel.x + 20,
            self.results_panel.y + 454,
            self.results_panel.width - 40,
            210,
        )
        pygame.draw.rect(self.screen, PANEL_ALT, section_rect, border_radius=20)
        pygame.draw.rect(self.screen, BORDER, section_rect, 2, border_radius=20)

        title = self.section_font.render("Student Pool Snapshot", True, TEXT)
        self.screen.blit(title, (section_rect.x + 20, section_rect.y + 18))
        meta = self.small_font.render(
            f"{len(self.student_records)} students available for matching",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(meta, (section_rect.x + 20, section_rect.y + 46))

        header_y = section_rect.y + 76
        header = self.small_font.render("Name", True, ACCENT)
        self.screen.blit(header, (section_rect.x + 20, header_y))
        header = self.small_font.render("Module", True, ACCENT)
        self.screen.blit(header, (section_rect.x + 238, header_y))
        header = self.small_font.render("Slot", True, ACCENT)
        self.screen.blit(header, (section_rect.x + 328, header_y))

        rows = list(reversed(self.student_records[-4:]))
        row_y = header_y + 24

        for record in rows:
            pygame.draw.line(
                self.screen,
                BORDER,
                (section_rect.x + 18, row_y - 8),
                (section_rect.right - 18, row_y - 8),
                1,
            )
            name_surface = self.small_font.render(str(record["name"])[:24], True, TEXT)
            module_surface = self.small_font.render(str(record["course"]), True, TEXT)
            slot_surface = self.small_font.render(str(record["matching_slot"]), True, TEXT)
            self.screen.blit(name_surface, (section_rect.x + 20, row_y))
            self.screen.blit(module_surface, (section_rect.x + 238, row_y))
            self.screen.blit(slot_surface, (section_rect.x + 328, row_y))
            row_y += 28

    def draw_results_panel(self) -> None:
        self.draw_panel(self.results_panel)

        title = self.section_font.render("Study Group Matching", True, TEXT)
        self.screen.blit(title, (self.results_panel.x + 24, self.results_panel.y + 22))
        subtitle = self.small_font.render(
            "Custom Pygame widgets, exact slot matching, and Pandas export in one screen.",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(subtitle, (self.results_panel.x + 24, self.results_panel.y + 52))

        self.draw_match_section()
        self.draw_pool_section()

    def draw_header(self) -> None:
        title = self.title_font.render("Study Group Matching System", True, TEXT)
        self.screen.blit(title, (36, 22))

        subtitle = self.subtitle_font.render(
            "Refactored Pygame desktop app wired into MatchingEngine and Pandas export.",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(subtitle, (36, 56))

    def draw(self) -> None:
        self.draw_background()
        self.draw_header()
        self.draw_form_panel()
        self.draw_results_panel()

        for dropdown in self.dropdowns:
            dropdown.draw_overlay(self.screen)

        pygame.display.flip()

    def run(self) -> None:
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

    def quit(self) -> None:
        pygame.quit()
        sys.exit()


def main() -> None:
    StudyGroupApp().run()


if __name__ == "__main__":
    main()
