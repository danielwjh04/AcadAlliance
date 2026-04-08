from typing import Dict, List, Optional, Sequence, Tuple

import pygame


FONT_NAME = "segoeui"

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


def build_fonts() -> Dict[str, pygame.font.Font]:
    return {
        "title": pygame.font.SysFont(FONT_NAME, 32, bold=True),
        "subtitle": pygame.font.SysFont(FONT_NAME, 18),
        "section": pygame.font.SysFont(FONT_NAME, 20, bold=True),
        "body": pygame.font.SysFont(FONT_NAME, 17),
        "small": pygame.font.SysFont(FONT_NAME, 14),
    }


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


def truncate_text(text: str, font: pygame.font.Font, max_width: int) -> str:
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    truncated = text
    while truncated and font.size(truncated + ellipsis)[0] > max_width:
        truncated = truncated[:-1]

    return truncated + ellipsis if truncated else ellipsis


def draw_panel(surface: pygame.Surface, rect: pygame.Rect) -> None:
    shadow = rect.move(0, 8)
    pygame.draw.rect(surface, OVERLAY_SHADOW, shadow, border_radius=24)
    pygame.draw.rect(surface, PANEL, rect, border_radius=24)
    pygame.draw.rect(surface, BORDER, rect, 2, border_radius=24)


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
            elif event.unicode and event.unicode.isprintable() and len(self.text) < self.max_length:
                self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        label = self.label_font.render(self.label, True, TEXT)
        surface.blit(label, (self.rect.x, self.rect.y - 24))

        pygame.draw.rect(surface, PANEL, self.rect, border_radius=12)
        border_color = ACCENT if self.active else BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=12)

        if self.text:
            text_surface = self.text_font.render(self.text, True, TEXT)
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (self.rect.x + 14, text_y))
        elif not self.active:
            placeholder_surface = self.text_font.render(self.placeholder, True, TEXT_MUTED)
            text_y = self.rect.y + (self.rect.height - placeholder_surface.get_height()) // 2
            surface.blit(placeholder_surface, (self.rect.x + 14, text_y))

        if self.active:
            active_surface = self.text_font.render(self.text, True, TEXT)
            caret_x = self.rect.x + 14 + active_surface.get_width() + 2
            pygame.draw.line(
                surface,
                ACCENT,
                (caret_x, self.rect.y + 11),
                (caret_x, self.rect.bottom - 11),
                2,
            )

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
        max_visible_options: int = 6,
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
        self.max_visible_options = max_visible_options
        self.scroll_offset = 0
        self.hovered_index = -1

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION and self.is_open:
            self.hovered_index = -1
            for option_rect, (option_index, _) in zip(self.option_rects(), self.visible_options()):
                if option_rect.collidepoint(event.pos):
                    self.hovered_index = option_index
                    break
        elif event.type == pygame.MOUSEWHEEL and self.is_open:
            mouse_pos = pygame.mouse.get_pos()
            if self.overlay_rect().collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                self.scroll_offset = max(0, min(self.scroll_offset - event.y, self.max_scroll_offset()))

    def handle_click(self, position: Tuple[int, int]) -> bool:
        if self.rect.collidepoint(position):
            self.is_open = not self.is_open
            if self.is_open and self.selected in self.options:
                selected_index = self.options.index(self.selected)
                self.scroll_offset = min(max(0, selected_index), self.max_scroll_offset())
            self.hovered_index = -1
            return True

        if self.is_open:
            for option_rect, (_, option_value) in zip(self.option_rects(), self.visible_options()):
                if option_rect.collidepoint(position):
                    self.selected = option_value
                    self.is_open = False
                    self.hovered_index = -1
                    return True
            self.close()

        return False

    def max_scroll_offset(self) -> int:
        return max(0, len(self.options) - self.max_visible_options)

    def visible_options(self) -> List[Tuple[int, str]]:
        start = self.scroll_offset
        end = min(start + self.max_visible_options, len(self.options))
        return list(enumerate(self.options[start:end], start=start))

    def overlay_rect(self) -> pygame.Rect:
        visible_count = min(len(self.options), self.max_visible_options)
        return pygame.Rect(
            self.rect.x,
            self.rect.bottom + 4,
            self.rect.width,
            self.option_height * visible_count,
        )

    def option_rects(self) -> List[pygame.Rect]:
        return [
            pygame.Rect(
                self.rect.x,
                self.rect.bottom + 4 + draw_index * self.option_height,
                self.rect.width,
                self.option_height,
            )
            for draw_index, _ in enumerate(self.visible_options())
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
        pygame.draw.polygon(
            surface,
            TEXT_MUTED,
            [
                (arrow_center_x - 6, arrow_center_y - 3),
                (arrow_center_x + 6, arrow_center_y - 3),
                (arrow_center_x, arrow_center_y + 4),
            ],
        )

    def draw_overlay(self, surface: pygame.Surface) -> None:
        if not self.is_open:
            return

        visible_options = self.visible_options()
        if not visible_options:
            return

        option_rects = self.option_rects()
        overlay_rect = self.overlay_rect()
        shadow_rect = overlay_rect.move(0, 4)
        pygame.draw.rect(surface, OVERLAY_SHADOW, shadow_rect, border_radius=12)
        pygame.draw.rect(surface, PANEL, overlay_rect, border_radius=12)
        pygame.draw.rect(surface, BORDER, overlay_rect, 2, border_radius=12)

        for option_rect, (option_index, option_value) in zip(option_rects, visible_options):
            fill = HOVER if option_index == self.hovered_index or option_value == self.selected else PANEL
            pygame.draw.rect(surface, fill, option_rect)
            option_text = self.text_font.render(option_value, True, TEXT)
            surface.blit(option_text, (option_rect.x + 14, option_rect.y + 4))

        if self.max_scroll_offset() > 0:
            track_rect = pygame.Rect(overlay_rect.right - 8, overlay_rect.y + 8, 4, overlay_rect.height - 16)
            thumb_height = max(24, int(track_rect.height * (self.max_visible_options / len(self.options))))
            travel = max(1, track_rect.height - thumb_height)
            thumb_y = track_rect.y + int(travel * (self.scroll_offset / self.max_scroll_offset()))
            thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
            pygame.draw.rect(surface, BORDER, track_rect, border_radius=4)
            pygame.draw.rect(surface, ACCENT, thumb_rect, border_radius=4)

        pygame.draw.rect(surface, BORDER, overlay_rect, 2, border_radius=12)

    def get_value(self) -> str:
        return self.selected or ""

    def close(self) -> None:
        self.is_open = False
        self.hovered_index = -1

    def clear(self) -> None:
        self.selected = None
        self.scroll_offset = 0
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
        surface.blit(label_surface, label_surface.get_rect(center=self.rect.center))

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )
