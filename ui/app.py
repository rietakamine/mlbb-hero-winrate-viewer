"""Main application window."""

import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import messagebox
from typing import Dict

from PIL import ImageTk

from api import fetch_all_heroes, fetch_player_winlist
from config import ICON_SIZE
from images import download_image, make_rounded
from stats import parse_winlist
from ui.hero_card import HeroCard
from ui.popup import StatsPopup
from ui.scrollbar import ThinScrollbar
from ui.theme import (
    ACCENT, ACCENT_HOV, BG, BORDER, CARD_PAD, COLS, PANEL, TEXT,
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
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._wheel)

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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

    # --- Grid building ---------------------------------------------------
    def _build(self, classic, rank, uid):
        self.classic = classic
        self.rank = rank
        self.fetch_btn.configure(state="normal")

        ids = sorted(
            set(classic) | set(rank),
            key=lambda h: -(classic.get(h, (0, 0))[0] + rank.get(h, (0, 0))[0])
        )
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
            self.after(0, lambda: self._place(ids, pil, uid))

        threading.Thread(target=load, daemon=True).start()

    def _place(self, ids, pil_images, uid):
        for h, img in pil_images.items():
            if img:
                self.photo_cache[h] = ImageTk.PhotoImage(img)

        for i, hid in enumerate(ids):
            name = self.heroes.get(hid, {}).get("name", f"#{hid}")
            photo = self.photo_cache.get(hid)
            card = HeroCard(
                self.grid_frame, hid, name, photo,
                self.classic.get(hid, (0, 0)),
                self.rank.get(hid, (0, 0)),
                on_click=self._show
            )
            r, c = divmod(i, COLS)
            card.grid(row=r, column=c, padx=CARD_PAD, pady=CARD_PAD)

        self.status_var.set(f"{uid} · {len(ids)} heroes · click portrait for details")
        self.grid_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _show(self, card: HeroCard):
        url = self.heroes.get(card.hero_id, {}).get("head_big", "")
        large = download_image(url, size=128, hero_id=card.hero_id)
        photo = ImageTk.PhotoImage(make_rounded(large, 10)) if large else card.photo
        StatsPopup(self, card.name, photo, card.classic, card.rank)
