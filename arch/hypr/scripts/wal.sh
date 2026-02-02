#!/usr/bin/env bash

WALLPAPER_DIR="${HOME}/Pictures/Wallpapers"
CACHE_DIR="${HOME}/.cache"
CACHE_FILE="${CACHE_DIR}/current_wallpaper"
CACHE_IMAGE="${CACHE_DIR}/current_wallpaper.png"

[[ ! -d "$WALLPAPER_DIR" ]] && notify-send "Wallpaper Selector" "Directory not found!" && exit 1

generate_list() {
    shopt -s nullglob nocaseglob
    for file in "$WALLPAPER_DIR"/*.{png,jpg,jpeg,webp}; do
        [[ -f "$file" ]] || continue
        name="${file##*/}"
        name="${name%.*}"
        printf '%s\0icon\x1f%s\n' "$name" "$file"
    done
}

ROFI_THEME='
window {
    width: 700px;
    height: 600px;
    border-radius: 5px;
}
listview {
    columns: 2;
    spacing: 10px;
    fixed-columns: true;
}
element {
    padding: 10px;
    border-radius: 8px;
}
element-icon {
    size: 90px;
    border-radius: 6px;
}
element-text {
    vertical-align: 0.5;
    horizontal-align: 0.0;
}
element selected {
    background-color: #5294e2;
}
inputbar {
    padding: 12px;
}
prompt {
    padding: 0 10px 0 0;
}
'

selected=$(generate_list | rofi -dmenu -theme ~/.config/rofi/wal.rasi \
    -i \
    -show-icons \
    -p "󰸉 Select Wallpaper" \
    -scroll-method 0 \
    -theme-str "$ROFI_THEME")

[[ -z "$selected" ]] && exit 0

for ext in png jpg jpeg webp PNG JPG JPEG WEBP; do
    wallpaper="${WALLPAPER_DIR}/${selected}.${ext}"
    [[ -f "$wallpaper" ]] && break
done

[[ ! -f "$wallpaper" ]] && notify-send "Error" "File not found" && exit 1

set_wallpaper() {
    if command -v swww &>/dev/null; then
        swww img "$1" --transition-type grow --transition-pos center --transition-duration 1
    elif command -v swaybg &>/dev/null; then
        pkill swaybg
        swaybg -i "$1" -m fill &
    elif command -v hyprctl &>/dev/null && pgrep -x hyprpaper &>/dev/null; then
        hyprctl hyprpaper unload all
        hyprctl hyprpaper preload "$1"
        hyprctl hyprpaper wallpaper ",$1"
    elif command -v feh &>/dev/null; then
        feh --bg-fill "$1"
    elif command -v nitrogen &>/dev/null; then
        nitrogen --set-zoom-fill --save "$1"
    elif command -v gsettings &>/dev/null; then
        gsettings set org.gnome.desktop.background picture-uri "file://$1"
        gsettings set org.gnome.desktop.background picture-uri-dark "file://$1"
    else
        notify-send "Error" "No wallpaper setter found"
        exit 1
    fi
}

set_wallpaper "$wallpaper"
echo "$wallpaper" > "$CACHE_FILE"
magick "$wallpaper" "$CACHE_IMAGE" 2>/dev/null || cp "$wallpaper" "$CACHE_IMAGE"
notify-send -i "$CACHE_IMAGE" "Wallpaper Changed" "$selected"
