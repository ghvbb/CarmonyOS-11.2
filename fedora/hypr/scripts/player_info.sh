#!/bin/bash
# Outputs formatted media info for hyprlock

status=$(playerctl status 2>/dev/null)
artist=$(playerctl metadata --format '{{ artist }}' 2>/dev/null)
title=$(playerctl metadata --format '{{ title }}' 2>/dev/null)

# If nothing is playing, output nothing (label becomes invisible)
if [[ -z "$status" ]]; then
    exit 0
fi

# Choose icon based on playback status
case "$status" in
    "Playing") icon="󰐊" ;;
    "Paused")  icon="󰏤" ;;
    *)         icon="󰝚" ;;
esac

# Build the display string
if [[ -n "$artist" && -n "$title" ]]; then
    text="$artist – $title"
elif [[ -n "$title" ]]; then
    text="$title"
elif [[ -n "$artist" ]]; then
    text="$artist"
else
    text="Unknown track"
fi

# Truncate to fit (adjust max_len as needed)
max_len=50
if [[ ${#text} -gt $max_len ]]; then
    text="${text:0:$max_len-3}..."
fi

echo "$icon $text"
