from abc import ABC, abstractmethod
from typing import Dict, Optional

import pygame

from ui_widgets import (
    ACCENT,
    ACCENT_DARK,
    BORDER,
    BUTTON_NEUTRAL,
    PANEL,
    PANEL_ALT,
    SUCCESS,
    TEXT,
    TEXT_MUTED,
    WARNING,
    Button,
    Checkbox,
    Dropdown,
    InputBox,
    draw_panel,
    truncate_text,
    wrap_text,
)


class FormPanelView:
    def __init__(
        self,
        rect: pygame.Rect,
        fonts: Dict[str, pygame.font.Font],
        day_options,
        time_options,
        objective_options,
    ) -> None:
        self.rect = rect
        self.fonts = fonts
        self.day_options = list(day_options)
        self.time_options = list(time_options)
        self.objective_options = list(objective_options)
        self.layout = self._build_layout()
        self._build_controls()

    def _build_layout(self) -> Dict[str, int]:
        field_height = 46
        standard_row_gap = 28
        name_y = self.rect.y + 80
        course_y = name_y + field_height + standard_row_gap
        telehandle_y = course_y + field_height + standard_row_gap
        dropdown_y = telehandle_y + field_height + standard_row_gap
        objectives_title_y = dropdown_y + field_height + 24
        objectives_hint_y = objectives_title_y + 22
        checkbox_y = objectives_hint_y + 24
        checkbox_gap = 32
        button_y = checkbox_y + checkbox_gap * 3 + 10
        status_title_y = button_y + 54
        status_text_y = status_title_y + 24
        hotkey_y = self.rect.bottom - 24

        return {
            "field_height": field_height,
            "name_y": name_y,
            "course_y": course_y,
            "telehandle_y": telehandle_y,
            "dropdown_y": dropdown_y,
            "objectives_title_y": objectives_title_y,
            "objectives_hint_y": objectives_hint_y,
            "checkbox_y": checkbox_y,
            "checkbox_gap": checkbox_gap,
            "button_y": button_y,
            "status_title_y": status_title_y,
            "status_text_y": status_text_y,
            "hotkey_y": hotkey_y,
        }

    def _build_controls(self) -> None:
        left = self.rect.x + 24
        full_width = self.rect.width - 48
        field_height = self.layout["field_height"]

        self.first_name_box = InputBox(left, self.layout["name_y"], 220, field_height, "First Name", "Eg. Alice", 24)
        self.last_name_box = InputBox(left + 240, self.layout["name_y"], 220, field_height, "Last Name", "Eg. Tan", 24)
        self.course_box = InputBox(left, self.layout["course_y"], full_width, field_height, "Module Code", "Eg. CV1014", 12)
        self.telehandle_box = InputBox(left, self.layout["telehandle_y"], full_width, field_height, "Telehandle", "Eg. @alice23", 24)

        dropdown_width = 141
        dropdown_gap = 18
        dropdown_y = self.layout["dropdown_y"]
        self.day_dropdown = Dropdown(left, dropdown_y, dropdown_width, field_height, "Day", self.day_options, "Select day")
        self.start_dropdown = Dropdown(
            left + dropdown_width + dropdown_gap,
            dropdown_y,
            dropdown_width,
            field_height,
            "Start Time",
            self.time_options,
            "Select start",
        )
        self.end_dropdown = Dropdown(
            left + (dropdown_width + dropdown_gap) * 2,
            dropdown_y,
            dropdown_width,
            field_height,
            "End Time",
            self.time_options,
            "Select end",
        )

        checkbox_y = self.layout["checkbox_y"]
        checkbox_gap = self.layout["checkbox_gap"]
        self.checkboxes = [
            Checkbox(left, checkbox_y, self.objective_options[0]),
            Checkbox(left, checkbox_y + checkbox_gap, self.objective_options[1]),
            Checkbox(left, checkbox_y + checkbox_gap * 2, self.objective_options[2]),
        ]

        button_y = self.layout["button_y"]
        self.submit_button = Button(left, button_y, 132, 46, "Submit", ACCENT, ACCENT_DARK)
        self.clear_button = Button(left + 146, button_y, 108, 46, "Clear", BUTTON_NEUTRAL, TEXT_MUTED)
        self.export_button = Button(left + 268, button_y, 192, 46, "Export to Excel", SUCCESS, (38, 107, 80))

        self.input_boxes = [self.first_name_box, self.last_name_box, self.course_box, self.telehandle_box]
        self.dropdowns = [self.day_dropdown, self.start_dropdown, self.end_dropdown]

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

    def any_dropdown_open(self) -> bool:
        return any(dropdown.is_open for dropdown in self.dropdowns)

    def get_submission_values(self) -> Dict[str, object]:
        return {
            "first_name": self.first_name_box.get_value(),
            "last_name": self.last_name_box.get_value(),
            "course": self.course_box.get_value().upper(),
            "telehandle": self.telehandle_box.get_value(),
            "day": self.day_dropdown.get_value(),
            "start_time": self.start_dropdown.get_value(),
            "end_time": self.end_dropdown.get_value(),
            "objectives": [checkbox.label for checkbox in self.checkboxes if checkbox.checked],
        }

    def clear(self) -> None:
        for box in self.input_boxes:
            box.clear()
        for dropdown in self.dropdowns:
            dropdown.clear()
        for checkbox in self.checkboxes:
            checkbox.clear()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        for dropdown in self.dropdowns:
            dropdown.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handled_by_dropdown = False
            for dropdown in reversed(self.dropdowns):
                if dropdown.handle_click(event.pos):
                    handled_by_dropdown = True
                    self.close_other_dropdowns(dropdown)
                    self.deactivate_inputs()
                    break

            if handled_by_dropdown:
                return None

            self.close_all_dropdowns()

        for box in self.input_boxes:
            box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for checkbox in self.checkboxes:
                checkbox.handle_event(event)

            if self.submit_button.is_clicked(event):
                return "submit"
            if self.clear_button.is_clicked(event):
                return "clear"
            if self.export_button.is_clicked(event):
                return "export"

        return None

    def draw(self, surface: pygame.Surface, status_message: str, status_color) -> None:
        draw_panel(surface, self.rect)

        section_font = self.fonts["section"]
        small_font = self.fonts["small"]

        title = section_font.render("Student Details", True, TEXT)
        surface.blit(title, (self.rect.x + 24, self.rect.y + 22))

        for box in self.input_boxes:
            box.draw(surface)
        for dropdown in self.dropdowns:
            dropdown.draw(surface)

        objective_label = section_font.render("Learning Objectives", True, TEXT)
        surface.blit(objective_label, (self.rect.x + 24, self.layout["objectives_title_y"]))
        objective_hint = small_font.render(
            "Tick every reason you want a study partner for.",
            True,
            TEXT_MUTED,
        )
        surface.blit(objective_hint, (self.rect.x + 24, self.layout["objectives_hint_y"]))

        for checkbox in self.checkboxes:
            checkbox.draw(surface)

        self.submit_button.draw(surface)
        self.clear_button.draw(surface)
        self.export_button.draw(surface)

        status_title = section_font.render("Status", True, TEXT)
        surface.blit(status_title, (self.rect.x + 24, self.layout["status_title_y"]))
        status_lines = wrap_text(status_message, small_font, self.rect.width - 48)
        for index, line in enumerate(status_lines):
            status_surface = small_font.render(line, True, status_color)
            surface.blit(status_surface, (self.rect.x + 24, self.layout["status_text_y"] + index * 20))

        hotkey_y = self.layout["status_text_y"] + len(status_lines) * 20 + 10
        hotkey_note = small_font.render(
            "Hotkey: press E outside a text field to export to Excel.",
            True,
            TEXT_MUTED,
        )
        surface.blit(hotkey_note, (self.rect.x + 24, min(hotkey_y, self.layout["hotkey_y"])))

    def draw_overlays(self, surface: pygame.Surface) -> None:
        for dropdown in self.dropdowns:
            dropdown.draw_overlay(surface)


