#!/bin/bash
# Output truncated title (max 40 chars) or nothing if no media

title=$(playerctl metadata --format '{{ title }}' 2>/dev/null)
status=$(playerctl status 2>/dev/null)

if [[ -z "$status" || -z "$title" ]]; then
    exit 0
fi

# Truncate with ellipsis
max_len=40
if [[ ${#title} -gt $max_len ]]; then
    echo "${title:0:$max_len-3}..."
else
    echo "$title"
fi
