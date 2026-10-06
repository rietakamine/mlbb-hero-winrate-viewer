"""Modal popup showing Classic / Rank / Combined stats for one hero."""

import tkinter as tk

from stats import calc_wr
from ui.theme import (
    ACCENT, ACCENT_HOV, BG, BORDER, CYAN, ORANGE, PANEL, PANEL2,
    PURPLE, TEXT, TEXT_BRIGHT, TEXT_DIM,
)


class StatsPopup(tk.Toplevel):
    def __init__(self, parent, name, photo, classic, rank, subtitle=""):
        super().__init__(parent)
        self.title(name)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        outer = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        outer.pack()
        frame = tk.Frame(outer, bg=PANEL, padx=20, pady=16)
        frame.pack()

        if photo:
            lbl = tk.Label(frame, image=photo, bg=PANEL)
            lbl.image = photo
            lbl.pack(pady=(0, 10))

        tk.Label(
            frame, text=name, font=("Segoe UI", 15, "bold"),
            fg=TEXT_BRIGHT, bg=PANEL
        ).pack(pady=(0, 2 if subtitle else 14))

        if subtitle:
            tk.Label(
                frame, text=subtitle, font=("Segoe UI", 9),
                fg=TEXT_DIM, bg=PANEL
            ).pack(pady=(0, 14))

        c_tot, c_win = classic
        r_tot, r_win = rank
        b_tot, b_win = c_tot + r_tot, c_win + r_win

        def stat_row(title, total, wins, color):
            row = tk.Frame(frame, bg=PANEL2, padx=12, pady=8)
            row.pack(fill="x", pady=3)
            tk.Label(
                row, text=title, font=("Segoe UI", 10, "bold"),
                fg=color, bg=PANEL2, width=10, anchor="w"
            ).pack(side="left")
            wr = calc_wr(total, wins)
            tk.Label(
                row,
                text=f"{wins}W / {total}   →   {wr:.1f}%",
                font=("Consolas", 11),
                fg=TEXT, bg=PANEL2
            ).pack(side="left", padx=6)

        stat_row("Classic", c_tot, c_win, CYAN)
        stat_row("Rank", r_tot, r_win, ORANGE)
        stat_row("Both", b_tot, b_win, PURPLE)

        btn = tk.Button(
            frame, text="Close", font=("Segoe UI", 9),
            bg=ACCENT, fg="white", activebackground=ACCENT_HOV,
            activeforeground="white", relief="flat", bd=0,
            padx=18, pady=4, cursor="hand2",
            command=self.destroy
        )
        btn.pack(pady=(14, 0))

        # The portrait image makes this window tall: keep it fully on screen.
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = parent.winfo_rootx() + 60
        y = parent.winfo_rooty() + 60
        x = max(0, min(x, self.winfo_screenwidth() - w - 20))
        y = max(0, min(y, self.winfo_screenheight() - h - 60))
        self.geometry(f"+{x}+{y}")