#!/bin/bash

CONFIG="$HOME/.config/hypr/hyprland.conf"
ROFI_CONFIG="$HOME/.config/rofi/config.rasi"
if [ -f "$CONFIG" ]; then
    sed -i -E \
        -e 's/(gaps_in|gaps_out|rounding) = [0-9]*/\1 = 0/g' \
        -e 's/border_size = [0-9]*/border_size = 2/g' "$CONFIG"
    sed -i '/animations {/,/}/ { /^[[:space:]]*enabled =/ s/true/false/ }' "$CONFIG"
    sed -i '/blur {/,/}/ s/enabled = false/enabled = true/' "$CONFIG"
fi
if [ -f "$ROFI_CONFIG" ]; then
    sed -i 's/border-radius:[^;]*/border-radius: 0/g' "$ROFI_CONFIG"
fi
