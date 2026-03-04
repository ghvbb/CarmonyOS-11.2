#!/usr/bin/env bash
#==============================================================================
# clock.sh - Simple & Stable Waybar Clock Module
#==============================================================================

STATE_FILE="/tmp/omarchy_status.json"
SIGNAL_FILE="/tmp/omarchy.signal"
CLOCK_APP="$HOME/.config/clock/clock.py"
ALT_CLOCK_APP="$HOME/.config/hypr/scripts/Clock.py"

# Get current time
get_time() {
    date '+%I:%M %p'
}

# Get current date
get_date() {
    date '+%A, %d %B %Y'
}

# Check if app is running
is_running() {
    pgrep -f "python.*clock\.py" >/dev/null 2>&1 || \
    pgrep -f "python.*try3\.py" >/dev/null 2>&1
}

# Find clock app
find_app() {
    if [[ -f "$CLOCK_APP" ]]; then
        echo "$CLOCK_APP"
    elif [[ -f "$ALT_CLOCK_APP" ]]; then
        echo "$ALT_CLOCK_APP"
    else
        echo ""
    fi
}

# Start app
start_app() {
    local app
    app=$(find_app)
    [[ -z "$app" ]] && return 1
    python3 "$app" &
    disown
}

# Toggle window
toggle_window() {
    if is_running; then
        touch "$SIGNAL_FILE"
    else
        start_app
    fi
}

# Send signal
send_signal() {
    echo "$1" > "$SIGNAL_FILE"
}

# Output status
output() {
    local text tooltip class

    # Check state file
    if [[ -f "$STATE_FILE" ]]; then
        local age=$(($(date +%s) - $(stat -c %Y "$STATE_FILE" 2>/dev/null || echo 0)))
        
        if [[ $age -lt 5 ]]; then
            cat "$STATE_FILE" 2>/dev/null
            return
        fi
    fi

    # Fallback
    text=$(get_time)
    tooltip=$(get_date)
    
    echo "{\"text\": \" $text\", \"tooltip\": \"$tooltip\", \"class\": \"clock\"}"
}

# Main
case "${1:-}" in
    --toggle)
        toggle_window
        ;;
    --open)
        if is_running; then
            send_signal "show"
        else
            start_app
        fi
        ;;
    --pomo)
        is_running || start_app
        send_signal "pomo-toggle"
        ;;
    --pomo-work)
        is_running || start_app
        send_signal "pomo-work"
        ;;
    --pomo-short)
        is_running || start_app
        send_signal "pomo-short"
        ;;
    --pomo-long)
        is_running || start_app
        send_signal "pomo-long"
        ;;
    --pomo-reset)
        send_signal "pomo-reset"
        ;;
    --timer)
        is_running || start_app
        send_signal "timer-toggle"
        ;;
    --timer-reset)
        send_signal "timer-reset"
        ;;
    --stopwatch|--sw)
        is_running || start_app
        send_signal "sw-toggle"
        ;;
    --sw-lap)
        send_signal "sw-lap"
        ;;
    --sw-reset)
        send_signal "sw-reset"
        ;;
    --start)
        start_app
        ;;
    --stop)
        pkill -f "python.*clock\.py" 2>/dev/null
        pkill -f "python.*try3\.py" 2>/dev/null
        rm -f "$STATE_FILE" "$SIGNAL_FILE"
        ;;
    --restart)
        pkill -f "python.*clock\.py" 2>/dev/null
        pkill -f "python.*try3\.py" 2>/dev/null
        sleep 0.5
        start_app
        ;;
    --status)
        echo "Running: $(is_running && echo 'yes' || echo 'no')"
        echo "State file: $(test -f "$STATE_FILE" && echo 'exists' || echo 'missing')"
        ;;
    --help|-h)
        echo "Usage: clock.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  (none)        Output JSON for waybar"
        echo "  --toggle      Toggle window"
        echo "  --pomo        Toggle pomodoro"
        echo "  --timer       Toggle timer"
        echo "  --stopwatch   Toggle stopwatch"
        echo "  --start       Start app"
        echo "  --stop        Stop app"
        echo "  --restart     Restart app"
        ;;
    *)
        output
        ;;
esac
