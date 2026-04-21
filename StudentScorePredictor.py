"""
Student Exam Score Predictor  —  Redesigned Version
=====================================================
A redesigned Tkinter GUI application that trains a Linear Regression model
to predict student exam scores.

Changes from original Project18:
  - Tabbed layout replaced with a single-page scrollable sidebar + main panel
  - Dark theme replaced with a clean light theme
  - Added a live bar chart of feature coefficients (drawn with tkinter Canvas)
  - Added a scatter plot of Actual vs Predicted scores (Canvas)
  - Prediction confidence range shown (±RMSE band)
  - Keyboard shortcut: Enter key triggers Predict
  - Restyled all widgets with rounded look via ttk.Style

Dependencies:
    pip install scikit-learn pandas numpy

Run:
    python StudentScorePredictor.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import random

try:
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# ─── Palette (light theme) ────────────────────────────────────────────────────
BG        = "#f5f6fa"
SURFACE   = "#ffffff"
SIDEBAR   = "#1e2230"
BORDER    = "#e0e3ed"
INPUT_BG  = "#f0f2f8"

BLUE      = "#3b82f6"
GREEN     = "#22c55e"
AMBER     = "#f59e0b"
RED       = "#ef4444"
PURPLE    = "#8b5cf6"
TEAL      = "#14b8a6"
DARK_TEXT = "#1e293b"
MID_TEXT  = "#64748b"
LIGHT_TEXT= "#94a3b8"
WHITE     = "#ffffff"
SIDEBAR_FG= "#cbd5e1"
SIDEBAR_ACC="#3b82f6"

FONT_H1   = ("Helvetica", 18, "bold")
FONT_H2   = ("Helvetica", 12, "bold")
FONT_H3   = ("Helvetica", 10, "bold")
FONT_MONO = ("Courier New", 10)
FONT_SM   = ("Helvetica", 9)
FONT_BODY = ("Helvetica", 10)
FONT_BTN  = ("Helvetica", 10, "bold")

FEATURES  = ["Hours Studied", "Attendance %", "Previous Score", "Assignments Done"]
TARGET    = "Exam Score"
COL_NAMES = FEATURES + [TARGET]

# ─── Synthetic Data ───────────────────────────────────────────────────────────
def generate_synthetic_data(n: int = 120) -> "pd.DataFrame":
    rng = np.random.default_rng(42)
    hours      = rng.uniform(1, 12, n)
    attendance = rng.uniform(40, 100, n)
    prev_score = rng.uniform(30, 95, n)
    assignments= rng.integers(0, 11, n).astype(float)
    score = (
        4.0 * hours + 0.25 * attendance +
        0.45 * prev_score + 2.5 * assignments +
        rng.normal(0, 4, n)
    )
    score = np.clip(score, 0, 100).round(1)
    return pd.DataFrame({
        "Hours Studied":    hours.round(1),
        "Attendance %":     attendance.round(1),
        "Previous Score":   prev_score.round(1),
        "Assignments Done": assignments,
        "Exam Score":       score,
    })

# ─── ML Model ────────────────────────────────────────────────────────────────
class StudentModel:
    def __init__(self):
        self.df      = None
        self.model   = None
        self.scaler  = StandardScaler()
        self.metrics = {}
        self.trained = False

    def load_csv(self, path):
        try:
            df = pd.read_csv(path)
            return self._validate(df)
        except Exception as e:
            return False, str(e)

    def load_synthetic(self, n=120):
        self.df = generate_synthetic_data(n)
        return True, f"Generated {n} synthetic rows."

    def load_manual(self, rows):
        try:
            df = pd.DataFrame(rows, columns=COL_NAMES)
            df = df.apply(pd.to_numeric, errors="coerce")
            return self._validate(df)
        except Exception as e:
            return False, str(e)

    def _validate(self, df):
        missing = [c for c in COL_NAMES if c not in df.columns]
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        df = df[COL_NAMES].copy().apply(pd.to_numeric, errors="coerce")
        df.fillna(df.median(numeric_only=True), inplace=True)
        df.dropna(inplace=True)
        if len(df) < 10:
            return False, f"Only {len(df)} valid rows — need ≥ 10."
        self.df = df
        return True, f"Loaded {len(df)} rows."

    def train(self, test_size=0.2):
        if self.df is None or len(self.df) < 10:
            return False, "Load data first."
        X = self.df[FEATURES].values
        y = self.df[TARGET].values
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=test_size, random_state=42)
        X_tr_s = self.scaler.fit_transform(X_tr)
        X_te_s = self.scaler.transform(X_te)
        self.model = LinearRegression()
        self.model.fit(X_tr_s, y_tr)
        y_pred = np.clip(self.model.predict(X_te_s), 0, 100)
        self.metrics = {
            "r2":     r2_score(y_te, y_pred),
            "mae":    mean_absolute_error(y_te, y_pred),
            "rmse":   math.sqrt(mean_squared_error(y_te, y_pred)),
            "n_train":len(X_tr), "n_test": len(X_te),
            "coefs":  dict(zip(FEATURES, self.model.coef_)),
            "y_te":   y_te.tolist(),
            "y_pred": y_pred.tolist(),
        }
        self.trained = True
        return True, "Model trained."

    def predict_one(self, vals):
        if not self.trained:
            return False, "Train the model first."
        try:
            x = np.array(vals, dtype=float).reshape(1, -1)
            p = float(self.model.predict(self.scaler.transform(x))[0])
            return True, round(min(max(p, 0), 100), 2)
        except Exception as e:
            return False, str(e)


# ─── Main App ─────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Score Predictor")
        self.configure(bg=BG)
        self.minsize(1050, 700)
        self.resizable(True, True)

        self.model = StudentModel()
        self._manual_rows = []

        if not ML_AVAILABLE:
            messagebox.showerror("Missing libs",
                "Install dependencies:\n  pip install scikit-learn pandas numpy")
            self.destroy()
            return

        self._apply_styles()
        self._build_ui()
        self.bind("<Return>", lambda e: self._predict())

    # ── Styles ────────────────────────────────────────────────────────────────
    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("Light.Treeview",
                    background=SURFACE, foreground=DARK_TEXT,
                    fieldbackground=SURFACE, rowheight=24, font=FONT_SM)
        s.configure("Light.Treeview.Heading",
                    background=INPUT_BG, foreground=MID_TEXT,
                    font=("Helvetica", 9, "bold"), relief="flat")
        s.map("Light.Treeview",
              background=[("selected", BLUE)],
              foreground=[("selected", WHITE)])

    # ── Root layout: sidebar + main ───────────────────────────────────────────
    def _build_ui(self):
        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(root_frame, bg=SIDEBAR, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # Main content (scrollable via Canvas)
        self._main_canvas = tk.Canvas(root_frame, bg=BG, highlightthickness=0)
        self._main_canvas.pack(side="left", fill="both", expand=True)
        vsb = tk.Scrollbar(root_frame, orient="vertical",
                           command=self._main_canvas.yview)
        vsb.pack(side="right", fill="y")
        self._main_canvas.configure(yscrollcommand=vsb.set)

        self._main_frame = tk.Frame(self._main_canvas, bg=BG)
        self._win_id = self._main_canvas.create_window(
            (0, 0), window=self._main_frame, anchor="nw")

        self._main_frame.bind("<Configure>", self._on_frame_configure)
        self._main_canvas.bind("<Configure>", self._on_canvas_configure)
        self._main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._build_main(self._main_frame)

    def _on_frame_configure(self, event):
        self._main_canvas.configure(
            scrollregion=self._main_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._main_canvas.itemconfig(self._win_id, width=event.width)

    def _on_mousewheel(self, event):
        self._main_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, sb):
        tk.Label(sb, text="Score\nPredictor", font=("Helvetica", 14, "bold"),
                 bg=SIDEBAR, fg=WHITE, pady=20).pack(fill="x", padx=16)
        tk.Frame(sb, bg=SIDEBAR_ACC, height=2).pack(fill="x", padx=16)

        nav_items = [
            ("Dataset",      self._scroll_to_data),
            ("Data Preview", self._scroll_to_preview),
            ("Train Model",  self._scroll_to_train),
            ("Predict",      self._scroll_to_predict),
        ]
        for label, cmd in nav_items:
            b = tk.Button(sb, text=label, font=FONT_BODY,
                          bg=SIDEBAR, fg=SIDEBAR_FG,
                          activebackground=SIDEBAR_ACC, activeforeground=WHITE,
                          relief="flat", anchor="w", padx=20, pady=10,
                          cursor="hand2", command=cmd)
            b.pack(fill="x")

        # Status in sidebar
        tk.Frame(sb, bg=MID_TEXT, height=1).pack(fill="x", padx=16, pady=20)
        tk.Label(sb, text="Status", font=FONT_SM,
                 bg=SIDEBAR, fg=LIGHT_TEXT).pack(anchor="w", padx=16)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self.status_var, font=FONT_SM,
                 bg=SIDEBAR, fg=SIDEBAR_FG, wraplength=160,
                 justify="left").pack(anchor="w", padx=16, pady=4)

    def _scroll_to(self, widget):
        self.update_idletasks()
        y = widget.winfo_y()
        canvas_h = self._main_canvas.winfo_height()
        total_h  = self._main_frame.winfo_height()
        frac = y / max(total_h, 1)
        self._main_canvas.yview_moveto(frac)

    def _scroll_to_data(self):    self._scroll_to(self._sec_data)
    def _scroll_to_preview(self): self._scroll_to(self._sec_preview)
    def _scroll_to_train(self):   self._scroll_to(self._sec_train)
    def _scroll_to_predict(self): self._scroll_to(self._sec_predict)

    # ── Main content ──────────────────────────────────────────────────────────
    def _build_main(self, parent):
        pad = dict(padx=24, pady=12)

        # Page title
        hdr = tk.Frame(parent, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x", **pad)
        tk.Label(hdr, text="🎓  Student Exam Score Predictor",
                 font=FONT_H1, bg=SURFACE, fg=DARK_TEXT,
                 pady=16, padx=20, anchor="w").pack(fill="x")

        # Sections
        self._sec_data    = self._section_data(parent, pad)
        self._sec_preview = self._section_preview(parent, pad)
        self._sec_train   = self._section_train(parent, pad)
        self._sec_predict = self._section_predict(parent, pad)

    # ── Section: Load Data ────────────────────────────────────────────────────
    def _section_data(self, parent, pad):
        sec = self._card(parent, "① Load Data", pad)
        cols = tk.Frame(sec, bg=SURFACE)
        cols.pack(fill="x", padx=16, pady=8)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)
        cols.columnconfigure(2, weight=1)

        # CSV
        csv_f = self._mini_card(cols, "CSV Upload", 0)
        self.csv_path_var = tk.StringVar(value="No file selected")
        tk.Label(csv_f, textvariable=self.csv_path_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID_TEXT,
                 wraplength=160).pack(pady=6)
        self._btn(csv_f, "Browse CSV", self._load_csv, BLUE)

        # Synthetic
        syn_f = self._mini_card(cols, "Synthetic Data", 1)
        tk.Label(syn_f, text="Number of rows:", font=FONT_SM,
                 bg=INPUT_BG, fg=MID_TEXT).pack(pady=(6, 2))
        self.syn_n_var = tk.StringVar(value="120")
        tk.Entry(syn_f, textvariable=self.syn_n_var, width=8,
                 font=FONT_MONO, bg=SURFACE, fg=DARK_TEXT,
                 relief="solid", bd=1).pack(ipady=4)
        self._btn(syn_f, "Generate", self._load_synthetic, GREEN)

        # Manual
        man_f = self._mini_card(cols, "Manual Entry", 2)
        self.manual_entries = {}
        for feat in COL_NAMES:
            r = tk.Frame(man_f, bg=INPUT_BG)
            r.pack(fill="x", pady=1)
            tk.Label(r, text=feat, font=FONT_SM, bg=INPUT_BG,
                     fg=MID_TEXT, width=16, anchor="w").pack(side="left")
            v = tk.StringVar()
            tk.Entry(r, textvariable=v, width=7, font=FONT_MONO,
                     bg=SURFACE, fg=DARK_TEXT, relief="solid", bd=1
                     ).pack(side="left", ipady=3)
            self.manual_entries[feat] = v
        self.manual_count_var = tk.StringVar(value="0 rows")
        tk.Label(man_f, textvariable=self.manual_count_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID_TEXT).pack(pady=4)
        br = tk.Frame(man_f, bg=INPUT_BG)
        br.pack()
        self._btn_inline(br, "+ Row", self._add_manual_row, AMBER)
        self._btn_inline(br, "Use Data", self._use_manual_data, PURPLE)

        return sec

    # ── Section: Data Preview ─────────────────────────────────────────────────
    def _section_preview(self, parent, pad):
        sec = self._card(parent, "② Data Preview", pad)
        frame = tk.Frame(sec, bg=SURFACE)
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        self.tree = ttk.Treeview(frame, columns=COL_NAMES,
                                 show="headings", style="Light.Treeview",
                                 height=10)
        for col in COL_NAMES:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = tk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        self.data_info_var = tk.StringVar(value="No data loaded.")
        tk.Label(sec, textvariable=self.data_info_var,
                 font=FONT_SM, bg=SURFACE, fg=MID_TEXT).pack(pady=(0, 10))
        return sec

    # ── Section: Train ────────────────────────────────────────────────────────
    def _section_train(self, parent, pad):
        sec = self._card(parent, "③ Train Model", pad)
        body = tk.Frame(sec, bg=SURFACE)
        body.pack(fill="x", padx=16, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)

        # Controls (left)
        ctrl = tk.Frame(body, bg=INPUT_BG, bd=1, relief="solid")
        ctrl.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(ctrl, text="Test split %", font=FONT_SM,
                 bg=INPUT_BG, fg=MID_TEXT).pack(anchor="w", padx=10, pady=(10, 2))
        self.split_var = tk.StringVar(value="20")
        tk.Entry(ctrl, textvariable=self.split_var, width=6,
                 font=FONT_MONO, bg=SURFACE, fg=DARK_TEXT,
                 relief="solid", bd=1).pack(anchor="w", padx=10, ipady=4)
        self._btn(ctrl, "🚀 Train", self._train_model, GREEN)
        self.train_msg_var = tk.StringVar()
        tk.Label(ctrl, textvariable=self.train_msg_var, font=FONT_SM,
                 bg=INPUT_BG, fg=MID_TEXT, wraplength=160).pack(padx=10, pady=6)

        # Metrics (right)
        met = tk.Frame(body, bg=SURFACE)
        met.grid(row=0, column=1, sticky="nsew")

        # Metric cards row
        mc = tk.Frame(met, bg=SURFACE)
        mc.pack(fill="x", pady=(0, 10))
        self.metric_vars = {}
        defs = [("R²", "r2", BLUE), ("MAE", "mae", AMBER), ("RMSE", "rmse", RED)]
        for label, key, color in defs:
            box = tk.Frame(mc, bg=color, padx=2, pady=2)
            box.pack(side="left", fill="both", expand=True, padx=4)
            inner = tk.Frame(box, bg=SURFACE)
            inner.pack(fill="both")
            v = tk.StringVar(value="—")
            self.metric_vars[key] = v
            tk.Label(inner, textvariable=v, font=("Helvetica", 20, "bold"),
                     bg=SURFACE, fg=color, pady=6).pack()
            tk.Label(inner, text=label, font=FONT_H3,
                     bg=SURFACE, fg=DARK_TEXT).pack(pady=(0, 8))

        self.split_info_var = tk.StringVar()
        tk.Label(met, textvariable=self.split_info_var,
                 font=FONT_SM, bg=SURFACE, fg=MID_TEXT).pack(anchor="w")

        # Coefficient bar chart (Canvas)
        tk.Label(met, text="Feature Coefficients", font=FONT_H3,
                 bg=SURFACE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(10, 2))
        self.coef_canvas = tk.Canvas(met, bg=SURFACE,
                                     height=120, highlightthickness=0)
        self.coef_canvas.pack(fill="x")

        # Scatter plot
        tk.Label(met, text="Actual vs Predicted", font=FONT_H3,
                 bg=SURFACE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(10, 2))
        self.scatter_canvas = tk.Canvas(met, bg=SURFACE,
                                        height=180, highlightthickness=0)
        self.scatter_canvas.pack(fill="x", pady=(0, 8))

        return sec

    # ── Section: Predict ──────────────────────────────────────────────────────
    def _section_predict(self, parent, pad):
        sec = self._card(parent, "④ Predict Score", pad)
        body = tk.Frame(sec, bg=SURFACE)
        body.pack(fill="x", padx=16, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # Input form
        form = tk.Frame(body, bg=INPUT_BG, bd=1, relief="solid")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(form, text="Enter Student Details",
                 font=FONT_H3, bg=INPUT_BG, fg=DARK_TEXT,
                 pady=8, padx=10, anchor="w").pack(fill="x")

        self.predict_entries = {}
        hints = {
            "Hours Studied":    "1–12",
            "Attendance %":     "40–100",
            "Previous Score":   "30–95",
            "Assignments Done": "0–10",
        }
        for feat in FEATURES:
            r = tk.Frame(form, bg=INPUT_BG)
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=feat, font=FONT_BODY, bg=INPUT_BG,
                     fg=DARK_TEXT, width=18, anchor="w").pack(side="left")
            v = tk.StringVar()
            tk.Entry(r, textvariable=v, width=10, font=FONT_MONO,
                     bg=SURFACE, fg=DARK_TEXT, relief="solid", bd=1
                     ).pack(side="left", ipady=5)
            tk.Label(r, text=hints[feat], font=FONT_SM,
                     bg=INPUT_BG, fg=LIGHT_TEXT).pack(side="left", padx=6)
            self.predict_entries[feat] = v

        btn_r = tk.Frame(form, bg=INPUT_BG)
        btn_r.pack(fill="x", padx=10, pady=8)
        self._btn_inline(btn_r, "⚡ Predict  [Enter]", self._predict, BLUE)
        self._btn_inline(btn_r, "Clear", self._clear_predict, MID_TEXT)

        # Result panel
        res = tk.Frame(body, bg=SURFACE)
        res.grid(row=0, column=1, sticky="nsew")

        score_box = tk.Frame(res, bg=INPUT_BG, bd=1, relief="solid")
        score_box.pack(fill="x")
        tk.Label(score_box, text="Predicted Score",
                 font=FONT_H3, bg=INPUT_BG, fg=MID_TEXT,
                 pady=8, anchor="center").pack(fill="x")
        self.score_var = tk.StringVar(value="—")
        tk.Label(score_box, textvariable=self.score_var,
                 font=("Helvetica", 52, "bold"),
                 bg=INPUT_BG, fg=BLUE, pady=8).pack()
        self.grade_var = tk.StringVar()
        tk.Label(score_box, textvariable=self.grade_var,
                 font=("Helvetica", 13, "bold"),
                 bg=INPUT_BG, fg=GREEN, pady=8).pack()
        self.conf_var = tk.StringVar()
        tk.Label(score_box, textvariable=self.conf_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID_TEXT).pack(pady=(0, 8))

        # Grade bands
        bands = [
            ("90–100", "Excellent",   GREEN),
            ("75–89",  "Good",        TEAL),
            ("60–74",  "Average",     AMBER),
            ("40–59",  "Below Avg",   RED),
            ("0–39",   "At Risk",     "#dc2626"),
        ]
        band_frame = tk.Frame(res, bg=SURFACE)
        band_frame.pack(fill="x", pady=8)
        for rng, label, color in bands:
            brow = tk.Frame(band_frame, bg=SURFACE)
            brow.pack(fill="x", pady=1)
            tk.Frame(brow, bg=color, width=8, height=22).pack(side="left")
            tk.Label(brow, text=f"  {rng}  →  {label}",
                     font=FONT_BODY, bg=SURFACE, fg=DARK_TEXT).pack(side="left")

        # Prediction log
        tk.Label(res, text="Prediction History",
                 font=FONT_H3, bg=SURFACE, fg=DARK_TEXT,
                 anchor="w").pack(fill="x", pady=(8, 2))
        log_frame = tk.Frame(res, bg=INPUT_BG, bd=1, relief="solid")
        log_frame.pack(fill="x")
        self.log_text = tk.Text(log_frame, font=FONT_SM,
                                bg=INPUT_BG, fg=MID_TEXT,
                                state="disabled", relief="flat",
                                height=5, padx=8, pady=6)
        self.log_text.pack(fill="x")

        return sec

    # ── Actions ───────────────────────────────────────────────────────────────
    def _load_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        ok, msg = self.model.load_csv(path)
        self.csv_path_var.set(path.split("/")[-1])
        self._set_status(msg, ok)
        if ok:
            self._refresh_preview()

    def _load_synthetic(self):
        try:
            n = int(self.syn_n_var.get())
            assert n >= 10
        except Exception:
            messagebox.showerror("Error", "Rows must be an integer ≥ 10.")
            return
        ok, msg = self.model.load_synthetic(n)
        self._set_status(msg, ok)
        if ok:
            self._refresh_preview()

    def _add_manual_row(self):
        vals = []
        for col in COL_NAMES:
            try:
                vals.append(float(self.manual_entries[col].get().strip()))
            except ValueError:
                messagebox.showerror("Error", f'Bad value for "{col}"')
                return
        self._manual_rows.append(vals)
        self.manual_count_var.set(f"{len(self._manual_rows)} rows")
        for v in self.manual_entries.values():
            v.set("")

    def _use_manual_data(self):
        if len(self._manual_rows) < 5:
            messagebox.showwarning("Too few", "Enter at least 5 rows first.")
            return
        ok, msg = self.model.load_manual(self._manual_rows)
        self._set_status(msg, ok)
        if ok:
            self._refresh_preview()

    def _refresh_preview(self):
        self.tree.delete(*self.tree.get_children())
        if self.model.df is None:
            return
        df = self.model.df
        for _, row in df.head(200).iterrows():
            self.tree.insert("", "end",
                             values=[f"{row[c]:.1f}" for c in COL_NAMES])
        self.data_info_var.set(
            f"{len(df)} rows loaded  (showing first {min(len(df),200)})")

    def _train_model(self):
        if self.model.df is None:
            messagebox.showwarning("No data", "Load data first.")
            return
        try:
            split = int(self.split_var.get())
            assert 5 <= split <= 50
        except Exception:
            messagebox.showerror("Error", "Test split must be 5–50.")
            return
        self.train_msg_var.set("Training…")
        self.update_idletasks()
        ok, msg = self.model.train(test_size=split / 100)
        self.train_msg_var.set(msg)
        self._set_status(msg, ok)
        if ok:
            m = self.model.metrics
            self.metric_vars["r2"].set(f"{m['r2']:.4f}")
            self.metric_vars["mae"].set(f"{m['mae']:.2f}")
            self.metric_vars["rmse"].set(f"{m['rmse']:.2f}")
            self.split_info_var.set(
                f"Train: {m['n_train']}  ·  Test: {m['n_test']}")
            self._draw_coef_chart(m["coefs"])
            self._draw_scatter(m["y_te"], m["y_pred"])

    def _draw_coef_chart(self, coefs):
        c = self.coef_canvas
        c.delete("all")
        self.update_idletasks()
        W, H = c.winfo_width() or 400, 120
        vals = list(coefs.values())
        labels = [f[:12] for f in coefs.keys()]
        max_v = max(abs(v) for v in vals) or 1
        bar_h = 18
        gap   = 8
        left  = 130
        right = W - 20
        scale = (right - left) / max_v

        for i, (label, val) in enumerate(zip(labels, vals)):
            y = 10 + i * (bar_h + gap)
            c.create_text(left - 4, y + bar_h // 2,
                          text=label, anchor="e",
                          font=FONT_SM, fill=MID_TEXT)
            bw = abs(val) * scale
            color = BLUE if val >= 0 else RED
            c.create_rectangle(left, y, left + bw, y + bar_h,
                                fill=color, outline="")
            c.create_text(left + bw + 4, y + bar_h // 2,
                          text=f"{val:+.3f}", anchor="w",
                          font=("Courier New", 8), fill=DARK_TEXT)

    def _draw_scatter(self, y_te, y_pred):
        c = self.scatter_canvas
        c.delete("all")
        self.update_idletasks()
        W = c.winfo_width() or 400
        H = 180
        pad = 30
        lo, hi = 0, 100
        def tx(v): return pad + (v - lo) / (hi - lo) * (W - 2 * pad)
        def ty(v): return H - pad - (v - lo) / (hi - lo) * (H - 2 * pad)
        # Diagonal reference
        c.create_line(tx(lo), ty(lo), tx(hi), ty(hi),
                      fill=BORDER, dash=(4, 4))
        # Axes labels
        c.create_text(W // 2, H - 6, text="Actual", font=FONT_SM, fill=MID_TEXT)
        c.create_text(10, H // 2, text="Pred", font=FONT_SM, fill=MID_TEXT,
                      angle=90)
        # Points
        for a, p in zip(y_te, y_pred):
            x, y = tx(a), ty(p)
            c.create_oval(x-3, y-3, x+3, y+3,
                          fill=BLUE, outline="", stipple="")

    def _predict(self, event=None):
        if not self.model.trained:
            messagebox.showwarning("Not trained", "Train the model first.")
            return
        vals = []
        for feat in FEATURES:
            try:
                vals.append(float(self.predict_entries[feat].get().strip()))
            except ValueError:
                messagebox.showerror("Error", f'Bad value for "{feat}"')
                return
        ok, result = self.model.predict_one(vals)
        if not ok:
            messagebox.showerror("Error", str(result))
            return

        score = result
        self.score_var.set(f"{score:.1f}")

        rmse = self.model.metrics.get("rmse", 0)
        lo = max(0, score - rmse)
        hi = min(100, score + rmse)
        self.conf_var.set(f"±RMSE range: {lo:.1f} – {hi:.1f}")

        if score >= 90:   grade, color = "🏆 Excellent", GREEN
        elif score >= 75: grade, color = "✅ Good",      TEAL
        elif score >= 60: grade, color = "📘 Average",   AMBER
        elif score >= 40: grade, color = "⚠️ Below Avg", RED
        else:             grade, color = "🔴 At Risk",   "#dc2626"
        self.grade_var.set(grade)

        # Log
        line = (f"Score={score:.1f}  " +
                "  ".join(f"{f[:4]}={v}" for f, v in zip(FEATURES, vals)) + "\n")
        self.log_text.config(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_predict(self):
        for v in self.predict_entries.values():
            v.set("")
        self.score_var.set("—")
        self.grade_var.set("")
        self.conf_var.set("")

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _card(self, parent, title, pad):
        outer = tk.Frame(parent, bg=BORDER, bd=1)
        outer.pack(fill="x", **pad)
        inner = tk.Frame(outer, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        hdr = tk.Frame(inner, bg=INPUT_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, font=FONT_H2, bg=INPUT_BG,
                 fg=DARK_TEXT, pady=10, padx=16, anchor="w").pack(fill="x")
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")
        return inner

    def _mini_card(self, parent, title, col):
        f = tk.Frame(parent, bg=INPUT_BG, bd=1, relief="solid")
        f.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
        tk.Label(f, text=title, font=FONT_H3,
                 bg=INPUT_BG, fg=DARK_TEXT,
                 pady=8, anchor="center").pack(fill="x")
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=10)
        return f

    def _btn(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_BTN, bg=color, fg=WHITE,
                  relief="flat", activebackground=DARK_TEXT,
                  activeforeground=WHITE, cursor="hand2",
                  pady=7, padx=14, bd=0).pack(
            fill="x", padx=10, pady=8)

    def _btn_inline(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_BTN, bg=color, fg=WHITE,
                  relief="flat", activebackground=DARK_TEXT,
                  activeforeground=WHITE, cursor="hand2",
                  pady=6, padx=12, bd=0).pack(side="left", padx=4)

    def _set_status(self, msg, ok=True):
        self.status_var.set(("✓ " if ok else "✗ ") + msg)


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
