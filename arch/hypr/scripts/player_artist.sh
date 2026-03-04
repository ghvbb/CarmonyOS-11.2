#!/bin/bash
# Output artist name (uppercase) or nothing if no media

artist=$(playerctl metadata --format '{{ artist }}' 2>/dev/null)
status=$(playerctl status 2>/dev/null)

if [[ -z "$status" || -z "$artist" ]]; then
    exit 0
fi

# Convert to uppercase and print
echo "$artist" | tr '[:lower:]' '[:upper:]'
