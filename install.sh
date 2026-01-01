#!/bin/bash

# --- Colors & Formatting ---
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Configuration ---
SOURCE_DIR="OmGlass"
TARGET_DIR="$HOME/.config"
FOLDERS=("hypr" "waybar" "walker")

clear
echo -e "${CYAN}${BOLD}==========================================${NC}"
echo -e "${CYAN}${BOLD}       OmGlass Distro Installer           ${NC}"
echo -e "${CYAN}${BOLD}==========================================${NC}"
echo ""

# --- Step 1: Confirmation ---
echo -ne "${BOLD}Install OmGlass inside Omarchy? (y/n): ${NC}"
read -r answer

if [[ "$answer" != "${answer#[Yy]}" ]]; then
    echo -e "\n${BLUE}>> Starting Installation...${NC}"
else
    echo -e "\n${RED}>> Installation cancelled.${NC}"
    exit 1
fi

# --- Step 2: Directory Check ---
if [ -d "$SOURCE_DIR" ]; then
    cd "$SOURCE_DIR" || exit
else
    echo -e "${RED}Error: Directory '$SOURCE_DIR' not found!${NC}"
    exit 1
fi

# --- Step 3: Copy with Progress Bar ---
total=${#FOLDERS[@]}
i=0

echo -e "${BLUE}Copying configuration files to $TARGET_DIR...${NC}"

for folder in "${FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        # Actual copy command
        cp -r "$folder" "$TARGET_DIR/"
        
        # Calculate progress
        ((i++))
        percent=$((i * 100 / total))
        
        # Create a visual bar [#####     ]
        bar_size=$((percent / 5))
        bar=$(printf "%${bar_size}s" | tr ' ' '#')
        spaces=$(printf "%$((20 - bar_size))s")
        
        # Print the progress line (\r keeps it on the same line)
        printf "\r${GREEN}[%-20s] %d%% - Processing: %s${NC}" "$bar" "$percent" "$folder"
        
        sleep 0.4 # Just for visual effect so it doesn't blink too fast
    fi
done

# --- Step 4: Finish ---
echo -e "\n\n${GREEN}${BOLD}SUCCESS!${NC}"
echo -e "OmGlass has been installed in ${BOLD}$TARGET_DIR${NC}"
echo -e "Restart Hyprland to apply changes."
echo -e "${CYAN}==========================================${NC}"
