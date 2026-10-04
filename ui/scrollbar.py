"""Minimal thin scrollbar (ImGui style)."""

import tkinter as tk

from ui.theme import BG, BORDER


class ThinScrollbar(tk.Canvas):
    """Minimal modern scrollbar."""

    def __init__(self, parent, command, **kwargs):
        super().__init__(
            parent,
            width=8,
            bg=BG,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.command = command
        self._thumb = None
        self._start = 0.0
        self._end = 1.0
        self.bind("<Button-1>", self._click)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<MouseWheel>", lambda e: "break")

    def set(self, first, last):
        self._start = float(first)
        self._end = float(last)
        self._redraw()

    def _redraw(self):
        self.delete("all")
        h = self.winfo_height()
        if h <= 1:
            return
        thumb_h = max(20, int((self._end - self._start) * h))
        y0 = int(self._start * h)
        self._thumb = self.create_rectangle(
            1, y0, 7, y0 + thumb_h,
            fill=BORDER, outline="",
            tags="thumb",
        )

    def _click(self, event):
        self._drag(event)

    def _drag(self, event):
        h = self.winfo_height()
        if h <= 0:
            return
        ratio = event.y / h
        self.command("moveto", max(0.0, min(1.0, ratio - (self._end - self._start) / 2)))
