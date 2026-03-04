#!/usr/bin/env python3
"""
CarmonyOS Settings
Material Design 3 — System Configuration Application
Version 2.0 — Improved Animations & Fixes
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Vte', '3.91')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio, Pango, Vte

import os
import re
import json
import subprocess
import threading
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Configuration Paths
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOME = Path.home()
HYPR_DIR = HOME / ".config" / "hypr"
HYPRLAND_CONF = HYPR_DIR / "hyprland.conf"
HYPRLOCK_CONF = HYPR_DIR / "hyprlock.conf"
HYPR_SCRIPTS = HYPR_DIR / "scripts"
WAL_SCRIPT = HYPR_SCRIPTS / "wal.sh"
KITTY_CONF = HOME / ".config" / "kitty" / "kitty.conf"
WALLPAPER_DIR = HOME / "Pictures" / "Wallpapers"
SETTINGS_FILE = HOME / ".config" / "carmonyos-settings" / "settings.json"

SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Hyprland Config Parser
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HyprlandConfig:
    """Parse and modify Hyprland configuration files."""
    
    def __init__(self, path: Path):
        self.path = path
        self.content = ""
        self.load()
    
    def load(self):
        if self.path.exists():
            self.content = self.path.read_text()
        else:
            self.content = ""
    
    def save(self):
        backup = self.path.with_suffix('.conf.bak')
        if self.path.exists():
            shutil.copy(self.path, backup)
        self.path.write_text(self.content)
    
    def _find_section_content(self, section: str) -> Tuple[Optional[int], Optional[int], str]:
        """Find section content, handling nested sections like 'decoration:blur'."""
        parts = section.split(':')
        
        if len(parts) == 1:
            # Simple section like 'decoration'
            pattern = rf'{section}\s*\{{\s*'
            match = re.search(pattern, self.content)
            if not match:
                return None, None, ""
            
            start = match.end()
            depth = 1
            end = start
            
            while end < len(self.content) and depth > 0:
                if self.content[end] == '{':
                    depth += 1
                elif self.content[end] == '}':
                    depth -= 1
                end += 1
            
            return start, end - 1, self.content[start:end - 1]
        else:
            # Nested section like 'decoration:blur'
            parent = parts[0]
            child = parts[1]
            
            p_start, p_end, p_content = self._find_section_content(parent)
            if p_content is None:
                return None, None, ""
            
            # Find child within parent
            pattern = rf'{child}\s*\{{\s*'
            match = re.search(pattern, p_content)
            if not match:
                return None, None, ""
            
            c_start = match.end()
            depth = 1
            c_end = c_start
            
            while c_end < len(p_content) and depth > 0:
                if p_content[c_end] == '{':
                    depth += 1
                elif p_content[c_end] == '}':
                    depth -= 1
                c_end += 1
            
            # Adjust to absolute positions
            abs_start = p_start + c_start
            abs_end = p_start + c_end - 1
            
            return abs_start, abs_end, p_content[c_start:c_end - 1]
    
    def get_value(self, section: str, key: str, default: str = "") -> str:
        """Get a value from config."""
        if section:
            _, _, content = self._find_section_content(section)
            if content:
                pattern = rf'^\s*{re.escape(key)}\s*=\s*(.+?)\s*$'
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    return match.group(1).strip()
        else:
            pattern = rf'^\s*{re.escape(key)}\s*=\s*(.+?)\s*$'
            match = re.search(pattern, self.content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return default
    
    def set_value(self, section: str, key: str, value: str):
        """Set a value in config."""
        if section:
            start, end, content = self._find_section_content(section)
            
            if content is not None:
                pattern = rf'^(\s*){re.escape(key)}\s*=\s*.+?$'
                match = re.search(pattern, content, re.MULTILINE)
                
                if match:
                    indent = match.group(1)
                    new_content = re.sub(pattern, f'{indent}{key} = {value}', content, flags=re.MULTILINE)
                    self.content = self.content[:start] + new_content + self.content[end:]
                else:
                    new_content = content.rstrip() + f'\n    {key} = {value}\n'
                    self.content = self.content[:start] + new_content + self.content[end:]
            else:
                # Create section(s)
                parts = section.split(':')
                if len(parts) == 1:
                    self.content += f'\n{section} {{\n    {key} = {value}\n}}\n'
                else:
                    parent, child = parts[0], parts[1]
                    p_start, p_end, p_content = self._find_section_content(parent)
                    if p_content is not None:
                        new_p = p_content.rstrip() + f'\n    {child} {{\n        {key} = {value}\n    }}\n'
                        self.content = self.content[:p_start] + new_p + self.content[p_end:]
                    else:
                        self.content += f'\n{parent} {{\n    {child} {{\n        {key} = {value}\n    }}\n}}\n'
        else:
            pattern = rf'^(\s*){re.escape(key)}\s*=\s*.+?$'
            if re.search(pattern, self.content, re.MULTILINE):
                self.content = re.sub(pattern, rf'\g<1>{key} = {value}', self.content, flags=re.MULTILINE)
            else:
                self.content += f'\n{key} = {value}\n'
    
    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        val = self.get_value(section, key, str(default).lower())
        return val.lower() in ('true', 'yes', '1', 'on')
    
    def set_bool(self, section: str, key: str, value: bool):
        self.set_value(section, key, 'true' if value else 'false')
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        try:
            return int(self.get_value(section, key, str(default)))
        except ValueError:
            return default
    
    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        try:
            return float(self.get_value(section, key, str(default)))
        except ValueError:
            return default
    
    def get_exec_once_list(self) -> List[str]:
        pattern = r'^\s*exec-once\s*=\s*(.+?)\s*$'
        return re.findall(pattern, self.content, re.MULTILINE)
    
    def add_exec_once(self, command: str):
        self.content += f'\nexec-once = {command}\n'
    
    def remove_exec_once(self, command: str):
        pattern = rf'^\s*exec-once\s*=\s*{re.escape(command)}\s*$\n?'
        self.content = re.sub(pattern, '', self.content, flags=re.MULTILINE)
    
    def get_binds(self) -> List[Tuple[str, str, str, str]]:
        binds = []
        pattern = r'^\s*(bind[a-z]*)\s*=\s*([^,]*),\s*([^,]+),\s*(.+?)\s*$'
        for match in re.finditer(pattern, self.content, re.MULTILINE):
            binds.append((match.group(1), match.group(2).strip(), 
                         match.group(3).strip(), match.group(4).strip()))
        return binds
    
    def add_bind(self, bind_type: str, mods: str, key: str, action: str):
        self.content += f'\n{bind_type} = {mods}, {key}, {action}\n'
    
    def remove_bind(self, mods: str, key: str):
        pattern = rf'^\s*bind[a-z]*\s*=\s*{re.escape(mods)}\s*,\s*{re.escape(key)}\s*,.*$\n?'
        self.content = re.sub(pattern, '', self.content, flags=re.MULTILINE)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Hyprlock Config Parser
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HyprlockConfig:
    """Parse and modify Hyprlock configuration."""
    
    def __init__(self, path: Path):
        self.path = path
        self.content = ""
        self.load()
    
    def load(self):
        if self.path.exists():
            self.content = self.path.read_text()
        else:
            # Create default config
            self.content = """
background {
    path = screenshot
    blur_passes = 3
    blur_size = 8
    noise = 0.0117
    contrast = 0.8916
    brightness = 0.8172
    vibrancy = 0.1696
    vibrancy_darkness = 0.0
}

input-field {
    size = 250, 50
    outline_thickness = 3
    dots_size = 0.2
    dots_spacing = 0.64
    dots_center = true
    fade_on_empty = true
    placeholder_text = <i>Password...</i>
    hide_input = false
    position = 0, -20
    halign = center
    valign = center
}

label {
    text = $TIME
    font_size = 64
    font_family = Google Sans Display
    position = 0, 150
    halign = center
    valign = center
}

