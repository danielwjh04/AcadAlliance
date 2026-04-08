"""
Refactored Pygame frontend for the study group matching system.

Run with:
    python main.py
"""

import random
import string
import sys
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import pygame

from engine import MatchingEngine, Student
from ui_panels import FormPanelView, RightPanelView
from ui_widgets import BACKGROUND, ERROR, SUCCESS, TEXT, TEXT_MUTED, WARNING, build_fonts


WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 820
FPS = 60
EXPORT_FILE = "student_data.xlsx"
EXPORT_SHEET_NAME = "student_data"

DAY_OPTIONS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
OBJECTIVE_OPTIONS = [
    "Concept understanding",
    "Tutorial Help",
    "Exam paper practice",
]


def build_time_options() -> List[str]:
    options: List[str] = []
    for hour in range(0, 24):
        suffix = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        options.append(f"{display_hour}{suffix}")
    return options


TIME_OPTIONS = build_time_options()
TIME_TO_ORDER = {label: index for index, label in enumerate(TIME_OPTIONS)}
DAY_TO_ORDER = {label: index for index, label in enumerate(DAY_OPTIONS)}


def parse_time_label(label: str) -> int:
    suffix = label[-2:]
    hour = int(label[:-2])
    if suffix == "AM":
        return 0 if hour == 12 else hour
    return 12 if hour == 12 else hour + 12


def generate_fake_telehandle() -> str:
    length = random.randint(5, 8)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"@{suffix}"


def build_record(
    name: str,
    course: str,
    day: str,
    start_time: str,
    end_time: str,
    objectives: Sequence[str],
    telehandle: Optional[str] = None,
) -> Dict[str, object]:
    normalized_handle = (telehandle or generate_fake_telehandle()).strip()
    if normalized_handle and not normalized_handle.startswith("@"):
        normalized_handle = f"@{normalized_handle}"

    return {
        "name": name,
        "course": course.upper(),
        "day": day,
        "start_time": start_time,
        "end_time": end_time,
        "telehandle": normalized_handle,
        "display_slot": f"{day} {start_time}-{end_time}",
        "matching_slot": f"{day} {start_time}",
        "objectives": list(objectives),
    }


def seed_records() -> List[Dict[str, object]]:
    return [
        build_record("Alice Tan", "CV1014", "Mon", "6PM", "8PM", ["Concept understanding"]),
        build_record("Benjamin Lee", "CV1014", "Mon", "6PM", "9PM", ["Concept understanding", "Tutorial Help"]),
        build_record("Chloe Goh", "CV1014", "Wed", "7PM", "9PM", ["Exam paper practice"]),
        build_record("Darren Koh", "CV1011", "Tue", "2PM", "4PM", ["Tutorial Help", "Exam paper practice"]),
        build_record("Eunice Lim", "CV1011", "Tue", "2PM", "5PM", ["Concept understanding"]),
        build_record("Farah Noor", "CV2020", "Thu", "2PM", "4PM", ["Concept understanding", "Tutorial Help"]),
        build_record("Gabriel Ong", "CV2020", "Thu", "2PM", "5PM", ["Tutorial Help"]),
        build_record("Hannah Teo", "CV2020", "Fri", "10AM", "12PM", ["Exam paper practice"]),
        build_record("Isaac Chua", "CV2002", "Tue", "6PM", "8PM", ["Concept understanding"]),
        build_record("Joanna Sim", "CV2002", "Tue", "6PM", "9PM", ["Concept understanding", "Exam paper practice"]),
        build_record("Kumar Raj", "MH1811", "Sat", "9AM", "11AM", ["Tutorial Help"]),
        build_record("Li Wen", "MH1811", "Sat", "9AM", "12PM", ["Concept understanding", "Tutorial Help"]),
        build_record("Marcus Yeo", "CV1014", "Fri", "4PM", "6PM", ["Tutorial Help"]),
        build_record("Nur Aisyah", "CV2002", "Wed", "6PM", "8PM", ["Concept understanding", "Tutorial Help"]),
    ]


class StudyGroupApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Study Group Matching System")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = build_fonts()

        self.engine = MatchingEngine()
        self.student_records = seed_records()
        self.student_pool = [self.record_to_student(record) for record in self.student_records]
        self.match_results: List[Tuple[Student, float]] = []
        self.last_submission: Optional[Dict[str, object]] = None
        self.has_submitted = False
        self.status_message = "Fill in the form and click Submit to find compatible study partners."
        self.status_color = TEXT_MUTED

        self.form_panel = FormPanelView(
            pygame.Rect(36, 92, 520, 692),
            self.fonts,
            DAY_OPTIONS,
            TIME_OPTIONS,
            OBJECTIVE_OPTIONS,
        )
        self.right_panel = RightPanelView(
            pygame.Rect(584, 92, 620, 692),
            self.fonts,
        )

    def record_to_student(self, record: Dict[str, object]) -> Student:
        return Student(
            name=str(record["name"]),
            course=str(record["course"]),
            time_slots={str(record["matching_slot"])},
            objectives=set(record["objectives"]),
        )

    def get_display_slot_for_student(self, student: Student) -> str:
        matching_slot = next(iter(student.time_slots), "")
        for record in reversed(self.student_records):
            if (
                record["name"] == student.name
                and record["course"] == student.course
                and record["matching_slot"] == matching_slot
            ):
                return str(record["display_slot"])
        return matching_slot

    def get_telehandle_for_student(self, student: Student) -> str:
        matching_slot = next(iter(student.time_slots), "")
        for record in reversed(self.student_records):
            if (
                record["name"] == student.name
                and record["course"] == student.course
                and record["matching_slot"] == matching_slot
            ):
                return str(record["telehandle"])
        return ""

    def build_export_frame(self) -> pd.DataFrame:
        rows = [
            {
                "Name": record["name"],
                "Module Code": record["course"],
                "Telehandle": record["telehandle"],
                "Day": record["day"],
                "Start Time": record["start_time"],
                "Slot": record["display_slot"],
                "Matching Slot": record["matching_slot"],
                "Objectives": ", ".join(record["objectives"]),
            }
            for record in self.student_records
        ]
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame

        frame["_day_order"] = frame["Day"].map(DAY_TO_ORDER)
        frame["_start_order"] = frame["Start Time"].map(TIME_TO_ORDER)
        return frame.sort_values(
            by=["Module Code", "_day_order", "_start_order", "Name"]
        ).drop(columns=["_day_order", "_start_order", "Day", "Start Time"])

    def set_status(self, message: str, color) -> None:
        self.status_message = message
        self.status_color = color

    def handle_submit(self) -> None:
        values = self.form_panel.get_submission_values()
        first_name = values["first_name"]
        last_name = values["last_name"]
        course = values["course"]
        telehandle = values["telehandle"]
        day = values["day"]
        start_time = values["start_time"]
        end_time = values["end_time"]
        objectives = values["objectives"]

        if not first_name:
            self.set_status("Please enter a first name.", ERROR)
            return
        if not last_name:
            self.set_status("Please enter a last name.", ERROR)
            return
        if not course:
            self.set_status("Please enter a module code.", ERROR)
            return
        if not telehandle:
            self.set_status("Please enter a Telegram handle.", ERROR)
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

        record = build_record(
            f"{first_name} {last_name}".strip(),
            course,
            day,
            start_time,
            end_time,
            objectives,
            telehandle,
        )
        student = self.record_to_student(record)

        self.match_results = self.engine.find_best_matches(student, self.student_pool, top_n=3)
        self.student_records.append(record)
        self.student_pool.append(student)
        self.last_submission = record
        self.has_submitted = True

        if self.match_results:
            self.set_status(f"Found {len(self.match_results)} match(es) for {record['name']}.", SUCCESS)
        else:
            self.set_status(f"{record['name']} was added to the pool. No compatible matches yet.", WARNING)

    def clear_form(self) -> None:
        self.form_panel.clear()
        self.match_results = []
        self.last_submission = None
        self.has_submitted = False
        self.set_status("Form cleared. Ready for a new submission.", TEXT_MUTED)

    def export_to_excel(self) -> None:
        frame = self.build_export_frame()
        try:
            frame.to_excel(EXPORT_FILE, index=False, sheet_name=EXPORT_SHEET_NAME)
            self.set_status(f"Exported {len(frame)} student records to {EXPORT_FILE}.", SUCCESS)
        except PermissionError:
            fallback = f"student_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            frame.to_excel(fallback, index=False, sheet_name=EXPORT_SHEET_NAME)
            self.set_status(f"{EXPORT_FILE} was busy, so export was saved as {fallback}.", WARNING)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if event.key == pygame.K_e and not self.form_panel.any_input_active():
                    self.export_to_excel()

            action = self.form_panel.handle_event(event)
            self.right_panel.handle_event(event, self, self.form_panel.any_dropdown_open())

            if action == "submit":
                self.handle_submit()
            elif action == "clear":
                self.clear_form()
            elif action == "export":
                self.export_to_excel()

    def draw_background(self) -> None:
        self.screen.fill(BACKGROUND)
        pygame.draw.circle(self.screen, (230, 238, 248), (90, 70), 90)
        pygame.draw.circle(self.screen, (233, 241, 250), (1140, 120), 120)
        pygame.draw.rect(self.screen, (236, 242, 249), pygame.Rect(0, 0, WINDOW_WIDTH, 74))

    def draw_header(self) -> None:
        title = self.fonts["title"].render("AcadAlliance", True, TEXT)
        self.screen.blit(title, (36, 22))

        subtitle = self.fonts["subtitle"].render("Study Group Matching System", True, TEXT_MUTED)
        self.screen.blit(subtitle, (36, 56))

    def draw(self) -> None:
        self.draw_background()
        self.draw_header()
        self.form_panel.draw(self.screen, self.status_message, self.status_color)
        self.right_panel.draw(self.screen, self)
        self.form_panel.draw_overlays(self.screen)
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
