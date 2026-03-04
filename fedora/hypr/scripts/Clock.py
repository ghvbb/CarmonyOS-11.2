#!/usr/bin/env python3
"""
CarmonyOS Clock
Material Design 3 — Android-style Native GTK4 Application
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio, Pango

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
        return ["UTC", "Africa/Tripoli", "Africa/Benghazi", "America/New_York",
                "Europe/London", "Asia/Tokyo", "Europe/Paris", "Asia/Dubai",
                "Australia/Sydney", "Asia/Riyadh", "Africa/Cairo"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATE_FILE = Path("/tmp/carmonyos_status.json")
SIGNAL_FILE = Path("/tmp/carmonyos.signal")
CONFIG_DIR = Path.home() / ".config" / "carmonyos-clock"
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
    "last_reset_date": "",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Material Design 3 CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MD3_CSS = """
/* ─── MD3 Foundation ─── */

window.main-window {
    font-family: 'Google Sans', 'Google Sans Text', 'Roboto', 'Noto Sans', 'Segoe UI', sans-serif;
}

/* ─── MD3 Navigation Rail ─── */

.md3-nav-rail {
    padding: 12px 0;
}

.md3-nav-rail-item {
    border-radius: 16px;
    padding: 4px 0;
    min-height: 56px;
    min-width: 56px;
    margin: 2px 12px;
    transition: all 200ms ease;
}

.md3-nav-rail-item:hover {
    background: alpha(@accent_bg_color, 0.08);
}

.md3-nav-rail-item:selected {
    background: alpha(@accent_bg_color, 0.14);
}

.md3-nav-icon {
    font-size: 24px;
    min-width: 24px;
    min-height: 24px;
}

