#!/bin/bash

# --- Settings ---
CENTER_TEXT="CarmonyOS - for all of the time"
COLOR_CYAN="\e[1;36m"
COLOR_RESET="\e[0m"

# --- Cleanup on Exit ---
cleanup() {
    tput cnorm # Show cursor
    kill $(jobs -p) 2>/dev/null
    clear
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- Function: Get Media Info ---
get_info() {
    if command -v playerctl >/dev/null 2>&1; then
        if [ "$(playerctl status 2>/dev/null)" = "Playing" ]; then
            # Get metadata
            local title=$(playerctl metadata title 2>/dev/null)
            local artist=$(playerctl metadata artist 2>/dev/null)
            
            # If it's a video (no artist), show video icon, else music icon
            if [ -z "$artist" ]; then
                echo "🎬 $title"
            else
                echo "🎵 $title — $artist"
            fi
            return
        fi
    fi
    echo "$CENTER_TEXT"
}

# --- Function: The Overlay Engine ---
# This runs cmatrix and forces the text to stay on top
run_sequence() {
    local duration=$1
    local show_cmatrix=$2 # true or false
    
    if [ "$show_cmatrix" = true ]; then
        cmatrix -b -u 10 & # Run in background, speed 10
        local PID=$!
    fi

    local start_time=$(date +%s)
    while [ $(( $(date +%s) - start_time )) -lt $duration ]; do
        local info=$(get_info)
        local cols=$(tput cols)
        local lines=$(tput lines)
        local x=$(( (cols - ${#info}) / 2 ))
        local y=$(( lines / 2 ))

        # Move to center and print over the matrix
        tput cup $y $x
        echo -ne "${COLOR_CYAN}${info}${COLOR_RESET}"
        
        sleep 0.5
    done

    if [ "$show_cmatrix" = true ]; then
        kill $PID 2>/dev/null
        wait $PID 2>/dev/null
    fi
    clear
}

# ==========================
#      MAIN SEQUENCE
# ==========================

# Prepare Terminal
clear
tput civis # Hide cursor

# 1. CMatrix for 20s with Overlay
run_sequence 20 true

# 2. Pfetch for 5s (Centering pfetch is tricky, so we show it normally)
if command -v pfetch >/dev/null; then pfetch; else neofetch 2>/dev/null || echo "CarmonyOS System Info"; fi
sleep 5
clear

# 3. CMatrix for 30s with Overlay
run_sequence 30 true

# 4. Final Loop (Infinite)
while true; do
    run_sequence 1 false
done