class PanelContent(ABC):
    @abstractmethod
    def draw(self, surface: pygame.Surface, rect: pygame.Rect, app) -> None:
        raise NotImplementedError

    def handle_event(self, event: pygame.event.Event, rect: pygame.Rect, app, dropdown_open: bool) -> None:
        return None


class MatchResultsContent(PanelContent):
    def __init__(self, fonts: Dict[str, pygame.font.Font]) -> None:
        self.fonts = fonts

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, app) -> None:
        pygame.draw.rect(surface, PANEL_ALT, rect, border_radius=20)
        pygame.draw.rect(surface, BORDER, rect, 2, border_radius=20)

        section_font = self.fonts["section"]
        body_font = self.fonts["body"]
        small_font = self.fonts["small"]

        title = section_font.render("Match Results", True, TEXT)
        surface.blit(title, (rect.x + 20, rect.y + 18))

        if not app.last_submission:
            info_lines = wrap_text(
                "Submit a student profile to see the top matches from the current pool. "
                "The engine compares module code, the exact Day + Start Time string, and the selected objectives.",
                body_font,
                rect.width - 40,
            )
            for index, line in enumerate(info_lines):
                line_surface = body_font.render(line, True, TEXT_MUTED)
                surface.blit(line_surface, (rect.x + 20, rect.y + 68 + index * 26))
            return

        submission_lines = [
            f"Submitted: {app.last_submission['name']} ({app.last_submission['course']})",
            f"Matching slot: {app.last_submission['matching_slot']}",
            f"Selected range: {app.last_submission['day']} {app.last_submission['start_time']} - {app.last_submission['end_time']}",
            "Objectives: " + ", ".join(app.last_submission["objectives"]),
        ]
        for index, line in enumerate(submission_lines):
            line_surface = small_font.render(line, True, TEXT_MUTED)
            surface.blit(line_surface, (rect.x + 20, rect.y + 58 + index * 18))

        if not app.match_results:
            empty_surface = body_font.render(
                "No compatible matches yet. Try another module or time slot.",
                True,
                WARNING,
            )
            surface.blit(empty_surface, (rect.x + 20, rect.y + 146))
            return

        user_objectives = set(app.last_submission["objectives"])
        card_y = rect.y + 142

        for index, (match, _score) in enumerate(app.match_results, start=1):
            card_rect = pygame.Rect(rect.x + 16, card_y, rect.width - 32, 82)
            pygame.draw.rect(surface, PANEL, card_rect, border_radius=16)
            pygame.draw.rect(surface, BORDER, card_rect, 2, border_radius=16)

            headline_text = f"{index}. {match.name}"
            telehandle = app.get_telehandle_for_student(match)
            if telehandle:
                headline_text += f" | {telehandle}"
            headline_text = truncate_text(headline_text, body_font, card_rect.width - 32)
            headline = body_font.render(headline_text, True, TEXT)
            surface.blit(headline, (card_rect.x + 16, card_rect.y + 10))

            slot = app.get_display_slot_for_student(match)
            detail = small_font.render(f"Module: {match.course}   Slot: {slot}", True, TEXT_MUTED)
            surface.blit(detail, (card_rect.x + 16, card_rect.y + 34))

            shared_objectives = sorted(user_objectives.intersection(match.objectives))
            objective_text = ", ".join(shared_objectives) if shared_objectives else "No shared objectives"
            objective_line = truncate_text(
                f"Shared objectives: {objective_text}",
                small_font,
                card_rect.width - 32,
            )
            objective_surface = small_font.render(objective_line, True, TEXT_MUTED)
            surface.blit(objective_surface, (card_rect.x + 16, card_rect.y + 54))

            card_y += 94