label {
    text = cmd[update:1000] echo "$(date '+%A, %B %d')"
    font_size = 18
    font_family = Google Sans
    position = 0, 80
    halign = center
    valign = center
}
"""
    
    def save(self):
        backup = self.path.with_suffix('.conf.bak')
        if self.path.exists():
            shutil.copy(self.path, backup)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.content)
    
    def _find_block(self, block_name: str, index: int = 0) -> Tuple[Optional[int], Optional[int], str]:
        """Find a block by name and optional index (for multiple labels)."""
        pattern = rf'{block_name}\s*\{{'
        matches = list(re.finditer(pattern, self.content))
        
        if index >= len(matches):
            return None, None, ""
        
        match = matches[index]
        start = match.end()
        depth = 1
        end = start
        
        while end < len(self.content) and depth > 0:
            if self.content[end] == '{':
                depth += 1
            elif self.content[end] == '}':
                depth -= 1
            end += 1
        
        return start, end - 1, self.content[start:end - 1]
    
    def get_value(self, block: str, key: str, default: str = "", index: int = 0) -> str:
        _, _, content = self._find_block(block, index)
        if content:
            pattern = rf'^\s*{re.escape(key)}\s*=\s*(.+?)\s*$'
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return default
    
    def set_value(self, block: str, key: str, value: str, index: int = 0):
        start, end, content = self._find_block(block, index)
        
        if content is not None:
            pattern = rf'^(\s*){re.escape(key)}\s*=\s*.+?$'
            match = re.search(pattern, content, re.MULTILINE)
            
            if match:
                indent = match.group(1)
                new_content = re.sub(pattern, f'{indent}{key} = {value}', content, flags=re.MULTILINE)
                self.content = self.content[:start] + new_content + self.content[end:]
            else:
                new_content = content.rstrip() + f'\n    {key} = {value}\n'
                self.content = self.content[:start] + new_content + self.content[end:]
        else:
            self.content += f'\n{block} {{\n    {key} = {value}\n}}\n'
    
    def get_int(self, block: str, key: str, default: int = 0, index: int = 0) -> int:
        try:
            return int(self.get_value(block, key, str(default), index))
        except ValueError:
            return default
    
    def get_float(self, block: str, key: str, default: float = 0.0, index: int = 0) -> float:
        try:
            return float(self.get_value(block, key, str(default), index))
        except ValueError:
            return default


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Kitty Config Parser
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class KittyConfig:
    def __init__(self, path: Path):
        self.path = path
        self.content = ""
        self.load()
    
    def load(self):
        if self.path.exists():
            self.content = self.path.read_text()
        else:
            self.content = ""
    
    def save(self):
        backup = self.path.with_suffix('.conf.bak')
        if self.path.exists():
            shutil.copy(self.path, backup)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.content)
    
    def get_shell(self) -> str:
        pattern = r'^\s*shell\s+(\S+)'
        match = re.search(pattern, self.content, re.MULTILINE)
        return match.group(1) if match else ""
    
    def set_shell(self, shell: str):
        pattern = r'^\s*shell\s+\S+.*$'
        if re.search(pattern, self.content, re.MULTILINE):
            self.content = re.sub(pattern, f'shell {shell}', self.content, flags=re.MULTILINE)
        else:
            self.content += f'\nshell {shell}\n'
    
    def remove_shell_setting(self):
        pattern = r'^\s*shell\s+.*$\n?'
        self.content = re.sub(pattern, '', self.content, flags=re.MULTILINE)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Material Design 3 CSS — Enhanced Animations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MD3_CSS = """
/* ─── MD3 Foundation ─── */

window.main-window {
    font-family: 'Google Sans', 'Google Sans Text', 'Roboto', 'Noto Sans', sans-serif;
}

/* ─── MD3 Typography ─── */

.md3-display-large {
    font-family: 'Google Sans Display', 'Product Sans', sans-serif;
    font-size: 57px;
    font-weight: 400;
    letter-spacing: -0.25px;
}

.md3-headline-large {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 32px;
    font-weight: 400;
}

.md3-headline-medium {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 28px;
    font-weight: 400;
}

.md3-headline-small {
    font-family: 'Google Sans Display', sans-serif;
    font-size: 24px;
    font-weight: 400;
}

.md3-title-large {
    font-family: 'Google Sans', sans-serif;
    font-size: 22px;
    font-weight: 400;
}

.md3-title-medium {
    font-family: 'Google Sans', sans-serif;
    font-size: 16px;
    font-weight: 500;
    letter-spacing: 0.15px;
}

.md3-title-small {
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
}

.md3-label-large {
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
}

