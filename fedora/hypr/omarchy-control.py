#!/usr/bin/env python3
"""
Omarchy Settings - Liquid Glass Edition
A beautiful GTK4/Libadwaita settings manager for Hyprland with Omarchy
Version 3.2 - Shadow Bug Fixed
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Gio, GLib
import sys
import re
import subprocess
from pathlib import Path
import json
import os

class OmarchyConfigParser:
    """Parse Omarchy/Hyprland configuration files"""
    
    def __init__(self, config_dir):
        self.config_dir = Path(config_dir)
        self.looknfeel_path = self.config_dir / "looknfeel.conf"
        self.input_path = self.config_dir / "input.conf"
        self.bindings_path = self.config_dir / "bindings.conf"
        
    def parse_decoration_settings(self):
        """Parse decoration block from looknfeel.conf"""
        if not self.looknfeel_path.exists():
            return self._default_decoration_settings()
        
        try:
            content = self.looknfeel_path.read_text()
            settings = {}
            
            blur_match = re.search(r'blur\s*{([^}]+)}', content, re.DOTALL)
            if blur_match:
                blur_content = blur_match.group(1)
                settings['blur_enabled'] = 'enabled = true' in blur_content.lower() or 'enabled=true' in blur_content.lower()
                
                for key, pattern in [
                    ('blur_size', r'size\s*=\s*(\d+)'),
                    ('blur_passes', r'passes\s*=\s*(\d+)'),
                ]:
                    match = re.search(pattern, blur_content)
                    if match:
                        settings[key] = int(match.group(1))
                
                for key, pattern in [
                    ('blur_noise', r'noise\s*=\s*([\d.]+)'),
                    ('blur_contrast', r'contrast\s*=\s*([\d.]+)'),
                    ('blur_brightness', r'brightness\s*=\s*([\d.]+)'),
                    ('blur_vibrancy', r'vibrancy\s*=\s*([\d.]+)'),
                    ('blur_vibrancy_darkness', r'vibrancy_darkness\s*=\s*([\d.]+)'),
                ]:
                    match = re.search(pattern, blur_content)
                    if match:
                        settings[key] = float(match.group(1))
                
                xray_match = re.search(r'xray\s*=\s*(true|false)', blur_content)
                if xray_match:
                    settings['blur_xray'] = xray_match.group(1) == 'true'
                    
                new_opt_match = re.search(r'new_optimizations\s*=\s*(true|false)', blur_content)
                if new_opt_match:
                    settings['blur_new_optimizations'] = new_opt_match.group(1) == 'true'
            
            rounding_match = re.search(r'rounding\s*=\s*(\d+)', content)
            if rounding_match:
                settings['rounding'] = int(rounding_match.group(1))
                
            shadow_match = re.search(r'shadow\s*{([^}]+)}', content, re.DOTALL)
            if shadow_match:
                shadow_content = shadow_match.group(1)
                settings['shadow_enabled'] = 'enabled = true' in shadow_content.lower()
                
                range_match = re.search(r'range\s*=\s*(\d+)', shadow_content)
                if range_match:
                    settings['shadow_range'] = int(range_match.group(1))
                    
                power_match = re.search(r'render_power\s*=\s*(\d+)', shadow_content)
                if power_match:
                    settings['shadow_power'] = int(power_match.group(1))
            
            return settings
        except Exception as e:
            print(f"Error parsing decoration settings: {e}")
            return self._default_decoration_settings()
    
    def parse_general_settings(self):
        """Parse general block"""
        if not self.looknfeel_path.exists():
            return self._default_general_settings()
        
        try:
            content = self.looknfeel_path.read_text()
            settings = {}
            
            general_match = re.search(r'general\s*{([^}]+)}', content, re.DOTALL)
            if general_match:
                general_content = general_match.group(1)
                
                for key, pattern in [
                    ('gaps_in', r'gaps_in\s*=\s*(\d+)'),
                    ('gaps_out', r'gaps_out\s*=\s*(\d+)'),
                    ('border_size', r'border_size\s*=\s*(\d+)'),
                ]:
                    match = re.search(pattern, general_content)
                    if match:
                        settings[key] = int(match.group(1))
            
            return settings
        except Exception as e:
            print(f"Error parsing general settings: {e}")
            return self._default_general_settings()
    
    def parse_input_settings(self):
        """Parse input configuration"""
        if not self.input_path.exists():
            return self._default_input_settings()
        
        try:
            content = self.input_path.read_text()
            settings = {}
            
            input_match = re.search(r'input\s*{([^}]+)}', content, re.DOTALL)
            if input_match:
                input_content = input_match.group(1)
                
                kb_layout_match = re.search(r'kb_layout\s*=\s*([^\n]+)', input_content)
                if kb_layout_match:
                    layouts = kb_layout_match.group(1).strip()
                    settings['kb_layout'] = layouts
                
                kb_options_match = re.search(r'kb_options\s*=\s*([^\n]+)', input_content)
                if kb_options_match:
                    settings['kb_options'] = kb_options_match.group(1).strip()
                
                repeat_rate_match = re.search(r'repeat_rate\s*=\s*(\d+)', input_content)
                if repeat_rate_match:
                    settings['repeat_rate'] = int(repeat_rate_match.group(1))
                repeat_delay_match = re.search(r'repeat_delay\s*=\s*(\d+)', input_content)
                if repeat_delay_match:
                    settings['repeat_delay'] = int(repeat_delay_match.group(1))
                
                numlock_match = re.search(r'numlock_by_default\s*=\s*(true|false)', input_content)
                if numlock_match:
                    settings['numlock_by_default'] = numlock_match.group(1) == 'true'
                
                sensitivity_match = re.search(r'sensitivity\s*=\s*([-\d.]+)', input_content)
                if sensitivity_match:
                    settings['sensitivity'] = float(sensitivity_match.group(1))
                
                touchpad_match = re.search(r'touchpad\s*{([^}]+)}', input_content, re.DOTALL)
                if touchpad_match:
                    touchpad_content = touchpad_match.group(1)
                    
                    natural_scroll_match = re.search(r'natural_scroll\s*=\s*(true|false)', touchpad_content)
                    if natural_scroll_match:
                        settings['touchpad_natural_scroll'] = natural_scroll_match.group(1) == 'true'
                    
                    scroll_factor_match = re.search(r'scroll_factor\s*=\s*([\d.]+)', touchpad_content)
                    if scroll_factor_match:
                        settings['touchpad_scroll_factor'] = float(scroll_factor_match.group(1))
            
            return settings
        except Exception as e:
            print(f"Error parsing input settings: {e}")
            return self._default_input_settings()
    
    def parse_animations_settings(self):
        """Parse animations block"""
        if not self.looknfeel_path.exists():
            return self._default_animations_settings()
        
        try:
            content = self.looknfeel_path.read_text()
            settings = {}
            
            animations_match = re.search(r'animations\s*{([^}]+)}', content, re.DOTALL)
            if animations_match:
                anim_content = animations_match.group(1)
                settings['animations_enabled'] = 'enabled = true' in anim_content.lower()
            
            return settings
        except Exception as e:
            print(f"Error parsing animations: {e}")
            return self._default_animations_settings()
    
    def _default_decoration_settings(self):
        return {
            'blur_enabled': True,
            'blur_size': 10,
            'blur_passes': 4,
            'blur_noise': 0.01,
            'blur_contrast': 1.3,
            'blur_brightness': 1.1,
            'blur_vibrancy': 0.6,
            'blur_vibrancy_darkness': 0.2,
            'blur_xray': False,
            'blur_new_optimizations': True,
            'rounding': 20,
            'shadow_enabled': True,
            'shadow_range': 30,
            'shadow_power': 3,
        }
    
    def _default_general_settings(self):
        return {
            'gaps_in': 5,
            'gaps_out': 10,
            'border_size': 2,
        }
    
    def _default_input_settings(self):
        return {
            'kb_layout': 'us,ara',
            'kb_options': 'grp:alt_shift_toggle',
            'repeat_rate': 40,
            'repeat_delay': 600,
            'numlock_by_default': True,
            'sensitivity': 0.0,
            'touchpad_natural_scroll': False,
            'touchpad_scroll_factor': 0.4,
        }
    
    def _default_animations_settings(self):
        return {
            'animations_enabled': True,
        }



class OmarchyConfigWriter:
    """Write settings back to Omarchy/Hyprland configuration files"""
    
    def __init__(self, config_dir):
        self.config_dir = Path(config_dir)
        self.looknfeel_path = self.config_dir / "looknfeel.conf"
        self.input_path = self.config_dir / "input.conf"
    
    def update_blur_settings(self, settings):
        """Update blur settings in looknfeel.conf"""
        if not self.looknfeel_path.exists():
            print(f"Error: {self.looknfeel_path} does not exist")
            return False
        
        try:
            content = self.looknfeel_path.read_text()
            
            for key, value in settings.items():
                if key.startswith('blur_'):
                    setting_name = key.replace('blur_', '')
                    
                    if isinstance(value, bool):
                        value_str = 'true' if value else 'false'
                    elif isinstance(value, float):
                        value_str = f'{value:.4f}'
                    else:
                        value_str = str(value)
                    
                    pattern = rf'(blur\s*{{[^}}]*?){setting_name}\s*=\s*[^\n]+'
                    replacement = rf'\g<1>{setting_name} = {value_str}'
                    
                    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    if new_content != content:
                        content = new_content
            
            self.looknfeel_path.write_text(content)
            self._reload_hyprland()
            return True
        except Exception as e:
            print(f"Error updating blur settings: {e}")
            return False
    
    def update_decoration_settings(self, settings):
        """Update decoration settings"""
        if not self.looknfeel_path.exists():
            return False
        
        try:
            content = self.looknfeel_path.read_text()
            
            for key, value in settings.items():
                if key == 'rounding':
                    content = re.sub(
                        r'rounding\s*=\s*\d+',
                        f'rounding = {value}',
                        content
                    )
                elif key.startswith('shadow_'):
                    setting_name = key.replace('shadow_', '')
                    if isinstance(value, bool):
                        value_str = 'true' if value else 'false'
                    else:
                        value_str = str(value)
                    
                    pattern = rf'(shadow\s*{{[^}}]*?){setting_name}\s*=\s*[^\n]+'
                    replacement = rf'\g<1>{setting_name} = {value_str}'
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            self.looknfeel_path.write_text(content)
            self._reload_hyprland()
            return True
        except Exception as e:
            print(f"Error updating decoration settings: {e}")
            return False
    
    def update_general_settings(self, settings):
        """Update general settings"""
        if not self.looknfeel_path.exists():
            return False
        
        try:
            content = self.looknfeel_path.read_text()
            
            for key, value in settings.items():
                pattern = rf'(general\s*{{[^}}]*?){key}\s*=\s*\d+'
                replacement = rf'\g<1>{key} = {value}'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            self.looknfeel_path.write_text(content)
            self._reload_hyprland()
            return True
        except Exception as e:
            print(f"Error updating general settings: {e}")
            return False
    
    def update_input_settings(self, settings):
        """Update input settings"""
        if not self.input_path.exists():
            print(f"Error: {self.input_path} does not exist")
            return False
        
        try:
            content = self.input_path.read_text()
            
            for key, value in settings.items():
                if key == 'kb_layout':
                    content = re.sub(
                        r'kb_layout\s*=\s*[^\n]+',
                        f'kb_layout = {value}',
                        content
                    )
                elif key == 'kb_options':
                    content = re.sub(
                        r'kb_options\s*=\s*[^\n]+',
                        f'kb_options = {value}',
                        content
                    )
                elif key in ['repeat_rate', 'repeat_delay']:
                    content = re.sub(
                        rf'{key}\s*=\s*\d+',
                        f'{key} = {value}',
                        content
                    )
                elif key == 'numlock_by_default':
                    value_str = 'true' if value else 'false'
                    content = re.sub(
                        r'numlock_by_default\s*=\s*(true|false)',
                        f'numlock_by_default = {value_str}',
                        content
                    )
                elif key == 'sensitivity':
                    if 'sensitivity' not in content:
                        content = re.sub(
                            r'(input\s*{)',
                            rf'\g<1>\n  sensitivity = {value}',
                            content
                        )
                    else:
                        content = re.sub(
                            r'sensitivity\s*=\s*[-\d.]+',
                            f'sensitivity = {value}',
                            content
                        )
                elif key.startswith('touchpad_'):
                    setting_name = key.replace('touchpad_', '')
                    if isinstance(value, bool):
                        value_str = 'true' if value else 'false'
                    else:
                        value_str = str(value)
                    
                    pattern = rf'(touchpad\s*{{[^}}]*?){setting_name}\s*=\s*[^\n]+'
                    replacement = rf'\g<1>{setting_name} = {value_str}'
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            self.input_path.write_text(content)
            self._reload_hyprland()
            return True
        except Exception as e:
            print(f"Error updating input settings: {e}")
            return False
    
    def _reload_hyprland(self):
        """Reload Hyprland configuration"""
        try:
            result = subprocess.run(
                ['hyprctl', 'reload'],
                check=False,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("Omarchy reloaded successfully")
            else:
                print(f"⚠️ Omarchy reload warning: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("⚠️ Omarchy reload timed out")
        except FileNotFoundError:
            print("⚠️ hyprctl not found - changes saved but not applied")
        except Exception as e:
            print(f"⚠️ Could not reload Omarchy: {e}")



class LanguageInputPage(Adw.PreferencesPage):
    """Language and input configuration page"""
    
    AVAILABLE_LANGUAGES = {
        'us': ' English (US)',
        'ara': ' Arabic',
        'uk': ' Ukrainian',
        'ru': ' Russian',
        'de': ' German',
        'fr': ' French',
        'es': ' Spanish',
        'it': ' Italian',
        'jp': ' Japanese',
        'kr': ' Korean',
        'cn': ' Chinese',
        'tr': ' Turkish',
        'pl': ' Polish',
        'cz': ' Czech',
        'dk': ' Danish',
        'no': ' Norwegian',
        'se': ' Swedish',
        'fi': ' Finnish',
        'nl': ' Dutch',
        'be': ' Belgian',
        'pt': ' Portuguese',
        'br': ' Brazilian',
        'gr': ' Greek',
    }
    
    SWITCH_METHODS = {
        'grp:alt_shift_toggle': 'Alt + Shift',
        'grp:alts_toggle': 'Left Alt + Right Alt',
        'grp:ctrl_shift_toggle': 'Ctrl + Shift',
        'grp:caps_toggle': 'Caps Lock',
        'grp:win_space_toggle': 'Win + Space',
        'grp:alt_space_toggle': 'Alt + Space',
    }
    
    def __init__(self, parser, writer):
        super().__init__()
        self.parser = parser
        self.writer = writer
        
        self.set_title("Language & Input")
        self.set_icon_name("input-keyboard-symbolic")
        
        self.settings = parser.parse_input_settings()
        
        current_layout = self.settings.get('kb_layout', 'us,ara')
        self.selected_languages = current_layout.split(',')
        
        self._create_ui()
    
    def _create_ui(self):
        layout_group = Adw.PreferencesGroup()
        layout_group.set_title(" Keyboard Layouts")
        layout_group.set_description("Select and configure your keyboard layouts")
        
        self._create_language_selector(layout_group)
        
        switch_row = Adw.ComboRow()
        switch_row.set_title("Layout Switch Keybind")
        switch_row.set_subtitle("Hotkey to switch between languages")
        
        switch_model = Gtk.StringList()
        current_method = self.settings.get('kb_options', 'grp:alt_shift_toggle')
        selected_index = 0
        
        for i, (method, label) in enumerate(self.SWITCH_METHODS.items()):
            switch_model.append(label)
            if method in current_method:
                selected_index = i
        
        switch_row.set_model(switch_model)
        switch_row.set_selected(selected_index)
        switch_row.connect("notify::selected", self._on_switch_method_changed)
        
        layout_group.add(switch_row)
        
        self.add(layout_group)
        mouse_group = Adw.PreferencesGroup()
        mouse_group.set_title(" Mouse and Touchpad")
        mouse_group.set_description("Configure pointer behavior")
        sensitivity_row = self._create_scale_row(
            "Mouse Sensitivity",
            "Adjust pointer speed (-1.0 to 1.0)",
            -1.0, 1.0, 0.05,
            self.settings.get('sensitivity', 0.0),
            'sensitivity',
            2
        )
        mouse_group.add(sensitivity_row)
        natural_scroll = Adw.SwitchRow()
        natural_scroll.set_title("Natural Scrolling")
        natural_scroll.set_subtitle("Reverse scroll direction (macOS style)")
        natural_scroll.set_active(self.settings.get('touchpad_natural_scroll', False))
        natural_scroll.connect("notify::active", lambda w, p: self._on_setting_changed('touchpad_natural_scroll', w.get_active()))
        mouse_group.add(natural_scroll)
        
        scroll_factor_row = self._create_scale_row(
            "Scroll Speed",
            "Touchpad scrolling speed (0.1 to 2.0)",
            0.1, 2.0, 0.1,
            self.settings.get('touchpad_scroll_factor', 0.4),
            'touchpad_scroll_factor',
            2
        )
        mouse_group.add(scroll_factor_row)
        
        self.add(mouse_group)
        
        keyboard_group = Adw.PreferencesGroup()
        keyboard_group.set_title(" Keyboard Behavior")
        
        numlock = Adw.SwitchRow()
        numlock.set_title("Numlock on Startup")
        numlock.set_subtitle("Enable numlock by default")
        numlock.set_active(self.settings.get('numlock_by_default', True))
        numlock.connect("notify::active", lambda w, p: self._on_setting_changed('numlock_by_default', w.get_active()))
        keyboard_group.add(numlock)
        
        repeat_rate = Adw.SpinRow()
        repeat_rate.set_title("Key Repeat Rate")
        repeat_rate.set_subtitle("How fast keys repeat (higher = faster)")
        repeat_rate.set_adjustment(Gtk.Adjustment(
            lower=10, upper=100, step_increment=5,
            value=self.settings.get('repeat_rate', 40)
        ))
        repeat_rate.connect("changed", lambda w: self._on_setting_changed('repeat_rate', int(w.get_value())))
        keyboard_group.add(repeat_rate)
        
        repeat_delay = Adw.SpinRow()
        repeat_delay.set_title("Key Repeat Delay")
        repeat_delay.set_subtitle("Delay before key starts repeating (ms)")
        repeat_delay.set_adjustment(Gtk.Adjustment(
            lower=200, upper=1000, step_increment=50,
            value=self.settings.get('repeat_delay', 600)
        ))
        repeat_delay.connect("changed", lambda w: self._on_setting_changed('repeat_delay', int(w.get_value())))
        keyboard_group.add(repeat_delay)
        
        self.add(keyboard_group)
    
    def _create_language_selector(self, group):
        """Create language selection UI"""
        current_row = Adw.ActionRow()
        current_row.set_title("Active Layouts")
        current_row.set_subtitle(self._get_languages_display())
        
        pick_button = Gtk.Button(label="Select Languages")
        pick_button.connect("clicked", self._show_language_picker)
        current_row.add_suffix(pick_button)
        
        group.add(current_row)
        
        self.current_languages_row = current_row
    
    def _get_languages_display(self):
        """Get display string for selected languages"""
        display_names = []
        for lang in self.selected_languages:
            lang = lang.strip()
            display_names.append(self.AVAILABLE_LANGUAGES.get(lang, lang))
        return ' + '.join(display_names)
    
    def _show_language_picker(self, button):
        """Show window to pick languages"""
        dialog = Adw.Window()
        dialog.set_transient_for(self.get_root())
        dialog.set_modal(True)
        dialog.set_default_size(450, 550)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dialog.set_content(main_box)
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Select Keyboard Layouts"))
        main_box.append(header)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        
        subtitle_label = Gtk.Label(label="Choose up to 4 layouts")
        subtitle_label.add_css_class("dim-label")
        subtitle_label.set_margin_top(10)
        subtitle_label.set_margin_bottom(20)
        content_box.append(subtitle_label)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        list_box = Gtk.ListBox()
        list_box.add_css_class("boxed-list")
        list_box.set_margin_start(20)
        list_box.set_margin_end(20)
        
        self.lang_checkboxes = {}
        
        for code, name in self.AVAILABLE_LANGUAGES.items():
            row = Gtk.ListBoxRow()
            box = Gtk.Box(spacing=12)
            box.set_margin_start(12)
            box.set_margin_end(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            
            check = Gtk.CheckButton()
            check.set_active(code in self.selected_languages)
            self.lang_checkboxes[code] = check
            
            label = Gtk.Label(label=name)
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            
            box.append(check)
            box.append(label)
            row.set_child(box)
            list_box.append(row)
        
        scrolled.set_child(list_box)
        content_box.append(scrolled)
        
        button_box = Gtk.Box(spacing=12)
        button_box.set_margin_top(20)
        button_box.set_margin_bottom(20)
        button_box.set_margin_start(20)
        button_box.set_margin_end(20)
        button_box.set_halign(Gtk.Align.END)
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: dialog.close())
        button_box.append(cancel_btn)
        
        apply_btn = Gtk.Button(label="Apply")
        apply_btn.add_css_class("suggested-action")
        apply_btn.connect("clicked", lambda b: self._on_language_picker_apply(dialog))
        button_box.append(apply_btn)
        
        content_box.append(button_box)
        
        main_box.append(content_box)
        dialog.present()
    
    def _on_language_picker_apply(self, dialog):
        """Handle language picker apply"""
        new_languages = []
        for code, check in self.lang_checkboxes.items():
            if check.get_active():
                new_languages.append(code)
        
        if new_languages:
            self.selected_languages = new_languages[:4]
            self._on_setting_changed('kb_layout', ','.join(self.selected_languages))
            self.current_languages_row.set_subtitle(self._get_languages_display())
        
        dialog.close()
    
    def _on_switch_method_changed(self, combo_row, pspec):
        """Handle switch method change"""
        selected = combo_row.get_selected()
        methods = list(self.SWITCH_METHODS.keys())
        if selected < len(methods):
            method = methods[selected]
            self._on_setting_changed('kb_options', method)
    
    def _create_scale_row(self, title, subtitle, min_val, max_val, step, value, setting_name, digits):
        """Helper to create a row with a scale widget"""
        row = Adw.ActionRow()
        row.set_title(title)
        row.set_subtitle(subtitle)
        
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        scale.set_range(min_val, max_val)
        scale.set_value(value)
        scale.set_digits(digits)
        scale.set_hexpand(True)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_size_request(200, -1)
        scale.connect("value-changed", lambda w: self._on_setting_changed(setting_name, round(w.get_value(), digits)))
        
        row.add_suffix(scale)
        return row
    
    def _on_setting_changed(self, setting_name, value):
        """Handle any setting change"""
        self.settings[setting_name] = value
        print(f"⚙️ Setting changed: {setting_name} = {value}")



class BlurEffectsPage(Adw.PreferencesPage):
    """Blur and glass effects configuration page"""
    
    def __init__(self, parser, writer):
        super().__init__()
        self.parser = parser
        self.writer = writer
        
        self.set_title("Blur & Glass Effects")
        self.set_icon_name("emblem-photos-symbolic")
        self.settings = parser.parse_decoration_settings()
        
        self._create_ui()
    
    def _create_ui(self):
        blur_group = Adw.PreferencesGroup()
        blur_group.set_title(" Liquid Glass Blur")
        blur_group.set_description("Create the perfect frosted glass effect")
        
        enable_blur = Adw.SwitchRow()
        enable_blur.set_title("Enable Blur")
        enable_blur.set_subtitle("Master switch for all blur effects")
        enable_blur.set_active(self.settings.get('blur_enabled', True))
        enable_blur.connect("notify::active", lambda w, p: self._on_setting_changed('blur_enabled', w.get_active()))
        blur_group.add(enable_blur)
        
        blur_size = Adw.SpinRow()
        blur_size.set_title("Blur Radius")
        blur_size.set_subtitle("Size of the blur effect (1-20)")
        blur_size.set_adjustment(Gtk.Adjustment(
            lower=1, upper=20, step_increment=1, 
            value=self.settings.get('blur_size', 10)
        ))
        blur_size.connect("changed", lambda w: self._on_setting_changed('blur_size', int(w.get_value())))
        blur_group.add(blur_size)
        
        blur_passes = Adw.SpinRow()
        blur_passes.set_title("Blur Quality")
        blur_passes.set_subtitle("Higher = smoother (1-8, affects performance)")
        blur_passes.set_adjustment(Gtk.Adjustment(
            lower=1, upper=8, step_increment=1,
            value=self.settings.get('blur_passes', 4)
        ))
        blur_passes.connect("changed", lambda w: self._on_setting_changed('blur_passes', int(w.get_value())))
        blur_group.add(blur_passes)
        
        optimizations = Adw.SwitchRow()
        optimizations.set_title("Performance Optimizations")
        optimizations.set_subtitle("Enable for better performance (recommended)")
        optimizations.set_active(self.settings.get('blur_new_optimizations', True))
        optimizations.connect("notify::active", lambda w, p: self._on_setting_changed('blur_new_optimizations', w.get_active()))
        blur_group.add(optimizations)
        
        self.add(blur_group)
        
        advanced_group = Adw.PreferencesGroup()
        advanced_group.set_title(" Advanced Glass Properties")
        advanced_group.set_description("Fine-tune the liquid glass appearance")
        
        noise_row = self._create_scale_row(
            "Glass Texture",
            "Add subtle grain for realism (0.000-0.100)",
            0, 0.1, 0.001,
            self.settings.get('blur_noise', 0.01),
            'blur_noise',
            3
        )
        advanced_group.add(noise_row)
        
        contrast_row = self._create_scale_row(
            "Color Contrast",
            "Make colors pop through glass (0.5-2.0)",
            0.5, 2.0, 0.05,
            self.settings.get('blur_contrast', 1.3),
            'blur_contrast',
            2
        )
        advanced_group.add(contrast_row)
        
        brightness_row = self._create_scale_row(
            "Glass Brightness",
            "Luminosity multiplier (0.5-1.5)",
            0.5, 1.5, 0.05,
            self.settings.get('blur_brightness', 1.1),
            'blur_brightness',
            2
        )
        advanced_group.add(brightness_row)
        
        vibrancy_row = self._create_scale_row(
            "Vibrancy ",
            "macOS-style color saturation (0.0-1.0)",
            0, 1.0, 0.05,
            self.settings.get('blur_vibrancy', 0.6),
            'blur_vibrancy',
            2
        )
        advanced_group.add(vibrancy_row)
        
        vib_dark_row = self._create_scale_row(
            "Vibrancy Darkness",
            "Dark tone preservation (0.0-1.0)",
            0, 1.0, 0.05,
            self.settings.get('blur_vibrancy_darkness', 0.2),
            'blur_vibrancy_darkness',
            2
        )
        advanced_group.add(vib_dark_row)
        
        xray = Adw.SwitchRow()
        xray.set_title("X-Ray Transparency")
        xray.set_subtitle("See through blur completely")
        xray.set_active(self.settings.get('blur_xray', False))
        xray.connect("notify::active", lambda w, p: self._on_setting_changed('blur_xray', w.get_active()))
        advanced_group.add(xray)
        
        self.add(advanced_group)
        
    def _create_scale_row(self, title, subtitle, min_val, max_val, step, value, setting_name, digits):
        """Helper to create a row with a scale widget"""
        row = Adw.ActionRow()
        row.set_title(title)
        row.set_subtitle(subtitle)
        
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        scale.set_range(min_val, max_val)
        scale.set_value(max(min_val, value))
        scale.set_digits(digits)
        scale.set_hexpand(True)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_size_request(200, -1)
        scale.connect("value-changed", lambda w: self._on_setting_changed(setting_name, round(w.get_value(), digits)))
        
        row.add_suffix(scale)
        return row
    
    def _on_setting_changed(self, setting_name, value):
        """Handle any setting change"""
        self.settings[setting_name] = value
        print(f"⚙️ Setting changed: {setting_name} = {value}")



class WindowAppearancePage(Adw.PreferencesPage):
    """Window appearance and layout settings page"""
    
    def __init__(self, parser, writer):
        super().__init__()
        self.parser = parser
        self.writer = writer
        
        self.set_title("Window Appearance")
        self.set_icon_name("view-grid-symbolic")
        
        self.settings = parser.parse_general_settings()
        self.decoration_settings = parser.parse_decoration_settings()
        
        self._create_ui()
    
    def _create_ui(self):
        border_group = Adw.PreferencesGroup()
        border_group.set_title(" Window Borders")
        border_group.set_description("Customize window frames")
        
        border_size = Adw.SpinRow()
        border_size.set_title("Border Thickness")
        border_size.set_subtitle("Width of window borders (0-10 pixels)")
        border_size.set_adjustment(Gtk.Adjustment(
            lower=0, upper=10, step_increment=1,
            value=self.settings.get('border_size', 2)
        ))
        border_size.connect("changed", lambda w: self._on_general_setting_changed('border_size', int(w.get_value())))
        border_group.add(border_size)
        
        rounding = Adw.SpinRow()
        rounding.set_title("Corner Rounding")
        rounding.set_subtitle("Radius of rounded corners (0-40 pixels)")
        rounding.set_adjustment(Gtk.Adjustment(
            lower=0, upper=40, step_increment=1,
            value=self.decoration_settings.get('rounding', 20)
        ))
        rounding.connect("changed", lambda w: self._on_decoration_setting_changed('rounding', int(w.get_value())))
        border_group.add(rounding)
        
        self.add(border_group)
        
        gaps_group = Adw.PreferencesGroup()
        gaps_group.set_title(" Window Spacing")
        gaps_group.set_description("Configure gaps between windows")
        
        gaps_in = Adw.SpinRow()
        gaps_in.set_title("Inner Gaps")
        gaps_in.set_subtitle("Space between windows (0-30 pixels)")
        gaps_in.set_adjustment(Gtk.Adjustment(
            lower=0, upper=30, step_increment=1,
            value=self.settings.get('gaps_in', 5)
        ))
        gaps_in.connect("changed", lambda w: self._on_general_setting_changed('gaps_in', int(w.get_value())))
        gaps_group.add(gaps_in)
        
        gaps_out = Adw.SpinRow()
        gaps_out.set_title("Outer Gaps")
        gaps_out.set_subtitle("Space from screen edges (0-30 pixels)")
        gaps_out.set_adjustment(Gtk.Adjustment(
            lower=0, upper=30, step_increment=1,
            value=self.settings.get('gaps_out', 10)
        ))
        gaps_out.connect("changed", lambda w: self._on_general_setting_changed('gaps_out', int(w.get_value())))
        gaps_group.add(gaps_out)
        
        self.add(gaps_group)
        
        anim_group = Adw.PreferencesGroup()
        anim_group.set_title(" Animations")
        anim_group.set_description("Window motion effects")
        
        anim_settings = self.parser.parse_animations_settings()
        
        enable_anim = Adw.SwitchRow()
        enable_anim.set_title("Enable Animations")
        enable_anim.set_subtitle("Smooth window transitions")
        enable_anim.set_active(anim_settings.get('animations_enabled', True))
        anim_group.add(enable_anim)
        
        self.add(anim_group)
    
    def _on_general_setting_changed(self, setting_name, value):
        """Handle general setting changes"""
        self.settings[setting_name] = value
        print(f"⚙️ Setting changed: {setting_name} = {value}")
    
    def _on_decoration_setting_changed(self, setting_name, value):
        """Handle decoration setting changes"""
        self.decoration_settings[setting_name] = value
        print(f"⚙️ Setting changed: {setting_name} = {value}")



class OmarchySettingsWindow(Adw.ApplicationWindow):
    """Main application window with liquid glass UI"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.config_path = Path.home() / ".config" / "hypr"
        self.parser = OmarchyConfigParser(self.config_path)
        self.writer = OmarchyConfigWriter(self.config_path)
        
        self.set_default_size(1100, 750)
        self.set_title("Omarchy Settings")
        
         
        self._apply_liquid_glass_style()
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)
        
        self._setup_headerbar()
        
        self.toast_overlay = Adw.ToastOverlay()
        self.main_box.append(self.toast_overlay)
        
        self._setup_navigation()
        
    def _apply_liquid_glass_style(self):
        """Apply the liquid glass CSS styling - SHADOW REMOVED"""
        css_provider = Gtk.CssProvider()
        css = """
        
        window {
            background: linear-gradient(135deg, 
                rgba(15, 15, 25, 0.95) 0%, 
                rgba(25, 25, 40, 0.90) 100%);
        }
        
        headerbar {
            background: linear-gradient(180deg,
                rgba(45, 50, 75, 0.90) 0%,
                rgba(35, 40, 65, 0.85) 100%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .glass-button {
            background: linear-gradient(135deg,
                rgba(104, 116, 206, 0.40) 0%,
                rgba(104, 116, 206, 0.25) 100%);
            border-radius: 18px;
            border: 1.5px solid rgba(104, 116, 206, 0.6);
            padding: 14px 28px;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .glass-button:hover {
            background: linear-gradient(135deg,
                rgba(104, 116, 206, 0.60) 0%,
                rgba(104, 116, 206, 0.40) 100%);
            transform: translateY(-2px);
            border-color: rgba(104, 116, 206, 0.8);
        }
        
        scale trough {
            background: linear-gradient(90deg,
                rgba(255, 255, 255, 0.08) 0%,
                rgba(255, 255, 255, 0.12) 100%);
            border-radius: 14px;
            min-height: 10px;
        }
        
        scale highlight {
            background: linear-gradient(90deg, 
                rgba(104, 116, 206, 0.9) 0%,
                rgba(137, 180, 250, 0.8) 50%,
                rgba(212, 131, 203, 0.9) 100%);
            border-radius: 14px;
        }
        
        scale slider {
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.95) 0%,
                rgba(240, 240, 255, 0.90) 100%);
            border: 2.5px solid rgba(104, 116, 206, 0.6);
            border-radius: 50%;
            min-width: 28px;
            min-height: 28px;
            transition: all 0.2s ease;
        }
        
        scale slider:hover {
            transform: scale(1.1);
        }
        
        .sidebar {
            background: linear-gradient(180deg,
                rgba(25, 28, 45, 0.85) 0%,
                rgba(20, 23, 40, 0.90) 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .nav-item {
            background: transparent;
            border-radius: 14px;
            margin: 8px 14px;
            padding: 14px 16px;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 500;
            transition: all 0.25s ease;
            border: 1px solid transparent;
        }
        
        .nav-item:hover {
            background: linear-gradient(135deg,
                rgba(104, 116, 206, 0.15) 0%,
                rgba(104, 116, 206, 0.08) 100%);
            color: rgba(255, 255, 255, 0.95);
            border-color: rgba(104, 116, 206, 0.3);
        }
        
        .nav-item.active {
            background: linear-gradient(135deg,
                rgba(104, 116, 206, 0.35) 0%,
                rgba(104, 116, 206, 0.20) 100%);
            color: white;
            border-left: 4px solid rgba(104, 116, 206, 1);
            border-color: rgba(104, 116, 206, 0.5);
        }
        
        switch {
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.12) 0%,
                rgba(255, 255, 255, 0.08) 100%);
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        switch:checked {
            background: linear-gradient(135deg,
                rgba(104, 116, 206, 0.85) 0%,
                rgba(104, 116, 206, 0.70) 100%);
            border-color: rgba(104, 116, 206, 0.8);
        }
        
        switch slider {
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.98) 0%,
                rgba(245, 245, 255, 0.95) 100%);
            border-radius: 50%;
        }
        
        entry, spinbutton {
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.09) 0%,
                rgba(255, 255, 255, 0.06) 100%);
            border: 1.5px solid rgba(255, 255, 255, 0.18);
            border-radius: 14px;
            color: white;
            padding: 12px 16px;
            transition: all 0.3s ease;
        }
        
        entry:focus, spinbutton:focus {
            border-color: rgba(104, 116, 206, 0.9);
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.12) 0%,
                rgba(255, 255, 255, 0.08) 100%);
        }
        
        .boxed-list {
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.06) 0%,
                rgba(255, 255, 255, 0.03) 100%);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        toast {
            background: linear-gradient(135deg,
                rgba(50, 55, 80, 0.95) 0%,
                rgba(40, 45, 70, 0.90) 100%);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        scrollbar {
            background: transparent;
        }
        
        scrollbar slider {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            min-width: 8px;
            min-height: 8px;
        }
        
        scrollbar slider:hover {
            background: rgba(255, 255, 255, 0.25);
        }
        """
        
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _setup_headerbar(self):
        """Setup the header bar"""
        header = Adw.HeaderBar()
        
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        
        menu = Gio.Menu()
        menu.append("About Settings", "app.about")
        menu.append("Quit", "app.quit")
        
        menu_button.set_menu_model(menu)
        header.pack_start(menu_button)
        
        apply_btn = Gtk.Button(label=" Apply ")
        apply_btn.add_css_class("glass-button")
        apply_btn.add_css_class("suggested-action")
        apply_btn.connect("clicked", self._on_apply_settings)
        header.pack_end(apply_btn)
        
        reload_btn = Gtk.Button()
        reload_btn.set_icon_name("view-refresh-symbolic")
        reload_btn.set_tooltip_text("Reload Hyprland")
        reload_btn.connect("clicked", self._on_reload_hyprland)
        header.pack_end(reload_btn)
        
        self.main_box.append(header)
    
    def _setup_navigation(self):
        """Setup the navigation sidebar and content area"""
        split_view = Adw.OverlaySplitView()
        split_view.set_sidebar_position(Gtk.PackType.START)
        split_view.set_show_sidebar(True)
        split_view.set_sidebar_width_fraction(0.25)
        
        sidebar = self._create_sidebar()
        split_view.set_sidebar(sidebar)
        
        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)
        
        self._add_pages()
        
        split_view.set_content(self.view_stack)
        self.toast_overlay.set_child(split_view)
    
    def _create_sidebar(self):
        """Create the navigation sidebar"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(300, -1)
        sidebar_box.add_css_class("sidebar")
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title_box.set_margin_top(28)
        title_box.set_margin_bottom(28)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title = Gtk.Label(label=" Omarchy")
        title.add_css_class("title-1")
        
        subtitle = Gtk.Label(label="GUI App Settings")
        subtitle.add_css_class("dim-label")
        subtitle.add_css_class("caption")
        
        version = Gtk.Label(label="v3.0")
        version.add_css_class("dim-label")
        version.add_css_class("caption")
        
        title_box.append(title)
        title_box.append(subtitle)
        title_box.append(version)
        
        sidebar_box.append(title_box)
        
        separator = Gtk.Separator()
        separator.set_margin_start(20)
        separator.set_margin_end(20)
        sidebar_box.append(separator)
        
        nav_items = [
            (" Language / input", "language"),
            (" Blur/Glass", "blur"),
            (" Window Appearance", "appearance"),
        ]
        
        self.nav_buttons = {}
        for label, page_name in nav_items:
            btn = Gtk.Button(label=label)
            btn.add_css_class("nav-item")
            btn.add_css_class("flat")
            btn.set_halign(Gtk.Align.FILL)
            btn.connect("clicked", lambda b, p=page_name: self._switch_page(p))
            sidebar_box.append(btn)
            self.nav_buttons[page_name] = btn
        
        if nav_items:
            self.nav_buttons[nav_items[0][1]].add_css_class("active")
        
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar_box.append(spacer)
        
        footer = Gtk.Label(label="Made By ghvbb for Omarchy")
        footer.add_css_class("dim-label")
        footer.add_css_class("caption")
        footer.set_margin_bottom(20)
        sidebar_box.append(footer)
        
        return sidebar_box
    
    def _switch_page(self, page_name):
        """Switch to a different page and update nav buttons"""
        self.view_stack.set_visible_child_name(page_name)
        
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")
    
    def _add_pages(self):
        """Add all configuration pages"""
        self.language_page = LanguageInputPage(self.parser, self.writer)
        self.view_stack.add_titled(
            self.language_page, "language", "Language & Input"
        )
        
        self.blur_page = BlurEffectsPage(self.parser, self.writer)
        self.view_stack.add_titled(
            self.blur_page, "blur", "Blur & Glass"
        )
        self.appearance_page = WindowAppearancePage(self.parser, self.writer)
        self.view_stack.add_titled(
            self.appearance_page, "appearance", "Window Appearance"
        )
    
    def _on_apply_settings(self, button):
        """Apply all settings to Hyprland configuration"""
        success_count = 0
        error_messages = []
        
        try:
            if hasattr(self.language_page, 'settings'):
                if self.writer.update_input_settings(self.language_page.settings):
                    success_count += 1
                else:
                    error_messages.append("Input settings")
            if hasattr(self.blur_page, 'settings'):
                if self.writer.update_blur_settings(self.blur_page.settings):
                    success_count += 1
                if self.writer.update_decoration_settings(self.blur_page.settings):
                    success_count += 1
                else:
                    error_messages.append("Blur settings")
            if hasattr(self.appearance_page, 'settings'):
                if self.writer.update_general_settings(self.appearance_page.settings):
                    success_count += 1
                else:
                    error_messages.append("General settings")
            
            if hasattr(self.appearance_page, 'decoration_settings'):
                if self.writer.update_decoration_settings(self.appearance_page.decoration_settings):
                    success_count += 1
            if error_messages:
                toast = Adw.Toast(title=f" Applied {success_count} settings, failed: {', '.join(error_messages)}")
                toast.set_timeout(4)
            else:
                toast = Adw.Toast(title=" All settings applied successfully!")
                toast.set_timeout(3)
            
            self.toast_overlay.add_toast(toast)
            
        except Exception as e:
            toast = Adw.Toast(title=f" Error: {str(e)}")
            toast.set_timeout(4)
            self.toast_overlay.add_toast(toast)
    
    def _on_reload_hyprland(self, button):
        """Manually reload Hyprland"""
        try:
            result = subprocess.run(
                ['hyprctl', 'reload'],
                check=False,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                toast = Adw.Toast(title=" Omarchy reloaded successfully")
            else:
                toast = Adw.Toast(title=f" Reload warning: {result.stderr[:50]}")
            
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)
            
        except Exception as e:
            toast = Adw.Toast(title=f" Could not reload: {str(e)}")
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)
    
    def _show_about(self):
        """Show about dialog"""
        about = Adw.AboutDialog(
            application_name="Settings",
            application_icon="preferences-system",
            developer_name="Omarchy Comminity developers",
            version="2.3",
            developers=["ghvbb on github/ mohamedxa"],
            copyright="© 2026",
            comments="Settings App For Omarchy",
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(self)



class OmarchySettingsApp(Adw.Application):
    """Main application class"""
    
    def __init__(self):
        super().__init__(application_id='com.omarchy.settings')
        self.create_action('quit', self.on_quit, ['<primary>q'])
        self.create_action('about', self.on_about)
        
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = OmarchySettingsWindow(application=self)
        win.present()
        
    def on_quit(self, action, param):
        self.quit()
    
    def on_about(self, action, param):
        win = self.props.active_window
        if win and hasattr(win, '_show_about'):
            win._show_about()
        
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)



def main():
    """Main entry point"""
    app = OmarchySettingsApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    main()