.md3-nav-label {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.md3-nav-indicator {
    background: @accent_bg_color;
    border-radius: 16px;
    min-height: 32px;
    min-width: 56px;
    padding: 0 16px;
}

/* ─── MD3 Display Typography ─── */

.md3-display-large {
    font-family: 'Google Sans Display', 'Product Sans', 'Roboto', sans-serif;
    font-size: 57px;
    font-weight: 400;
    letter-spacing: -0.25px;
    line-height: 64px;
}

.md3-display-medium {
    font-family: 'Google Sans Display', 'Product Sans', 'Roboto', sans-serif;
    font-size: 45px;
    font-weight: 400;
    line-height: 52px;
}

.md3-display-small {
    font-family: 'Google Sans Display', 'Product Sans', 'Roboto', sans-serif;
    font-size: 36px;
    font-weight: 400;
    line-height: 44px;
}

.md3-headline-large {
    font-family: 'Google Sans Display', 'Roboto', sans-serif;
    font-size: 32px;
    font-weight: 400;
    line-height: 40px;
}

.md3-headline-medium {
    font-family: 'Google Sans Display', 'Roboto', sans-serif;
    font-size: 28px;
    font-weight: 400;
    line-height: 36px;
}

.md3-headline-small {
    font-family: 'Google Sans Display', 'Roboto', sans-serif;
    font-size: 24px;
    font-weight: 400;
    line-height: 32px;
}

.md3-title-large {
    font-family: 'Google Sans', 'Roboto', sans-serif;
    font-size: 22px;
    font-weight: 400;
    line-height: 28px;
}

.md3-title-medium {
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 16px;
    font-weight: 500;
    letter-spacing: 0.15px;
    line-height: 24px;
}

.md3-title-small {
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    line-height: 20px;
}

.md3-label-large {
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    line-height: 20px;
}

.md3-label-medium {
    font-family: 'Google Sans Text', 'Roboto', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
    line-height: 16px;
}

.md3-label-small {
    font-family: 'Google Sans Text', 'Roboto', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
    line-height: 16px;
}

.md3-body-large {
    font-family: 'Google Sans Text', 'Roboto', sans-serif;
    font-size: 16px;
    font-weight: 400;
    letter-spacing: 0.5px;
    line-height: 24px;
}

.md3-body-medium {
    font-family: 'Google Sans Text', 'Roboto', sans-serif;
    font-size: 14px;
    font-weight: 400;
    letter-spacing: 0.25px;
    line-height: 20px;
}

.md3-body-small {
    font-family: 'Google Sans Text', 'Roboto', sans-serif;
    font-size: 12px;
    font-weight: 400;
    letter-spacing: 0.4px;
    line-height: 16px;
}

/* ─── MD3 Buttons ─── */

.md3-filled-button {
    border-radius: 20px;
    padding: 10px 24px;
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 40px;
    transition: all 200ms ease;
}

.md3-filled-tonal-button {
    border-radius: 20px;
    padding: 10px 24px;
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 40px;
    background: alpha(@accent_bg_color, 0.15);
    transition: all 200ms ease;
}

.md3-filled-tonal-button:hover {
    background: alpha(@accent_bg_color, 0.22);
}

.md3-outlined-button {
    border-radius: 20px;
    padding: 10px 24px;
    border: 1px solid alpha(currentColor, 0.2);
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 40px;
    transition: all 200ms ease;
}

.md3-outlined-button:hover {
    background: alpha(currentColor, 0.05);
}

.md3-text-button {
    border-radius: 20px;
    padding: 10px 16px;
    font-family: 'Google Sans', 'Roboto Medium', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 40px;
    transition: all 200ms ease;
}

.md3-text-button:hover {
    background: alpha(currentColor, 0.05);
}

.md3-fab {
    border-radius: 16px;
    padding: 16px;
    min-height: 56px;
    min-width: 56px;
    background: @accent_bg_color;
    color: @accent_fg_color;
    font-size: 24px;
    box-shadow: 0 3px 6px alpha(black, 0.15);
    transition: all 200ms ease;
}

.md3-fab:hover {
    box-shadow: 0 6px 12px alpha(black, 0.2);
}

.md3-fab-extended {
    border-radius: 16px;
    padding: 16px 24px;
    min-height: 56px;
    background: @accent_bg_color;
    color: @accent_fg_color;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    transition: all 200ms ease;
}

/* ─── MD3 Cards ─── */

.md3-card-elevated {
    border-radius: 12px;
    padding: 0;
    background: mix(@window_bg_color, @card_bg_color, 0.5);
    box-shadow: 0 1px 3px alpha(black, 0.08), 0 1px 2px alpha(black, 0.06);
    transition: all 200ms ease;
}

.md3-card-filled {
    border-radius: 12px;
    padding: 0;
    background: alpha(@card_bg_color, 0.6);
    transition: all 200ms ease;
}

.md3-card-outlined {
    border-radius: 12px;
    padding: 0;
    border: 1px solid alpha(currentColor, 0.12);
    transition: all 200ms ease;
}

/* ─── MD3 Chips ─── */

.md3-chip {
    border-radius: 8px;
    padding: 6px 16px;
    border: 1px solid alpha(currentColor, 0.15);
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 32px;
    transition: all 150ms ease;
}

.md3-chip:hover {
    background: alpha(currentColor, 0.06);
}

.md3-chip-selected {
    border-radius: 8px;
    padding: 6px 16px;
    background: alpha(@accent_bg_color, 0.18);
    border: 1px solid alpha(@accent_bg_color, 0.4);
    color: @accent_color;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 32px;
}

/* ─── MD3 Progress ─── */

.md3-progress-linear {
    min-height: 4px;
    border-radius: 2px;
}

.md3-progress-linear trough {
    min-height: 4px;
    border-radius: 2px;
    background: alpha(@accent_bg_color, 0.15);
}

.md3-progress-linear progress {
    min-height: 4px;
    border-radius: 2px;
    background: @accent_bg_color;
}

/* ─── MD3 Divider ─── */

.md3-divider {
    min-height: 1px;
    background: alpha(currentColor, 0.08);
}

/* ─── Clock Specific ─── */

.clock-time-hero {
    font-family: 'Google Sans Display', 'Product Sans', sans-serif;
    font-size: 80px;
    font-weight: 400;
    letter-spacing: -2px;
}

.clock-seconds-hero {
    font-family: 'Google Sans Display', 'Product Sans', sans-serif;
    font-size: 32px;
    font-weight: 300;
    opacity: 0.38;
    margin-top: -12px;
}

.clock-day-hero {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 24px;
    font-weight: 500;
    letter-spacing: 0.15px;
}

.clock-date-hero {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 16px;
    font-weight: 400;
    opacity: 0.6;
    letter-spacing: 0.25px;
}

.clock-tz-hero {
    font-family: 'JetBrains Mono', 'Fira Code', 'monospace';
    font-size: 12px;
    font-weight: 400;
    opacity: 0.3;
    letter-spacing: 0.4px;
}

/* ─── World Clock ─── */

.world-card-city {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
    opacity: 0.5;
}

.world-card-time {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 20px;
    font-weight: 500;
}

/* ─── Timer / Focus Display ─── */

.timer-hero {
    font-family: 'Google Sans Display', 'Product Sans', sans-serif;
    font-size: 72px;
    font-weight: 300;
    letter-spacing: -1px;
}

.timer-hero-medium {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 56px;
    font-weight: 300;
    letter-spacing: -1px;
}

.timer-hero-small {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 44px;
    font-weight: 400;
}

/* ─── Stopwatch ─── */

.sw-hero {
    font-family: 'Google Sans Display', 'Product Sans', sans-serif;
    font-size: 64px;
    font-weight: 300;
    letter-spacing: -1px;
}

.lap-row {
    padding: 12px 20px;
    border-bottom: 1px solid alpha(currentColor, 0.06);
}

.lap-num {
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    opacity: 0.45;
}

.lap-dur {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 16px;
    font-weight: 500;
}

.lap-tot {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px;
    opacity: 0.35;
}

.lap-best .lap-dur {
    color: @success_color;
    font-weight: 600;
}

.lap-worst {
    opacity: 0.4;
}

/* ─── Mode Chips ─── */

.mode-active {
    background: @accent_bg_color;
    color: @accent_fg_color;
    border-color: transparent;
}

/* ─── Status Label ─── */

.status-text {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 14px;
    font-weight: 400;
    opacity: 0.55;
}

/* ─── Section Header ─── */

.section-overline {
    font-family: 'Google Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 1.5px;
    opacity: 0.4;
}

/* ─── Nav Rail ─── */

.rail-bg {
    background: alpha(@headerbar_bg_color, 0.4);
}

/* ─── Sidebar Stat ─── */

.stat-num {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 28px;
    font-weight: 500;
}

.stat-unit {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 12px;
    font-weight: 500;
    opacity: 0.45;
    letter-spacing: 0.5px;
}

/* ─── Logo ─── */

.app-logo-icon {
    font-size: 40px;
}

.app-logo-name {
    font-family: 'Google Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    opacity: 0.6;
}

.app-logo-sub {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 1px;
    opacity: 0.28;
}

/* ─── Timer Input ─── */

.timer-entry-large {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 32px;
    font-weight: 300;
}

/* ─── Preset Button ─── */

.md3-preset {
    border-radius: 8px;
    padding: 8px 16px;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    min-height: 36px;
    min-width: 48px;
    transition: all 150ms ease;
}

/* ─── Page Container ─── */

.page-scroll {
    background: transparent;
}
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Clock Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ClockPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_valign(Gtk.Align.CENTER)
        content.set_halign(Gtk.Align.CENTER)
        content.set_margin_start(48)
        content.set_margin_end(48)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        scroll.set_child(content)

        # ── Hero Time ──
        self.lbl_time = Gtk.Label(label="--:--")
        self.lbl_time.add_css_class("clock-time-hero")
        content.append(self.lbl_time)

        self.lbl_seconds = Gtk.Label(label="")
        self.lbl_seconds.add_css_class("clock-seconds-hero")
        content.append(self.lbl_seconds)

        # ── Day + Date ──
        spacer = Gtk.Box()
        spacer.set_size_request(-1, 20)
        content.append(spacer)

        self.lbl_day = Gtk.Label(label="...")
        self.lbl_day.add_css_class("clock-day-hero")
        content.append(self.lbl_day)

        self.lbl_date = Gtk.Label(label="...")
        self.lbl_date.add_css_class("clock-date-hero")
        self.lbl_date.set_margin_top(4)
        content.append(self.lbl_date)

        self.lbl_tz = Gtk.Label(label="")
        self.lbl_tz.add_css_class("clock-tz-hero")
        self.lbl_tz.set_margin_top(12)
        content.append(self.lbl_tz)

        # ── World Clocks ──
        divider = Gtk.Box()
        divider.set_size_request(-1, 40)
        content.append(divider)

        header = Gtk.Label(label="WORLD CLOCKS")
        header.add_css_class("section-overline")
        header.set_margin_bottom(20)
        content.append(header)

        world_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        world_box.set_halign(Gtk.Align.CENTER)
        content.append(world_box)

        self.world_clocks = []
        cities = [("New York", "America/New_York"), ("London", "Europe/London"),
                  ("Tokyo", "Asia/Tokyo"), ("Dubai", "Asia/Dubai")]

        for city_name, tz_str in cities:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.add_css_class("md3-card-filled")

            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            inner.set_margin_start(20)
            inner.set_margin_end(20)
            inner.set_margin_top(16)
            inner.set_margin_bottom(16)
            inner.set_halign(Gtk.Align.CENTER)
            card.append(inner)

            nm = Gtk.Label(label=city_name.upper())
            nm.add_css_class("world-card-city")
            inner.append(nm)

            tm = Gtk.Label(label="--:--")
            tm.add_css_class("world-card-time")
            inner.append(tm)

            world_box.append(card)
            self.world_clocks.append((tm, tz_str))

    def update(self, now, settings):
        fmt = "%H:%M" if settings["format_24h"] else "%I:%M %p"
        display = now.strftime(fmt)
        if not settings["format_24h"]:
            display = display.lstrip("0")
        self.lbl_time.set_label(display)

        if settings.get("show_seconds", True):
            self.lbl_seconds.set_label(f":{now.strftime('%S')}")
            self.lbl_seconds.set_visible(True)
        else:
            self.lbl_seconds.set_visible(False)

        self.lbl_date.set_label(now.strftime("%d %B %Y"))
        self.lbl_day.set_label(now.strftime("%A"))
        tz = settings['timezone_str']
        self.lbl_tz.set_label(tz if tz != "Local" else "")
        self.lbl_tz.set_visible(tz != "Local")

        for lbl, tz_s in self.world_clocks:
            try:
                t = datetime.now(ZoneInfo(tz_s))
                f = "%H:%M" if settings["format_24h"] else "%I:%M %p"
                lbl.set_label(t.strftime(f).lstrip("0"))
            except Exception:
                lbl.set_label("--:--")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Focus Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PomoPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_valign(Gtk.Align.CENTER)
        content.set_halign(Gtk.Align.CENTER)
        content.set_margin_start(48)
        content.set_margin_end(48)
        content.set_margin_top(32)
        content.set_margin_bottom(32)
        scroll.set_child(content)

        # ── Header ──
        title = Gtk.Label(label="Focus")
        title.add_css_class("md3-headline-large")
        title.set_margin_bottom(4)
        content.append(title)

        subtitle = Gtk.Label(label="Stay productive with timed sessions")
        subtitle.add_css_class("md3-body-medium")
        subtitle.add_css_class("dim-label")
        subtitle.set_margin_bottom(36)
        content.append(subtitle)

        # ── Mode ──
        self.lbl_mode = Gtk.Label(label="WORK SESSION")
        self.lbl_mode.add_css_class("section-overline")
        self.lbl_mode.set_margin_bottom(16)
        content.append(self.lbl_mode)

        # ── Time ──
        self.lbl_time = Gtk.Label(label="25:00")
        self.lbl_time.add_css_class("timer-hero")
        content.append(self.lbl_time)

        # ── Progress ──
        self.progress = Gtk.ProgressBar()
        self.progress.add_css_class("md3-progress-linear")
        self.progress.set_margin_top(24)
        self.progress.set_margin_bottom(16)
        self.progress.set_size_request(380, -1)
        self.progress.set_halign(Gtk.Align.CENTER)
        content.append(self.progress)

        # ── Status ──
        self.lbl_status = Gtk.Label(label="Ready to focus")
        self.lbl_status.add_css_class("status-text")
        self.lbl_status.set_margin_bottom(32)
        content.append(self.lbl_status)

        # ── Mode Chips ──
        chip_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        chip_box.set_halign(Gtk.Align.CENTER)
        chip_box.set_margin_bottom(16)
        content.append(chip_box)

        s = app.settings
        self.btn_work = Gtk.Button(label=f"Work · {s['work_duration']}m")
        self.btn_work.add_css_class("md3-chip-selected")
        self.btn_work.connect("clicked", lambda b: app.set_pomo_mode("work"))
        chip_box.append(self.btn_work)

        self.btn_short = Gtk.Button(label=f"Short · {s['short_break']}m")
        self.btn_short.add_css_class("md3-chip")
        self.btn_short.connect("clicked", lambda b: app.set_pomo_mode("short"))
        chip_box.append(self.btn_short)

        self.btn_long = Gtk.Button(label=f"Long · {s['long_break']}m")
        self.btn_long.add_css_class("md3-chip")
        self.btn_long.connect("clicked", lambda b: app.set_pomo_mode("long"))
        chip_box.append(self.btn_long)

        # ── Custom ──
        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_box.set_halign(Gtk.Align.CENTER)
        custom_box.set_margin_bottom(36)
        content.append(custom_box)

        c_lbl = Gtk.Label(label="Custom")
        c_lbl.add_css_class("md3-body-medium")
        c_lbl.add_css_class("dim-label")
        custom_box.append(c_lbl)

        self.ent_custom = Gtk.Entry()
        self.ent_custom.set_text("25")
        self.ent_custom.set_max_width_chars(4)
        self.ent_custom.set_alignment(0.5)
        self.ent_custom.set_size_request(60, -1)
        custom_box.append(self.ent_custom)

        c_min = Gtk.Label(label="min")
        c_min.add_css_class("md3-body-medium")
        c_min.add_css_class("dim-label")
        custom_box.append(c_min)

        btn_set = Gtk.Button(label="Set")
        btn_set.add_css_class("md3-outlined-button")
        btn_set.connect("clicked", lambda b: app.apply_custom_pomo())
        custom_box.append(btn_set)

        # ── Actions ──
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        action_box.set_halign(Gtk.Align.CENTER)
        content.append(action_box)

        self.btn_action = Gtk.Button(label="Start")
        self.btn_action.add_css_class("suggested-action")
        self.btn_action.add_css_class("md3-filled-button")
        self.btn_action.set_size_request(180, 48)
        self.btn_action.connect("clicked", lambda b: app.toggle_pomo())
        action_box.append(self.btn_action)

        btn_reset = Gtk.Button(label="Reset")
        btn_reset.add_css_class("md3-filled-tonal-button")
        btn_reset.connect("clicked", lambda b: app.reset_pomo())
        action_box.append(btn_reset)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Timer Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TimerPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_valign(Gtk.Align.CENTER)
        content.set_halign(Gtk.Align.CENTER)
        content.set_margin_start(48)
        content.set_margin_end(48)
        content.set_margin_top(32)
        content.set_margin_bottom(32)
        scroll.set_child(content)

        title = Gtk.Label(label="Timer")
        title.add_css_class("md3-headline-large")
        title.set_margin_bottom(4)
        content.append(title)

        subtitle = Gtk.Label(label="Set a countdown for any duration")
        subtitle.add_css_class("md3-body-medium")
        subtitle.add_css_class("dim-label")
        subtitle.set_margin_bottom(40)
        content.append(subtitle)

        # ── Input ──
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        input_box.set_halign(Gtk.Align.CENTER)
        input_box.set_margin_bottom(20)
        content.append(input_box)

        self.ent_timer = Gtk.Entry()
        self.ent_timer.set_text("10")
        self.ent_timer.set_max_width_chars(5)
        self.ent_timer.set_alignment(0.5)
        self.ent_timer.add_css_class("timer-entry-large")
        self.ent_timer.set_size_request(120, -1)
        input_box.append(self.ent_timer)

        lbl_min = Gtk.Label(label="minutes")
        lbl_min.add_css_class("md3-body-large")
        lbl_min.add_css_class("dim-label")
        lbl_min.set_valign(Gtk.Align.CENTER)
        input_box.append(lbl_min)

        # ── Presets ──
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        preset_box.set_halign(Gtk.Align.CENTER)
        preset_box.set_margin_bottom(36)
        content.append(preset_box)

        for mins in [1, 3, 5, 10, 15, 30, 60]:
            label = f"{mins}m" if mins < 60 else "1h"
            btn = Gtk.Button(label=label)
            btn.add_css_class("md3-preset")
            btn.connect("clicked", lambda b, m=mins: self.ent_timer.set_text(str(m)))
            preset_box.append(btn)

        # ── Display ──
        self.lbl_time = Gtk.Label(label="00:00")
        self.lbl_time.add_css_class("timer-hero")
        content.append(self.lbl_time)

        # ── Progress ──
        self.progress = Gtk.ProgressBar()
        self.progress.add_css_class("md3-progress-linear")
        self.progress.set_margin_top(24)
        self.progress.set_margin_bottom(36)
        self.progress.set_size_request(380, -1)
        self.progress.set_halign(Gtk.Align.CENTER)
        content.append(self.progress)

        # ── Actions ──
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        action_box.set_halign(Gtk.Align.CENTER)
        content.append(action_box)

        self.btn_action = Gtk.Button(label="Start")
        self.btn_action.add_css_class("suggested-action")
        self.btn_action.add_css_class("md3-filled-button")
        self.btn_action.set_size_request(180, 48)
        self.btn_action.connect("clicked", lambda b: app.toggle_timer())
        action_box.append(self.btn_action)

        btn_reset = Gtk.Button(label="Reset")
        btn_reset.add_css_class("md3-filled-tonal-button")
        btn_reset.connect("clicked", lambda b: app.reset_timer())
        action_box.append(btn_reset)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Stopwatch Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StopwatchPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.set_margin_start(48)
        self.set_margin_end(48)
        self.set_margin_top(32)
        self.set_margin_bottom(16)

        # ── Header ──
        title = Gtk.Label(label="Stopwatch")
        title.add_css_class("md3-headline-large")
        title.set_margin_bottom(4)
        self.append(title)

        subtitle = Gtk.Label(label="Measure elapsed time with laps")
        subtitle.add_css_class("md3-body-medium")
        subtitle.add_css_class("dim-label")
        subtitle.set_margin_bottom(32)
        self.append(subtitle)

        # ── Time ──
        self.lbl_time = Gtk.Label(label="00:00.00")
        self.lbl_time.add_css_class("sw-hero")
        self.lbl_time.set_margin_bottom(32)
        self.append(self.lbl_time)

        # ── Actions ──
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_bottom(36)
        self.append(action_box)

        self.btn_toggle = Gtk.Button(label="Start")
        self.btn_toggle.add_css_class("suggested-action")
        self.btn_toggle.add_css_class("md3-filled-button")
        self.btn_toggle.set_size_request(160, 48)
        self.btn_toggle.connect("clicked", lambda b: app.toggle_sw())
        action_box.append(self.btn_toggle)

        self.btn_lap = Gtk.Button(label="Lap")
        self.btn_lap.add_css_class("md3-filled-tonal-button")
        self.btn_lap.set_sensitive(False)
        self.btn_lap.connect("clicked", lambda b: app.record_lap())
        action_box.append(self.btn_lap)

        btn_reset = Gtk.Button(label="Reset")
        btn_reset.add_css_class("md3-outlined-button")
        btn_reset.connect("clicked", lambda b: app.reset_sw())
        action_box.append(btn_reset)

        # ── Lap Header ──
        lap_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lap_hdr.set_margin_bottom(12)
        self.append(lap_hdr)

        l_title = Gtk.Label(label="LAPS")
        l_title.add_css_class("section-overline")
        lap_hdr.append(l_title)

        self.lbl_lap_count = Gtk.Label(label="")
        self.lbl_lap_count.add_css_class("md3-label-small")
        self.lbl_lap_count.add_css_class("dim-label")
        lap_hdr.append(self.lbl_lap_count)

        # ── Lap List ──
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_min_content_height(160)
        self.append(scroll)

        self.lap_list = Gtk.ListBox()
        self.lap_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.lap_list.add_css_class("boxed-list")
        scroll.set_child(self.lap_list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Settings Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SettingsPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main.set_margin_start(28)
        main.set_margin_end(28)
        main.set_margin_top(24)
        main.set_margin_bottom(32)
        scroll.set_child(main)

        title = Gtk.Label(label="Settings")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(28)
        main.append(title)

        # ── General ──
        gen = Adw.PreferencesGroup(title="General", description="App behavior and display")
        main.append(gen)

        self.sw_bg = Adw.SwitchRow(title="Background Mode",
                                   subtitle="Keep running when window is closed")
        self.sw_bg.set_active(app.settings["background"])
        self.sw_bg.connect("notify::active", lambda w, p: self._save())
        gen.add(self.sw_bg)

        self.sw_24h = Adw.SwitchRow(title="24-Hour Format",
                                    subtitle="Use 24-hour time display")
        self.sw_24h.set_active(app.settings["format_24h"])
        self.sw_24h.connect("notify::active", lambda w, p: self._save())
        gen.add(self.sw_24h)

        self.sw_sec = Adw.SwitchRow(title="Show Seconds")
        self.sw_sec.set_active(app.settings.get("show_seconds", True))
        self.sw_sec.connect("notify::active", lambda w, p: self._save())
        gen.add(self.sw_sec)

        self.sw_snd = Adw.SwitchRow(title="Sound Alerts",
                                    subtitle="Play sound on completion")
        self.sw_snd.set_active(app.settings["sound_enabled"])
        self.sw_snd.connect("notify::active", lambda w, p: self._save())
        gen.add(self.sw_snd)

        self.sw_auto = Adw.SwitchRow(title="Auto-start Breaks",
                                     subtitle="Begin break automatically after work session")
        self.sw_auto.set_active(app.settings.get("auto_start_breaks", False))
        self.sw_auto.connect("notify::active", lambda w, p: self._save())
        gen.add(self.sw_auto)

        # ── Focus Durations ──
        pomo = Adw.PreferencesGroup(title="Focus Durations",
                                    description="Configure session lengths")
        pomo.set_margin_top(24)
        main.append(pomo)

        self.spins = {}
        for label, key, default, sub in [
            ("Work", "work_duration", 25, "Minutes per work session"),
            ("Short Break", "short_break", 5, "Minutes for short break"),
            ("Long Break", "long_break", 15, "Minutes for long break")]:
            row = Adw.SpinRow.new_with_range(1, 180, 1)
            row.set_title(label)
            row.set_subtitle(sub)
            row.set_value(app.settings.get(key, default))
            row.connect("notify::value", lambda w, p, k=key: self._save_spin(k, w))
            pomo.add(row)
            self.spins[key] = row

        # ── Timezone ──
        tz = Adw.PreferencesGroup(title="Timezone")
        tz.set_margin_top(24)
        main.append(tz)

        self.tz_search = Gtk.SearchEntry()
        self.tz_search.set_placeholder_text("Search timezones...")
        self.tz_search.connect("search-changed", self._filter_tz)
        self.tz_search.set_margin_bottom(8)
        tz.add(self.tz_search)

        tz_scroll = Gtk.ScrolledWindow()
        tz_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        tz_scroll.set_min_content_height(160)
        tz_scroll.set_max_content_height(160)

        self.tz_list = Gtk.ListBox()
        self.tz_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.tz_list.add_css_class("boxed-list")
        self.tz_list.connect("row-selected", self._on_tz_sel)
        tz_scroll.set_child(self.tz_list)
        tz.add(tz_scroll)
        self._populate_tz()

        # ── Exit ──
        exit_g = Adw.PreferencesGroup()
        exit_g.set_margin_top(32)
        main.append(exit_g)

        btn_exit = Gtk.Button(label="Exit Application")
        btn_exit.add_css_class("destructive-action")
        btn_exit.add_css_class("md3-filled-button")
        btn_exit.connect("clicked", lambda b: app.quit_app())
        exit_g.add(btn_exit)

    def _save(self):
        s = self.app.settings
        s["background"] = self.sw_bg.get_active()
        s["format_24h"] = self.sw_24h.get_active()
        s["show_seconds"] = self.sw_sec.get_active()
        s["sound_enabled"] = self.sw_snd.get_active()
        s["auto_start_breaks"] = self.sw_auto.get_active()
        self.app.save_settings()

    def _save_spin(self, key, w):
        v = int(w.get_value())
        if v > 0:
            self.app.settings[key] = v
            self.app.save_settings()
            self.app.refresh_pomo_buttons()

    def _populate_tz(self, filt=""):
        while True:
            r = self.tz_list.get_row_at_index(0)
            if r is None:
                break
            self.tz_list.remove(r)

        search = filt.lower()
        current = self.app.settings["timezone_str"]
        sel_row = None
        count = 0
        for tz in ALL_TIMEZONES:
            if search and search not in tz.lower():
                continue
            if count > 80:
                break
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=tz)
            lbl.set_halign(Gtk.Align.START)
            lbl.set_margin_start(16)
            lbl.set_margin_end(16)
            lbl.set_margin_top(10)
            lbl.set_margin_bottom(10)
            lbl.add_css_class("md3-body-medium")
            row.set_child(lbl)
            row._tz = tz
            self.tz_list.append(row)
            if tz == current:
                sel_row = row
            count += 1
        if sel_row:
            self.tz_list.select_row(sel_row)

    def _filter_tz(self, entry):
        self._populate_tz(entry.get_text())

    def _on_tz_sel(self, lb, row):
        if row and hasattr(row, '_tz'):
            self.app.settings["timezone_str"] = row._tz
            self.app.save_settings()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main Application
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CarmonyClockApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.carmonyos.clock")
        self.connect("activate", self.on_activate)
        self.settings_data = self._load_settings()
        self.pomo_state = "stopped"
        self.pomo_time = self.settings_data["work_duration"] * 60
        self.pomo_mode = "work"
        self.pomo_total_time = self.pomo_time
        self.pomo_sessions_today = self.settings_data.get("pomodoro_count", 0)
        self.timer_state = "stopped"
        self.timer_curr = 0
        self.timer_target = 0
        self.sw_state = "stopped"
        self.sw_start = 0
        self.sw_elapsed = 0
        self.sw_offset = 0
        self.lap_count = 0
        self.lap_times = []
        self.last_tick = time.perf_counter()
        self.running = True
        self._check_daily_reset()
        self._load_session()

    @property
    def settings(self):
        return self.settings_data

    def on_activate(self, app):
        sm = Adw.StyleManager.get_default()
        sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("Clock — CarmonyOS")
        self.win.set_default_size(920, 760)
        self.win.add_css_class("main-window")

        css = Gtk.CssProvider()
        css.load_from_string(MD3_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # ── Main Layout ──
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.win.set_content(root)

        # ── Navigation Rail (MD3 style) ──
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        rail.add_css_class("rail-bg")
        rail.set_size_request(80, -1)
        root.append(rail)

        # Logo
        logo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        logo_box.set_margin_top(20)
        logo_box.set_margin_bottom(24)
        logo_box.set_halign(Gtk.Align.CENTER)
        rail.append(logo_box)

        logo_icon = Gtk.Label(label="◷")
        logo_icon.add_css_class("app-logo-icon")
        logo_box.append(logo_icon)

        # Nav items
        nav_items = [
            ("clock", "🕐", "Clock"),
            ("pomo", "🎯", "Focus"),
            ("timer", "⏱", "Timer"),
            ("sw", "⏲", "Watch"),
        ]

        self.nav_btns = {}
        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.nav_box.set_halign(Gtk.Align.CENTER)
        rail.append(self.nav_box)

        for tab_id, icon, label in nav_items:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            btn.add_css_class("md3-nav-rail-item")

            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            inner.set_halign(Gtk.Align.CENTER)

            ic = Gtk.Label(label=icon)
            ic.add_css_class("md3-nav-icon")
            inner.append(ic)

            lb = Gtk.Label(label=label)
            lb.add_css_class("md3-nav-label")
            inner.append(lb)

            btn.set_child(inner)
            btn.connect("clicked", lambda b, t=tab_id: self._nav_to(t))
            self.nav_box.append(btn)
            self.nav_btns[tab_id] = btn

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        rail.append(spacer)

        # Stats
        stat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        stat_box.set_halign(Gtk.Align.CENTER)
        stat_box.set_margin_bottom(8)
        rail.append(stat_box)

        self.lbl_stat_num = Gtk.Label(label="0")
        self.lbl_stat_num.add_css_class("stat-num")
        stat_box.append(self.lbl_stat_num)

        stat_u = Gtk.Label(label="sessions")
        stat_u.add_css_class("stat-unit")
        stat_box.append(stat_u)

        # Settings nav
        settings_btn = Gtk.Button()
        settings_btn.add_css_class("flat")
        settings_btn.add_css_class("md3-nav-rail-item")
        s_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        s_inner.set_halign(Gtk.Align.CENTER)
        s_ic = Gtk.Label(label="⚙")
        s_ic.add_css_class("md3-nav-icon")
        s_inner.append(s_ic)
        s_lb = Gtk.Label(label="Settings")
        s_lb.add_css_class("md3-nav-label")
        s_inner.append(s_lb)
        settings_btn.set_child(s_inner)
        settings_btn.connect("clicked", lambda b: self._nav_to("settings"))
        settings_btn.set_margin_bottom(16)
        rail.append(settings_btn)
        self.nav_btns["settings"] = settings_btn

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        root.append(sep)

        # ── Content Stack ──
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        root.append(self.stack)

        self.clock_page = ClockPage(self)
        self.stack.add_named(self.clock_page, "clock")

        self.pomo_page = PomoPage(self)
        self.stack.add_named(self.pomo_page, "pomo")

        self.timer_page = TimerPage(self)
        self.stack.add_named(self.timer_page, "timer")

        self.sw_page = StopwatchPage(self)
        self.stack.add_named(self.sw_page, "sw")

        self.settings_page = SettingsPage(self)
        self.stack.add_named(self.settings_page, "settings")

        self._nav_to("clock")

        # Keyboard
        kc = Gtk.EventControllerKey()
        kc.connect("key-pressed", self._on_key)
        self.win.add_controller(kc)
        self.win.connect("close-request", self._on_close)

        GLib.timeout_add(33, self._tick)
        GLib.timeout_add(200, self._check_signal)

        self.win.present()

    def _nav_to(self, tab_id):
        self.stack.set_visible_child_name(tab_id)
        for tid, btn in self.nav_btns.items():
            if tid == tab_id:
                btn.add_css_class("md3-nav-indicator")
            else:
                btn.remove_css_class("md3-nav-indicator")

    def _on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_space:
            v = self.stack.get_visible_child_name()
            if v == "pomo": self.toggle_pomo()
            elif v == "timer": self.toggle_timer()
            elif v == "sw": self.toggle_sw()
            return True
        if keyval == Gdk.KEY_q and state & Gdk.ModifierType.CONTROL_MASK:
            self.quit_app()
            return True
        if keyval == Gdk.KEY_Escape:
            self._on_close(None)
            return True
        return False

    def _on_close(self, w):
        if self.settings_data["background"]:
            self.win.set_visible(False)
            return True
        self.quit_app()
        return False

    # ── Settings I/O ──

    def _load_settings(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings_data, f, indent=2)
        except Exception:
            pass

    # ── Session ──

    def _load_session(self):
        if not PERSIST_FILE.exists():
            return
        try:
            with open(PERSIST_FILE, 'r') as f:
                s = json.load(f)
            if s.get('pomo_state') == 'running':
                rem = s.get('pomo_time', 0) - (time.time() - s.get('pomo_start', 0))
                if rem > 0:
                    self.pomo_time = rem
                    self.pomo_mode = s.get('pomo_mode', 'work')
                    self.pomo_total_time = s.get('pomo_total_time', self.pomo_time)
                    self.pomo_state = 'running'
            if s.get('timer_state') == 'running':
                rem = s.get('timer_curr', 0) - (time.time() - s.get('timer_start', 0))
                if rem > 0:
                    self.timer_curr = rem
                    self.timer_target = s.get('timer_target', rem)
                    self.timer_state = 'running'
            if s.get('sw_state') == 'running':
                self.sw_offset = s.get('sw_offset', 0) + (time.time() - s.get('sw_start', 0))
                self.sw_start = time.perf_counter()
                self.sw_state = 'running'
            elif s.get('sw_state') == 'paused':
                self.sw_offset = s.get('sw_offset', 0)
                self.sw_elapsed = self.sw_offset
                self.sw_state = 'paused'
        except Exception:
            pass

    def _save_session(self):
        try:
            s = {
                'pomo_state': self.pomo_state, 'pomo_time': self.pomo_time,
                'pomo_mode': self.pomo_mode, 'pomo_total_time': self.pomo_total_time,
                'pomo_start': time.time() if self.pomo_state == 'running' else 0,
                'timer_state': self.timer_state, 'timer_curr': self.timer_curr,
                'timer_target': self.timer_target,
                'timer_start': time.time() if self.timer_state == 'running' else 0,
                'sw_state': self.sw_state,
                'sw_offset': (self.sw_offset if self.sw_state == 'paused' else
                              (self.sw_offset + time.perf_counter() - self.sw_start
                               if self.sw_state == 'running' else 0)),
                'sw_start': time.time() if self.sw_state == 'running' else 0,
            }
            with open(PERSIST_FILE, 'w') as f:
                json.dump(s, f)
        except Exception:
            pass

    def _check_daily_reset(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.settings_data.get("last_reset_date", "") != today:
            self.settings_data["pomodoro_count"] = 0
            self.settings_data["daily_focus_minutes"] = 0
            self.settings_data["last_reset_date"] = today
            self.save_settings()

    # ── Time Helpers ──

    def get_time(self):
        tz = self.settings_data["timezone_str"]
        if tz == "Local":
            return datetime.now()
        try:
            return datetime.now(ZoneInfo(tz))
        except Exception:
            return datetime.now()

    def format_time(self, secs):
        secs = max(0, int(secs))
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def format_sw(self, elapsed):
        m = int(elapsed // 60)
        s = elapsed % 60
        return f"{m:02d}:{s:05.2f}"

    # ── Main Loop ──

    def _tick(self):
        if not self.running:
            return False
        now_ts = time.perf_counter()
        dt = now_ts - self.last_tick
        self.last_tick = now_ts
        now = self.get_time()

        self.clock_page.update(now, self.settings_data)

        if self.pomo_state == "running":
            self.pomo_time = max(0, self.pomo_time - dt)
            self.pomo_page.lbl_time.set_label(self.format_time(self.pomo_time))
            p = (self.pomo_total_time - self.pomo_time) / self.pomo_total_time
            self.pomo_page.progress.set_fraction(p)
            rm = int(self.pomo_time / 60)
            self.pomo_page.lbl_status.set_label(f"{rm + 1} min remaining")
            if self.pomo_time <= 0:
                self._pomo_done()

        if self.timer_state == "running":
            self.timer_curr = max(0, self.timer_curr - dt)
            self.timer_page.lbl_time.set_label(self.format_time(self.timer_curr))
            if self.timer_target > 0:
                self.timer_page.progress.set_fraction(
                    (self.timer_target - self.timer_curr) / self.timer_target)
            if self.timer_curr <= 0:
                self._timer_done()

        if self.sw_state == "running":
            self.sw_elapsed = time.perf_counter() - self.sw_start + self.sw_offset
            self.sw_page.lbl_time.set_label(self.format_sw(self.sw_elapsed))

        self.lbl_stat_num.set_label(str(self.pomo_sessions_today))

        self._write_status(now)
        return True

    def _write_status(self, now):
        try:
            fmt = "%H:%M" if self.settings_data["format_24h"] else "%I:%M %p"
            st = {"text": f" {now.strftime(fmt)}", "tooltip": now.strftime('%A, %d %B %Y'),
                  "class": "clock", "alt": "clock", "percentage": 0}

            if self.pomo_state == "running":
                p = int(((self.pomo_total_time - self.pomo_time) / self.pomo_total_time) * 100)
                ic = "🎯" if self.pomo_mode == "work" else "☕"
                st = {"text": f"{ic} {self.format_time(self.pomo_time)}", "tooltip": f"Focus: {self.pomo_mode} ({p}%)",
                      "class": f"pomodoro-{self.pomo_mode}", "alt": "pomodoro", "percentage": p}
            elif self.pomo_state == "paused":
                st = {"text": f"⏸ {self.format_time(self.pomo_time)}", "tooltip": "Focus Paused",
                      "class": "pomodoro-work", "alt": "pomodoro-paused", "percentage": 0}
            elif self.timer_state == "running":
                p = int(((self.timer_target - self.timer_curr) / self.timer_target) * 100) if self.timer_target > 0 else 0
                st = {"text": f"⏱ {self.format_time(self.timer_curr)}", "tooltip": f"Timer ({p}%)",
                      "class": "timer", "alt": "timer", "percentage": p}
            elif self.sw_state == "running":
                st = {"text": f"⏱ {self.format_sw(self.sw_elapsed)[:5]}", "tooltip": f"Stopwatch — {self.lap_count} laps",
                      "class": "stopwatch", "alt": "stopwatch", "percentage": 0}
            elif self.sw_state == "paused":
                st = {"text": f"⏸ {self.format_sw(self.sw_elapsed)[:5]}", "tooltip": "Stopwatch Paused",
                      "class": "stopwatch", "alt": "stopwatch-paused", "percentage": 0}

            with open(STATE_FILE, "w") as f:
                json.dump(st, f)
        except Exception:
            pass

    # ── Pomodoro ──

    def set_pomo_mode(self, mode):
        self.pomo_mode = mode
        self.pomo_state = "stopped"
        durations = {"work": self.settings_data["work_duration"],
                     "short": self.settings_data["short_break"],
                     "long": self.settings_data["long_break"]}
        labels = {"work": "WORK SESSION", "short": "SHORT BREAK", "long": "LONG BREAK"}
        mins = durations.get(mode, 25)
        self.pomo_time = mins * 60
        self.pomo_total_time = self.pomo_time

        self.pomo_page.lbl_mode.set_label(labels.get(mode, "WORK SESSION"))
        self.pomo_page.lbl_time.set_label(self.format_time(self.pomo_time))
        self.pomo_page.btn_action.set_label("Start")
        self.pomo_page.btn_action.remove_css_class("destructive-action")
        self.pomo_page.btn_action.add_css_class("suggested-action")
        self.pomo_page.progress.set_fraction(0)
        self.pomo_page.lbl_status.set_label("Ready")

        chips = [(self.pomo_page.btn_work, "work"),
                 (self.pomo_page.btn_short, "short"),
                 (self.pomo_page.btn_long, "long")]
        for btn, m in chips:
            if m == mode:
                btn.remove_css_class("md3-chip")
                btn.add_css_class("md3-chip-selected")
            else:
                btn.remove_css_class("md3-chip-selected")
                btn.add_css_class("md3-chip")

    def apply_custom_pomo(self):
        try:
            mins = int(self.pomo_page.ent_custom.get_text())
            if not 1 <= mins <= 180:
                raise ValueError
            self.pomo_mode = "work"
            self.pomo_time = mins * 60
            self.pomo_total_time = self.pomo_time
            self.pomo_state = "stopped"
            self.pomo_page.lbl_mode.set_label(f"CUSTOM · {mins} MIN")
            self.pomo_page.lbl_time.set_label(self.format_time(self.pomo_time))
            self.pomo_page.btn_action.set_label("Start")
            self.pomo_page.btn_action.remove_css_class("destructive-action")
            self.pomo_page.btn_action.add_css_class("suggested-action")
            self.pomo_page.progress.set_fraction(0)
            self.pomo_page.lbl_status.set_label("Custom session ready")
            for btn in [self.pomo_page.btn_work, self.pomo_page.btn_short, self.pomo_page.btn_long]:
                btn.remove_css_class("md3-chip-selected")
                btn.add_css_class("md3-chip")
        except ValueError:
            d = Adw.MessageDialog(transient_for=self.win, heading="Invalid Duration",
                                  body="Enter a value between 1 and 180 minutes.")
            d.add_response("ok", "OK")
            d.present()

    def toggle_pomo(self):
        if self.pomo_state in ("stopped", "paused"):
            self.pomo_state = "running"
            self.pomo_page.btn_action.set_label("Pause")
            self.pomo_page.btn_action.remove_css_class("suggested-action")
            self.pomo_page.btn_action.add_css_class("destructive-action")
            self.pomo_page.lbl_status.set_label("Focusing...")
        else:
            self.pomo_state = "paused"
            self.pomo_page.btn_action.set_label("Resume")
            self.pomo_page.btn_action.remove_css_class("destructive-action")
            self.pomo_page.btn_action.add_css_class("suggested-action")
            self.pomo_page.lbl_status.set_label("Paused")

    def reset_pomo(self):
        self.pomo_state = "stopped"
        m = self.pomo_mode if self.pomo_mode in ("work", "short", "long") else "work"
        self.set_pomo_mode(m)

    def _pomo_done(self):
        self.pomo_state = "stopped"
        self._play_sound()
        self.pomo_page.btn_action.set_label("Start")
        self.pomo_page.btn_action.remove_css_class("destructive-action")
        self.pomo_page.btn_action.add_css_class("suggested-action")

        if self.pomo_mode == "work":
            self.pomo_sessions_today += 1
            self.settings_data["pomodoro_count"] = self.pomo_sessions_today
            self.settings_data["daily_focus_minutes"] = self.settings_data.get("daily_focus_minutes", 0) + self.settings_data["work_duration"]
            self.save_settings()
            self._notify("🎯 Focus Complete!", f"Sessions today: {self.pomo_sessions_today}")
            if self.settings_data.get("auto_start_breaks", False):
                self.set_pomo_mode("long" if self.pomo_sessions_today % 4 == 0 else "short")
                self.toggle_pomo()
            else:
                self.set_pomo_mode("short")
        else:
            self._notify("☕ Break Over!", "Time to focus again")
            self.set_pomo_mode("work")
        self.pomo_page.lbl_status.set_label("Session complete!")

    def refresh_pomo_buttons(self):
        s = self.settings_data
        self.pomo_page.btn_work.set_label(f"Work · {s['work_duration']}m")
        self.pomo_page.btn_short.set_label(f"Short · {s['short_break']}m")
        self.pomo_page.btn_long.set_label(f"Long · {s['long_break']}m")

    # ── Timer ──

    def toggle_timer(self):
        if self.timer_state == "running":
            self.timer_state = "stopped"
            self.timer_page.btn_action.set_label("Start")
            self.timer_page.btn_action.remove_css_class("destructive-action")
            self.timer_page.btn_action.add_css_class("suggested-action")
        else:
            try:
                mins = float(self.timer_page.ent_timer.get_text())
                if mins <= 0:
                    raise ValueError
                self.timer_curr = mins * 60
                self.timer_target = self.timer_curr
                self.timer_state = "running"
                self.timer_page.btn_action.set_label("Stop")
                self.timer_page.btn_action.remove_css_class("suggested-action")
                self.timer_page.btn_action.add_css_class("destructive-action")
                self.timer_page.progress.set_fraction(0)
            except ValueError:
                d = Adw.MessageDialog(transient_for=self.win, heading="Invalid",
                                      body="Enter a valid number of minutes.")
                d.add_response("ok", "OK")
                d.present()

    def reset_timer(self):
        self.timer_state = "stopped"
        self.timer_curr = self.timer_target = 0
        self.timer_page.lbl_time.set_label("00:00")
        self.timer_page.btn_action.set_label("Start")
        self.timer_page.btn_action.remove_css_class("destructive-action")
        self.timer_page.btn_action.add_css_class("suggested-action")
        self.timer_page.progress.set_fraction(0)

    def _timer_done(self):
        self.timer_state = "stopped"
        self._play_sound()
        self.timer_page.btn_action.set_label("Start")
        self.timer_page.btn_action.remove_css_class("destructive-action")
        self.timer_page.btn_action.add_css_class("suggested-action")
        self.timer_page.progress.set_fraction(1.0)
        self._notify("⏱ Timer Complete!", "Time's up!")

    # ── Stopwatch ──

    def toggle_sw(self):
        if self.sw_state == "stopped":
            self.sw_start = time.perf_counter()
            self.sw_offset = self.sw_elapsed = 0
            self.sw_state = "running"
            self.sw_page.btn_toggle.set_label("Pause")
            self.sw_page.btn_toggle.remove_css_class("suggested-action")
            self.sw_page.btn_toggle.add_css_class("destructive-action")
            self.sw_page.btn_lap.set_sensitive(True)
        elif self.sw_state == "running":
            self.sw_offset += time.perf_counter() - self.sw_start
            self.sw_state = "paused"
            self.sw_page.btn_toggle.set_label("Resume")
            self.sw_page.btn_toggle.remove_css_class("destructive-action")
            self.sw_page.btn_toggle.add_css_class("suggested-action")
        else:
            self.sw_start = time.perf_counter()
            self.sw_state = "running"
            self.sw_page.btn_toggle.set_label("Pause")
            self.sw_page.btn_toggle.remove_css_class("suggested-action")
            self.sw_page.btn_toggle.add_css_class("destructive-action")

    def record_lap(self):
        if self.sw_elapsed <= 0:
            return
        self.lap_count += 1
        cur = self.sw_elapsed
        dur = cur - (self.lap_times[-1][1] if self.lap_times else 0)
        self.lap_times.append((dur, cur))

        css = ""
        if len(self.lap_times) >= 2:
            sl = sorted(lt[0] for lt in self.lap_times)
            if dur == sl[0]:
                css = "lap-best"
            elif dur == sl[-1]:
                css = "lap-worst"

        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.add_css_class("lap-row")
        if css:
            box.add_css_class(css)

        num = Gtk.Label(label=f"Lap {self.lap_count}")
        num.add_css_class("lap-num")
        num.set_size_request(80, -1)
        num.set_halign(Gtk.Align.START)
        box.append(num)

        sp = Gtk.Box()
        sp.set_hexpand(True)
        box.append(sp)

        d = Gtk.Label(label=self.format_sw(dur))
        d.add_css_class("lap-dur")
        box.append(d)

        t = Gtk.Label(label=self.format_sw(cur))
        t.add_css_class("lap-tot")
        t.set_margin_start(20)
        box.append(t)

        row.set_child(box)
        self.sw_page.lap_list.prepend(row)
        self.sw_page.lbl_lap_count.set_label(f"({self.lap_count})")

    def reset_sw(self):
        self.sw_state = "stopped"
        self.sw_elapsed = self.sw_offset = self.lap_count = 0
        self.lap_times = []
        self.sw_page.lbl_time.set_label("00:00.00")
        self.sw_page.btn_toggle.set_label("Start")
        self.sw_page.btn_toggle.remove_css_class("destructive-action")
        self.sw_page.btn_toggle.add_css_class("suggested-action")
        self.sw_page.btn_lap.set_sensitive(False)
        self.sw_page.lbl_lap_count.set_label("")
        self.sw_page.lap_list.remove_all()

    # ── Notifications / Sound ──

    def _notify(self, title, msg):
        try:
            subprocess.Popen(["notify-send", "-a", "CarmonyOS Clock", title, msg],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _play_sound(self):
        if not self.settings_data["sound_enabled"]:
            return
        def _p():
            for p in ["/usr/share/sounds/freedesktop/stereo/complete.oga",
                      "/usr/share/sounds/freedesktop/stereo/bell.oga"]:
                if os.path.exists(p):
                    try:
                        subprocess.Popen(["paplay", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        pass
                    return
        threading.Thread(target=_p, daemon=True).start()

    # ── Signal IPC ──

    def _check_signal(self):
        if not self.running:
            return False
        if SIGNAL_FILE.exists():
            try:
                content = SIGNAL_FILE.read_text().strip()
                SIGNAL_FILE.unlink()
                actions = {
                    "pomo-toggle": self.toggle_pomo, "pomo-work": lambda: self.set_pomo_mode("work"),
                    "pomo-short": lambda: self.set_pomo_mode("short"), "pomo-long": lambda: self.set_pomo_mode("long"),
                    "pomo-reset": self.reset_pomo, "timer-toggle": self.toggle_timer,
                    "timer-reset": self.reset_timer, "sw-toggle": self.toggle_sw,
                    "sw-lap": self.record_lap, "sw-reset": self.reset_sw,
                    "show": lambda: (self.win.set_visible(True), self.win.present()),
                }
                if content in actions:
                    actions[content]()
                else:
                    if self.win.get_visible():
                        self.win.set_visible(False)
                    else:
                        self.win.set_visible(True)
                        self.win.present()
            except Exception:
                pass
        return True

    # ── Quit ──

    def quit_app(self):
        self.running = False
        self._save_session()
        for f in [STATE_FILE, SIGNAL_FILE]:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
        self.quit()


if __name__ == "__main__":
    app = CarmonyClockApp()
    app.run(None)