.md3-label-medium {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.md3-label-small {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.md3-body-large {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 16px;
    font-weight: 400;
    letter-spacing: 0.5px;
}

.md3-body-medium {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 14px;
    font-weight: 400;
    letter-spacing: 0.25px;
}

.md3-body-small {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 12px;
    font-weight: 400;
    letter-spacing: 0.4px;
}

/* ─── MD3 Navigation Rail ─── */

.rail-bg {
    background: alpha(@headerbar_bg_color, 0.4);
}

.md3-nav-rail-item {
    border-radius: 16px;
    padding: 4px 0;
    min-height: 56px;
    min-width: 56px;
    margin: 2px 12px;
    transition: all 250ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-nav-rail-item:hover {
    background: alpha(@accent_bg_color, 0.12);
    transform: scale(1.05);
}

.md3-nav-indicator {
    background: alpha(@accent_bg_color, 0.22);
}

.md3-nav-icon {
    font-size: 22px;
    min-width: 24px;
    min-height: 24px;
    transition: transform 200ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-nav-rail-item:hover .md3-nav-icon {
    transform: scale(1.15);
}

.md3-nav-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

/* ─── MD3 Buttons — Enhanced Animations ─── */

.md3-filled-button {
    border-radius: 20px;
    padding: 10px 24px;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    min-height: 40px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1),
                transform 150ms cubic-bezier(0.2, 0, 0, 1),
                box-shadow 200ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-filled-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px alpha(@accent_bg_color, 0.4);
}

.md3-filled-button:active {
    transform: translateY(0px) scale(0.98);
    box-shadow: 0 2px 6px alpha(@accent_bg_color, 0.3);
}

.md3-filled-tonal-button {
    border-radius: 20px;
    padding: 10px 24px;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    background: alpha(@accent_bg_color, 0.15);
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1),
                transform 150ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-filled-tonal-button:hover {
    background: alpha(@accent_bg_color, 0.25);
    transform: translateY(-1px);
}

.md3-filled-tonal-button:active {
    transform: scale(0.98);
}

.md3-outlined-button {
    border-radius: 20px;
    padding: 10px 24px;
    border: 1px solid alpha(currentColor, 0.25);
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    min-height: 40px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1),
                transform 150ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-outlined-button:hover {
    background: alpha(currentColor, 0.08);
    border-color: alpha(currentColor, 0.4);
    transform: translateY(-1px);
}

.md3-outlined-button:active {
    transform: scale(0.98);
}

.md3-text-button {
    border-radius: 20px;
    padding: 10px 16px;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    min-height: 40px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-text-button:hover {
    background: alpha(currentColor, 0.08);
}

.md3-icon-button {
    border-radius: 20px;
    padding: 8px;
    min-height: 40px;
    min-width: 40px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1),
                transform 150ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-icon-button:hover {
    background: alpha(currentColor, 0.1);
    transform: scale(1.1);
}

.md3-icon-button:active {
    transform: scale(0.95);
}

.md3-fab {
    border-radius: 16px;
    padding: 16px;
    min-height: 56px;
    min-width: 56px;
    background: @accent_bg_color;
    color: @accent_fg_color;
    box-shadow: 0 3px 8px alpha(black, 0.2);
    transition: all 250ms cubic-bezier(0.2, 0, 0, 1),
                transform 200ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-fab:hover {
    box-shadow: 0 6px 16px alpha(black, 0.25);
    transform: translateY(-3px) scale(1.02);
}

.md3-fab:active {
    transform: translateY(-1px) scale(0.98);
}

.md3-fab-small {
    border-radius: 12px;
    padding: 8px;
    min-height: 40px;
    min-width: 40px;
    background: alpha(@accent_bg_color, 0.18);
    color: @accent_color;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1),
                transform 150ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-fab-small:hover {
    background: alpha(@accent_bg_color, 0.28);
    transform: scale(1.08);
}

/* ─── MD3 Cards — With Hover Effects ─── */

.md3-card-elevated {
    border-radius: 12px;
    background: mix(@window_bg_color, @card_bg_color, 0.5);
    box-shadow: 0 1px 3px alpha(black, 0.08), 0 1px 2px alpha(black, 0.06);
    transition: all 300ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-card-elevated:hover {
    box-shadow: 0 4px 12px alpha(black, 0.12), 0 2px 6px alpha(black, 0.08);
    transform: translateY(-2px);
}

.md3-card-filled {
    border-radius: 12px;
    background: alpha(@card_bg_color, 0.6);
    transition: all 250ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-card-filled:hover {
    background: alpha(@card_bg_color, 0.8);
}

.md3-card-outlined {
    border-radius: 12px;
    border: 1px solid alpha(currentColor, 0.12);
    transition: all 250ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-card-outlined:hover {
    border-color: alpha(currentColor, 0.25);
    background: alpha(currentColor, 0.03);
}

/* ─── MD3 Chips ─── */

.md3-chip {
    border-radius: 8px;
    padding: 6px 16px;
    border: 1px solid alpha(currentColor, 0.15);
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    min-height: 32px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-chip:hover {
    background: alpha(currentColor, 0.08);
    border-color: alpha(currentColor, 0.25);
    transform: translateY(-1px);
}

.md3-chip-selected {
    border-radius: 8px;
    padding: 6px 16px;
    background: alpha(@accent_bg_color, 0.2);
    border: 1px solid alpha(@accent_bg_color, 0.5);
    color: @accent_color;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    min-height: 32px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

/* ─── Section Headers ─── */

.section-overline {
    font-family: 'Google Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 1.5px;
    opacity: 0.4;
}

.section-description {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 13px;
    font-weight: 400;
    opacity: 0.55;
}

/* ─── App Logo ─── */

.app-logo-icon {
    font-size: 36px;
    transition: transform 300ms cubic-bezier(0.2, 0, 0, 1);
}

.app-logo-icon:hover {
    transform: rotate(45deg) scale(1.1);
}

.app-logo-name {
    font-family: 'Google Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    opacity: 0.6;
}

/* ─── List Items with Animations ─── */

.setting-row {
    padding: 12px 16px;
    min-height: 56px;
    border-radius: 12px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

.setting-row:hover {
    background: alpha(currentColor, 0.06);
}

.setting-title {
    font-family: 'Google Sans', sans-serif;
    font-size: 16px;
    font-weight: 400;
}

.setting-subtitle {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 13px;
    font-weight: 400;
    opacity: 0.55;
}

/* ─── Terminal Container — Larger & Better ─── */

.terminal-container {
    border-radius: 16px;
    background: #0a0a0a;
    padding: 8px;
    border: 1px solid alpha(@accent_bg_color, 0.15);
    box-shadow: inset 0 2px 8px alpha(black, 0.3);
}

.terminal-widget {
    background: transparent;
    padding: 8px;
}

/* ─── Bind Editor ─── */

.bind-row {
    border-radius: 12px;
    padding: 14px 18px;
    margin: 6px 0;
    background: alpha(@card_bg_color, 0.45);
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

.bind-row:hover {
    background: alpha(@card_bg_color, 0.65);
    transform: translateX(4px);
}

.bind-type {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 8px;
    background: alpha(@accent_bg_color, 0.18);
    color: @accent_color;
}

.bind-keys {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px;
    font-weight: 500;
}

.bind-action {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 13px;
    opacity: 0.6;
}

/* ─── Autostart Item ─── */

.autostart-row {
    border-radius: 12px;
    padding: 14px 18px;
    margin: 6px 0;
    background: alpha(@card_bg_color, 0.45);
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

.autostart-row:hover {
    background: alpha(@card_bg_color, 0.65);
    transform: translateX(4px);
}

.autostart-cmd {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px;
}

/* ─── Package Row — Enhanced Install Button ─── */

.package-row {
    border-radius: 16px;
    padding: 18px 20px;
    margin: 8px 0;
    background: alpha(@card_bg_color, 0.5);
    transition: all 250ms cubic-bezier(0.2, 0, 0, 1);
}

.package-row:hover {
    background: alpha(@card_bg_color, 0.7);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px alpha(black, 0.1);
}

.package-name {
    font-family: 'Google Sans', sans-serif;
    font-size: 15px;
    font-weight: 500;
}

.package-version {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    opacity: 0.5;
}

.package-desc {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 13px;
    opacity: 0.65;
}

.package-repo {
    font-family: 'Google Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 8px;
    background: alpha(@accent_bg_color, 0.15);
    color: @accent_color;
}

/* Install button special styling */
.install-button {
    border-radius: 20px;
    padding: 8px 20px;
    font-family: 'Google Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    background: @accent_bg_color;
    color: @accent_fg_color;
    min-height: 36px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1),
                transform 150ms cubic-bezier(0.2, 0, 0, 1),
                box-shadow 200ms cubic-bezier(0.2, 0, 0, 1);
}

.install-button:hover {
    transform: scale(1.05) translateY(-2px);
    box-shadow: 0 6px 16px alpha(@accent_bg_color, 0.45);
}

.install-button:active {
    transform: scale(0.97);
    box-shadow: 0 2px 8px alpha(@accent_bg_color, 0.3);
}

.installing {
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* ─── Wallpaper Grid ─── */

.wallpaper-thumb {
    border-radius: 12px;
    transition: all 250ms cubic-bezier(0.2, 0, 0, 1);
    box-shadow: 0 2px 8px alpha(black, 0.15);
}

.wallpaper-thumb:hover {
    transform: scale(1.08);
    box-shadow: 0 8px 24px alpha(black, 0.3);
}

.wallpaper-selected {
    border: 3px solid @accent_bg_color;
    box-shadow: 0 0 0 3px alpha(@accent_bg_color, 0.3);
}

/* ─── Status Badge ─── */

.status-success {
    color: #4ade80;
}

.status-error {
    color: #f87171;
}

.status-warning {
    color: #fbbf24;
}

.status-installing {
    color: @accent_color;
    animation: blink 1s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ─── Search Entry ─── */

.md3-search {
    border-radius: 28px;
    padding: 12px 24px;
    font-family: 'Google Sans Text', sans-serif;
    font-size: 16px;
    min-height: 56px;
    background: alpha(@card_bg_color, 0.6);
    border: 2px solid transparent;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

.md3-search:focus {
    background: alpha(@card_bg_color, 0.8);
    border-color: @accent_bg_color;
    box-shadow: 0 0 0 4px alpha(@accent_bg_color, 0.15);
}

/* ─── Progress ─── */

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

/* ─── Font Preview ─── */

.font-preview {
    font-size: 48px;
    padding: 24px;
    border-radius: 16px;
    background: alpha(@card_bg_color, 0.5);
    border: 1px solid alpha(currentColor, 0.08);
    transition: all 300ms cubic-bezier(0.2, 0, 0, 1);
}

.font-preview:hover {
    background: alpha(@card_bg_color, 0.7);
}

/* ─── Scrolled Windows ─── */

scrollbar {
    background: transparent;
}

scrollbar slider {
    background: alpha(currentColor, 0.15);
    border-radius: 10px;
    min-width: 8px;
    min-height: 8px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

scrollbar slider:hover {
    background: alpha(currentColor, 0.25);
}

scrollbar slider:active {
    background: alpha(currentColor, 0.35);
}

/* ─── Ripple Effect for Buttons ─── */

button {
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

/* ─── Preferences Group Styling ─── */

preferencesgroup > box > label.title {
    font-family: 'Google Sans', sans-serif;
    font-weight: 500;
}

/* ─── Switch Row Animation ─── */

row.activatable {
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

row.activatable:hover {
    background: alpha(currentColor, 0.04);
}

/* ─── Spin Row ─── */

spinbutton {
    border-radius: 8px;
}

/* ─── Entry Row ─── */

entry {
    border-radius: 8px;
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

entry:focus {
    box-shadow: 0 0 0 3px alpha(@accent_bg_color, 0.2);
}

/* ─── Combo Row ─── */

dropdown button {
    border-radius: 8px;
}

/* ─── List Boxes ─── */

list.boxed-list {
    border-radius: 12px;
}

list.boxed-list > row {
    transition: all 200ms cubic-bezier(0.2, 0, 0, 1);
}

list.boxed-list > row:hover {
    background: alpha(currentColor, 0.04);
}
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Hyprland Page — Fixed Shadow
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HyprlandPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.config = None
        self._loading = True
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        scroll.set_child(content)
        
        # Header
        title = Gtk.Label(label="Hyprland")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(4)
        content.append(title)
        
        subtitle = Gtk.Label(label="Window manager configuration")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(28)
        content.append(subtitle)
        
        # ── Decoration Group ──
        deco_group = Adw.PreferencesGroup(title="Decoration",
                                          description="Visual effects and appearance")
        content.append(deco_group)
        
        # Blur enabled
        self.sw_blur = Adw.SwitchRow(title="Enable Blur",
                                      subtitle="Blur behind transparent windows")
        self.sw_blur.connect("notify::active", self._on_setting_changed)
        deco_group.add(self.sw_blur)
        
        # Blur size
        self.spin_blur_size = Adw.SpinRow.new_with_range(1, 20, 1)
        self.spin_blur_size.set_title("Blur Size")
        self.spin_blur_size.set_subtitle("Blur radius strength")
        self.spin_blur_size.connect("notify::value", self._on_setting_changed)
        deco_group.add(self.spin_blur_size)
        
        # Blur passes
        self.spin_blur_passes = Adw.SpinRow.new_with_range(1, 10, 1)
        self.spin_blur_passes.set_title("Blur Passes")
        self.spin_blur_passes.set_subtitle("Number of blur iterations")
        self.spin_blur_passes.connect("notify::value", self._on_setting_changed)
        deco_group.add(self.spin_blur_passes)
        
        # Active opacity
        self.spin_active_opacity = Adw.SpinRow.new_with_range(0.1, 1.0, 0.05)
        self.spin_active_opacity.set_title("Active Window Opacity")
        self.spin_active_opacity.set_subtitle("Transparency of focused windows")
        self.spin_active_opacity.set_digits(2)
        self.spin_active_opacity.connect("notify::value", self._on_setting_changed)
        deco_group.add(self.spin_active_opacity)
        
        # Inactive opacity
        self.spin_inactive_opacity = Adw.SpinRow.new_with_range(0.1, 1.0, 0.05)
        self.spin_inactive_opacity.set_title("Inactive Window Opacity")
        self.spin_inactive_opacity.set_subtitle("Transparency of unfocused windows")
        self.spin_inactive_opacity.set_digits(2)
        self.spin_inactive_opacity.connect("notify::value", self._on_setting_changed)
        deco_group.add(self.spin_inactive_opacity)
        
        # Rounding
        self.spin_rounding = Adw.SpinRow.new_with_range(0, 30, 1)
        self.spin_rounding.set_title("Corner Rounding")
        self.spin_rounding.set_subtitle("Window corner radius in pixels")
        self.spin_rounding.connect("notify::value", self._on_setting_changed)
        deco_group.add(self.spin_rounding)
        
        # ── Animations Group ──
        anim_group = Adw.PreferencesGroup(title="Animations",
                                          description="Window and workspace animations")
        anim_group.set_margin_top(24)
        content.append(anim_group)
        
        self.sw_animations = Adw.SwitchRow(title="Enable Animations",
                                            subtitle="Animated transitions and effects")
        self.sw_animations.connect("notify::active", self._on_setting_changed)
        anim_group.add(self.sw_animations)
        
        # ── Misc Group ──
        misc_group = Adw.PreferencesGroup(title="Miscellaneous",
                                          description="Performance and behavior tweaks")
        misc_group.set_margin_top(24)
        content.append(misc_group)
        
        self.sw_vfr = Adw.SwitchRow(title="Variable Frame Rate (VFR)",
                                     subtitle="Reduce GPU usage when idle")
        self.sw_vfr.connect("notify::active", self._on_setting_changed)
        misc_group.add(self.sw_vfr)
        
        self.sw_mouse_drag = Adw.SwitchRow(title="Animate Mouse Dragging",
                                            subtitle="Smooth window movement while dragging")
        self.sw_mouse_drag.connect("notify::active", self._on_setting_changed)
        misc_group.add(self.sw_mouse_drag)
        
        self.sw_manual_resize = Adw.SwitchRow(title="Animate Manual Resizes",
                                               subtitle="Smooth resizing animations")
        self.sw_manual_resize.connect("notify::active", self._on_setting_changed)
        misc_group.add(self.sw_manual_resize)
        
        # ── Actions ──
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_margin_top(32)
        action_box.set_halign(Gtk.Align.END)
        content.append(action_box)
        
        btn_reload = Gtk.Button(label="Reload Config")
        btn_reload.add_css_class("md3-filled-tonal-button")
        btn_reload.connect("clicked", self._reload_hyprland)
        action_box.append(btn_reload)
        
        self.load_config()
    
    def load_config(self):
        self._loading = True
        self.config = HyprlandConfig(HYPRLAND_CONF)
        
        # Blur settings (decoration:blur section)
        self.sw_blur.set_active(self.config.get_bool("decoration:blur", "enabled", True))
        self.spin_blur_size.set_value(self.config.get_int("decoration:blur", "size", 8))
        self.spin_blur_passes.set_value(self.config.get_int("decoration:blur", "passes", 2))
        
        # Opacity
        self.spin_active_opacity.set_value(self.config.get_float("decoration", "active_opacity", 1.0))
        self.spin_inactive_opacity.set_value(self.config.get_float("decoration", "inactive_opacity", 1.0))
        
        # Rounding
        self.spin_rounding.set_value(self.config.get_int("decoration", "rounding", 10))
        
        # Animations
        self.sw_animations.set_active(self.config.get_bool("animations", "enabled", True))
        
        # Misc
        self.sw_vfr.set_active(self.config.get_bool("misc", "vfr", True))
        self.sw_mouse_drag.set_active(self.config.get_bool("misc", "animate_mouse_windowdragging", True))
        self.sw_manual_resize.set_active(self.config.get_bool("misc", "animate_manual_resizes", False))
        
        self._loading = False
    
    def _on_setting_changed(self, widget, param):
        if self._loading or not self.config:
            return
        
        # Apply all current values
        self.config.set_bool("decoration:blur", "enabled", self.sw_blur.get_active())
        self.config.set_value("decoration:blur", "size", str(int(self.spin_blur_size.get_value())))
        self.config.set_value("decoration:blur", "passes", str(int(self.spin_blur_passes.get_value())))
        
        self.config.set_value("decoration", "active_opacity", f"{self.spin_active_opacity.get_value():.2f}")
        self.config.set_value("decoration", "inactive_opacity", f"{self.spin_inactive_opacity.get_value():.2f}")
        self.config.set_value("decoration", "rounding", str(int(self.spin_rounding.get_value())))
        
        self.config.set_bool("animations", "enabled", self.sw_animations.get_active())
        
        self.config.set_bool("misc", "vfr", self.sw_vfr.get_active())
        self.config.set_bool("misc", "animate_mouse_windowdragging", self.sw_mouse_drag.get_active())
        self.config.set_bool("misc", "animate_manual_resizes", self.sw_manual_resize.get_active())
        
        self.config.save()
    
    def _reload_hyprland(self, btn):
        subprocess.Popen(["hyprctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.app.toast("Hyprland configuration reloaded")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Autostart Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AutostartPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.config = None
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        scroll.set_child(content)
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.set_margin_bottom(24)
        content.append(header)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_box.set_hexpand(True)
        header.append(title_box)
        
        title = Gtk.Label(label="Autostart")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title_box.append(title)
        
        subtitle = Gtk.Label(label="Applications started with Hyprland")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        title_box.append(subtitle)
        
        btn_add = Gtk.Button()
        btn_add.add_css_class("md3-fab-small")
        btn_add.set_valign(Gtk.Align.CENTER)
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.set_tooltip_text("Add application")
        btn_add.connect("clicked", self._show_add_dialog)
        header.append(btn_add)
        
        self.apps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.append(self.apps_box)
        
        self.load_apps()
    
    def load_apps(self):
        while child := self.apps_box.get_first_child():
            self.apps_box.remove(child)
        
        self.config = HyprlandConfig(HYPRLAND_CONF)
        apps = self.config.get_exec_once_list()
        
        if not apps:
            empty = Gtk.Label(label="No autostart applications configured")
            empty.add_css_class("dim-label")
            empty.add_css_class("md3-body-large")
            empty.set_margin_top(40)
            self.apps_box.append(empty)
            return
        
        for cmd in apps:
            row = self._create_app_row(cmd)
            self.apps_box.append(row)
    
    def _create_app_row(self, cmd: str) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("autostart-row")
        
        icon = Gtk.Label(label="🚀")
        icon.set_size_request(32, -1)
        row.append(icon)
        
        cmd_lbl = Gtk.Label(label=cmd)
        cmd_lbl.add_css_class("autostart-cmd")
        cmd_lbl.set_hexpand(True)
        cmd_lbl.set_halign(Gtk.Align.START)
        cmd_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        row.append(cmd_lbl)
        
        btn_remove = Gtk.Button()
        btn_remove.add_css_class("flat")
        btn_remove.add_css_class("md3-icon-button")
        btn_remove.set_icon_name("user-trash-symbolic")
        btn_remove.set_tooltip_text("Remove")
        btn_remove.connect("clicked", lambda b, c=cmd: self._remove_app(c))
        row.append(btn_remove)
        
        return row
    
    def _show_add_dialog(self, btn):
        dialog = Adw.MessageDialog(transient_for=self.app.win)
        dialog.set_heading("Add Autostart Application")
        dialog.set_body("Enter the command to run at startup:")
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("e.g., waybar &")
        entry.set_margin_top(12)
        entry.add_css_class("md3-body-large")
        dialog.set_extra_child(entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("add", "Add")
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(d, response):
            if response == "add":
                cmd = entry.get_text().strip()
                if cmd:
                    self.config.add_exec_once(cmd)
                    self.config.save()
                    self.load_apps()
                    self.app.toast(f"Added: {cmd}")
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _remove_app(self, cmd: str):
        self.config.remove_exec_once(cmd)
        self.config.save()
        self.load_apps()
        self.app.toast(f"Removed: {cmd[:30]}...")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Hyprlock Page — Fixed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HyprlockPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.config = None
        self._loading = True
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        scroll.set_child(content)
        
        # Header
        title = Gtk.Label(label="Hyprlock")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(4)
        content.append(title)
        
        subtitle = Gtk.Label(label="Lock screen configuration")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(28)
        content.append(subtitle)
        
        # ── Background Group ──
        bg_group = Adw.PreferencesGroup(title="Background",
                                        description="Lock screen background effects")
        content.append(bg_group)
        
        self.spin_blur_passes = Adw.SpinRow.new_with_range(0, 10, 1)
        self.spin_blur_passes.set_title("Blur Passes")
        self.spin_blur_passes.set_subtitle("Number of blur iterations (0 = disabled)")
        self.spin_blur_passes.connect("notify::value", self._on_setting_changed)
        bg_group.add(self.spin_blur_passes)
        
        self.spin_blur_size = Adw.SpinRow.new_with_range(1, 30, 1)
        self.spin_blur_size.set_title("Blur Size")
        self.spin_blur_size.set_subtitle("Blur radius strength")
        self.spin_blur_size.connect("notify::value", self._on_setting_changed)
        bg_group.add(self.spin_blur_size)
        
        self.spin_noise = Adw.SpinRow.new_with_range(0.0, 0.1, 0.005)
        self.spin_noise.set_title("Noise")
        self.spin_noise.set_subtitle("Film grain effect intensity")
        self.spin_noise.set_digits(4)
        self.spin_noise.connect("notify::value", self._on_setting_changed)
        bg_group.add(self.spin_noise)
        
        self.spin_brightness = Adw.SpinRow.new_with_range(0.0, 1.0, 0.05)
        self.spin_brightness.set_title("Brightness")
        self.spin_brightness.set_digits(2)
        self.spin_brightness.connect("notify::value", self._on_setting_changed)
        bg_group.add(self.spin_brightness)
        
        self.spin_contrast = Adw.SpinRow.new_with_range(0.0, 2.0, 0.05)
        self.spin_contrast.set_title("Contrast")
        self.spin_contrast.set_digits(2)
        self.spin_contrast.connect("notify::value", self._on_setting_changed)
        bg_group.add(self.spin_contrast)
        
        # ── Label/Typography Group ──
        label_group = Adw.PreferencesGroup(title="Time Display",
                                           description="Clock appearance on lock screen")
        label_group.set_margin_top(24)
        content.append(label_group)
        
        self.font_entry = Adw.EntryRow(title="Font Family")
        self.font_entry.set_text("Google Sans Display")
        self.font_entry.connect("changed", self._on_font_changed)
        label_group.add(self.font_entry)
        
        self.spin_font_size = Adw.SpinRow.new_with_range(12, 200, 4)
        self.spin_font_size.set_title("Font Size")
        self.spin_font_size.set_subtitle("Size of the time display")
        self.spin_font_size.set_value(64)
        self.spin_font_size.connect("notify::value", self._on_setting_changed)
        label_group.add(self.spin_font_size)
        
        # Font preview
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_box.set_margin_top(16)
        preview_box.set_margin_bottom(8)
        content.append(preview_box)
        
        preview_label = Gtk.Label(label="PREVIEW")
        preview_label.add_css_class("section-overline")
        preview_label.set_halign(Gtk.Align.START)
        preview_box.append(preview_label)
        
        self.font_preview = Gtk.Label(label="12:00")
        self.font_preview.add_css_class("font-preview")
        self.font_preview.set_halign(Gtk.Align.CENTER)
        preview_box.append(self.font_preview)
        
        # ── Input Field Group ──
        input_group = Adw.PreferencesGroup(title="Password Input",
                                           description="Password field appearance")
        input_group.set_margin_top(24)
        content.append(input_group)
        
        self.spin_input_width = Adw.SpinRow.new_with_range(100, 500, 10)
        self.spin_input_width.set_title("Field Width")
        self.spin_input_width.set_value(250)
        self.spin_input_width.connect("notify::value", self._on_setting_changed)
        input_group.add(self.spin_input_width)
        
        self.spin_input_height = Adw.SpinRow.new_with_range(30, 100, 5)
        self.spin_input_height.set_title("Field Height")
        self.spin_input_height.set_value(50)
        self.spin_input_height.connect("notify::value", self._on_setting_changed)
        input_group.add(self.spin_input_height)
        
        self.spin_outline = Adw.SpinRow.new_with_range(0, 10, 1)
        self.spin_outline.set_title("Outline Thickness")
        self.spin_outline.set_value(3)
        self.spin_outline.connect("notify::value", self._on_setting_changed)
        input_group.add(self.spin_outline)
        
        # ── Actions ──
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_margin_top(32)
        action_box.set_halign(Gtk.Align.END)
        content.append(action_box)
        
        btn_test = Gtk.Button(label="Test Lock Screen")
        btn_test.add_css_class("md3-filled-tonal-button")
        btn_test.connect("clicked", self._test_lock)
        action_box.append(btn_test)
        
        self.load_config()
    
    def load_config(self):
        self._loading = True
        self.config = HyprlockConfig(HYPRLOCK_CONF)
        
        # Background
        self.spin_blur_passes.set_value(self.config.get_int("background", "blur_passes", 3))
        self.spin_blur_size.set_value(self.config.get_int("background", "blur_size", 8))
        self.spin_noise.set_value(self.config.get_float("background", "noise", 0.0117))
        self.spin_brightness.set_value(self.config.get_float("background", "brightness", 0.8172))
        self.spin_contrast.set_value(self.config.get_float("background", "contrast", 0.8916))
        
        # Label (first one - time display)
        self.font_entry.set_text(self.config.get_value("label", "font_family", "Google Sans Display", 0))
        self.spin_font_size.set_value(self.config.get_int("label", "font_size", 64, 0))
        
        # Input field
        size_str = self.config.get_value("input-field", "size", "250, 50")
        try:
            parts = size_str.split(',')
            self.spin_input_width.set_value(int(parts[0].strip()))
            self.spin_input_height.set_value(int(parts[1].strip()))
        except Exception:
            pass
        
        self.spin_outline.set_value(self.config.get_int("input-field", "outline_thickness", 3))
        
        self._update_font_preview()
        self._loading = False
    
    def _update_font_preview(self):
        font = self.font_entry.get_text()
        size = min(int(self.spin_font_size.get_value()), 72)
        
        provider = Gtk.CssProvider()
        provider.load_from_string(f"""
            .font-preview {{
                font-family: '{font}', sans-serif;
                font-size: {size}px;
            }}
        """)
        
        ctx = self.font_preview.get_style_context()
        ctx.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def _on_setting_changed(self, widget, param):
        if self._loading or not self.config:
            return
        self._save_config()
    
    def _on_font_changed(self, widget):
        if self._loading or not self.config:
            return
        self._update_font_preview()
        self._save_config()
    
    def _save_config(self):
        # Background
        self.config.set_value("background", "blur_passes", str(int(self.spin_blur_passes.get_value())))
        self.config.set_value("background", "blur_size", str(int(self.spin_blur_size.get_value())))
        self.config.set_value("background", "noise", f"{self.spin_noise.get_value():.4f}")
        self.config.set_value("background", "brightness", f"{self.spin_brightness.get_value():.4f}")
        self.config.set_value("background", "contrast", f"{self.spin_contrast.get_value():.4f}")
        
        # Label
        self.config.set_value("label", "font_family", self.font_entry.get_text(), 0)
        self.config.set_value("label", "font_size", str(int(self.spin_font_size.get_value())), 0)
        
        # Input field
        w = int(self.spin_input_width.get_value())
        h = int(self.spin_input_height.get_value())
        self.config.set_value("input-field", "size", f"{w}, {h}")
        self.config.set_value("input-field", "outline_thickness", str(int(self.spin_outline.get_value())))
        
        self.config.save()
    
    def _test_lock(self, btn):
        subprocess.Popen(["hyprlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Keybinds Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class KeybindsPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.config = None
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        scroll.set_child(content)
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.set_margin_bottom(24)
        content.append(header)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_box.set_hexpand(True)
        header.append(title_box)
        
        title = Gtk.Label(label="Keybinds")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title_box.append(title)
        
        subtitle = Gtk.Label(label="Keyboard shortcuts configuration")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        title_box.append(subtitle)
        
        btn_add = Gtk.Button()
        btn_add.add_css_class("md3-fab-small")
        btn_add.set_valign(Gtk.Align.CENTER)
        btn_add.set_icon_name("list-add-symbolic")
        btn_add.set_tooltip_text("Add keybind")
        btn_add.connect("clicked", self._show_add_dialog)
        header.append(btn_add)
        
        # Search
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Search keybinds...")
        self.search.add_css_class("md3-search")
        self.search.set_margin_bottom(16)
        self.search.connect("search-changed", self._filter_binds)
        content.append(self.search)
        
        # Binds list
        binds_scroll = Gtk.ScrolledWindow()
        binds_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        binds_scroll.set_vexpand(True)
        binds_scroll.set_min_content_height(400)
        content.append(binds_scroll)
        
        self.binds_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        binds_scroll.set_child(self.binds_box)
        
        self.all_binds = []
        self.load_binds()
    
    def load_binds(self):
        while child := self.binds_box.get_first_child():
            self.binds_box.remove(child)
        
        self.config = HyprlandConfig(HYPRLAND_CONF)
        self.all_binds = self.config.get_binds()
        self._display_binds(self.all_binds)
    
    def _display_binds(self, binds):
        while child := self.binds_box.get_first_child():
            self.binds_box.remove(child)
        
        if not binds:
            empty = Gtk.Label(label="No keybinds found")
            empty.add_css_class("dim-label")
            empty.add_css_class("md3-body-large")
            empty.set_margin_top(40)
            self.binds_box.append(empty)
            return
        
        for bind_type, mods, key, action in binds:
            row = self._create_bind_row(bind_type, mods, key, action)
            self.binds_box.append(row)
    
    def _create_bind_row(self, bind_type: str, mods: str, key: str, action: str) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("bind-row")
        
        type_lbl = Gtk.Label(label=bind_type)
        type_lbl.add_css_class("bind-type")
        type_lbl.set_size_request(70, -1)
        row.append(type_lbl)
        
        keys_str = f"{mods} + {key}" if mods else key
        keys_lbl = Gtk.Label(label=keys_str)
        keys_lbl.add_css_class("bind-keys")
        keys_lbl.set_size_request(180, -1)
        keys_lbl.set_halign(Gtk.Align.START)
        row.append(keys_lbl)
        
        action_lbl = Gtk.Label(label=action)
        action_lbl.add_css_class("bind-action")
        action_lbl.set_hexpand(True)
        action_lbl.set_halign(Gtk.Align.START)
        action_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        row.append(action_lbl)
        
        btn_remove = Gtk.Button()
        btn_remove.add_css_class("flat")
        btn_remove.add_css_class("md3-icon-button")
        btn_remove.set_icon_name("user-trash-symbolic")
        btn_remove.set_tooltip_text("Remove")
        btn_remove.connect("clicked", lambda b: self._remove_bind(mods, key))
        row.append(btn_remove)
        
        return row
    
    def _filter_binds(self, entry):
        search = entry.get_text().lower()
        if not search:
            self._display_binds(self.all_binds)
        else:
            filtered = [(t, m, k, a) for t, m, k, a in self.all_binds
                       if search in m.lower() or search in k.lower() or search in a.lower()]
            self._display_binds(filtered)
    
    def _show_add_dialog(self, btn):
        dialog = Adw.MessageDialog(transient_for=self.app.win)
        dialog.set_heading("Add Keybind")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        
        # Type
        type_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        type_lbl = Gtk.Label(label="Type:")
        type_lbl.set_size_request(80, -1)
        type_lbl.set_halign(Gtk.Align.START)
        type_row.append(type_lbl)
        
        type_combo = Gtk.DropDown()
        type_model = Gtk.StringList()
        for t in ["bind", "bindl", "bindel", "binde", "bindr", "bindm"]:
            type_model.append(t)
        type_combo.set_model(type_model)
        type_combo.set_hexpand(True)
        type_row.append(type_combo)
        box.append(type_row)
        
        mods_entry = Adw.EntryRow(title="Modifiers")
        mods_entry.set_text("SUPER")
        box.append(mods_entry)
        
        key_entry = Adw.EntryRow(title="Key")
        key_entry.set_text("Return")
        box.append(key_entry)
        
        action_entry = Adw.EntryRow(title="Action")
        action_entry.set_text("exec, kitty")
        box.append(action_entry)
        
        dialog.set_extra_child(box)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("add", "Add")
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(d, response):
            if response == "add":
                bind_type = type_model.get_string(type_combo.get_selected())
                mods = mods_entry.get_text().strip()
                key = key_entry.get_text().strip()
                action = action_entry.get_text().strip()
                
                if key and action:
                    self.config.add_bind(bind_type, mods, key, action)
                    self.config.save()
                    self.load_binds()
                    self.app.toast(f"Added: {mods} + {key}")
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _remove_bind(self, mods: str, key: str):
        self.config.remove_bind(mods, key)
        self.config.save()
        self.load_binds()
        self.app.toast(f"Removed: {mods} + {key}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Wallpaper Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WallpaperPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        scroll.set_child(content)
        
        # Header
        title = Gtk.Label(label="Wallpaper")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(4)
        content.append(title)
        
        subtitle = Gtk.Label(label="Background and wallpaper settings")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(28)
        content.append(subtitle)
        
        # Actions
        actions_group = Adw.PreferencesGroup(title="Quick Actions")
        content.append(actions_group)
        
        set_row = Adw.ActionRow(title="Set Wallpaper",
                                subtitle="Run wallpaper selection script")
        set_row.set_activatable(True)
        set_btn = Gtk.Button(label="Select")
        set_btn.add_css_class("md3-filled-tonal-button")
        set_btn.set_valign(Gtk.Align.CENTER)
        set_btn.connect("clicked", self._set_wallpaper)
        set_row.add_suffix(set_btn)
        actions_group.add(set_row)
        
        edit_row = Adw.ActionRow(title="Edit Wallpaper Script",
                                 subtitle=str(WAL_SCRIPT))
        edit_row.set_activatable(True)
        edit_btn = Gtk.Button(label="Edit")
        edit_btn.add_css_class("md3-outlined-button")
        edit_btn.set_valign(Gtk.Align.CENTER)
        edit_btn.connect("clicked", self._edit_script)
        edit_row.add_suffix(edit_btn)
        actions_group.add(edit_row)
        
        # Move wallpapers
        move_group = Adw.PreferencesGroup(title="Move Wallpapers",
                                          description="Quickly organize image files")
        move_group.set_margin_top(24)
        content.append(move_group)
        
        self.src_entry = Adw.EntryRow(title="From")
        self.src_entry.set_text(str(HOME / "Downloads"))
        move_group.add(self.src_entry)
        
        src_browse = Gtk.Button(icon_name="folder-open-symbolic")
        src_browse.add_css_class("flat")
        src_browse.connect("clicked", lambda b: self._browse_folder(self.src_entry))
        self.src_entry.add_suffix(src_browse)
        
        self.dst_entry = Adw.EntryRow(title="To")
        self.dst_entry.set_text(str(WALLPAPER_DIR))
        move_group.add(self.dst_entry)
        
        dst_browse = Gtk.Button(icon_name="folder-open-symbolic")
        dst_browse.add_css_class("flat")
        dst_browse.connect("clicked", lambda b: self._browse_folder(self.dst_entry))
        self.dst_entry.add_suffix(dst_browse)
        
        move_btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        move_btn_row.set_margin_top(16)
        move_btn_row.set_halign(Gtk.Align.END)
        content.append(move_btn_row)
        
        move_btn = Gtk.Button(label="Move Image Files")
        move_btn.add_css_class("suggested-action")
        move_btn.add_css_class("md3-filled-button")
        move_btn.connect("clicked", self._move_wallpapers)
        move_btn_row.append(move_btn)
        
        # Gallery
        gallery_label = Gtk.Label(label="WALLPAPER GALLERY")
        gallery_label.add_css_class("section-overline")
        gallery_label.set_halign(Gtk.Align.START)
        gallery_label.set_margin_top(32)
        gallery_label.set_margin_bottom(12)
        content.append(gallery_label)
        
        self.gallery_flow = Gtk.FlowBox()
        self.gallery_flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.gallery_flow.set_max_children_per_line(5)
        self.gallery_flow.set_min_children_per_line(2)
        self.gallery_flow.set_column_spacing(12)
        self.gallery_flow.set_row_spacing(12)
        self.gallery_flow.set_homogeneous(True)
        content.append(self.gallery_flow)
        
        self._load_gallery()
    
    def _set_wallpaper(self, btn):
        if WAL_SCRIPT.exists():
            subprocess.Popen(["bash", str(WAL_SCRIPT)], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.app.toast("Wallpaper script executed")
        else:
            self.app.toast("Wallpaper script not found", error=True)
    
    def _edit_script(self, btn):
        editor = os.environ.get("EDITOR", "vim")
        subprocess.Popen(["kitty", "-e", editor, str(WAL_SCRIPT)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _browse_folder(self, entry):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Folder")
        
        def on_folder(d, result):
            try:
                folder = d.select_folder_finish(result)
                if folder:
                    entry.set_text(folder.get_path())
            except Exception:
                pass
        
        dialog.select_folder(self.app.win, None, on_folder)
    
    def _move_wallpapers(self, btn):
        src = Path(self.src_entry.get_text())
        dst = Path(self.dst_entry.get_text())
        
        if not src.exists():
            self.app.toast("Source folder not found", error=True)
            return
        
        dst.mkdir(parents=True, exist_ok=True)
        
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
        moved = 0
        
        for f in src.iterdir():
            if f.suffix.lower() in extensions:
                try:
                    shutil.move(str(f), str(dst / f.name))
                    moved += 1
                except Exception:
                    pass
        
        self.app.toast(f"Moved {moved} image(s)")
        self._load_gallery()
    
    def _load_gallery(self):
        while child := self.gallery_flow.get_first_child():
            self.gallery_flow.remove(child)
        
        if not WALLPAPER_DIR.exists():
            return
        
        extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        images = sorted([f for f in WALLPAPER_DIR.iterdir()
                        if f.suffix.lower() in extensions])[:20]
        
        for img_path in images:
            try:
                texture = Gdk.Texture.new_from_filename(str(img_path))
                picture = Gtk.Picture.new_for_paintable(texture)
                picture.set_content_fit(Gtk.ContentFit.COVER)
                picture.set_size_request(140, 90)
                picture.add_css_class("wallpaper-thumb")
                
                frame = Gtk.Frame()
                frame.set_child(picture)
                self.gallery_flow.append(frame)
            except Exception:
                pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Shell Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ShellPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.kitty_config = None
        self._loading = True
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.append(scroll)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(32)
        scroll.set_child(content)
        
        title = Gtk.Label(label="Shell")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(4)
        content.append(title)
        
        subtitle = Gtk.Label(label="Terminal shell configuration")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(28)
        content.append(subtitle)
        
        # Kitty settings
        kitty_group = Adw.PreferencesGroup(title="Kitty Terminal",
                                           description="Configure default shell")
        content.append(kitty_group)
        
        self.shell_row = Adw.ComboRow(title="Default Shell",
                                       subtitle="Shell used when opening Kitty")
        shell_model = Gtk.StringList()
        self.shells = ["System Default", "bash", "zsh", "fish"]
        for s in self.shells:
            shell_model.append(s)
        self.shell_row.set_model(shell_model)
        self.shell_row.connect("notify::selected", self._on_shell_changed)
        kitty_group.add(self.shell_row)
        
        self.sw_zsh = Adw.SwitchRow(title="Enable ZSH (Recommended)",
                                     subtitle="Use ZSH with Oh-My-ZSH if available")
        self.sw_zsh.connect("notify::active", self._on_zsh_toggle)
        kitty_group.add(self.sw_zsh)
        
        # Info
        info_group = Adw.PreferencesGroup(title="Information")
        info_group.set_margin_top(24)
        content.append(info_group)
        
        current_shell = os.environ.get("SHELL", "unknown")
        current_row = Adw.ActionRow(title="Current Login Shell", subtitle=current_shell)
        current_row.add_prefix(Gtk.Label(label="🐚"))
        info_group.add(current_row)
        
        try:
            with open("/etc/shells") as f:
                available = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        except Exception:
            available = ["/bin/bash"]
        
        avail_str = ", ".join([Path(s).name for s in available])
        avail_row = Adw.ActionRow(title="Available Shells", subtitle=avail_str)
        info_group.add(avail_row)
        
        # ZSH Plugins
        zsh_group = Adw.PreferencesGroup(title="ZSH Plugins",
                                         description="Common plugins status")
        zsh_group.set_margin_top(24)
        content.append(zsh_group)
        
        plugins = [
            ("zsh-autosuggestions", "Fish-like autosuggestions"),
            ("zsh-syntax-highlighting", "Syntax highlighting"),
            ("zsh-completions", "Additional completions"),
        ]
        
        for plugin, desc in plugins:
            plugin_path = HOME / ".oh-my-zsh" / "custom" / "plugins" / plugin
            installed = plugin_path.exists()
            
            row = Adw.ActionRow(title=plugin, subtitle=desc)
            status = Gtk.Label(label="✓" if installed else "✗")
            status.add_css_class("status-success" if installed else "dim-label")
            status.add_css_class("md3-label-large")
            row.add_suffix(status)
            zsh_group.add(row)
        
        self.load_config()
    
    def load_config(self):
        self._loading = True
        self.kitty_config = KittyConfig(KITTY_CONF)
        
        current = self.kitty_config.get_shell()
        if not current:
            self.shell_row.set_selected(0)
        elif "bash" in current:
            self.shell_row.set_selected(1)
        elif "zsh" in current:
            self.shell_row.set_selected(2)
            self.sw_zsh.set_active(True)
        elif "fish" in current:
            self.shell_row.set_selected(3)
        
        self._loading = False
    
    def _on_shell_changed(self, row, param):
        if self._loading or not self.kitty_config:
            return
        
        idx = row.get_selected()
        if idx == 0:
            self.kitty_config.remove_shell_setting()
        elif idx == 1:
            self.kitty_config.set_shell("/bin/bash")
        elif idx == 2:
            self.kitty_config.set_shell("/bin/zsh")
        elif idx == 3:
            self.kitty_config.set_shell("/usr/bin/fish")
        
        self.kitty_config.save()
        self.app.toast("Shell configuration updated")
    
    def _on_zsh_toggle(self, row, param):
        if self._loading:
            return
        if row.get_active():
            self.shell_row.set_selected(2)
        else:
            self.shell_row.set_selected(0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Downloads Page — Enhanced Terminal & Animations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DownloadsPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.search_results = []
        self.installing = False
        self.current_install_btn = None
        
        # Main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        self.append(content)
        
        # Header
        title = Gtk.Label(label="Downloads")
        title.add_css_class("md3-headline-large")
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(4)
        content.append(title)
        
        subtitle = Gtk.Label(label="Search and install packages from repositories")
        subtitle.add_css_class("section-description")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(24)
        content.append(subtitle)
        
        # Enable toggle
        enable_group = Adw.PreferencesGroup()
        content.append(enable_group)
        
        self.sw_enable = Adw.SwitchRow(title="Enable Downloads",
                                        subtitle="Allow package installation from this app")
        self.sw_enable.set_active(True)
        self.sw_enable.connect("notify::active", self._on_enable_changed)
        enable_group.add(self.sw_enable)
        
        # Search
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        search_box.set_margin_top(20)
        search_box.set_margin_bottom(16)
        content.append(search_box)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search for packages...")
        self.search_entry.add_css_class("md3-search")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self._do_search)
        search_box.append(self.search_entry)
        
        self.btn_search = Gtk.Button(label="Search")
        self.btn_search.add_css_class("suggested-action")
        self.btn_search.add_css_class("md3-filled-button")
        self.btn_search.connect("clicked", self._do_search)
        search_box.append(self.btn_search)
        
        # Progress & Status
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_box.set_margin_bottom(12)
        content.append(status_box)
        
        self.progress = Gtk.ProgressBar()
        self.progress.add_css_class("md3-progress-linear")
        self.progress.set_hexpand(True)
        self.progress.set_visible(False)
        status_box.append(self.progress)
        
        self.status_label = Gtk.Label(label="")
        self.status_label.add_css_class("md3-body-medium")
        self.status_label.set_halign(Gtk.Align.START)
        content.append(self.status_label)
        
        # Results (scrollable, limited height)
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        results_scroll.set_min_content_height(200)
        results_scroll.set_max_content_height(280)
        content.append(results_scroll)
        
        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        results_scroll.set_child(self.results_box)
        
        # Terminal section - LARGER
        term_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        term_header.set_margin_top(20)
        term_header.set_margin_bottom(8)
        content.append(term_header)
        
        term_label = Gtk.Label(label="INSTALLATION OUTPUT")
        term_label.add_css_class("section-overline")
        term_header.append(term_label)
        
        self.term_status = Gtk.Label(label="")
        self.term_status.add_css_class("md3-label-medium")
        self.term_status.add_css_class("status-installing")
        self.term_status.set_visible(False)
        term_header.append(self.term_status)
        
        # Terminal container - MUCH LARGER
        term_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        term_container.add_css_class("terminal-container")
        term_container.set_vexpand(True)
        term_container.set_size_request(-1, 300)
        content.append(term_container)
        
        try:
            self.terminal = Vte.Terminal()
            self.terminal.add_css_class("terminal-widget")
            self.terminal.set_vexpand(True)
            self.terminal.set_hexpand(True)
            self.terminal.set_scroll_on_output(True)
            self.terminal.set_scrollback_lines(5000)
            self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
            
            # Set colors
            self.terminal.set_color_background(Gdk.RGBA(red=0.04, green=0.04, blue=0.04, alpha=1.0))
            self.terminal.set_color_foreground(Gdk.RGBA(red=0.9, green=0.9, blue=0.9, alpha=1.0))
            
            # Font
            font_desc = Pango.FontDescription.from_string("JetBrains Mono 11")
            self.terminal.set_font(font_desc)
            
            term_scroll = Gtk.ScrolledWindow()
            term_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            term_scroll.set_child(self.terminal)
            term_scroll.set_vexpand(True)
            term_container.append(term_scroll)
            
            # Spawn initial shell
            self._spawn_shell()
            
        except Exception as e:
            self.terminal = None
            lbl = Gtk.Label(label=f"Terminal not available: {e}")
            lbl.add_css_class("dim-label")
            lbl.set_vexpand(True)
            term_container.append(lbl)
    
    def _spawn_shell(self):
        """Spawn a shell in the terminal."""
        if self.terminal:
            self.terminal.spawn_async(
                Vte.PtyFlags.DEFAULT,
                str(HOME),
                ["/bin/bash"],
                None,
                GLib.SpawnFlags.DEFAULT,
                None,
                None,
                -1,
                None,
                None,
                None
            )
    
    def _on_enable_changed(self, row, param):
        enabled = row.get_active()
        self.search_entry.set_sensitive(enabled)
        self.btn_search.set_sensitive(enabled)
    
    def _do_search(self, widget):
        if not self.sw_enable.get_active():
            return
        
        query = self.search_entry.get_text().strip()
        if not query:
            return
        
        self.status_label.set_label("🔍 Searching...")
        self.status_label.remove_css_class("status-success")
        self.status_label.remove_css_class("status-error")
        self.progress.set_visible(True)
        
        # Pulse animation
        self._pulse_id = GLib.timeout_add(100, self._pulse_progress)
        
        while child := self.results_box.get_first_child():
            self.results_box.remove(child)
        
        def search_thread():
            results = []
            
            # Pacman
            try:
                out = subprocess.check_output(["pacman", "-Ss", query],
                                             stderr=subprocess.DEVNULL, text=True)
                results.extend(self._parse_output(out, "pacman"))
            except Exception:
                pass
            
            # AUR (yay)
            try:
                out = subprocess.check_output(["yay", "-Ss", "--aur", query],
                                             stderr=subprocess.DEVNULL, text=True)
                results.extend(self._parse_output(out, "AUR"))
            except Exception:
                pass
            
            GLib.idle_add(self._show_results, results)
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def _pulse_progress(self):
        if self.progress.get_visible():
            self.progress.pulse()
            return True
        return False
    
    def _parse_output(self, output: str, repo: str) -> List[Dict]:
        results = []
        lines = output.strip().split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if '/' in line and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 2:
                    name_full = parts[0]
                    version = parts[1] if len(parts) > 1 else ""
                    name = name_full.split('/')[-1] if '/' in name_full else name_full
                    
                    desc = ""
                    if i + 1 < len(lines):
                        desc = lines[i + 1].strip()
                        i += 1
                    
                    results.append({
                        "name": name,
                        "version": version,
                        "description": desc,
                        "repo": repo
                    })
            i += 1
        
        return results[:30]
    
    def _show_results(self, results: List[Dict]):
        if hasattr(self, '_pulse_id'):
            GLib.source_remove(self._pulse_id)
        self.progress.set_visible(False)
        self.search_results = results
        
        if not results:
            self.status_label.set_label("❌ No packages found")
            self.status_label.add_css_class("status-error")
            return
        
        self.status_label.set_label(f"✓ Found {len(results)} package(s)")
        self.status_label.add_css_class("status-success")
        
        for pkg in results:
            row = self._create_package_row(pkg)
            self.results_box.append(row)
    
    def _create_package_row(self, pkg: Dict) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        row.add_css_class("package-row")
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        row.append(info_box)
        
        name_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        info_box.append(name_row)
        
        name_lbl = Gtk.Label(label=pkg["name"])
        name_lbl.add_css_class("package-name")
        name_lbl.set_halign(Gtk.Align.START)
        name_row.append(name_lbl)
        
        ver_lbl = Gtk.Label(label=pkg["version"])
        ver_lbl.add_css_class("package-version")
        name_row.append(ver_lbl)
        
        repo_lbl = Gtk.Label(label=pkg["repo"])
        repo_lbl.add_css_class("package-repo")
        name_row.append(repo_lbl)
        
        desc_lbl = Gtk.Label(label=pkg["description"])
        desc_lbl.add_css_class("package-desc")
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        desc_lbl.set_max_width_chars(50)
        info_box.append(desc_lbl)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_valign(Gtk.Align.CENTER)
        row.append(btn_box)
        
        btn_install = Gtk.Button(label="Install")
        btn_install.add_css_class("install-button")
        btn_install.connect("clicked", lambda b, p=pkg: self._install_package(p, b))
        btn_box.append(btn_install)
        
        btn_ignore = Gtk.Button(label="Ignore")
        btn_ignore.add_css_class("md3-text-button")
        btn_ignore.connect("clicked", lambda b: row.set_visible(False))
        btn_box.append(btn_ignore)
        
        return row
    
    def _install_package(self, pkg: Dict, btn: Gtk.Button):
        if self.installing:
            self.app.toast("Installation already in progress", error=True)
            return
        
        self.installing = True
        self.current_install_btn = btn
        name = pkg["name"]
        repo = pkg["repo"]
        
        # Update button state
        btn.set_label("Installing...")
        btn.add_css_class("installing")
        btn.set_sensitive(False)
        
        # Show terminal status
        self.term_status.set_label(f"Installing {name}...")
        self.term_status.set_visible(True)
        
        if self.terminal:
            # Build command
            if repo == "AUR":
                cmd = f"yay -S {name} --noconfirm && echo '\\n✓ Installation complete!' || echo '\\n✗ Installation failed!'\n"
            else:
                cmd = f"sudo pacman -S {name} --noconfirm && echo '\\n✓ Installation complete!' || echo '\\n✗ Installation failed!'\n"
            
            # Feed command to terminal
            self.terminal.feed_child(cmd.encode())
            
            # Monitor for completion (simple timer-based check)
            GLib.timeout_add(1000, self._check_install_complete, name, btn)
        else:
            # Fallback
            def install_thread():
                try:
                    if repo == "AUR":
                        subprocess.run(["yay", "-S", name, "--noconfirm"], check=True)
                    else:
                        subprocess.run(["sudo", "pacman", "-S", name, "--noconfirm"], check=True)
                    GLib.idle_add(self._on_install_success, name, btn)
                except Exception as e:
                    GLib.idle_add(self._on_install_error, name, btn, str(e))
            
            threading.Thread(target=install_thread, daemon=True).start()
    
    def _check_install_complete(self, name: str, btn: Gtk.Button) -> bool:
        """Simple completion check - timeout after 60 seconds."""
        if not self.installing:
            return False
        
        # After some time, assume it's done and reset
        if not hasattr(self, '_install_timer'):
            self._install_timer = 0
        
        self._install_timer += 1
        
        # Auto-complete after 60 seconds or check terminal output
        if self._install_timer > 60:
            self._install_timer = 0
            self._on_install_success(name, btn)
            return False
        
        return True
    
    def _on_install_success(self, name: str, btn: Gtk.Button):
        self.installing = False
        self._install_timer = 0
        
        btn.set_label("✓ Installed")
        btn.remove_css_class("installing")
        btn.add_css_class("suggested-action")
        
        self.term_status.set_label("✓ Complete")
        self.term_status.remove_css_class("status-installing")
        self.term_status.add_css_class("status-success")
        
        # Notification
        subprocess.Popen([
            "notify-send", "-a", "CarmonyOS Settings",
            "Package Installed", f"{name} has been installed successfully",
            "-i", "package-x-generic"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.app.toast(f"✓ {name} installed successfully")
        
        # Hide status after delay
        GLib.timeout_add(3000, lambda: self.term_status.set_visible(False) or False)
    
    def _on_install_error(self, name: str, btn: Gtk.Button, error: str):
        self.installing = False
        self._install_timer = 0
        
        btn.set_label("✗ Failed")
        btn.remove_css_class("installing")
        btn.add_css_class("destructive-action")
        btn.set_sensitive(True)
        
        self.term_status.set_label("✗ Failed")
        self.term_status.remove_css_class("status-installing")
        self.term_status.add_css_class("status-error")
        
        self.app.toast(f"Failed to install {name}", error=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  About Page
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AboutPage(Gtk.Box):
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
        content.set_margin_top(48)
        content.set_margin_bottom(48)
        scroll.set_child(content)
        
        logo = Gtk.Label(label="⚙")
        logo.add_css_class("app-logo-icon")
        logo.set_margin_bottom(12)
        content.append(logo)
        
        name = Gtk.Label(label="CarmonyOS Settings")
        name.add_css_class("md3-headline-large")
        name.set_margin_bottom(4)
        content.append(name)
        
        version = Gtk.Label(label="Version 2.0.0")
        version.add_css_class("md3-body-medium")
        version.add_css_class("dim-label")
        version.set_margin_bottom(32)
        content.append(version)
        
        desc = Gtk.Label(label="System configuration and customization\nfor CarmonyOS with Material Design 3")
        desc.add_css_class("md3-body-large")
        desc.set_wrap(True)
        desc.set_max_width_chars(50)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_margin_bottom(40)
        content.append(desc)
        
        info_group = Adw.PreferencesGroup(title="System Information")
        content.append(info_group)
        
        try:
            hypr_ver = subprocess.check_output(["hyprctl", "version", "-j"],
                                               stderr=subprocess.DEVNULL, text=True)
            hypr_data = json.loads(hypr_ver)
            hypr_version = hypr_data.get("tag", "unknown")
        except Exception:
            hypr_version = "Not detected"
        
        info_group.add(Adw.ActionRow(title="Hyprland", subtitle=hypr_version))
        
        gtk_ver = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        info_group.add(Adw.ActionRow(title="GTK", subtitle=gtk_ver))
        
        try:
            kernel = subprocess.check_output(["uname", "-r"], text=True).strip()
        except Exception:
            kernel = "Unknown"
        info_group.add(Adw.ActionRow(title="Kernel", subtitle=kernel))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main Application
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CarmonySettingsApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.carmonyos.settings")
        self.connect("activate", self.on_activate)
    
    def on_activate(self, app):
        sm = Adw.StyleManager.get_default()
        sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("Settings — CarmonyOS")
        self.win.set_default_size(1050, 850)
        self.win.add_css_class("main-window")
        
        css = Gtk.CssProvider()
        css.load_from_string(MD3_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self.toast_overlay = Adw.ToastOverlay()
        self.win.set_content(self.toast_overlay)
        
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.toast_overlay.set_child(root)
        
        # Nav rail
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        rail.add_css_class("rail-bg")
        rail.set_size_request(88, -1)
        root.append(rail)
        
        logo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        logo_box.set_margin_top(20)
        logo_box.set_margin_bottom(24)
        logo_box.set_halign(Gtk.Align.CENTER)
        rail.append(logo_box)
        
        logo_icon = Gtk.Label(label="⚙")
        logo_icon.add_css_class("app-logo-icon")
        logo_box.append(logo_icon)
        
        nav_items = [
            ("hyprland", "🪟", "Hyprland"),
            ("autostart", "🚀", "Autostart"),
            ("hyprlock", "🔒", "Hyprlock"),
            ("keybinds", "⌨", "Keybinds"),
            ("wallpaper", "🖼", "Wallpaper"),
            ("shell", "🐚", "Shell"),
            ("downloads", "📦", "Downloads"),
        ]
        
        self.nav_btns = {}
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        nav_box.set_halign(Gtk.Align.CENTER)
        rail.append(nav_box)
        
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
            nav_box.append(btn)
            self.nav_btns[tab_id] = btn
        
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        rail.append(spacer)
        
        about_btn = Gtk.Button()
        about_btn.add_css_class("flat")
        about_btn.add_css_class("md3-nav-rail-item")
        about_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        about_inner.set_halign(Gtk.Align.CENTER)
        about_ic = Gtk.Label(label="ℹ")
        about_ic.add_css_class("md3-nav-icon")
        about_inner.append(about_ic)
        about_lb = Gtk.Label(label="About")
        about_lb.add_css_class("md3-nav-label")
        about_inner.append(about_lb)
        about_btn.set_child(about_inner)
        about_btn.connect("clicked", lambda b: self._nav_to("about"))
        about_btn.set_margin_bottom(16)
        rail.append(about_btn)
        self.nav_btns["about"] = about_btn
        
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        root.append(sep)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        root.append(self.stack)
        
        self.stack.add_named(HyprlandPage(self), "hyprland")
        self.stack.add_named(AutostartPage(self), "autostart")
        self.stack.add_named(HyprlockPage(self), "hyprlock")
        self.stack.add_named(KeybindsPage(self), "keybinds")
        self.stack.add_named(WallpaperPage(self), "wallpaper")
        self.stack.add_named(ShellPage(self), "shell")
        self.stack.add_named(DownloadsPage(self), "downloads")
        self.stack.add_named(AboutPage(self), "about")
        
        self._nav_to("hyprland")
        
        kc = Gtk.EventControllerKey()
        kc.connect("key-pressed", self._on_key)
        self.win.add_controller(kc)
        
        self.win.present()
    
    def _nav_to(self, tab_id):
        self.stack.set_visible_child_name(tab_id)
        for tid, btn in self.nav_btns.items():
            if tid == tab_id:
                btn.add_css_class("md3-nav-indicator")
            else:
                btn.remove_css_class("md3-nav-indicator")
    
    def _on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_q and state & Gdk.ModifierType.CONTROL_MASK:
            self.quit()
            return True
        return False
    
    def toast(self, message: str, error: bool = False):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        if error:
            toast.set_priority(Adw.ToastPriority.HIGH)
        self.toast_overlay.add_toast(toast)


if __name__ == "__main__":
    app = CarmonySettingsApp()
    app.run(None)
