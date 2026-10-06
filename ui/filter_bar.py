"""Filter / sort bar made of flat 'chip' buttons (ImGui style)."""

import tkinter as tk
from typing import Callable, Iterable, List, Tuple

from config import LANE_ORDER, TYPE_ORDER
from ui.theme import ACCENT, BG, BORDER, PANEL2, TEXT, TEXT_DIM

SORT_OPTIONS = [("matches", "Most played"), ("winrate", "Winrate"), ("name", "Name")]


def ordered(values: Iterable[str], preferred: List[str]) -> List[str]:
    """Known names first (in preferred order), anything else alphabetically after."""
    values = set(values)
    known = [v for v in preferred if v in values]
    rest = sorted(values - set(preferred))
    return known + rest


class ChipRow(tk.Frame):
    """A labelled row of mutually exclusive chips. The first option is the default."""

    def __init__(self, parent, label: str, on_select: Callable[[], None]):
        super().__init__(parent, bg=BG)
        self._on_select = on_select
        self._chips = {}
        self.value = ""

        tk.Label(
            self, text=label, width=5, anchor="w",
            font=("Segoe UI", 9), fg=TEXT_DIM, bg=BG
        ).pack(side="left")
        self._holder = tk.Frame(self, bg=BG)
        self._holder.pack(side="left", fill="x")

    def set_options(self, options: List[Tuple[str, str]]):
        """options = [(value, text), ...]; keeps the current value if still present."""
        for w in self._holder.winfo_children():
            w.destroy()
        self._chips.clear()

        values = [v for v, _ in options]
        if self.value not in values:
            self.value = values[0] if values else ""

        for value, text in options:
            chip = tk.Label(
                self._holder, text=text, font=("Segoe UI", 9),
                padx=10, pady=3, cursor="hand2"
            )
            chip.pack(side="left", padx=(0, 4))
            chip.bind("<Button-1>", lambda e, v=value: self._select(v))
            chip.bind("<Enter>", lambda e, v=value: self._paint(v, hover=True))
            chip.bind("<Leave>", lambda e, v=value: self._paint(v))
            self._chips[value] = chip
        for v in values:
            self._paint(v)

    def _select(self, value: str):
        if value == self.value:
            return
        self.value = value
        for v in self._chips:
            self._paint(v)
        self._on_select()

    def _paint(self, value: str, hover: bool = False):
        chip = self._chips.get(value)
        if chip is None:
            return
        if value == self.value:
            chip.configure(bg=ACCENT, fg="white")
        else:
            chip.configure(bg=BORDER if hover else PANEL2, fg=TEXT)


class FilterBar(tk.Frame):
    """Type / Lane filters plus a Sort selector."""

    def __init__(self, parent, on_change: Callable[[], None]):
        super().__init__(parent, bg=BG)
        self._on_change = on_change

        self.type_row = ChipRow(self, "Type", on_change)
        self.lane_row = ChipRow(self, "Lane", on_change)
        self.sort_row = ChipRow(self, "Sort", on_change)
        for row in (self.type_row, self.lane_row, self.sort_row):
            row.pack(fill="x", padx=14, pady=(0, 4))

        self.type_row.set_options([("", "All")])
        self.lane_row.set_options([("", "All")])
        self.sort_row.set_options(SORT_OPTIONS)

    def set_hero_options(self, types: Iterable[str], lanes: Iterable[str]):
        self.type_row.set_options([("", "All")] + [(t, t) for t in ordered(types, TYPE_ORDER)])
        self.lane_row.set_options([("", "All")] + [(l, l) for l in ordered(lanes, LANE_ORDER)])

    @property
    def type_value(self) -> str:
        return self.type_row.value

    @property
    def lane_value(self) -> str:
        return self.lane_row.value

    @property
    def sort_value(self) -> str:
        return self.sort_row.value