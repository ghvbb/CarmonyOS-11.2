#!/bin/bash

CONFIG="$HOME/.config/hypr/hyprland.conf"
ROFI_CONFIG="$HOME/.config/rofi/config.rasi"

if [ -f "$CONFIG" ]; then
    sed -i \
        -e 's/gaps_in = [0-9]*/gaps_in = 2/' \
        -e 's/gaps_out = [0-9]*/gaps_out = 1/' \
        -e 's/border_size = [0-9]*/border_size = 2/' \
        -e 's/enabled = false/enabled = true/' \
        -e 's/rounding = [0-9]*/rounding = 3/' "$CONFIG"
fi

if [ -f "$ROFI_CONFIG" ]; then
    sed -i 's/border-radius:[^;]*/border-radius: 10/g' "$ROFI_CONFIG"
fi
