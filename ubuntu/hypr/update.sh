#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UI="$SCRIPT_DIR/ui.sh"

if [ -f /etc/arch-release ]; then
    CHECK_CMD="pacman -Qu"
    UPDATE_CMD="sudo pacman -Su --noconfirm"
    HAS_UPDATES=$(pacman -Qu 2>/dev/null | wc -l)
elif [ -f /etc/fedora-release ]; then
    CHECK_CMD="dnf check-update"
    UPDATE_CMD="sudo dnf upgrade -y"
    HAS_UPDATES=$(dnf check-update > /dev/null 2>&1; echo $?)
elif [ -f /etc/os-release ] && grep -qi ubuntu /etc/os-release; then
    CHECK_CMD="apt list --upgradable"
    UPDATE_CMD="sudo apt update && sudo apt upgrade -y"
    HAS_UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
else
    exit 0
fi

if [ "$HAS_UPDATES" = "0" ] || [ "$HAS_UPDATES" = "100" ]; then
    exit 0
fi

if command -v kitty >/dev/null; then
    kitty bash -c "
        clear
        bash \"$UI\"
        echo
        echo '!!! OmGlass Packages Had To Update !!!'
        echo
        $UPDATE_CMD
        echo
        read -p 'Press Enter to close'
    "
elif command -v gnome-terminal >/dev/null; then
    gnome-terminal -- bash -c "
        clear
        bash \"$UI\"
        echo
        echo '!!! OmGlass Packages Had To Update !!!'
        echo
        $UPDATE_CMD
        echo
        read -p 'Press Enter to close'
    "
else
    bash \"$UI\"
    echo
    echo '!!! OmGlass Packages Had To Update !!!'
    echo
    $UPDATE_CMD
fi