class StudentPoolContent(PanelContent):
    def __init__(self, fonts: Dict[str, pygame.font.Font]) -> None:
        self.fonts = fonts
        self.scroll_offset = 0

    def handle_event(self, event: pygame.event.Event, rect: pygame.Rect, app, dropdown_open: bool) -> None:
        if event.type != pygame.MOUSEWHEEL or app.has_submitted or dropdown_open:
            return
        if not rect.collidepoint(pygame.mouse.get_pos()):
            return

        rows_visible = max(1, (rect.height - 122) // 28)
        max_scroll = max(0, len(app.student_records) - rows_visible)
        self.scroll_offset = max(0, min(self.scroll_offset - event.y, max_scroll))

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, app) -> None:
        pygame.draw.rect(surface, PANEL_ALT, rect, border_radius=20)
        pygame.draw.rect(surface, BORDER, rect, 2, border_radius=20)

        section_font = self.fonts["section"]
        small_font = self.fonts["small"]
        content_x = rect.x + 40
        module_x = content_x + 160
        slot_x = content_x + 245
        telehandle_x = content_x + 385

        title = section_font.render("Student Pool", True, TEXT)
        surface.blit(title, (rect.x + 20, rect.y + 18))
        meta = small_font.render(
            f"{len(app.student_records)} students available for matching",
            True,
            TEXT_MUTED,
        )
        surface.blit(meta, (rect.x + 20, rect.y + 46))

        header_y = rect.y + 74
        header_divider_y = rect.y + 96
        surface.blit(small_font.render("Name", True, ACCENT), (content_x, header_y))
        surface.blit(small_font.render("Module", True, ACCENT), (module_x, header_y))
        surface.blit(small_font.render("Slot", True, ACCENT), (slot_x, header_y))
        surface.blit(small_font.render("Telehandle", True, ACCENT), (telehandle_x, header_y))
        pygame.draw.line(surface, BORDER, (rect.x + 28, header_divider_y), (rect.right - 28, header_divider_y), 1)

        rows_visible = max(1, (rect.height - 122) // 28)
        reversed_records = list(reversed(app.student_records))
        max_scroll = max(0, len(reversed_records) - rows_visible)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        rows = reversed_records[self.scroll_offset:self.scroll_offset + rows_visible]
        row_y = header_divider_y + 6

        for index, record in enumerate(rows):
            if index > 0:
                pygame.draw.line(surface, BORDER, (rect.x + 28, row_y - 8), (rect.right - 28, row_y - 8), 1)

            name_value = truncate_text(str(record["name"]), small_font, module_x - content_x - 10)
            module_value = truncate_text(str(record["course"]), small_font, slot_x - module_x - 10)
            slot_value = truncate_text(str(record["display_slot"]), small_font, telehandle_x - slot_x - 10)
            telehandle_value = truncate_text(str(record["telehandle"]), small_font, rect.right - 40 - telehandle_x)
            surface.blit(small_font.render(name_value, True, TEXT), (content_x, row_y))
            surface.blit(small_font.render(module_value, True, TEXT), (module_x, row_y))
            surface.blit(small_font.render(slot_value, True, TEXT), (slot_x, row_y))
            surface.blit(small_font.render(telehandle_value, True, TEXT), (telehandle_x, row_y))
            row_y += 28

        if max_scroll > 0:
            track_rect = pygame.Rect(rect.right - 14, header_divider_y + 8, 4, rect.height - 118)
            thumb_height = max(24, int(track_rect.height * (rows_visible / len(reversed_records))))
            travel = max(1, track_rect.height - thumb_height)
            thumb_y = track_rect.y + int(travel * (self.scroll_offset / max_scroll))
            thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
            pygame.draw.rect(surface, BORDER, track_rect, border_radius=4)
            pygame.draw.rect(surface, ACCENT, thumb_rect, border_radius=4)
            scroll_hint = small_font.render("Scroll to see more", True, TEXT_MUTED)
            surface.blit(scroll_hint, (rect.x + 20, rect.bottom - 24))


class RightPanelView:
    def __init__(self, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
        self.rect = rect
        self.content_views = {
            False: StudentPoolContent(fonts),
            True: MatchResultsContent(fonts),
        }

    def content_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x + 20,
            self.rect.y + 20,
            self.rect.width - 40,
            self.rect.height - 40,
        )

    def active_content(self, app) -> PanelContent:
        return self.content_views[app.has_submitted]

    def handle_event(self, event: pygame.event.Event, app, dropdown_open: bool) -> None:
        self.active_content(app).handle_event(event, self.content_rect(), app, dropdown_open)

    def draw(self, surface: pygame.Surface, app) -> None:
        draw_panel(surface, self.rect)
        self.active_content(app).draw(surface, self.content_rect(), app)
