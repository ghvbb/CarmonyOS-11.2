#!/bin/bash
HYPR_CONF="$HOME/.config/hypr/hyprland.conf"
ROFI_CONF="$HOME/.config/rofi/config.rasi"
if [ -f "$HYPR_CONF" ]; then
  sed -i -E \
    -e 's/gaps_in = [0-9]*/gaps_in = 2/' \
    -e 's/gaps_out = [0-9]*/gaps_out = 3/' \
    -e 's/border_size = [0-9]*/border_size = 3/' \
    -e 's/rounding = [0-9]*/rounding = 8/' \
    -e 's/enabled = false/enabled = true/' "$HYPR_CONF"
fi
if [ -f "$ROFI_CONF" ]; then
  sed -i 's/border-radius:[^;]*/border-radius: 24px/g' "$ROFI_CONF"
fi
