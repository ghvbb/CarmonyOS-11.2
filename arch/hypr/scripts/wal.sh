#!/usr/bin/env bash
# ~/scripts/wallpaper-selector.sh
# Ultra-fast Wallpaper Selector + Color Extractor
# MD3 Google Material Style

set -euo pipefail

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
WALLPAPER_DIR="${WALLPAPER_DIR:-$HOME/Pictures/Wallpapers}"
CACHE_DIR="${HOME}/.cache"
COLOR_DIR="${CACHE_DIR}/colors"
CACHE_FILE="${CACHE_DIR}/current_wallpaper"
CACHE_IMAGE="${CACHE_DIR}/current_wallpaper.png"

# Create directories
mkdir -p "$COLOR_DIR"

# Validate wallpaper directory
if [[ ! -d "$WALLPAPER_DIR" ]]; then
    notify-send -u critical "Wallpaper Selector" "Directory not found: $WALLPAPER_DIR"
    exit 1
fi

# ─────────────────────────────────────────────
# Ultra-Fast Color Extraction (< 0.2s)
# Uses ImageMagick with aggressive downscaling
# ─────────────────────────────────────────────
extract_colors() {
    local wallpaper="$1"
    local tmp_resized="/tmp/.wal_thumb_$$.png"

    # Step 1: Aggressively downscale to 50x50 for speed (< 0.05s)
    magick "$wallpaper" -resize 50x50! -depth 8 "$tmp_resized" 2>/dev/null

    # Step 2: Extract 16 dominant colors using quantize (< 0.1s)
    local raw_colors
    raw_colors=$(magick "$tmp_resized" \
        -colors 16 \
        -unique-colors \
        -depth 8 \
        txt:- 2>/dev/null | grep -oP '#[0-9A-Fa-f]{6}' | head -16)

    rm -f "$tmp_resized"

    # Parse into array
    local -a colors=()
    while IFS= read -r c; do
        [[ -n "$c" ]] && colors+=("$c")
    done <<< "$raw_colors"

    # Pad to 16 colors if needed
    local defaults=(
        "#1a1b26" "#f7768e" "#9ece6a" "#e0af68"
        "#7aa2f7" "#bb9af7" "#7dcfff" "#c0caf5"
        "#414868" "#f7768e" "#9ece6a" "#e0af68"
        "#7aa2f7" "#bb9af7" "#7dcfff" "#c0caf5"
    )
    while [[ ${#colors[@]} -lt 16 ]]; do
        colors+=("${defaults[${#colors[@]}]}")
    done

    # Sort: darkest first for background, lightest for foreground
    mapfile -t sorted < <(
        for c in "${colors[@]}"; do
            # Calculate luminance
            r=$((16#${c:1:2}))
            g=$((16#${c:3:2}))
            b=$((16#${c:5:2}))
            lum=$(( r * 299 + g * 587 + b * 114 ))
            echo "$lum $c"
        done | sort -n | awk '{print $2}'
    )

    # Assign semantic color roles
    local bg="${sorted[0]}"
    local fg="${sorted[14]}"
    local cursor="${sorted[12]}"

    # Generate darker background variant
    local bg_r=$((16#${bg:1:2}))
    local bg_g=$((16#${bg:3:2}))
    local bg_b=$((16#${bg:5:2}))
    local bg_alt
    bg_alt=$(printf '#%02x%02x%02x' \
        $(( bg_r > 20 ? bg_r - 20 : 0 )) \
        $(( bg_g > 20 ? bg_g - 20 : 0 )) \
        $(( bg_b > 20 ? bg_b - 20 : 0 )))

    # Generate surface color (slightly lighter than bg)
    local surface
    surface=$(printf '#%02x%02x%02x' \
        $(( bg_r + 30 > 255 ? 255 : bg_r + 30 )) \
        $(( bg_g + 30 > 255 ? 255 : bg_g + 30 )) \
        $(( bg_b + 30 > 255 ? 255 : bg_b + 30 )))

    # Map to color0-color15
    local color0="$bg"
    local color1="${sorted[2]}"
    local color2="${sorted[4]}"
    local color3="${sorted[6]}"
    local color4="${sorted[8]}"
    local color5="${sorted[10]}"
    local color6="${sorted[12]}"
    local color7="$fg"
    local color8="$bg_alt"
    local color9="${sorted[3]}"
    local color10="${sorted[5]}"
    local color11="${sorted[7]}"
    local color12="${sorted[9]}"
    local color13="${sorted[11]}"
    local color14="${sorted[13]}"
    local color15="${sorted[15]:-$fg}"

    # ─────────────────────────────────────────
    # Generate: colors.conf (Kitty)
    # ─────────────────────────────────────────
    cat > "${COLOR_DIR}/colors.conf" << KITTY
# Kitty Color Configuration
# Auto-generated from wallpaper
# $(date '+%Y-%m-%d %H:%M:%S')

# Special
foreground              ${fg}
background              ${color0}
background_opacity      0.95
selection_foreground    ${color0}
selection_background    ${fg}
cursor                  ${cursor}
cursor_text_color       ${color0}
url_color               ${color4}

# Normal Colors
color0                  ${color0}
color1                  ${color1}
color2                  ${color2}
color3                  ${color3}
color4                  ${color4}
color5                  ${color5}
color6                  ${color6}
color7                  ${color7}

# Bright Colors
color8                  ${color8}
color9                  ${color9}
color10                 ${color10}
color11                 ${color11}
color12                 ${color12}
color13                 ${color13}
color14                 ${color14}
color15                 ${color15}

# Tab Bar
active_tab_foreground   ${color0}
active_tab_background   ${color4}
inactive_tab_foreground ${color7}
inactive_tab_background ${color8}
KITTY

    # ─────────────────────────────────────────
    # Generate: colors2.conf (Hyprland)
    # ─────────────────────────────────────────
    # Strip '#' for Hyprland hex format
    local h_bg="${color0//#/}"
    local h_fg="${fg//#/}"
    local h_c1="${color1//#/}"
    local h_c2="${color2//#/}"
    local h_c3="${color3//#/}"
    local h_c4="${color4//#/}"
    local h_c5="${color5//#/}"
    local h_c6="${color6//#/}"
    local h_surface="${surface//#/}"
    local h_bgalt="${bg_alt//#/}"

    cat > "${COLOR_DIR}/colors2.conf" << HYPR
# Hyprland Color Configuration
# Auto-generated from wallpaper
# $(date '+%Y-%m-%d %H:%M:%S')

\$background    = rgb(${h_bg})
\$backgroundAlt = rgb(${h_bgalt})
\$surface       = rgb(${h_surface})
\$foreground    = rgb(${h_fg})

\$color0  = rgb(${h_bg})
\$color1  = rgb(${h_c1})
\$color2  = rgb(${h_c2})
\$color3  = rgb(${h_c3})
\$color4  = rgb(${h_c4})
\$color5  = rgb(${h_c5})
\$color6  = rgb(${h_c6})
\$color7  = rgb(${h_fg})

\$color8  = rgb(${color8//#/})
\$color9  = rgb(${color9//#/})
\$color10 = rgb(${color10//#/})
\$color11 = rgb(${color11//#/})
\$color12 = rgb(${color12//#/})
\$color13 = rgb(${color13//#/})
\$color14 = rgb(${color14//#/})
\$color15 = rgb(${color15//#/})

# Border colors
\$activeBorder   = rgb(${h_c4})
\$inactiveBorder = rgb(${h_bgalt})

# Shadow
\$shadow = rgba(${h_bg}cc)
HYPR

    # ─────────────────────────────────────────
    # Generate: colors.css (Waybar)
    # ─────────────────────────────────────────
    # Calculate RGBA variants
    local bg_r_f bg_g_f bg_b_f
    bg_r_f=$((16#${h_bg:0:2}))
    bg_g_f=$((16#${h_bg:2:2}))
    bg_b_f=$((16#${h_bg:4:2}))

    cat > "${COLOR_DIR}/colors.css" << WAYBAR
/* Waybar Color Configuration */
/* Auto-generated from wallpaper */
/* $(date '+%Y-%m-%d %H:%M:%S') */

@define-color background ${color0};
@define-color backgroundAlt ${bg_alt};
@define-color surface ${surface};
@define-color foreground ${fg};

@define-color color0  ${color0};
@define-color color1  ${color1};
@define-color color2  ${color2};
@define-color color3  ${color3};
@define-color color4  ${color4};
@define-color color5  ${color5};
@define-color color6  ${color6};
@define-color color7  ${color7};

@define-color color8  ${color8};
@define-color color9  ${color9};
@define-color color10 ${color10};
@define-color color11 ${color11};
@define-color color12 ${color12};
@define-color color13 ${color13};
@define-color color14 ${color14};
@define-color color15 ${color15};

/* Transparency variants */
@define-color backgroundAlpha rgba(${bg_r_f}, ${bg_g_f}, ${bg_b_f}, 0.85);
@define-color backgroundAlpha70 rgba(${bg_r_f}, ${bg_g_f}, ${bg_b_f}, 0.70);
@define-color backgroundAlpha50 rgba(${bg_r_f}, ${bg_g_f}, ${bg_b_f}, 0.50);

/* Semantic colors */
@define-color primary ${color4};
@define-color secondary ${color5};
@define-color accent ${color6};
@define-color warning ${color3};
@define-color error ${color1};
@define-color success ${color2};
WAYBAR

    # ─────────────────────────────────────────
    # Generate: colors.rasi (Rofi)
    # ─────────────────────────────────────────
    cat > "${COLOR_DIR}/colors.rasi" << ROFI
/**
 * Rofi Color Configuration
 * Auto-generated from wallpaper
 * $(date '+%Y-%m-%d %H:%M:%S')
 */

* {
    background:       ${color0};
    background-alt:   ${bg_alt};
    surface:          ${surface};
    foreground:       ${fg};
    primary:          ${color4};
    secondary:        ${color5};
    accent:           ${color6};
    urgent:           ${color1};
    success:          ${color2};
    warning:          ${color3};

    color0:  ${color0};
    color1:  ${color1};
    color2:  ${color2};
    color3:  ${color3};
    color4:  ${color4};
    color5:  ${color5};
    color6:  ${color6};
    color7:  ${color7};
    color8:  ${color8};
    color9:  ${color9};
    color10: ${color10};
    color11: ${color11};
    color12: ${color12};
    color13: ${color13};
    color14: ${color14};
    color15: ${color15};

    selected-background: ${color4}40;
    selected-foreground: ${fg};
    active-background:   ${color2}30;
    urgent-background:   ${color1}30;
}
ROFI

    echo "  Colors extracted: bg=${color0} fg=${fg} accent=${color4}"
}

# ─────────────────────────────────────────────
# Reload Services (parallel for speed)
# ─────────────────────────────────────────────
reload_services() {
    echo "Reloading services..."

    # Kill waybar and rofi instantly
    pkill -x waybar 2>/dev/null || true
    pkill -x rofi 2>/dev/null || true

    # Reload kitty (all instances)
    if pgrep -x kitty &>/dev/null; then
        pkill -USR1 kitty 2>/dev/null || true
    fi

    # Reload Hyprland config
    if command -v hyprctl &>/dev/null; then
        hyprctl reload &>/dev/null &
    fi

    # Small delay for Hyprland to process
    sleep 0.1

    # Restart waybar
    if command -v waybar &>/dev/null; then
        waybar &>/dev/null &
        disown
    fi

    echo "  Services reloaded"
}

# ─────────────────────────────────────────────
# Set Wallpaper
# ─────────────────────────────────────────────
set_wallpaper() {
    local wp="$1"
    if command -v swww &>/dev/null; then
        # Ensure swww daemon is running
        swww query &>/dev/null || swww-daemon &>/dev/null &
        sleep 0.1
        swww img "$wp" \
            --transition-type grow \
            --transition-pos center \
            --transition-duration 1 \
            --transition-fps 60 &
    elif command -v swaybg &>/dev/null; then
        pkill swaybg 2>/dev/null || true
        swaybg -i "$wp" -m fill &>/dev/null &
        disown
    elif command -v hyprctl &>/dev/null && pgrep -x hyprpaper &>/dev/null; then
        hyprctl hyprpaper unload all &>/dev/null
        hyprctl hyprpaper preload "$wp" &>/dev/null
        hyprctl hyprpaper wallpaper ",$wp" &>/dev/null
    elif command -v feh &>/dev/null; then
        feh --bg-fill "$wp"
    elif command -v nitrogen &>/dev/null; then
        nitrogen --set-zoom-fill --save "$wp"
    elif command -v gsettings &>/dev/null; then
        gsettings set org.gnome.desktop.background picture-uri "file://$wp"
        gsettings set org.gnome.desktop.background picture-uri-dark "file://$wp"
    else
        notify-send -u critical "Error" "No wallpaper setter found"
        return 1
    fi
}

# ─────────────────────────────────────────────
# Generate Wallpaper List for Rofi
# ─────────────────────────────────────────────
generate_list() {
    shopt -s nullglob nocaseglob
    local files=("$WALLPAPER_DIR"/*.{png,jpg,jpeg,webp})
    for file in "${files[@]}"; do
        [[ -f "$file" ]] || continue
        local name="${file##*/}"
        name="${name%.*}"
        printf '%s\0icon\x1f%s\n' "$name" "$file"
    done
}

# ─────────────────────────────────────────────
# MD3 Material Design Rofi Theme
# ─────────────────────────────────────────────
ROFI_THEME='
configuration {
    show-icons:     true;
    icon-theme:     "Papirus-Dark";
    drun-display-format: "{name}";
}

* {
    font: "Google Sans Medium 11";
}

window {
    width:              720px;
    height:             620px;
    border-radius:      28px;
    border:             2px solid;
    border-color:       #79747E40;
    background-color:   #1C1B1Fee;
    transparency:       "real";
    padding:            0;
}

mainbox {
    background-color:   transparent;
    children:           [ inputbar, message, listview ];
    spacing:            0;
    padding:            8px;
}

inputbar {
    background-color:   #2B2930;
    border-radius:      24px;
    padding:            14px 20px;
    margin:             8px 8px 12px 8px;
    children:           [ prompt, entry ];
    spacing:            12px;
}

prompt {
    background-color:   transparent;
    text-color:         #D0BCFF;
    font:               "Material Symbols Rounded 13";
    vertical-align:     0.5;
}

entry {
    background-color:   transparent;
    text-color:         #E6E1E5;
    placeholder:        "Search wallpapers...";
    placeholder-color:  #938F99;
    vertical-align:     0.5;
    cursor:             text;
}

message {
    background-color:   transparent;
    padding:            4px 16px;
}

textbox {
    background-color:   transparent;
    text-color:         #CAC4D0;
}

listview {
    background-color:   transparent;
    columns:            3;
    lines:              3;
    spacing:            8px;
    padding:            4px 8px;
    fixed-columns:      true;
    fixed-height:       true;
    cycle:              true;
    dynamic:            true;
    scrollbar:          false;
}

element {
    background-color:   #2B293080;
    border-radius:      20px;
    padding:            12px;
    orientation:        vertical;
    spacing:            8px;
    cursor:             pointer;
}

element normal.normal {
    background-color:   #2B293060;
    text-color:         #E6E1E5;
}

element normal.active {
    background-color:   #D0BCFF20;
    text-color:         #D0BCFF;
}

element selected.normal {
    background-color:   #D0BCFF30;
    text-color:         #D0BCFF;
    border:             2px solid;
    border-color:       #D0BCFF60;
}

element selected.active {
    background-color:   #D0BCFF40;
    text-color:         #D0BCFF;
}

element alternate.normal {
    background-color:   #2B293060;
    text-color:         #E6E1E5;
}

element-icon {
    background-color:   transparent;
    size:               110px;
    border-radius:      16px;
    cursor:             inherit;
    horizontal-align:   0.5;
}

element-text {
    background-color:   transparent;
    text-color:         inherit;
    horizontal-align:   0.5;
    vertical-align:     0.5;
    font:               "Google Sans Medium 10";
    cursor:             inherit;
}
'

# ─────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────
main() {
    local start_time
    start_time=$(date +%s%N)

    # Show Rofi selector
    local selected
    selected=$(generate_list | rofi -dmenu \
        -i \
        -show-icons \
        -p "󰸉" \
        -mesg "  Select a wallpaper to apply" \
        -scroll-method 0 \
        -theme-str "$ROFI_THEME" \
        2>/dev/null) || exit 0

    [[ -z "$selected" ]] && exit 0

    # Find the actual file
    local wallpaper=""
    for ext in png jpg jpeg webp PNG JPG JPEG WEBP; do
        wallpaper="${WALLPAPER_DIR}/${selected}.${ext}"
        [[ -f "$wallpaper" ]] && break
        wallpaper=""
    done

    if [[ -z "$wallpaper" || ! -f "$wallpaper" ]]; then
        notify-send -u critical "Error" "Wallpaper file not found: ${selected}"
        exit 1
    fi

    echo "Selected: $wallpaper"

    # Run everything in parallel for maximum speed
    # Phase 1: Cache + Colors (parallel)
    {
        echo "$wallpaper" > "$CACHE_FILE"
        magick "$wallpaper" -resize 800x800 -quality 90 "$CACHE_IMAGE" 2>/dev/null \
            || cp "$wallpaper" "$CACHE_IMAGE"
    } &
    local pid_cache=$!

    # Phase 2: Extract colors (fast - runs on small image)
    extract_colors "$wallpaper" &
    local pid_colors=$!

    # Phase 3: Set wallpaper (runs immediately)
    set_wallpaper "$wallpaper" &
    local pid_wall=$!

    # Wait for colors before reloading services
    wait "$pid_colors" 2>/dev/null
    wait "$pid_cache" 2>/dev/null

    # Phase 4: Reload all services
    reload_services

    # Wait for wallpaper to finish
    wait "$pid_wall" 2>/dev/null

    # Calculate elapsed time
    local end_time
    end_time=$(date +%s%N)
    local elapsed=$(( (end_time - start_time) / 1000000 ))

    notify-send -i "$CACHE_IMAGE" \
        "Wallpaper Applied" \
        "${selected}\nColors extracted & applied in ${elapsed}ms" \
        -t 3000

    echo "Total time: ${elapsed}ms"
}

main "$@"
