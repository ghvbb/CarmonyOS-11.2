#!/bin/bash

SRC=""
DST="/usr/share/sddm/themes/sugar-candy/Backgrounds/wal.jpg"

while true; do
    CUR=$(swww query | awk -F'image: ' '/image:/ {print $2}')

    if [[ -n "$CUR" && "$CUR" != "$SRC" && -f "$CUR" ]]; then
        cp -f "$CUR" "$DST"
        SRC="$CUR"
    fi

    sleep 5
done

