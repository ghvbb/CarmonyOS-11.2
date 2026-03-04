#!/bin/bash
# Detect Caps Lock using multiple methods (no xset required)

# Method 1: check via xset if installed
if command -v xset &>/dev/null; then
    xset q | grep -q 'Caps Lock: *on' && echo "󰪛 CAPS LOCK" && exit 0
fi

# Method 2: check sysfs (common for backlit keyboards)
for led in /sys/class/leds/input*::capslock/brightness; do
    if [[ -f "$led" && "$(cat "$led")" -eq 1 ]]; then
        echo "󰪛 CAPS LOCK"
        exit 0
    fi
done

# If none detected, output nothing
exit 0
