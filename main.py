#!/usr/bin/env python3
"""
MLBB Hero Winrate Viewer – ImGui-inspired dark UI
- Grid of hero portraits (head_big)
- Click a hero → popup with Classic / Rank / Combined stats

Entry point. Run with:  python main.py
"""

from ui.app import App


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
