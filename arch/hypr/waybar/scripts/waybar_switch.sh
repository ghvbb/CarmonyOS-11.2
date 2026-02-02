#!/bin/bash

WAYBAR_DIR="$HOME/.config/waybar"
THEMES_DIR="$WAYBAR_DIR/themes"

# 1. Define available themes
# You can add more folders to ~/.config/waybar/themes/ and they will show up automatically
THEMES=$(ls "$THEMES_DIR")

# 2. Open Walker in dmenu mode to select a theme
# We use --dmenu to tell Walker to show our list instead of apps
CHOICE=$(echo -e "$THEMES" | rofi -dmenu)

# 3. Check if the user actually picked something or just closed the menu
if [ -z "$CHOICE" ]; then
    echo "No theme selected. Exiting."
    exit 0
fi

echo "Switching to $CHOICE..."

# 4. Apply the symlinks
ln -sf "$THEMES_DIR/$CHOICE/config.jsonc" "$WAYBAR_DIR/config.jsonc"
ln -sf "$THEMES_DIR/$CHOICE/style.css" "$WAYBAR_DIR/style.css"

# 5. Reload Waybar
pkill waybar
sleep 0.2
waybar &
