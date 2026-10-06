"""Main application window."""

import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import messagebox
from typing import Dict, List

from PIL import ImageTk

from api import fetch_all_heroes, fetch_player_winlist
from config import ICON_SIZE, POPUP_ICON_SIZE, POPUP_SMALLMAP_SIZE
from images import download_image, make_rounded
from stats import calc_wr, parse_winlist
from ui.filter_bar import FilterBar
from ui.hero_card import HeroCard
from ui.popup import StatsPopup
from ui.scrollbar import ThinScrollbar
from ui.theme import (
    ACCENT, ACCENT_HOV, BG, BORDER, CARD_PAD, PANEL, TEXT,
    TEXT_BRIGHT, TEXT_DIM,
)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MLBB Hero Winrates")
        self.geometry("960x700")
        self.minsize(780, 560)
        self.configure(bg=BG)

        self.heroes: Dict[int, dict] = {}
        self.photo_cache: Dict[int, ImageTk.PhotoImage] = {}
        self.classic = {}
        self.rank = {}

        self.uid = ""
        self.cards: Dict[int, HeroCard] = {}   # every card for the current player
        self._visible: List[int] = []          # hero ids shown, in display order
        self._cols = 0
        self._reflow_job = None

        self._build_ui()
        self._load_heroes_async()

    # --- UI construction -------------------------------------------------
    def _build_ui(self):
        # --- Top bar ---
        top = tk.Frame(self, bg=PANEL, height=48)
        top.pack(fill="x")
        top.pack_propagate(False)

        inner = tk.Frame(top, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=14, pady=8)

        tk.Label(
            inner, text="MLBB Winrates", font=("Segoe UI", 12, "bold"),
            fg=TEXT_BRIGHT, bg=PANEL
        ).pack(side="left", padx=(0, 20))

        tk.Label(
            inner, text="UID", font=("Segoe UI", 9),
            fg=TEXT_DIM, bg=PANEL
        ).pack(side="left", padx=(0, 6))

        self.uid_var = tk.StringVar()
        entry = tk.Entry(
            inner, textvariable=self.uid_var, font=("Consolas", 11),
            width=16, bg=BG, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT
        )
        entry.pack(side="left", ipady=3, padx=(0, 8))
        entry.bind("<Return>", lambda e: self.start_fetch())

        self.fetch_btn = tk.Button(
            inner, text="Fetch", font=("Segoe UI", 9),
            bg=ACCENT, fg="white", activebackground=ACCENT_HOV,
            activeforeground="white", relief="flat", bd=0,
            padx=14, pady=2, cursor="hand2",
            command=self.start_fetch
        )
        self.fetch_btn.pack(side="left")

        self.status_var = tk.StringVar(value="Loading heroes…")
        tk.Label(
            inner, textvariable=self.status_var, font=("Segoe UI", 9),
            fg=TEXT_DIM, bg=PANEL
        ).pack(side="right")

        # --- Filter / sort bar ---
        self.filter_bar = FilterBar(self, on_change=self._apply_view)
        self.filter_bar.pack(fill="x", pady=(8, 0))

        # --- Content area ---
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(content, bg=BG, highlightthickness=0, bd=0)
        self.scrollbar = ThinScrollbar(content, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._wheel)

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        # debounce: re-flow the grid once resizing settles
        if self._reflow_job is not None:
            self.after_cancel(self._reflow_job)
        self._reflow_job = self.after(60, self._reflow)

    # --- Data loading ----------------------------------------------------
    def _load_heroes_async(self):
        def work():
            try:
                heroes = fetch_all_heroes()
                self.after(0, lambda: self._on_heroes(heroes))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Error: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _on_heroes(self, heroes):
        self.heroes = heroes
        types = {t for h in heroes.values() for t in h.get("types", [])}
        lanes = {l for h in heroes.values() for l in h.get("lanes", [])}
        self.filter_bar.set_hero_options(types, lanes)
        self.status_var.set(f"{len(heroes)} heroes ready · enter UID")

    def start_fetch(self):
        uid = self.uid_var.get().strip()
        if not uid:
            messagebox.showwarning("UID", "Enter a Player UID")
            return
        if not uid.isdigit():
            messagebox.showwarning("UID", "UID must be numeric")
            return

        self.fetch_btn.configure(state="disabled")
        self.status_var.set(f"Fetching {uid}…")
        self._clear()

        def work():
            try:
                raw = fetch_player_winlist(uid)
                classic, rank = parse_winlist(raw)
                self.after(0, lambda: self._build(classic, rank, uid))
            except Exception as e:
                self.after(0, lambda: self._err(str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _err(self, msg):
        self.fetch_btn.configure(state="normal")
        self.status_var.set("Error")
        messagebox.showerror("Error", msg)

    def _clear(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.photo_cache.clear()
        self.cards.clear()
        self._visible = []
        self._cols = 0

    # --- Grid building ---------------------------------------------------
    def _build(self, classic, rank, uid):
        self.classic = classic
        self.rank = rank
        self.uid = uid
        self.fetch_btn.configure(state="normal")

        ids = sorted(set(classic) | set(rank), key=lambda h: -self._totals(h)[0])
        if not ids:
            self.status_var.set(f"No data for {uid}")
            return

        self.status_var.set(f"Loading {len(ids)} portraits…")

        def load():
            pil = {}
            with ThreadPoolExecutor(max_workers=12) as pool:
                futs = {
                    pool.submit(
                        download_image,
                        self.heroes.get(h, {}).get("head_big", ""),
                        ICON_SIZE,
                        h,  # hero_id for cache
                    ): h
                    for h in ids
                }
                for fut in as_completed(futs):
                    h = futs[fut]
                    img = fut.result()
                    pil[h] = make_rounded(img) if img else None
            self.after(0, lambda: self._place(ids, pil))

        threading.Thread(target=load, daemon=True).start()

    def _place(self, ids, pil_images):
        for h, img in pil_images.items():
            if img:
                self.photo_cache[h] = ImageTk.PhotoImage(img)

        # Create every card once; filtering/sorting only re-grids them.
        for hid in ids:
            name = self.heroes.get(hid, {}).get("name", f"#{hid}")
            self.cards[hid] = HeroCard(
                self.grid_frame, hid, name, self.photo_cache.get(hid),
                self.classic.get(hid, (0, 0)),
                self.rank.get(hid, (0, 0)),
                on_click=self._show
            )
        self._apply_view()

    # --- Filtering / sorting / responsive layout -------------------------
    def _totals(self, hid):
        c = self.classic.get(hid, (0, 0))
        r = self.rank.get(hid, (0, 0))
        return c[0] + r[0], c[1] + r[1]

    def _apply_view(self):
        """Filter by type/lane, sort, then re-grid."""
        if not self.cards:
            return

        want_type = self.filter_bar.type_value
        want_lane = self.filter_bar.lane_value
        sort_by = self.filter_bar.sort_value

        def matches(hid):
            hero = self.heroes.get(hid, {})
            return (
                (not want_type or want_type in hero.get("types", []))
                and (not want_lane or want_lane in hero.get("lanes", []))
            )

        def sort_key(hid):
            total, wins = self._totals(hid)
            if sort_by == "winrate":
                return (-calc_wr(total, wins), -total)
            if sort_by == "name":
                return self.cards[hid].name.lower()
            return -total  # most played

        self._visible = sorted((h for h in self.cards if matches(h)), key=sort_key)

        for card in self.cards.values():
            card.grid_forget()

        if self._visible:
            self.status_var.set(
                f"{self.uid} · {len(self._visible)}/{len(self.cards)} heroes · click portrait for details"
            )
        else:
            self.status_var.set(f"{self.uid} · no heroes match this filter")

        self._reflow(force=True)
        self.canvas.yview_moveto(0)

    def _reflow(self, force=False):
        """Lay the visible cards out in as many columns as the window fits."""
        self._reflow_job = None
        if not self._visible:
            return

        self.grid_frame.update_idletasks()  # make sure card sizes are up to date
        avail = self.canvas.winfo_width()
        cell_w = max(self.cards[h].winfo_reqwidth() for h in self._visible) + 2 * CARD_PAD
        cols = max(1, avail // cell_w)

        if not force and cols == self._cols:
            return

        # equal-width, stretchy columns; reset any columns left over from a wider layout
        for c in range(max(self._cols, cols)):
            if c < cols:
                self.grid_frame.grid_columnconfigure(c, weight=1, uniform="cards")
            else:
                self.grid_frame.grid_columnconfigure(c, weight=0, uniform="")

        for i, hid in enumerate(self._visible):
            r, c = divmod(i, cols)
            self.cards[hid].grid(row=r, column=c, padx=CARD_PAD, pady=CARD_PAD)

        self._cols = cols
        self.grid_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # --- Popup -----------------------------------------------------------
    def _show(self, card: HeroCard):
        hero = self.heroes.get(card.hero_id, {})
        smallmap = hero.get("smallmap", "")
        head_big = hero.get("head_big", "")
        subtitle = "  ·  ".join(
            p for p in ("/".join(hero.get("types", [])), "/".join(hero.get("lanes", []))) if p
        )

        def work():
            img = None
            if smallmap:
                img = download_image(smallmap, POPUP_SMALLMAP_SIZE, card.hero_id, "smallmap")
            if img is None:  # no smallmap (or it failed) → fall back to the square portrait
                img = download_image(head_big, POPUP_ICON_SIZE, card.hero_id)
            self.after(0, lambda: self._open_popup(card, img, subtitle))

        threading.Thread(target=work, daemon=True).start()

    def _open_popup(self, card, img, subtitle):
        photo = ImageTk.PhotoImage(make_rounded(img, 10)) if img else card.photo
        StatsPopup(self, card.name, photo, card.classic, card.rank, subtitle)