#!/usr/bin/env python3
"""
Clock Application - Grayscale Theme
Colors: #000000, #444444, #888888, #cccccc, #ffffff
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo, available_timezones
except ImportError:
    from datetime import timezone as ZoneInfo
    def available_timezones():
        return ["UTC", "Africa/Tripoli", "America/New_York", "Europe/London", 
                "Asia/Tokyo", "Europe/Paris", "Asia/Dubai", "Australia/Sydney"]

# --- CONFIGURATION ---
STATE_FILE = Path("/tmp/omarchy_status.json")
SIGNAL_FILE = Path("/tmp/omarchy.signal")
CONFIG_DIR = Path.home() / ".config" / "clock"
CONFIG_FILE = CONFIG_DIR / "settings.json"
PERSIST_FILE = CONFIG_DIR / "session.json"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

ALL_TIMEZONES = sorted(list(available_timezones()))
ALL_TIMEZONES = ["Local", "UTC"] + [tz for tz in ALL_TIMEZONES if tz not in ["Local", "UTC"]]

DEFAULT_SETTINGS = {
    "background": True,
    "sound_enabled": True,
    "work_duration": 25,
    "short_break": 5,
    "long_break": 15,
    "timezone_str": "Local",
    "format_24h": False,
    "show_seconds": True,
    "auto_start_breaks": False,
    "pomodoro_count": 0,
    "daily_focus_minutes": 0,
    "last_reset_date": ""
}

# --- GRAYSCALE COLORS ---
C_BLACK = "#000000"
C_DARK = "#444444"
C_MID = "#888888"
C_LIGHT = "#cccccc"
C_WHITE = "#ffffff"

# Semantic mapping
C_BG = C_BLACK
C_SIDEBAR = "#111111"
C_SURFACE = C_DARK
C_FG = C_WHITE
C_ACCENT = C_LIGHT
C_ACCENT_DIM = C_DARK
C_TEXT_DIM = C_MID
C_BORDER = C_DARK

# State colors (all grayscale)
C_SUCCESS = C_LIGHT
C_URGENT = C_WHITE
C_WARN = C_LIGHT

# --- FONTS ---
FONT_TITLE = ("Google Sans Display", 13, "bold")
FONT_DISPLAY = ("Google Sans Display", 48, "bold")
FONT_DISPLAY_SMALL = ("Google Sans Display", 32, "bold")
FONT_BODY = ("Google Sans Display", 11)
FONT_NAV = ("Google Sans Display", 10, "bold")
FONT_MONO = ("JetBrains Mono", 11)


class OmarchyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clock")
        self.geometry("750x700")
        self.configure(bg=C_BG)
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (375)
        y = (self.winfo_screenheight() // 2) - (350)
        self.geometry(f'+{x}+{y}')

        self.settings = self.load_settings()
        self.current_tab = "clock"
        
        # Pomodoro state
        self.pomo_state = "stopped"
        self.pomo_time = self.settings["work_duration"] * 60
        self.pomo_mode = "work"
        self.pomo_total_time = self.pomo_time
        self.pomo_sessions_today = self.settings.get("pomodoro_count", 0)
        
        # Timer state
        self.timer_state = "stopped"
        self.timer_curr = 0
        self.timer_target = 0
        
        # Stopwatch state
        self.sw_state = "stopped"
        self.sw_start = 0
        self.sw_elapsed = 0
        self.sw_offset = 0
        self.lap_count = 0
        self.lap_times = []
        
        # Time tracking
        self.last_tick = time.perf_counter()
        self.running = True

        self.check_daily_reset()
        self.load_session()
        self.setup_styles()
        self.create_layout()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind('<Control-q>', lambda e: self.quit_app())
        self.bind('<Escape>', lambda e: self.on_close())
        self.bind('<space>', lambda e: self.handle_space())
        
        self.update_loop()
        self.check_signal()

    def check_daily_reset(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.settings.get("last_reset_date", "") != today:
            self.settings["pomodoro_count"] = 0
            self.settings["daily_focus_minutes"] = 0
            self.settings["last_reset_date"] = today
            self.save_settings()

    def handle_space(self):
        if self.current_tab == "pomo":
            self.toggle_pomo()
        elif self.current_tab == "timer":
            self.toggle_timer()
        elif self.current_tab == "sw":
            self.toggle_sw()

    def load_settings(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    return {**DEFAULT_SETTINGS, **loaded}
            except:
                pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def load_session(self):
        if PERSIST_FILE.exists():
            try:
                with open(PERSIST_FILE, 'r') as f:
                    session = json.load(f)
                    
                if session.get('pomo_state') == 'running':
                    elapsed = time.time() - session.get('pomo_start', 0)
                    remaining = session.get('pomo_time', 0) - elapsed
                    if remaining > 0:
                        self.pomo_time = remaining
                        self.pomo_mode = session.get('pomo_mode', 'work')
                        self.pomo_total_time = session.get('pomo_total_time', self.pomo_time)
                        self.pomo_state = 'running'
                
                if session.get('timer_state') == 'running':
                    elapsed = time.time() - session.get('timer_start', 0)
                    remaining = session.get('timer_curr', 0) - elapsed
                    if remaining > 0:
                        self.timer_curr = remaining
                        self.timer_target = session.get('timer_target', remaining)
                        self.timer_state = 'running'
                        
                if session.get('sw_state') == 'running':
                    self.sw_offset = session.get('sw_offset', 0)
                    elapsed = time.time() - session.get('sw_start', 0)
                    self.sw_offset += elapsed
                    self.sw_start = time.perf_counter()
                    self.sw_state = 'running'
                elif session.get('sw_state') == 'paused':
                    self.sw_offset = session.get('sw_offset', 0)
                    self.sw_elapsed = self.sw_offset
                    self.sw_state = 'paused'
            except:
                pass

    def save_session(self):
        try:
            session = {
                'pomo_state': self.pomo_state,
                'pomo_time': self.pomo_time,
                'pomo_mode': self.pomo_mode,
                'pomo_total_time': self.pomo_total_time,
                'pomo_start': time.time() if self.pomo_state == 'running' else 0,
                'timer_state': self.timer_state,
                'timer_curr': self.timer_curr,
                'timer_target': self.timer_target,
                'timer_start': time.time() if self.timer_state == 'running' else 0,
                'sw_state': self.sw_state,
                'sw_offset': self.sw_offset if self.sw_state == 'paused' else 
                             (self.sw_offset + time.perf_counter() - self.sw_start if self.sw_state == 'running' else 0),
                'sw_start': time.time() if self.sw_state == 'running' else 0
            }
            with open(PERSIST_FILE, 'w') as f:
                json.dump(session, f)
        except:
            pass

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=C_BG)
        style.configure("Sidebar.TFrame", background=C_SIDEBAR)
        style.configure("Card.TFrame", background=C_SURFACE)
        
        style.configure("Sidebar.TButton", 
            background=C_SIDEBAR, foreground=C_MID, 
            font=FONT_NAV, borderwidth=0, focuscolor="none", padding=[12, 18])
        style.map("Sidebar.TButton", 
            background=[("active", C_DARK)], 
            foreground=[("active", C_WHITE)])
        
        style.configure("Active.Sidebar.TButton", 
            background=C_DARK, foreground=C_WHITE, 
            font=FONT_NAV, borderwidth=0, focuscolor="none", padding=[12, 18])
        
        style.configure("Action.TButton", 
            font=FONT_TITLE, background=C_WHITE, foreground=C_BLACK, 
            borderwidth=0, padding=[20, 12])
        style.map("Action.TButton",
            background=[("active", C_LIGHT), ("pressed", C_MID)])
        
        style.configure("Sec.TButton", 
            font=FONT_BODY, background=C_DARK, foreground=C_WHITE, 
            borderwidth=0, padding=[12, 8])
        style.map("Sec.TButton",
            background=[("active", C_MID)])
        
        style.configure("Danger.TButton", 
            font=FONT_BODY, background=C_MID, foreground=C_BLACK, 
            borderwidth=0, padding=[12, 8])
        style.map("Danger.TButton",
            background=[("active", C_LIGHT)])
        
        style.configure("TEntry", 
            fieldbackground=C_DARK, foreground=C_WHITE, 
            borderwidth=0, insertcolor=C_WHITE, padding=8)
        
        style.configure("TLabel", background=C_BG, foreground=C_FG)
        style.configure("Display.TLabel", font=FONT_DISPLAY, background=C_BG, foreground=C_FG)
        style.configure("Card.TLabel", background=C_SURFACE, foreground=C_FG)
        
        style.configure("Horizontal.TProgressbar",
            background=C_WHITE, troughcolor=C_DARK, borderwidth=0, thickness=8)

    def create_layout(self):
        main = tk.Frame(self, bg=C_BG)
        main.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ttk.Frame(main, style="Sidebar.TFrame", width=140)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self.sidebar, bg=C_SIDEBAR)
        logo_frame.pack(fill="x", pady=(20, 30))
        tk.Label(logo_frame, text="◷", font=("", 28), bg=C_SIDEBAR, fg=C_WHITE).pack()
        tk.Label(logo_frame, text="CLOCK", font=FONT_NAV, bg=C_SIDEBAR, fg=C_LIGHT).pack()

        nav_buttons = [
            (" CLOCK", "clock"),
            (" FOCUS", "pomo"),
            (" TIMER", "timer"),
            (" STOPWATCH", "sw")
        ]
        
        self.nav_btns = {}
        for btn_text, tab in nav_buttons:
            btn = ttk.Button(self.sidebar, text=btn_text, style="Sidebar.TButton", 
                           command=lambda t=tab: self.switch_tab(t))
            btn.pack(fill="x", pady=2)
            self.nav_btns[tab] = btn
            
        tk.Frame(self.sidebar, bg=C_SIDEBAR).pack(expand=True)
        
        # Stats
        self.stats_frame = tk.Frame(self.sidebar, bg=C_SIDEBAR)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(self.stats_frame, text="Today", font=("Google Sans Display", 9), 
                bg=C_SIDEBAR, fg=C_MID).pack()
        self.lbl_sessions = tk.Label(self.stats_frame, text="0 sessions", 
                                     font=FONT_BODY, bg=C_SIDEBAR, fg=C_WHITE)
        self.lbl_sessions.pack()
        
        # Settings button
        self.btn_settings = ttk.Button(self.sidebar, text=" SETTINGS", 
                                      style="Sidebar.TButton", 
                                      command=lambda: self.switch_tab("settings"))
        self.btn_settings.pack(fill="x", pady=(10, 20))
        self.nav_btns["settings"] = self.btn_settings

        # Content
        self.content = ttk.Frame(main)
        self.content.pack(side="right", fill="both", expand=True, padx=30, pady=20)
        self.frames = {}
        
        self.create_clock_tab()
        self.create_pomo_tab()
        self.create_timer_tab()
        self.create_stopwatch_tab()
        self.create_settings_tab()

        self.switch_tab("clock")

    def create_clock_tab(self):
        self.frames["clock"] = ttk.Frame(self.content)
        
        self.lbl_clock_main = ttk.Label(self.frames["clock"], text="...", 
                                        style="Display.TLabel")
        self.lbl_clock_main.pack(pady=(30, 10))
        
        self.lbl_seconds = ttk.Label(self.frames["clock"], text="", 
                                     font=("Google Sans Display", 18), 
                                     foreground=C_MID)
        self.lbl_seconds.pack()
        
        self.lbl_date = ttk.Label(self.frames["clock"], text="...", 
                                 font=FONT_BODY, foreground=C_MID)
        self.lbl_date.pack(pady=(20, 5))
        
        self.lbl_day = ttk.Label(self.frames["clock"], text="...", 
                                font=("Google Sans Display", 18, "bold"), 
                                foreground=C_WHITE)
        self.lbl_day.pack(pady=5)
        
        self.lbl_tz_view = ttk.Label(self.frames["clock"], text="", 
                                    font=("monospace", 10), foreground=C_MID)
        self.lbl_tz_view.pack(pady=10)
        
        # World clocks
        tk.Frame(self.frames["clock"], bg=C_DARK, height=1).pack(fill="x", pady=20)
        
        ttk.Label(self.frames["clock"], text="World Clocks", 
                 font=FONT_TITLE, foreground=C_LIGHT).pack(pady=(0, 15))
        
        world_frame = ttk.Frame(self.frames["clock"])
        world_frame.pack(pady=10)
        
        self.world_clocks = []
        world_cities = [
            ("New York", "America/New_York"),
            ("London", "Europe/London"),
            ("Tokyo", "Asia/Tokyo"),
            ("Dubai", "Asia/Dubai")
        ]
        
        for tz_name, tz_str in world_cities:
            frame = tk.Frame(world_frame, bg=C_DARK, padx=15, pady=10)
            frame.pack(side="left", padx=8)
            
            tk.Label(frame, text=tz_name, font=("Google Sans Display", 9), 
                    bg=C_DARK, fg=C_MID).pack()
            lbl = tk.Label(frame, text="--:--", font=("Google Sans Display", 14, "bold"),
                          bg=C_DARK, fg=C_WHITE)
            lbl.pack()
            
            self.world_clocks.append((lbl, tz_str))

    def create_pomo_tab(self):
        self.frames["pomo"] = ttk.Frame(self.content)
        
        self.lbl_pomo_mode = ttk.Label(self.frames["pomo"], text="WORK SESSION", 
                                       font=FONT_TITLE, foreground=C_WHITE)
        self.lbl_pomo_mode.pack(pady=(20, 10))
        
        self.lbl_pomo_time = ttk.Label(self.frames["pomo"], text="25:00", 
                                       style="Display.TLabel")
        self.lbl_pomo_time.pack(pady=10)
        
        self.pomo_progress = ttk.Progressbar(self.frames["pomo"], length=450, 
                                             mode='determinate')
        self.pomo_progress.pack(pady=15)
        
        self.lbl_pomo_status = ttk.Label(self.frames["pomo"], text="Ready to focus", 
                                        font=FONT_BODY, foreground=C_MID)
        self.lbl_pomo_status.pack(pady=5)
        
        # Mode buttons
        mode_frame = ttk.Frame(self.frames["pomo"])
        mode_frame.pack(pady=15)
        
        self.btn_mode_work = ttk.Button(mode_frame, text=f"Work ({self.settings['work_duration']}m)", 
                  style="Sec.TButton", command=lambda: self.set_pomo_mode("work"))
        self.btn_mode_work.pack(side="left", padx=5)
        
        self.btn_mode_short = ttk.Button(mode_frame, text=f"Short ({self.settings['short_break']}m)", 
                  style="Sec.TButton", command=lambda: self.set_pomo_mode("short"))
        self.btn_mode_short.pack(side="left", padx=5)
        
        self.btn_mode_long = ttk.Button(mode_frame, text=f"Long ({self.settings['long_break']}m)", 
                  style="Sec.TButton", command=lambda: self.set_pomo_mode("long"))
        self.btn_mode_long.pack(side="left", padx=5)
        
        # Custom
        custom_frame = ttk.Frame(self.frames["pomo"])
        custom_frame.pack(pady=10)
        
        ttk.Label(custom_frame, text="Custom (min):", font=FONT_BODY).pack(side="left", padx=5)
        self.ent_pomo_custom = ttk.Entry(custom_frame, width=6, justify="center", font=FONT_MONO)
        self.ent_pomo_custom.insert(0, "25")
        self.ent_pomo_custom.pack(side="left", padx=5)
        ttk.Button(custom_frame, text="Set", style="Sec.TButton", 
                  command=self.apply_custom_pomo).pack(side="left", padx=5)

        # Controls
        control_frame = ttk.Frame(self.frames["pomo"])
        control_frame.pack(pady=20)
        
        self.btn_pomo_action = ttk.Button(control_frame, text="▶ START", 
                                         style="Action.TButton", command=self.toggle_pomo)
        self.btn_pomo_action.pack(side="left", padx=10, ipadx=20)
        
        ttk.Button(control_frame, text="↺ Reset", style="Sec.TButton",
                  command=self.reset_pomo).pack(side="left", padx=5)

    def create_timer_tab(self):
        self.frames["timer"] = ttk.Frame(self.content)
        
        ttk.Label(self.frames["timer"], text="Countdown Timer", 
                 font=FONT_TITLE, foreground=C_LIGHT).pack(pady=(20, 10))
        
        input_frame = ttk.Frame(self.frames["timer"])
        input_frame.pack(pady=20)
        
        ttk.Label(input_frame, text="Minutes:", font=FONT_BODY).pack(side="left", padx=5)
        self.ent_timer = ttk.Entry(input_frame, justify="center", 
                                   font=("JetBrains Mono", 24), width=6)
        self.ent_timer.insert(0, "10")
        self.ent_timer.pack(side="left", padx=10)
        
        # Presets
        preset_frame = ttk.Frame(self.frames["timer"])
        preset_frame.pack(pady=10)
        
        for mins in [1, 3, 5, 10, 15, 30, 60]:
            label = f"{mins}m" if mins < 60 else "1h"
            ttk.Button(preset_frame, text=label, style="Sec.TButton",
                      command=lambda m=mins: self.set_timer_preset(m)).pack(side="left", padx=3)
        
        self.lbl_timer_count = ttk.Label(self.frames["timer"], text="00:00", 
                                        style="Display.TLabel", foreground=C_LIGHT)
        self.lbl_timer_count.pack(pady=15)
        
        self.timer_progress = ttk.Progressbar(self.frames["timer"], length=450, 
                                              mode='determinate')
        self.timer_progress.pack(pady=10)
        
        btn_frame = ttk.Frame(self.frames["timer"])
        btn_frame.pack(pady=20)
        
        self.btn_timer_action = ttk.Button(btn_frame, text="▶ START", 
                                          style="Action.TButton", command=self.toggle_timer)
        self.btn_timer_action.pack(side="left", padx=10, ipadx=20)
        
        ttk.Button(btn_frame, text="↺ Reset", style="Sec.TButton",
                  command=self.reset_timer).pack(side="left", padx=5)

    def create_stopwatch_tab(self):
        self.frames["sw"] = ttk.Frame(self.content)
        
        ttk.Label(self.frames["sw"], text="Stopwatch", 
                 font=FONT_TITLE, foreground=C_LIGHT).pack(pady=(20, 10))
        
        self.lbl_sw_time = ttk.Label(self.frames["sw"], text="00:00.00", 
                                     style="Display.TLabel", foreground=C_WHITE)
        self.lbl_sw_time.pack(pady=20)
        
        sw_btns = ttk.Frame(self.frames["sw"])
        sw_btns.pack(pady=15)
        
        self.btn_sw_toggle = ttk.Button(sw_btns, text="▶ Start", 
                                        style="Action.TButton", command=self.toggle_sw)
        self.btn_sw_toggle.pack(side="left", padx=10, ipadx=15)
        
        self.btn_sw_lap = ttk.Button(sw_btns, text="◉ Lap", 
                                    style="Sec.TButton", command=self.record_lap, 
                                    state="disabled")
        self.btn_sw_lap.pack(side="left", padx=5)
        
        ttk.Button(sw_btns, text="↺ Reset", style="Sec.TButton", 
                  command=self.reset_sw).pack(side="left", padx=5)
        
        # Laps
        lap_header = ttk.Frame(self.frames["sw"])
        lap_header.pack(fill="x", pady=(25, 10))
        
        ttk.Label(lap_header, text="Lap Times", font=FONT_TITLE, 
                 foreground=C_LIGHT).pack(side="left")
        
        self.lbl_lap_count = ttk.Label(lap_header, text="(0 laps)", 
                                       font=FONT_BODY, foreground=C_MID)
        self.lbl_lap_count.pack(side="left", padx=10)
        
        lap_container = tk.Frame(self.frames["sw"], bg=C_DARK)
        lap_container.pack(fill="both", expand=True, pady=10)
        
        self.sw_scroll = ttk.Scrollbar(lap_container)
        self.sw_scroll.pack(side="right", fill="y")
        
        self.txt_laps = tk.Text(lap_container, height=8, bg=C_DARK, 
                               fg=C_WHITE, bd=0, highlightthickness=0, 
                               yscrollcommand=self.sw_scroll.set, 
                               font=FONT_MONO, padx=15, pady=10)
        self.txt_laps.pack(side="left", fill="both", expand=True)
        self.sw_scroll.config(command=self.txt_laps.yview)
        
        self.txt_laps.tag_configure("best", foreground=C_WHITE, font=(FONT_MONO[0], FONT_MONO[1], "bold"))
        self.txt_laps.tag_configure("worst", foreground=C_MID)
        self.txt_laps.tag_configure("normal", foreground=C_LIGHT)
        self.txt_laps.config(state="disabled")

    def create_settings_tab(self):
        self.frames["settings"] = ttk.Frame(self.content)
        
        canvas = tk.Canvas(self.frames["settings"], bg=C_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frames["settings"], orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # General
        ttk.Label(scrollable, text="General Settings", font=FONT_TITLE, 
                 foreground=C_LIGHT).pack(anchor="w", pady=(15, 20))
        
        self.var_bg = tk.BooleanVar(value=self.settings["background"])
        ttk.Checkbutton(scrollable, text="Enable Background Mode", 
                       variable=self.var_bg, command=self.save_simple_settings).pack(anchor="w", pady=8)
        
        self.var_24h = tk.BooleanVar(value=self.settings["format_24h"])
        ttk.Checkbutton(scrollable, text="24-Hour Format", 
                       variable=self.var_24h, command=self.save_simple_settings).pack(anchor="w", pady=8)
        
        self.var_seconds = tk.BooleanVar(value=self.settings.get("show_seconds", True))
        ttk.Checkbutton(scrollable, text="Show Seconds", 
                       variable=self.var_seconds, command=self.save_simple_settings).pack(anchor="w", pady=8)
        
        self.var_sound = tk.BooleanVar(value=self.settings["sound_enabled"])
        ttk.Checkbutton(scrollable, text="Sound Alerts", 
                       variable=self.var_sound, command=self.save_simple_settings).pack(anchor="w", pady=8)
        
        self.var_auto_break = tk.BooleanVar(value=self.settings.get("auto_start_breaks", False))
        ttk.Checkbutton(scrollable, text="Auto-start Breaks", 
                       variable=self.var_auto_break, command=self.save_simple_settings).pack(anchor="w", pady=8)

        # Pomodoro
        tk.Frame(scrollable, bg=C_DARK, height=1).pack(fill="x", pady=20)
        
        ttk.Label(scrollable, text="Pomodoro Durations", font=FONT_TITLE, 
                 foreground=C_LIGHT).pack(anchor="w", pady=(0, 15))
        
        self.pomo_entries = {}
        for label, key, default in [
            ("Work (min):", "work_duration", 25),
            ("Short Break (min):", "short_break", 5),
            ("Long Break (min):", "long_break", 15)
        ]:
            frame = ttk.Frame(scrollable)
            frame.pack(fill="x", pady=8)
            ttk.Label(frame, text=label, font=FONT_BODY).pack(side="left")
            
            entry = ttk.Entry(frame, width=6, justify="center", font=FONT_MONO)
            entry.insert(0, str(self.settings.get(key, default)))
            entry.pack(side="right", padx=10)
            entry.bind("<FocusOut>", lambda e, k=key, ent=entry: self.update_pomo_setting(k, ent))
            self.pomo_entries[key] = entry

        # Timezone
        tk.Frame(scrollable, bg=C_DARK, height=1).pack(fill="x", pady=20)
        
        ttk.Label(scrollable, text="Timezone", font=FONT_TITLE, 
                 foreground=C_LIGHT).pack(anchor="w", pady=(0, 15))
        
        ttk.Label(scrollable, text="Search:", font=FONT_BODY).pack(anchor="w", pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_timezone)
        ttk.Entry(scrollable, textvariable=self.search_var, font=FONT_BODY).pack(fill="x", pady=5)
        
        self.list_tz = tk.Listbox(scrollable, height=6, bg=C_DARK, fg=C_WHITE, 
                                  bd=0, font=FONT_MONO, selectbackground=C_MID,
                                  selectforeground=C_BLACK, highlightthickness=0)
        self.list_tz.pack(fill="x", pady=10)
        self.list_tz.bind("<<ListboxSelect>>", self.on_select_tz)
        self.filter_timezone()

        # Exit
        tk.Frame(scrollable, bg=C_DARK, height=1).pack(fill="x", pady=20)
        
        ttk.Button(scrollable, text="Exit Application", style="Danger.TButton", 
                  command=self.quit_app).pack(pady=20, fill="x")

    # === Utilities ===
    
    def format_sw_time(self, elapsed):
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        return f"{minutes:02d}:{seconds:05.2f}"

    def format_time(self, seconds):
        seconds = max(0, int(seconds))
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def get_time(self):
        tz = self.settings["timezone_str"]
        if tz == "Local":
            return datetime.now()
        try:
            return datetime.now(ZoneInfo(tz))
        except:
            return datetime.now()

    # === Update Loop ===
    
    def update_loop(self):
        if not self.running:
            return
        
        now_ts = time.perf_counter()
        delta = now_ts - self.last_tick
        self.last_tick = now_ts

        # Clock
        now = self.get_time()
        fmt = "%H:%M" if self.settings["format_24h"] else "%I:%M %p"
        self.lbl_clock_main.config(text=now.strftime(fmt))
        
        if self.settings.get("show_seconds", True):
            self.lbl_seconds.config(text=f":{now.strftime('%S')}")
        else:
            self.lbl_seconds.config(text="")
            
        self.lbl_date.config(text=now.strftime("%d %B %Y"))
        self.lbl_day.config(text=now.strftime("%A"))
        self.lbl_tz_view.config(text=f"[{self.settings['timezone_str']}]")
        
        # World clocks
        for lbl, tz_str in self.world_clocks:
            try:
                tz_time = datetime.now(ZoneInfo(tz_str))
                fmt_world = "%H:%M" if self.settings["format_24h"] else "%I:%M %p"
                lbl.config(text=tz_time.strftime(fmt_world))
            except:
                lbl.config(text="--:--")

        # Pomodoro
        if self.pomo_state == "running":
            self.pomo_time = max(0, self.pomo_time - delta)
            self.lbl_pomo_time.config(text=self.format_time(self.pomo_time))
            
            progress = ((self.pomo_total_time - self.pomo_time) / self.pomo_total_time) * 100
            self.pomo_progress['value'] = progress
            
            remaining_mins = int(self.pomo_time / 60)
            self.lbl_pomo_status.config(text=f"{remaining_mins + 1} min remaining")
            
            if self.pomo_time <= 0:
                self.pomo_complete()

        # Timer
        if self.timer_state == "running":
            self.timer_curr = max(0, self.timer_curr - delta)
            self.lbl_timer_count.config(text=self.format_time(self.timer_curr))
            
            if self.timer_target > 0:
                progress = ((self.timer_target - self.timer_curr) / self.timer_target) * 100
                self.timer_progress['value'] = progress
            
            if self.timer_curr <= 0:
                self.timer_complete()

        # Stopwatch
        if self.sw_state == "running":
            self.sw_elapsed = time.perf_counter() - self.sw_start + self.sw_offset
            self.lbl_sw_time.config(text=self.format_sw_time(self.sw_elapsed))

        # Stats
        self.lbl_sessions.config(text=f"{self.pomo_sessions_today} sessions")
        
        # Waybar
        self.write_status(now)
        
        self.after(33, self.update_loop)

    def pomo_complete(self):
        self.pomo_state = "stopped"
        self.play_sound()
        self.btn_pomo_action.config(text="▶ START")
        
        if self.pomo_mode == "work":
            self.pomo_sessions_today += 1
            self.settings["pomodoro_count"] = self.pomo_sessions_today
            mins = self.settings["work_duration"]
            self.settings["daily_focus_minutes"] = self.settings.get("daily_focus_minutes", 0) + mins
            self.save_settings()
            
            self.send_notification("Focus Complete!", f"Sessions today: {self.pomo_sessions_today}")
            
            if self.settings.get("auto_start_breaks", False):
                if self.pomo_sessions_today % 4 == 0:
                    self.set_pomo_mode("long")
                else:
                    self.set_pomo_mode("short")
                self.toggle_pomo()
            else:
                self.set_pomo_mode("short")
        else:
            self.send_notification("Break Over!", "Time to focus")
            self.set_pomo_mode("work")
        
        self.lbl_pomo_status.config(text="Complete!")

    def timer_complete(self):
        self.timer_state = "stopped"
        self.play_sound()
        self.btn_timer_action.config(text="▶ START")
        self.timer_progress['value'] = 100
        self.send_notification("Timer Complete!", "Time's up!")

    def send_notification(self, title, message):
        try:
            subprocess.Popen([
                "notify-send", "-a", "Clock", title, message
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

    def play_sound(self):
        if not self.settings["sound_enabled"]:
            return
        
        def _play():
            try:
                paths = [
                    "/usr/share/sounds/freedesktop/stereo/complete.oga",
                    "/usr/share/sounds/freedesktop/stereo/bell.oga"
                ]
                for path in paths:
                    if os.path.exists(path):
                        subprocess.Popen(["paplay", path], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        return
            except:
                pass
        
        threading.Thread(target=_play, daemon=True).start()

    def write_status(self, now):
        try:
            fmt = "%H:%M" if self.settings["format_24h"] else "%I:%M %p"
            status = {
                "text": f" {now.strftime(fmt)}",
                "tooltip": now.strftime('%A, %d %B %Y'),
                "class": "clock",
                "alt": "clock",
                "percentage": 0
            }
            
            if self.pomo_state == "running":
                progress = int(((self.pomo_total_time - self.pomo_time) / self.pomo_total_time) * 100)
                icon = "" if self.pomo_mode == "work" else "☕"
                status = {
                    "text": f"{icon} {self.format_time(self.pomo_time)}",
                    "tooltip": f"Pomodoro: {self.pomo_mode} ({progress}%)",
                    "class": f"pomodoro-{self.pomo_mode}",
                    "alt": "pomodoro",
                    "percentage": progress
                }
            elif self.pomo_state == "paused":
                status = {
                    "text": f" {self.format_time(self.pomo_time)} ||",
                    "tooltip": "Pomodoro Paused",
                    "class": "pomodoro-work",
                    "alt": "pomodoro-paused",
                    "percentage": 0
                }
            elif self.timer_state == "running":
                progress = int(((self.timer_target - self.timer_curr) / self.timer_target) * 100) if self.timer_target > 0 else 0
                status = {
                    "text": f" {self.format_time(self.timer_curr)}",
                    "tooltip": f"Timer ({progress}%)",
                    "class": "timer",
                    "alt": "timer",
                    "percentage": progress
                }
            elif self.sw_state == "running":
                status = {
                    "text": f" {self.format_sw_time(self.sw_elapsed)[:5]}",
                    "tooltip": f"Stopwatch - {self.lap_count} laps",
                    "class": "stopwatch",
                    "alt": "stopwatch",
                    "percentage": 0
                }
            elif self.sw_state == "paused":
                status = {
                    "text": f" {self.format_sw_time(self.sw_elapsed)[:5]} ||",
                    "tooltip": "Stopwatch Paused",
                    "class": "stopwatch",
                    "alt": "stopwatch-paused",
                    "percentage": 0
                }
            
            with open(STATE_FILE, "w") as f:
                json.dump(status, f)
        except:
            pass

    # === Navigation ===
    
    def switch_tab(self, tab_name):
        self.current_tab = tab_name
        
        for f in self.frames.values():
            f.pack_forget()
        
        self.frames[tab_name].pack(fill="both", expand=True)
        
        for name, btn in self.nav_btns.items():
            if name == tab_name:
                btn.configure(style="Active.Sidebar.TButton")
            else:
                btn.configure(style="Sidebar.TButton")

    # === Pomodoro ===
    
    def set_pomo_mode(self, mode):
        self.pomo_mode = mode
        self.pomo_state = "stopped"
        
        durations = {
            "work": self.settings["work_duration"],
            "short": self.settings["short_break"],
            "long": self.settings["long_break"]
        }
        labels = {
            "work": "WORK SESSION",
            "short": "SHORT BREAK",
            "long": "LONG BREAK"
        }
        
        mins = durations.get(mode, 25)
        self.pomo_time = mins * 60
        self.pomo_total_time = self.pomo_time
        
        self.lbl_pomo_mode.config(text=labels.get(mode, "WORK SESSION"))
        self.lbl_pomo_time.config(text=self.format_time(self.pomo_time))
        self.btn_pomo_action.config(text="▶ START")
        self.pomo_progress['value'] = 0
        self.lbl_pomo_status.config(text="Ready")

    def apply_custom_pomo(self):
        try:
            mins = int(self.ent_pomo_custom.get())
            if mins <= 0 or mins > 180:
                raise ValueError
            
            self.pomo_mode = "work"
            self.pomo_time = mins * 60
            self.pomo_total_time = self.pomo_time
            self.pomo_state = "stopped"
            
            self.lbl_pomo_mode.config(text=f"CUSTOM ({mins} MIN)")
            self.lbl_pomo_time.config(text=self.format_time(self.pomo_time))
            self.btn_pomo_action.config(text="▶ START")
            self.pomo_progress['value'] = 0
            self.lbl_pomo_status.config(text="Custom ready")
        except ValueError:
            messagebox.showerror("Error", "Enter 1-180 minutes")

    def toggle_pomo(self):
        if self.pomo_state == "stopped" or self.pomo_state == "paused":
            self.pomo_state = "running"
            self.btn_pomo_action.config(text="|| PAUSE")
            self.lbl_pomo_status.config(text="Focus!")
        else:
            self.pomo_state = "paused"
            self.btn_pomo_action.config(text="▶ RESUME")
            self.lbl_pomo_status.config(text="Paused")

    def reset_pomo(self):
        self.pomo_state = "stopped"
        self.set_pomo_mode(self.pomo_mode if self.pomo_mode in ["work", "short", "long"] else "work")

    # === Timer ===
    
    def set_timer_preset(self, minutes):
        self.ent_timer.delete(0, tk.END)
        self.ent_timer.insert(0, str(minutes))

    def toggle_timer(self):
        if self.timer_state == "running":
            self.timer_state = "stopped"
            self.btn_timer_action.config(text="▶ START")
        else:
            try:
                mins = float(self.ent_timer.get())
                if mins <= 0:
                    raise ValueError
                
                self.timer_curr = mins * 60
                self.timer_target = self.timer_curr
                self.timer_state = "running"
                self.btn_timer_action.config(text="■ STOP")
                self.timer_progress['value'] = 0
            except ValueError:
                messagebox.showerror("Error", "Enter valid minutes")

    def reset_timer(self):
        self.timer_state = "stopped"
        self.timer_curr = 0
        self.timer_target = 0
        self.lbl_timer_count.config(text="00:00")
        self.btn_timer_action.config(text="▶ START")
        self.timer_progress['value'] = 0

    # === Stopwatch ===
    
    def toggle_sw(self):
        if self.sw_state == "stopped":
            self.sw_start = time.perf_counter()
            self.sw_offset = 0
            self.sw_elapsed = 0
            self.sw_state = "running"
            self.btn_sw_toggle.config(text="|| Pause")
            self.btn_sw_lap.config(state="normal")
        elif self.sw_state == "running":
            self.sw_offset += time.perf_counter() - self.sw_start
            self.sw_state = "paused"
            self.btn_sw_toggle.config(text="▶ Resume")
        else:
            self.sw_start = time.perf_counter()
            self.sw_state = "running"
            self.btn_sw_toggle.config(text="|| Pause")

    def record_lap(self):
        if self.sw_elapsed > 0:
            self.lap_count += 1
            current = self.sw_elapsed
            
            lap_duration = current - (self.lap_times[-1][1] if self.lap_times else 0)
            self.lap_times.append((lap_duration, current))
            
            if len(self.lap_times) >= 2:
                sorted_laps = sorted([lt[0] for lt in self.lap_times])
                if lap_duration == sorted_laps[0]:
                    tag = "best"
                elif lap_duration == sorted_laps[-1]:
                    tag = "worst"
                else:
                    tag = "normal"
            else:
                tag = "normal"
            
            lap_text = f"LAP {self.lap_count:02d}    {self.format_sw_time(lap_duration):>10}    (Total: {self.format_sw_time(current)})\n"
            
            self.txt_laps.config(state="normal")
            self.txt_laps.insert("1.0", lap_text, tag)
            self.txt_laps.config(state="disabled")
            
            self.lbl_lap_count.config(text=f"({self.lap_count} laps)")

    def reset_sw(self):
        self.sw_state = "stopped"
        self.sw_elapsed = 0
        self.sw_offset = 0
        self.lap_count = 0
        self.lap_times = []
        self.lbl_sw_time.config(text="00:00.00")
        self.btn_sw_toggle.config(text="▶ Start")
        self.btn_sw_lap.config(state="disabled")
        self.lbl_lap_count.config(text="(0 laps)")
        
        self.txt_laps.config(state="normal")
        self.txt_laps.delete("1.0", tk.END)
        self.txt_laps.config(state="disabled")

    # === Settings ===
    
    def filter_timezone(self, *args):
        search = self.search_var.get().lower()
        self.list_tz.delete(0, tk.END)
        
        matches = [tz for tz in ALL_TIMEZONES if search in tz.lower()][:50]
        for tz in matches:
            self.list_tz.insert(tk.END, tz)
        
        try:
            current = self.settings["timezone_str"]
            if current in matches:
                idx = matches.index(current)
                self.list_tz.selection_set(idx)
                self.list_tz.see(idx)
        except:
            pass

    def on_select_tz(self, event):
        if self.list_tz.curselection():
            self.settings["timezone_str"] = self.list_tz.get(self.list_tz.curselection())
            self.save_settings()

    def update_pomo_setting(self, key, entry):
        try:
            value = int(entry.get())
            if value > 0 and value <= 180:
                self.settings[key] = value
                self.save_settings()
                
                if self.pomo_state == "stopped":
                    if key == "work_duration" and self.pomo_mode == "work":
                        self.set_pomo_mode("work")
                    elif key == "short_break" and self.pomo_mode == "short":
                        self.set_pomo_mode("short")
                    elif key == "long_break" and self.pomo_mode == "long":
                        self.set_pomo_mode("long")
                        
                self.btn_mode_work.config(text=f"Work ({self.settings['work_duration']}m)")
                self.btn_mode_short.config(text=f"Short ({self.settings['short_break']}m)")
                self.btn_mode_long.config(text=f"Long ({self.settings['long_break']}m)")
        except ValueError:
            entry.delete(0, tk.END)
            entry.insert(0, str(self.settings[key]))

    def save_simple_settings(self):
        self.settings["background"] = self.var_bg.get()
        self.settings["format_24h"] = self.var_24h.get()
        self.settings["show_seconds"] = self.var_seconds.get()
        self.settings["sound_enabled"] = self.var_sound.get()
        self.settings["auto_start_breaks"] = self.var_auto_break.get()
        self.save_settings()

    # === Signals ===
    
    def check_signal(self):
        if SIGNAL_FILE.exists():
            try:
                content = SIGNAL_FILE.read_text().strip()
                SIGNAL_FILE.unlink()
                
                if content == "pomo-toggle":
                    self.toggle_pomo()
                elif content == "pomo-work":
                    self.set_pomo_mode("work")
                    self.switch_tab("pomo")
                elif content == "pomo-short":
                    self.set_pomo_mode("short")
                    self.switch_tab("pomo")
                elif content == "pomo-long":
                    self.set_pomo_mode("long")
                    self.switch_tab("pomo")
                elif content == "pomo-reset":
                    self.reset_pomo()
                elif content == "timer-toggle":
                    self.toggle_timer()
                elif content == "timer-reset":
                    self.reset_timer()
                elif content == "sw-toggle":
                    self.toggle_sw()
                elif content == "sw-lap":
                    self.record_lap()
                elif content == "sw-reset":
                    self.reset_sw()
                elif content == "show":
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                else:
                    if self.winfo_viewable():
                        self.withdraw()
                    else:
                        self.deiconify()
                        self.lift()
                        self.focus_force()
            except:
                pass
        
        if self.running:
            self.after(200, self.check_signal)

    def on_close(self):
        if self.settings["background"]:
            self.withdraw()
        else:
            self.quit_app()

    def quit_app(self):
        self.running = False
        self.save_session()
        
        try:
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            if SIGNAL_FILE.exists():
                SIGNAL_FILE.unlink()
        except:
            pass
        
        self.destroy()


if __name__ == "__main__":
    app = OmarchyApp()
    app.mainloop()
