#!/bin/bash

WAYBAR_DIR="$HOME/.config/waybar"
THEMES_DIR="$WAYBAR_DIR/themes"

THEMES=$(ls "$THEMES_DIR")

CHOICE=$(echo -e "$THEMES" | rofi -dmenu -p "Select Theme:")

if [ -z "$CHOICE" ]; then
    exit 0
fi

ln -sf "$THEMES_DIR/$CHOICE/config.jsonc" "$WAYBAR_DIR/config.jsonc"
ln -sf "$THEMES_DIR/$CHOICE/style.css" "$WAYBAR_DIR/style.css"

for script in "$THEMES_DIR/$CHOICE"/*.sh; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        bash "$script" &
    fi
done

pkill waybar
sleep 0.2
waybar &
