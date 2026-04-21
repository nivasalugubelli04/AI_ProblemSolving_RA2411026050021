"""
Tourist Travel Planner
======================
A Tkinter GUI application for planning trips, managing destinations,
tracking budget, building itineraries, and packing lists.

Features:
  ① Destination Manager  — add/remove/search destinations with details
  ② Trip Itinerary       — day-by-day activity planner with timeline view
  ③ Budget Tracker       — categorized expense tracker with visual chart
  ④ Packing List         — smart checklist with categories and progress bar
  ⑤ Trip Summary         — overview card with all trip info exportable to TXT

No external dependencies required — uses only Python standard library.

Run:
    python TouristTravelPlanner.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import math
import datetime
import random

# ─── Palette ──────────────────────────────────────────────────────────────────
BG        = "#f7f8fc"
SURFACE   = "#ffffff"
SIDEBAR   = "#0f172a"
BORDER    = "#e2e8f0"
INPUT_BG  = "#f1f5f9"

TEAL      = "#0d9488"
TEAL_LT   = "#ccfbf1"
BLUE      = "#2563eb"
BLUE_LT   = "#dbeafe"
AMBER     = "#d97706"
AMBER_LT  = "#fef3c7"
RED       = "#dc2626"
RED_LT    = "#fee2e2"
GREEN     = "#16a34a"
GREEN_LT  = "#dcfce7"
PURPLE    = "#7c3aed"
PURPLE_LT = "#ede9fe"
CORAL     = "#ea580c"
CORAL_LT  = "#ffedd5"

DARK      = "#0f172a"
MID       = "#64748b"
LIGHT     = "#94a3b8"
WHITE     = "#ffffff"

FONT_H1   = ("Georgia", 20, "bold")
FONT_H2   = ("Georgia", 13, "bold")
FONT_H3   = ("Georgia", 11, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SM   = ("Helvetica", 9)
FONT_MONO = ("Courier New", 10)
FONT_BTN  = ("Helvetica", 10, "bold")
FONT_TINY = ("Helvetica", 8)

# ─── Data Store ───────────────────────────────────────────────────────────────
class TripData:
    def __init__(self):
        self.trip_name    = "My Dream Trip"
        self.trip_start   = ""
        self.trip_end     = ""
        self.travelers    = 1
        self.currency     = "USD"
        self.total_budget = 0.0
        self.destinations = []   # [{name, country, days, notes, rating}]
        self.itinerary    = {}   # {day_num: [{time, activity, location, type}]}
        self.expenses     = []   # [{category, item, amount, date}]
        self.packing      = []   # [{category, item, packed}]

    def to_dict(self):
        return self.__dict__

    def from_dict(self, d):
        for k, v in d.items():
            setattr(self, k, v)


# ─── Main App ─────────────────────────────────────────────────────────────────
class TravelPlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tourist Travel Planner")
        self.configure(bg=BG)
        self.minsize(1100, 720)
        self.resizable(True, True)

        self.data = TripData()
        self._active_section = None

        self._build_ui()
        self._load_sample_data()

    # ── Root layout ───────────────────────────────────────────────────────────
    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        # Sidebar
        sb = tk.Frame(root, bg=SIDEBAR, width=210)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self._build_sidebar(sb)

        # Right: header + scrollable content
        right = tk.Frame(root, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Top header bar
        self._build_header(right)

        # Scrollable main area
        scroll_frame = tk.Frame(right, bg=BG)
        scroll_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(scroll_frame, bg=BG, highlightthickness=0)
        self._canvas.pack(side="left", fill="both", expand=True)
        vsb = tk.Scrollbar(scroll_frame, orient="vertical",
                           command=self._canvas.yview)
        vsb.pack(side="right", fill="y")
        self._canvas.configure(yscrollcommand=vsb.set)

        self._content = tk.Frame(self._canvas, bg=BG)
        self._win = self._canvas.create_window(
            (0, 0), window=self._content, anchor="nw")

        self._content.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._win, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Build all sections into content
        self._build_sections(self._content)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=SURFACE,
                       highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=SURFACE)
        inner.pack(fill="x", padx=24, pady=12)

        self.trip_name_var = tk.StringVar(value=self.data.trip_name)
        name_entry = tk.Entry(inner, textvariable=self.trip_name_var,
                              font=FONT_H1, bg=SURFACE, fg=DARK,
                              relief="flat", bd=0, insertbackground=TEAL)
        name_entry.pack(side="left")
        name_entry.bind("<FocusOut>",
            lambda e: setattr(self.data, "trip_name",
                               self.trip_name_var.get()))

        right_hdr = tk.Frame(inner, bg=SURFACE)
        right_hdr.pack(side="right")
        self._btn_small(right_hdr, "💾 Save", self._save_trip, TEAL, "right")
        self._btn_small(right_hdr, "📂 Load", self._load_trip, MID, "right")
        self._btn_small(right_hdr, "📄 Export TXT",
                        self._export_txt, BLUE, "right")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, sb):
        # Logo
        logo = tk.Frame(sb, bg=SIDEBAR)
        logo.pack(fill="x", pady=20, padx=16)
        tk.Label(logo, text="✈", font=("Georgia", 28), bg=SIDEBAR,
                 fg=TEAL).pack(side="left")
        tk.Label(logo, text=" Travel\nPlanner", font=("Georgia", 13, "bold"),
                 bg=SIDEBAR, fg=WHITE, justify="left").pack(side="left", padx=6)

        tk.Frame(sb, bg="#1e293b", height=1).pack(fill="x", padx=16, pady=4)

        nav = [
            ("🗺  Destinations",  self._goto_destinations),
            ("📅  Itinerary",     self._goto_itinerary),
            ("💰  Budget",        self._goto_budget),
            ("🧳  Packing List",  self._goto_packing),
            ("📋  Trip Summary",  self._goto_summary),
        ]
        self._nav_buttons = []
        for label, cmd in nav:
            b = tk.Button(sb, text=label, font=FONT_BODY,
                          bg=SIDEBAR, fg="#94a3b8",
                          activebackground=TEAL, activeforeground=WHITE,
                          relief="flat", anchor="w",
                          padx=20, pady=11, cursor="hand2", command=cmd)
            b.pack(fill="x")
            self._nav_buttons.append(b)

        tk.Frame(sb, bg="#1e293b", height=1).pack(fill="x", padx=16, pady=16)

        # Quick stats in sidebar
        tk.Label(sb, text="QUICK STATS", font=FONT_TINY,
                 bg=SIDEBAR, fg="#475569", anchor="w").pack(
            fill="x", padx=20, pady=(0, 6))

        self.stat_dest  = self._sidebar_stat(sb, "Destinations", "0")
        self.stat_days  = self._sidebar_stat(sb, "Total Days",   "0")
        self.stat_spent = self._sidebar_stat(sb, "Total Spent",  "$0")
        self.stat_items = self._sidebar_stat(sb, "Packed Items", "0/0")

    def _sidebar_stat(self, parent, label, val):
        f = tk.Frame(parent, bg=SIDEBAR)
        f.pack(fill="x", padx=20, pady=2)
        tk.Label(f, text=label, font=FONT_TINY,
                 bg=SIDEBAR, fg="#64748b", anchor="w").pack(fill="x")
        v = tk.StringVar(value=val)
        tk.Label(f, textvariable=v, font=("Helvetica", 11, "bold"),
                 bg=SIDEBAR, fg=WHITE, anchor="w").pack(fill="x")
        return v

    def _nav_highlight(self, idx):
        for i, b in enumerate(self._nav_buttons):
            b.configure(bg=TEAL if i == idx else SIDEBAR,
                        fg=WHITE if i == idx else "#94a3b8")

    def _goto_destinations(self): self._scroll_to(self._sec_dest);  self._nav_highlight(0)
    def _goto_itinerary(self):    self._scroll_to(self._sec_itin);  self._nav_highlight(1)
    def _goto_budget(self):       self._scroll_to(self._sec_budget);self._nav_highlight(2)
    def _goto_packing(self):      self._scroll_to(self._sec_pack);  self._nav_highlight(3)
    def _goto_summary(self):      self._scroll_to(self._sec_summ);  self._nav_highlight(4)

    def _scroll_to(self, widget):
        self.update_idletasks()
        total = self._content.winfo_height()
        y     = widget.winfo_y()
        self._canvas.yview_moveto(y / max(total, 1))

    # ── All Sections ──────────────────────────────────────────────────────────
    def _build_sections(self, parent):
        P = dict(padx=24, pady=10)
        self._sec_dest   = self._build_destinations(parent, P)
        self._sec_itin   = self._build_itinerary(parent, P)
        self._sec_budget = self._build_budget(parent, P)
        self._sec_pack   = self._build_packing(parent, P)
        self._sec_summ   = self._build_summary(parent, P)

    # ── ① Destinations ────────────────────────────────────────────────────────
    def _build_destinations(self, parent, P):
        sec = self._section(parent, "🗺  Destination Manager", TEAL, P)

        cols = tk.Frame(sec, bg=SURFACE)
        cols.pack(fill="x", padx=16, pady=8)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=2)

        # Input form
        form = self._mini_section(cols, "Add Destination", 0)

        fields = [
            ("City / Place",  "dest_city",    "e.g. Paris"),
            ("Country",       "dest_country", "e.g. France"),
            ("Days Planned",  "dest_days",    "e.g. 4"),
            ("Est. Cost ($)", "dest_cost",    "e.g. 1200"),
        ]
        self._dest_vars = {}
        for label, key, hint in fields:
            r = tk.Frame(form, bg=INPUT_BG)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=FONT_SM, bg=INPUT_BG,
                     fg=MID, width=14, anchor="w").pack(side="left", padx=6)
            v = tk.StringVar()
            e = tk.Entry(r, textvariable=v, font=FONT_BODY,
                         bg=SURFACE, fg=DARK, relief="solid", bd=1,
                         width=18)
            e.pack(side="left", ipady=4)
            e.insert(0, hint)
            e.bind("<FocusIn>",
                lambda ev, h=hint, en=e: en.delete(0,"end")
                if en.get()==h else None)
            e.configure(fg=LIGHT)
            e.bind("<Key>", lambda ev, en=e: en.configure(fg=DARK))
            self._dest_vars[key] = v

        tk.Label(form, text="Notes", font=FONT_SM,
                 bg=INPUT_BG, fg=MID, anchor="w").pack(
            fill="x", padx=6, pady=(6, 2))
        self.dest_notes = tk.Text(form, height=3, font=FONT_SM,
                                  bg=SURFACE, fg=DARK,
                                  relief="solid", bd=1, padx=6, pady=4)
        self.dest_notes.pack(fill="x", padx=6)

        tk.Label(form, text="Rating", font=FONT_SM,
                 bg=INPUT_BG, fg=MID, anchor="w").pack(
            fill="x", padx=6, pady=(6, 2))
        self.dest_rating = tk.IntVar(value=5)
        star_row = tk.Frame(form, bg=INPUT_BG)
        star_row.pack(anchor="w", padx=6)
        for i in range(1, 6):
            tk.Radiobutton(star_row, text=f"{'★'*i}", variable=self.dest_rating,
                           value=i, bg=INPUT_BG, fg=AMBER,
                           activebackground=INPUT_BG,
                           font=FONT_SM, selectcolor=INPUT_BG).pack(side="left")

        btn_row = tk.Frame(form, bg=INPUT_BG)
        btn_row.pack(fill="x", padx=6, pady=8)
        self._btn_inline(btn_row, "+ Add", self._add_destination, TEAL)
        self._btn_inline(btn_row, "Clear", self._clear_dest_form, MID)

        # Destinations list
        list_f = self._mini_section(cols, "Your Destinations", 1)

        # Search bar
        search_row = tk.Frame(list_f, bg=INPUT_BG)
        search_row.pack(fill="x", pady=(0, 6))
        tk.Label(search_row, text="🔍", font=FONT_SM,
                 bg=INPUT_BG, fg=MID).pack(side="left", padx=6)
        self.dest_search_var = tk.StringVar()
        self.dest_search_var.trace("w", lambda *a: self._refresh_dest_list())
        tk.Entry(search_row, textvariable=self.dest_search_var,
                 font=FONT_BODY, bg=SURFACE, fg=DARK,
                 relief="solid", bd=1).pack(
            side="left", fill="x", expand=True, ipady=4, padx=4)

        # Destination cards frame (scrollable)
        dest_canvas = tk.Canvas(list_f, bg=INPUT_BG, height=280,
                                highlightthickness=0)
        dest_canvas.pack(fill="x")
        dest_vsb = tk.Scrollbar(list_f, orient="vertical",
                                command=dest_canvas.yview)
        dest_canvas.configure(yscrollcommand=dest_vsb.set)
        self.dest_cards_frame = tk.Frame(dest_canvas, bg=INPUT_BG)
        dest_canvas.create_window((0,0), window=self.dest_cards_frame,
                                  anchor="nw")
        self.dest_cards_frame.bind("<Configure>",
            lambda e: dest_canvas.configure(
                scrollregion=dest_canvas.bbox("all")))

        # Summary stats row
        self.dest_stats_var = tk.StringVar(value="No destinations added yet.")
        tk.Label(list_f, textvariable=self.dest_stats_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID, anchor="w").pack(
            fill="x", pady=4)

        return sec

    def _add_destination(self):
        city    = self.dest_vars["dest_city"].get().strip()
        country = self.dest_vars["dest_country"].get().strip()
        if not city or city == "e.g. Paris":
            messagebox.showwarning("Missing", "Enter a city name.")
            return
        try:
            days = int(self.dest_vars["dest_days"].get())
            cost = float(self.dest_vars["dest_cost"].get())
        except ValueError:
            days, cost = 1, 0.0

        dest = {
            "name":    city,
            "country": country,
            "days":    days,
            "cost":    cost,
            "notes":   self.dest_notes.get("1.0", "end").strip(),
            "rating":  self.dest_rating.get(),
            "id":      random.randint(10000, 99999),
        }
        self.data.destinations.append(dest)
        self._clear_dest_form()
        self._refresh_dest_list()
        self._refresh_itinerary_days()
        self._update_sidebar_stats()

    def _clear_dest_form(self):
        hints = {"dest_city":"e.g. Paris","dest_country":"e.g. France",
                 "dest_days":"e.g. 4","dest_cost":"e.g. 1200"}
        for k,h in hints.items():
            self.dest_vars[k].set(h)
        self.dest_notes.delete("1.0","end")
        self.dest_rating.set(5)

    def _refresh_dest_list(self):
        for w in self.dest_cards_frame.winfo_children():
            w.destroy()
        q = self.dest_search_var.get().lower()
        shown = [d for d in self.data.destinations
                 if q in d["name"].lower() or q in d["country"].lower()]

        if not shown:
            tk.Label(self.dest_cards_frame, text="No destinations yet.",
                     font=FONT_SM, bg=INPUT_BG, fg=LIGHT).pack(pady=20)
        for dest in shown:
            self._dest_card(self.dest_cards_frame, dest)

        total_days = sum(d["days"] for d in self.data.destinations)
        total_cost = sum(d["cost"] for d in self.data.destinations)
        self.dest_stats_var.set(
            f"{len(self.data.destinations)} destinations  ·  "
            f"{total_days} total days  ·  "
            f"${total_cost:,.0f} est. cost")

    def _dest_card(self, parent, dest):
        colors = [TEAL, BLUE, PURPLE, CORAL, GREEN, AMBER]
        color  = colors[hash(dest["name"]) % len(colors)]
        card = tk.Frame(parent, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=4, pady=4)

        left_bar = tk.Frame(card, bg=color, width=5)
        left_bar.pack(side="left", fill="y")

        body = tk.Frame(card, bg=SURFACE)
        body.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        top = tk.Frame(body, bg=SURFACE)
        top.pack(fill="x")
        tk.Label(top, text=f"{dest['name']}, {dest['country']}",
                 font=FONT_H3, bg=SURFACE, fg=DARK).pack(side="left")
        tk.Label(top, text="★" * dest["rating"],
                 font=FONT_SM, bg=SURFACE, fg=AMBER).pack(side="right")

        info = tk.Frame(body, bg=SURFACE)
        info.pack(fill="x", pady=2)
        self._badge(info, f"📅 {dest['days']} days", BLUE_LT, BLUE)
        self._badge(info, f"💵 ${dest['cost']:,.0f}", GREEN_LT, GREEN)
        if dest.get("notes"):
            tk.Label(body, text=dest["notes"][:60],
                     font=FONT_TINY, bg=SURFACE, fg=LIGHT).pack(anchor="w")

        del_btn = tk.Button(card, text="✕", font=FONT_TINY,
                            bg=SURFACE, fg=LIGHT, relief="flat",
                            cursor="hand2",
                            command=lambda d=dest: self._remove_dest(d))
        del_btn.pack(side="right", padx=8)

    def _remove_dest(self, dest):
        self.data.destinations = [
            d for d in self.data.destinations if d["id"] != dest["id"]]
        self._refresh_dest_list()
        self._refresh_itinerary_days()
        self._update_sidebar_stats()

    # ── ② Itinerary ───────────────────────────────────────────────────────────
    def _build_itinerary(self, parent, P):
        sec = self._section(parent, "📅  Day-by-Day Itinerary", BLUE, P)

        top = tk.Frame(sec, bg=SURFACE)
        top.pack(fill="x", padx=16, pady=(0,8))

        # Day selector
        tk.Label(top, text="Day:", font=FONT_BODY,
                 bg=SURFACE, fg=MID).pack(side="left")
        self.itin_day_var = tk.StringVar()
        self.itin_day_cb = ttk.Combobox(top, textvariable=self.itin_day_var,
                                        state="readonly", width=12)
        self.itin_day_cb.pack(side="left", padx=8)
        self.itin_day_cb.bind("<<ComboboxSelected>>",
                              lambda e: self._refresh_timeline())

        cols = tk.Frame(sec, bg=SURFACE)
        cols.pack(fill="both", expand=True, padx=16, pady=4)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=2)

        # Add activity form
        form = self._mini_section(cols, "Add Activity", 0)
        itin_fields = [
            ("Time",     "itin_time",     "e.g. 09:00"),
            ("Activity", "itin_act",      "e.g. Visit Eiffel Tower"),
            ("Location", "itin_loc",      "e.g. Champ de Mars"),
        ]
        self._itin_vars = {}
        for label, key, hint in itin_fields:
            r = tk.Frame(form, bg=INPUT_BG)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=FONT_SM, bg=INPUT_BG,
                     fg=MID, width=10, anchor="w").pack(side="left", padx=6)
            v = tk.StringVar()
            e = tk.Entry(r, textvariable=v, font=FONT_BODY,
                         bg=SURFACE, fg=DARK, relief="solid", bd=1, width=22)
            e.pack(side="left", ipady=4)
            e.insert(0, hint)
            e.configure(fg=LIGHT)
            e.bind("<FocusIn>",
                lambda ev, h=hint, en=e: en.delete(0,"end")
                if en.get()==h else None)
            e.bind("<Key>", lambda ev, en=e: en.configure(fg=DARK))
            self._itin_vars[key] = v

        tk.Label(form, text="Type", font=FONT_SM,
                 bg=INPUT_BG, fg=MID, anchor="w").pack(
            fill="x", padx=6, pady=(6,2))
        self.itin_type_var = tk.StringVar(value="Sightseeing")
        type_cb = ttk.Combobox(form, textvariable=self.itin_type_var,
                               state="readonly",
                               values=["Sightseeing","Food & Drink",
                                       "Transport","Adventure","Shopping",
                                       "Relaxation","Culture","Other"])
        type_cb.pack(fill="x", padx=6, ipady=4)

        btn_r = tk.Frame(form, bg=INPUT_BG)
        btn_r.pack(fill="x", padx=6, pady=8)
        self._btn_inline(btn_r, "+ Add Activity", self._add_activity, BLUE)

        # Timeline view
        tl_f = self._mini_section(cols, "Timeline", 1)
        self.timeline_canvas = tk.Canvas(tl_f, bg=INPUT_BG,
                                         height=320, highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True)
        tl_vsb = tk.Scrollbar(tl_f, orient="vertical",
                              command=self.timeline_canvas.yview)
        tl_vsb.pack(side="right", fill="y")
        self.timeline_canvas.configure(yscrollcommand=tl_vsb.set)

        self.timeline_inner = tk.Frame(self.timeline_canvas, bg=INPUT_BG)
        self.tl_win = self.timeline_canvas.create_window(
            (0,0), window=self.timeline_inner, anchor="nw")
        self.timeline_inner.bind("<Configure>",
            lambda e: self.timeline_canvas.configure(
                scrollregion=self.timeline_canvas.bbox("all")))
        self.timeline_canvas.bind("<Configure>",
            lambda e: self.timeline_canvas.itemconfig(
                self.tl_win, width=e.width))

        return sec

    def _refresh_itinerary_days(self):
        total = sum(d["days"] for d in self.data.destinations)
        days = [f"Day {i+1}" for i in range(total)]
        self.itin_day_cb["values"] = days
        if days and not self.itin_day_var.get():
            self.itin_day_var.set(days[0])
        self._refresh_timeline()

    def _add_activity(self):
        day = self.itin_day_var.get()
        if not day:
            messagebox.showwarning("No day", "Select a day first.")
            return
        time = self._itin_vars["itin_time"].get().strip()
        act  = self._itin_vars["itin_act"].get().strip()
        loc  = self._itin_vars["itin_loc"].get().strip()
        if not act or act == "e.g. Visit Eiffel Tower":
            messagebox.showwarning("Missing", "Enter an activity.")
            return
        if day not in self.data.itinerary:
            self.data.itinerary[day] = []
        self.data.itinerary[day].append({
            "time": time, "activity": act,
            "location": loc, "type": self.itin_type_var.get()
        })
        for key, hint in [("itin_time","e.g. 09:00"),
                          ("itin_act","e.g. Visit Eiffel Tower"),
                          ("itin_loc","e.g. Champ de Mars")]:
            self._itin_vars[key].set(hint)
        self._refresh_timeline()

    def _refresh_timeline(self):
        for w in self.timeline_inner.winfo_children():
            w.destroy()
        day  = self.itin_day_var.get()
        acts = self.data.itinerary.get(day, [])

        type_colors = {
            "Sightseeing": TEAL, "Food & Drink": AMBER,
            "Transport": BLUE,   "Adventure": RED,
            "Shopping": PURPLE,  "Relaxation": GREEN,
            "Culture": CORAL,    "Other": MID,
        }

        if not acts:
            tk.Label(self.timeline_inner,
                     text="No activities for this day yet.",
                     font=FONT_SM, bg=INPUT_BG, fg=LIGHT,
                     pady=20).pack()
            return

        for i, act in enumerate(sorted(acts, key=lambda x: x["time"])):
            color = type_colors.get(act["type"], MID)
            row = tk.Frame(self.timeline_inner, bg=INPUT_BG)
            row.pack(fill="x", padx=10, pady=4)

            # Time column
            tk.Label(row, text=act["time"] or "—",
                     font=FONT_MONO, bg=INPUT_BG,
                     fg=MID, width=7).pack(side="left")

            # Dot + line
            dot_frame = tk.Frame(row, bg=INPUT_BG, width=24)
            dot_frame.pack(side="left", fill="y")
            dot_frame.pack_propagate(False)
            tk.Label(dot_frame, text="●", font=("Helvetica", 12),
                     bg=INPUT_BG, fg=color).pack()

            # Card
            card = tk.Frame(row, bg=SURFACE,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(card, text=act["activity"],
                     font=FONT_H3, bg=SURFACE, fg=DARK,
                     anchor="w", pady=4, padx=8).pack(fill="x")
            info_r = tk.Frame(card, bg=SURFACE)
            info_r.pack(fill="x", padx=8, pady=(0, 4))
            if act["location"]:
                tk.Label(info_r, text=f"📍 {act['location']}",
                         font=FONT_SM, bg=SURFACE, fg=MID).pack(side="left")
            self._badge(info_r, act["type"], BLUE_LT, BLUE)

            del_btn = tk.Button(card, text="✕", font=FONT_TINY,
                                bg=SURFACE, fg=LIGHT, relief="flat",
                                cursor="hand2",
                                command=lambda a=act, d=day: self._del_activity(d,a))
            del_btn.pack(side="right", padx=4)

    def _del_activity(self, day, act):
        self.data.itinerary[day] = [
            a for a in self.data.itinerary[day] if a != act]
        self._refresh_timeline()

    # ── ③ Budget ──────────────────────────────────────────────────────────────
    def _build_budget(self, parent, P):
        sec = self._section(parent, "💰  Budget Tracker", AMBER, P)

        # Budget setup row
        setup = tk.Frame(sec, bg=SURFACE)
        setup.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(setup, text="Total Budget ($):", font=FONT_BODY,
                 bg=SURFACE, fg=MID).pack(side="left")
        self.budget_total_var = tk.StringVar(value="0")
        tk.Entry(setup, textvariable=self.budget_total_var,
                 font=FONT_MONO, bg=INPUT_BG, fg=DARK,
                 relief="solid", bd=1, width=12).pack(
            side="left", padx=8, ipady=4)
        self._btn_inline(setup, "Set", self._set_budget, AMBER)

        cols = tk.Frame(sec, bg=SURFACE)
        cols.pack(fill="x", padx=16, pady=4)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=2)

        # Add expense form
        form = self._mini_section(cols, "Add Expense", 0)
        exp_fields = [
            ("Item",    "exp_item",   "e.g. Hotel night"),
            ("Amount",  "exp_amt",    "e.g. 120.00"),
            ("Date",    "exp_date",   "YYYY-MM-DD"),
        ]
        self._exp_vars = {}
        for label, key, hint in exp_fields:
            r = tk.Frame(form, bg=INPUT_BG)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=FONT_SM, bg=INPUT_BG,
                     fg=MID, width=8, anchor="w").pack(side="left", padx=6)
            v = tk.StringVar()
            e = tk.Entry(r, textvariable=v, font=FONT_BODY,
                         bg=SURFACE, fg=DARK, relief="solid", bd=1, width=20)
            e.pack(side="left", ipady=4)
            e.insert(0, hint); e.configure(fg=LIGHT)
            e.bind("<FocusIn>",
                lambda ev, h=hint, en=e: en.delete(0,"end")
                if en.get()==h else None)
            e.bind("<Key>", lambda ev, en=e: en.configure(fg=DARK))
            self._exp_vars[key] = v

        tk.Label(form, text="Category", font=FONT_SM,
                 bg=INPUT_BG, fg=MID, anchor="w").pack(
            fill="x", padx=6, pady=(6,2))
        self.exp_cat_var = tk.StringVar(value="Accommodation")
        cat_cb = ttk.Combobox(form, textvariable=self.exp_cat_var,
                              state="readonly",
                              values=["Accommodation","Food","Transport",
                                      "Activities","Shopping","Health",
                                      "Communication","Other"])
        cat_cb.pack(fill="x", padx=6, ipady=4)

        btn_r = tk.Frame(form, bg=INPUT_BG)
        btn_r.pack(fill="x", padx=6, pady=8)
        self._btn_inline(btn_r, "+ Add Expense", self._add_expense, AMBER)

        # Budget display
        right_f = self._mini_section(cols, "Budget Overview", 1)

        # Budget bar
        self.budget_bar_canvas = tk.Canvas(right_f, bg=INPUT_BG,
                                            height=60, highlightthickness=0)
        self.budget_bar_canvas.pack(fill="x", pady=4)

        # Category chart
        self.budget_chart_canvas = tk.Canvas(right_f, bg=INPUT_BG,
                                              height=160, highlightthickness=0)
        self.budget_chart_canvas.pack(fill="x", pady=4)

        # Expense list
        tree_frame = tk.Frame(right_f, bg=INPUT_BG)
        tree_frame.pack(fill="x")
        cols2 = ("Date", "Category", "Item", "Amount")
        self.exp_tree = ttk.Treeview(tree_frame, columns=cols2,
                                     show="headings", height=7)
        widths = [90, 110, 180, 80]
        for col, w in zip(cols2, widths):
            self.exp_tree.heading(col, text=col)
            self.exp_tree.column(col, width=w, anchor="center")
        self.exp_tree.pack(side="left", fill="x", expand=True)
        vsb = tk.Scrollbar(tree_frame, orient="vertical",
                           command=self.exp_tree.yview)
        vsb.pack(side="right", fill="y")
        self.exp_tree.configure(yscrollcommand=vsb.set)
        self.exp_tree.bind("<Delete>", self._del_expense)

        self.budget_summary_var = tk.StringVar(value="Press Delete to remove selected expense.")
        tk.Label(right_f, textvariable=self.budget_summary_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID).pack(pady=4)

        return sec

    def _set_budget(self):
        try:
            self.data.total_budget = float(self.budget_total_var.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number.")
            return
        self._refresh_budget()

    def _add_expense(self):
        item = self._exp_vars["exp_item"].get().strip()
        if not item or item == "e.g. Hotel night":
            messagebox.showwarning("Missing", "Enter an item name.")
            return
        try:
            amt = float(self._exp_vars["exp_amt"].get())
        except ValueError:
            amt = 0.0
        date = self._exp_vars["exp_date"].get().strip()
        if not date or date == "YYYY-MM-DD":
            date = str(datetime.date.today())
        self.data.expenses.append({
            "category": self.exp_cat_var.get(),
            "item":     item,
            "amount":   amt,
            "date":     date,
        })
        for k,h in [("exp_item","e.g. Hotel night"),
                    ("exp_amt","e.g. 120.00"),
                    ("exp_date","YYYY-MM-DD")]:
            self._exp_vars[k].set(h)
        self._refresh_budget()
        self._update_sidebar_stats()

    def _del_expense(self, event=None):
        sel = self.exp_tree.selection()
        if not sel:
            return
        idx = self.exp_tree.index(sel[0])
        del self.data.expenses[idx]
        self._refresh_budget()
        self._update_sidebar_stats()

    def _refresh_budget(self):
        # Tree
        self.exp_tree.delete(*self.exp_tree.get_children())
        for exp in self.data.expenses:
            self.exp_tree.insert("", "end", values=(
                exp["date"], exp["category"],
                exp["item"], f"${exp['amount']:.2f}"))

        total_spent = sum(e["amount"] for e in self.data.expenses)
        budget = self.data.total_budget
        remaining = budget - total_spent

        self.budget_summary_var.set(
            f"Spent: ${total_spent:,.2f}  ·  "
            f"Budget: ${budget:,.2f}  ·  "
            f"Remaining: ${remaining:,.2f}")

        # Draw budget bar
        c = self.budget_bar_canvas
        c.delete("all")
        self.update_idletasks()
        W = c.winfo_width() or 400
        H = 60
        pct = min(total_spent / budget, 1.0) if budget > 0 else 0
        bar_color = RED if pct > 0.9 else AMBER if pct > 0.7 else GREEN
        c.create_rectangle(10, 20, W-10, 44, fill=BORDER, outline="")
        if pct > 0:
            c.create_rectangle(10, 20, 10 + (W-20)*pct, 44,
                                fill=bar_color, outline="")
        c.create_text(W//2, 32, text=f"{pct*100:.1f}% used",
                      font=FONT_SM, fill=WHITE if pct > 0.3 else MID)
        c.create_text(10, 10, text=f"${total_spent:,.0f}",
                      anchor="w", font=FONT_TINY, fill=MID)
        c.create_text(W-10, 10, text=f"${budget:,.0f}",
                      anchor="e", font=FONT_TINY, fill=MID)

        # Category donut chart (simple bar chart)
        cat_totals = {}
        for exp in self.data.expenses:
            cat_totals[exp["category"]] = \
                cat_totals.get(exp["category"], 0) + exp["amount"]

        c2 = self.budget_chart_canvas
        c2.delete("all")
        W2 = c2.winfo_width() or 400
        H2 = 160
        cat_colors = {
            "Accommodation": BLUE, "Food": AMBER, "Transport": TEAL,
            "Activities": GREEN, "Shopping": PURPLE, "Health": RED,
            "Communication": CORAL, "Other": MID,
        }
        if cat_totals:
            max_val = max(cat_totals.values())
            bar_w = max(20, (W2 - 20) // len(cat_totals) - 8)
            x = 20
            for cat, val in cat_totals.items():
                bh = int((val / max_val) * (H2 - 40))
                y_top = H2 - 20 - bh
                c2.create_rectangle(x, y_top, x+bar_w, H2-20,
                                    fill=cat_colors.get(cat, MID), outline="")
                c2.create_text(x + bar_w//2, H2-10,
                               text=cat[:5], font=FONT_TINY, fill=MID)
                c2.create_text(x + bar_w//2, y_top - 8,
                               text=f"${val:.0f}", font=FONT_TINY, fill=DARK)
                x += bar_w + 8

    # ── ④ Packing List ────────────────────────────────────────────────────────
    def _build_packing(self, parent, P):
        sec = self._section(parent, "🧳  Packing List", PURPLE, P)

        cols = tk.Frame(sec, bg=SURFACE)
        cols.pack(fill="x", padx=16, pady=8)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=2)

        # Add item form
        form = self._mini_section(cols, "Add Item", 0)
        r = tk.Frame(form, bg=INPUT_BG)
        r.pack(fill="x", pady=4)
        tk.Label(r, text="Item", font=FONT_SM, bg=INPUT_BG,
                 fg=MID, width=8, anchor="w").pack(side="left", padx=6)
        self.pack_item_var = tk.StringVar()
        e = tk.Entry(r, textvariable=self.pack_item_var,
                     font=FONT_BODY, bg=SURFACE, fg=DARK,
                     relief="solid", bd=1, width=20)
        e.pack(side="left", ipady=4)
        e.insert(0, "e.g. Passport"); e.configure(fg=LIGHT)
        e.bind("<FocusIn>",
            lambda ev: e.delete(0,"end") if e.get()=="e.g. Passport" else None)
        e.bind("<Key>", lambda ev: e.configure(fg=DARK))
        e.bind("<Return>", lambda ev: self._add_pack_item())

        tk.Label(form, text="Category", font=FONT_SM,
                 bg=INPUT_BG, fg=MID, anchor="w").pack(
            fill="x", padx=6, pady=(6,2))
        self.pack_cat_var = tk.StringVar(value="Documents")
        pack_cb = ttk.Combobox(form, textvariable=self.pack_cat_var,
                               state="readonly",
                               values=["Documents","Clothing","Toiletries",
                                       "Electronics","Health","Money",
                                       "Entertainment","Misc"])
        pack_cb.pack(fill="x", padx=6, ipady=4)

        btn_r = tk.Frame(form, bg=INPUT_BG)
        btn_r.pack(fill="x", padx=6, pady=8)
        self._btn_inline(btn_r, "+ Add Item", self._add_pack_item, PURPLE)
        self._btn_inline(btn_r, "Add Defaults", self._add_default_pack, MID)

        # Progress
        prog_f = tk.Frame(form, bg=INPUT_BG)
        prog_f.pack(fill="x", padx=6, pady=4)
        self.pack_progress_var = tk.StringVar(value="0 / 0 packed")
        tk.Label(prog_f, textvariable=self.pack_progress_var,
                 font=FONT_H3, bg=INPUT_BG, fg=PURPLE).pack(anchor="w")
        self.pack_bar = tk.Canvas(prog_f, bg=BORDER, height=8,
                                   highlightthickness=0)
        self.pack_bar.pack(fill="x", pady=4)

        # Packing checklist
        list_f = self._mini_section(cols, "Checklist", 1)

        # Filter by category
        filter_r = tk.Frame(list_f, bg=INPUT_BG)
        filter_r.pack(fill="x", pady=(0,6))
        tk.Label(filter_r, text="Filter:", font=FONT_SM,
                 bg=INPUT_BG, fg=MID).pack(side="left", padx=6)
        self.pack_filter_var = tk.StringVar(value="All")
        filter_cb = ttk.Combobox(filter_r, textvariable=self.pack_filter_var,
                                  state="readonly", width=14,
                                  values=["All","Documents","Clothing",
                                          "Toiletries","Electronics","Health",
                                          "Money","Entertainment","Misc"])
        filter_cb.pack(side="left")
        filter_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_packing())

        self.pack_list_frame = tk.Frame(list_f, bg=INPUT_BG)
        self.pack_list_frame.pack(fill="both", expand=True)

        return sec

    def _add_pack_item(self):
        item = self.pack_item_var.get().strip()
        if not item or item == "e.g. Passport":
            return
        self.data.packing.append({
            "category": self.pack_cat_var.get(),
            "item":     item,
            "packed":   False,
        })
        self.pack_item_var.set("")
        self._refresh_packing()
        self._update_sidebar_stats()

    def _add_default_pack(self):
        defaults = [
            ("Documents", "Passport"), ("Documents", "Travel Insurance"),
            ("Documents", "Booking Confirmations"), ("Documents", "Visa"),
            ("Clothing", "T-Shirts"), ("Clothing", "Trousers"),
            ("Clothing", "Underwear"), ("Clothing", "Socks"),
            ("Clothing", "Jacket"), ("Clothing", "Comfortable Shoes"),
            ("Toiletries", "Toothbrush"), ("Toiletries", "Shampoo"),
            ("Toiletries", "Sunscreen"), ("Toiletries", "Deodorant"),
            ("Electronics", "Phone Charger"), ("Electronics", "Power Bank"),
            ("Electronics", "Camera"), ("Electronics", "Universal Adapter"),
            ("Health", "Prescription Medications"),
            ("Health", "First Aid Kit"), ("Health", "Hand Sanitizer"),
            ("Money", "Credit/Debit Cards"), ("Money", "Emergency Cash"),
        ]
        existing = {(p["category"], p["item"]) for p in self.data.packing}
        for cat, item in defaults:
            if (cat, item) not in existing:
                self.data.packing.append({"category":cat,"item":item,"packed":False})
        self._refresh_packing()
        self._update_sidebar_stats()

    def _refresh_packing(self):
        for w in self.pack_list_frame.winfo_children():
            w.destroy()

        flt = self.pack_filter_var.get()
        items = [p for p in self.data.packing
                 if flt == "All" or p["category"] == flt]

        # Group by category
        by_cat = {}
        for p in items:
            by_cat.setdefault(p["category"], []).append(p)

        cat_colors = {
            "Documents":"#2563eb","Clothing":"#7c3aed","Toiletries":"#0d9488",
            "Electronics":"#d97706","Health":"#dc2626","Money":"#16a34a",
            "Entertainment":"#ea580c","Misc":"#64748b",
        }

        for cat, plist in by_cat.items():
            color = cat_colors.get(cat, MID)
            hdr = tk.Frame(self.pack_list_frame, bg=INPUT_BG)
            hdr.pack(fill="x", pady=(8,2))
            tk.Label(hdr, text=f"  {cat}",
                     font=FONT_H3, bg=color, fg=WHITE,
                     anchor="w", pady=3).pack(fill="x")
            for p in plist:
                self._pack_item_row(self.pack_list_frame, p)

        # Progress
        total  = len(self.data.packing)
        packed = sum(1 for p in self.data.packing if p["packed"])
        self.pack_progress_var.set(f"{packed} / {total} packed")
        self.update_idletasks()
        W = self.pack_bar.winfo_width() or 300
        self.pack_bar.delete("all")
        self.pack_bar.create_rectangle(0,0,W,8,fill=BORDER,outline="")
        if total:
            pw = int((packed/total)*W)
            self.pack_bar.create_rectangle(0,0,pw,8,fill=PURPLE,outline="")

    def _pack_item_row(self, parent, p):
        row = tk.Frame(parent, bg=SURFACE,
                       highlightthickness=1, highlightbackground=BORDER)
        row.pack(fill="x", pady=1)
        var = tk.BooleanVar(value=p["packed"])

        def toggle(p=p, v=var):
            p["packed"] = v.get()
            lbl.configure(fg=LIGHT if p["packed"] else DARK)
            self._refresh_packing()
            self._update_sidebar_stats()

        cb = tk.Checkbutton(row, variable=var, command=toggle,
                            bg=SURFACE, activebackground=SURFACE,
                            selectcolor=PURPLE)
        cb.pack(side="left", padx=8)
        lbl = tk.Label(row, text=p["item"], font=FONT_BODY,
                       bg=SURFACE, fg=LIGHT if p["packed"] else DARK,
                       anchor="w")
        if p["packed"]:
            lbl.configure(font=("Helvetica", 10, "overstrike"))
        lbl.pack(side="left", fill="x", expand=True, pady=6)

        del_btn = tk.Button(row, text="✕", font=FONT_TINY,
                            bg=SURFACE, fg=LIGHT, relief="flat",
                            cursor="hand2",
                            command=lambda pp=p: self._del_pack_item(pp))
        del_btn.pack(side="right", padx=8)

    def _del_pack_item(self, p):
        self.data.packing = [x for x in self.data.packing if x is not p]
        self._refresh_packing()
        self._update_sidebar_stats()

    # ── ⑤ Trip Summary ────────────────────────────────────────────────────────
    def _build_summary(self, parent, P):
        sec = self._section(parent, "📋  Trip Summary", GREEN, P)
        body = tk.Frame(sec, bg=SURFACE)
        body.pack(fill="x", padx=16, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # Left: Trip info
        info_f = self._mini_section(body, "Trip Details", 0)

        trip_fields = [
            ("Trip Name",  "sum_name",  "My Dream Trip"),
            ("Start Date", "sum_start", "YYYY-MM-DD"),
            ("End Date",   "sum_end",   "YYYY-MM-DD"),
            ("Travelers",  "sum_trav",  "1"),
            ("Currency",   "sum_curr",  "USD"),
        ]
        self._sum_vars = {}
        for label, key, hint in trip_fields:
            r = tk.Frame(info_f, bg=INPUT_BG)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=FONT_SM, bg=INPUT_BG,
                     fg=MID, width=12, anchor="w").pack(side="left", padx=6)
            v = tk.StringVar(value=hint)
            e = tk.Entry(r, textvariable=v, font=FONT_BODY,
                         bg=SURFACE, fg=DARK, relief="solid", bd=1, width=20)
            e.pack(side="left", ipady=4)
            self._sum_vars[key] = v

        self._btn(info_f, "💾 Save Trip Details", self._save_trip_details, GREEN)

        # Right: Summary stats
        stat_f = self._mini_section(body, "Stats", 1)
        self.summary_text = tk.Text(stat_f, font=FONT_MONO,
                                    bg=INPUT_BG, fg=DARK,
                                    relief="flat", height=16,
                                    padx=10, pady=8, state="disabled")
        self.summary_text.pack(fill="both", expand=True)

        btn_r = tk.Frame(stat_f, bg=INPUT_BG)
        btn_r.pack(fill="x", padx=6, pady=8)
        self._btn_inline(btn_r, "🔄 Refresh", self._refresh_summary, GREEN)
        self._btn_inline(btn_r, "📄 Export TXT", self._export_txt, BLUE)

        return sec

    def _save_trip_details(self):
        self.data.trip_name    = self._sum_vars["sum_name"].get()
        self.data.trip_start   = self._sum_vars["sum_start"].get()
        self.data.trip_end     = self._sum_vars["sum_end"].get()
        self.data.travelers    = self._sum_vars["sum_trav"].get()
        self.data.currency     = self._sum_vars["sum_curr"].get()
        self.trip_name_var.set(self.data.trip_name)
        messagebox.showinfo("Saved", "Trip details saved!")
        self._refresh_summary()

    def _refresh_summary(self):
        total_days  = sum(d["days"] for d in self.data.destinations)
        total_cost  = sum(d["cost"] for d in self.data.destinations)
        total_spent = sum(e["amount"] for e in self.data.expenses)
        total_pack  = len(self.data.packing)
        packed_cnt  = sum(1 for p in self.data.packing if p["packed"])
        total_acts  = sum(len(v) for v in self.data.itinerary.values())

        lines = [
            f"{'='*40}",
            f"  {self.data.trip_name.upper()}",
            f"{'='*40}",
            f"  Dates      : {self.data.trip_start} → {self.data.trip_end}",
            f"  Travelers  : {self.data.travelers}",
            f"  Currency   : {self.data.currency}",
            f"",
            f"  DESTINATIONS ({len(self.data.destinations)})",
        ]
        for d in self.data.destinations:
            lines.append(f"    • {d['name']}, {d['country']} "
                         f"({d['days']} days, ${d['cost']:,.0f})")
        lines += [
            f"",
            f"  ITINERARY",
            f"    Total activities : {total_acts}",
            f"    Days planned     : {total_days}",
            f"",
            f"  BUDGET",
            f"    Total budget     : ${self.data.total_budget:,.2f}",
            f"    Total spent      : ${total_spent:,.2f}",
            f"    Remaining        : ${self.data.total_budget-total_spent:,.2f}",
            f"    Est. dest. cost  : ${total_cost:,.2f}",
            f"",
            f"  PACKING",
            f"    {packed_cnt} / {total_pack} items packed",
            f"",
            f"{'='*40}",
        ]
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "\n".join(lines))
        self.summary_text.config(state="disabled")

    # ── File Operations ───────────────────────────────────────────────────────
    def _save_trip(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            title="Save Trip")
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self.data.to_dict(), f, indent=2)
        messagebox.showinfo("Saved", f"Trip saved to:\n{path}")

    def _load_trip(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            title="Load Trip")
        if not path:
            return
        with open(path) as f:
            d = json.load(f)
        self.data.from_dict(d)
        self.trip_name_var.set(self.data.trip_name)
        self._refresh_dest_list()
        self._refresh_itinerary_days()
        self._refresh_budget()
        self._refresh_packing()
        self._refresh_summary()
        self._update_sidebar_stats()
        messagebox.showinfo("Loaded", "Trip loaded successfully!")

    def _export_txt(self):
        self._refresh_summary()
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            title="Export Trip Summary")
        if not path:
            return
        content = self.summary_text.get("1.0", "end")
        with open(path, "w") as f:
            f.write(content)
        messagebox.showinfo("Exported", f"Summary saved to:\n{path}")

    # ── Sample Data ───────────────────────────────────────────────────────────
    def _load_sample_data(self):
        sample_dests = [
            {"name":"Paris","country":"France","days":4,
             "cost":1800,"notes":"City of Light!","rating":5,"id":10001},
            {"name":"Rome","country":"Italy","days":3,
             "cost":1200,"notes":"Ancient ruins & pizza","rating":5,"id":10002},
            {"name":"Barcelona","country":"Spain","days":3,
             "cost":1000,"notes":"Gaudí & beaches","rating":4,"id":10003},
        ]
        self.data.destinations = sample_dests
        self.data.itinerary["Day 1"] = [
            {"time":"09:00","activity":"Eiffel Tower visit",
             "location":"Champ de Mars","type":"Sightseeing"},
            {"time":"13:00","activity":"Lunch at Le Marais",
             "location":"Le Marais","type":"Food & Drink"},
            {"time":"15:00","activity":"Louvre Museum",
             "location":"Rue de Rivoli","type":"Culture"},
        ]
        self.data.total_budget = 5000
        self.budget_total_var.set("5000")
        self.data.expenses = [
            {"category":"Accommodation","item":"Hotel Paris 4n",
             "amount":600,"date":"2025-06-01"},
            {"category":"Transport","item":"Eurostar tickets",
             "amount":220,"date":"2025-06-01"},
            {"category":"Food","item":"Restaurants budget",
             "amount":350,"date":"2025-06-01"},
        ]
        self._add_default_pack()
        self._refresh_dest_list()
        self._refresh_itinerary_days()
        self._refresh_budget()
        self._refresh_summary()
        self._update_sidebar_stats()

    # ── Sidebar stats refresh ─────────────────────────────────────────────────
    def _update_sidebar_stats(self):
        self.stat_dest.set(str(len(self.data.destinations)))
        total_days = sum(d["days"] for d in self.data.destinations)
        self.stat_days.set(str(total_days))
        spent = sum(e["amount"] for e in self.data.expenses)
        self.stat_spent.set(f"${spent:,.0f}")
        total = len(self.data.packing)
        packed = sum(1 for p in self.data.packing if p["packed"])
        self.stat_items.set(f"{packed}/{total}")

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _section(self, parent, title, color, pad):
        outer = tk.Frame(parent, bg=BORDER, bd=1)
        outer.pack(fill="x", **pad)
        inner = tk.Frame(outer, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        hdr = tk.Frame(inner, bg=SURFACE)
        hdr.pack(fill="x")
        accent = tk.Frame(hdr, bg=color, width=5)
        accent.pack(side="left", fill="y")
        tk.Label(hdr, text=title, font=FONT_H2, bg=SURFACE,
                 fg=DARK, pady=12, padx=14, anchor="w").pack(
            side="left", fill="x")
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")
        return inner

    def _mini_section(self, parent, title, col):
        f = tk.Frame(parent, bg=INPUT_BG, bd=1, relief="solid")
        f.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
        tk.Label(f, text=title, font=FONT_H3, bg=INPUT_BG,
                 fg=DARK, pady=8, anchor="center").pack(fill="x")
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=10)
        return f

    def _badge(self, parent, text, bg_color, fg_color):
        tk.Label(parent, text=text, font=FONT_TINY,
                 bg=bg_color, fg=fg_color,
                 padx=6, pady=2).pack(side="left", padx=2)

    def _btn(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_BTN, bg=color, fg=WHITE,
                  relief="flat", activebackground=DARK,
                  activeforeground=WHITE, cursor="hand2",
                  pady=7, padx=14, bd=0).pack(
            fill="x", padx=10, pady=8)

    def _btn_inline(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_BTN, bg=color, fg=WHITE,
                  relief="flat", activebackground=DARK,
                  activeforeground=WHITE, cursor="hand2",
                  pady=6, padx=12, bd=0).pack(side="left", padx=4)

    def _btn_small(self, parent, text, cmd, color, side="left"):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_SM, bg=color, fg=WHITE,
                  relief="flat", cursor="hand2",
                  pady=5, padx=10, bd=0).pack(
            side=side, padx=4)


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = TravelPlannerApp()
    app.mainloop()
