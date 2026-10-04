"""Clickable hero portrait card for the grid."""

import tkinter as tk

from stats import calc_wr
from ui.theme import ACCENT, BORDER, PANEL, PANEL2, TEXT, TEXT_DIM


class HeroCard(tk.Frame):
    def __init__(self, parent, hero_id, name, photo, classic, rank, on_click):
        super().__init__(parent, bg=PANEL, padx=3, pady=3)
        self.hero_id = hero_id
        self.name = name
        self.photo = photo
        self.classic = classic
        self.rank = rank
        self.on_click = on_click

        # subtle border via outer frame
        self.configure(highlightbackground=BORDER, highlightthickness=1)

        if photo:
            img_lbl = tk.Label(self, image=photo, bg=PANEL, cursor="hand2")
            img_lbl.image = photo
            img_lbl.pack()
            img_lbl.bind("<Button-1>", self._click)
            img_lbl.bind("<Enter>", self._hover_in)
            img_lbl.bind("<Leave>", self._hover_out)
        else:
            ph = tk.Label(
                self, text="?", font=("Segoe UI", 24),
                width=4, height=2, bg=PANEL2, fg=TEXT_DIM, cursor="hand2"
            )
            ph.pack()
            ph.bind("<Button-1>", self._click)

        b_tot = classic[0] + rank[0]
        b_win = classic[1] + rank[1]
        wr = calc_wr(b_tot, b_win)

        tk.Label(
            self, text=name[:11], font=("Segoe UI", 8, "bold"),
            fg=TEXT, bg=PANEL, cursor="hand2"
        ).pack()
        tk.Label(
            self, text=f"{wr:.0f}%  ·  {b_tot}", font=("Consolas", 8),
            fg=TEXT_DIM, bg=PANEL, cursor="hand2"
        ).pack()

        for w in self.winfo_children():
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._hover_in)
        self.bind("<Leave>", self._hover_out)

    def _click(self, _=None):
        self.on_click(self)

    def _hover_in(self, _=None):
        self.configure(highlightbackground=ACCENT, highlightthickness=1)

    def _hover_out(self, _=None):
        self.configure(highlightbackground=BORDER, highlightthickness=1)
