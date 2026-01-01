#!/bin/bash

# --- Colors & Formatting ---
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Configuration ---
OMGLASS_DIR="OmGlass"
TARGET_DIR="$HOME/.config"
CORE_APPS=("python" "python-gobject" "gtk4" "gtk3" "tty-clock" "cmatrix" "cava" "snapshot")
FOLDERS_REQUIRED=("hypr" "waybar" "walker")

clear
echo -e "${CYAN}${BOLD}==========================================${NC}"
echo -e "${CYAN}${BOLD}       OmGlass Distro Installer           ${NC}"
echo -e "${CYAN}${BOLD}==========================================${NC}"
echo ""

# --- Step 1: Confirmation ---
echo -ne "${BOLD}Install OmGlass inside Omarchy? (y/n): ${NC}"
read -r answer
if [[ "$answer" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "\n${BLUE}>> Initializing OmGlass Setup...${NC}"
    sleep 1
else
    echo -e "\n${RED}>> Installation cancelled.${NC}"
    exit 1
fi

# --- Step 2: Smart Folder Discovery ---
echo -e "${BLUE}Searching for configuration files...${NC}"
sleep 1

if [ -d "$OMGLASS_DIR" ]; then
    echo -e "${GREEN}Found main directory: $OMGLASS_DIR${NC}"
    cd "$OMGLASS_DIR" || exit
else
    echo -e "${YELLOW}Main directory '$OMGLASS_DIR' not found. Checking current folder...${NC}"
    # We stay in current directory and check if required folders exist here
    for folder in "${FOLDERS_REQUIRED[@]}"; do
        if [ ! -d "$folder" ]; then
            echo -e "${RED}Error: Could not find '$folder' folder.${NC}"
            echo -e "Please run this script inside the folder containing your configs."
            exit 1
        fi
    done
    echo -e "${GREEN}Found individual config folders. Continuing...${NC}"
fi

# --- Step 3: Copy Configs with Progress ---
echo -e "\n${PURPLE}${BOLD}[1/3] Copying Configurations${NC}"
total_f=${#FOLDERS_REQUIRED[@]}
i=0
for folder in "${FOLDERS_REQUIRED[@]}"; do
    if [ -d "$folder" ]; then
        # Copy to ~/.config
        cp -r "$folder" "$TARGET_DIR/"
        
        # UI Progress Bar
        ((i++))
        percent=$((i * 100 / total_f))
        bar_size=$((percent / 5))
        bar=$(printf "%${bar_size}s" | tr ' ' '━')
        printf "\r${BLUE}Progress: [%-20s] %d%% - %s${NC}" "$bar" "$percent" "$folder"
        sleep 1.5 # Slow progress as requested
    fi
done
echo -e "\n${GREEN}Configurations deployed to $TARGET_DIR.${NC}"

# --- Step 4: Install Dependencies ---
echo -e "\n${PURPLE}${BOLD}[2/3] Software Dependencies${NC}"
echo -e "${YELLOW}Required: python3, gtk4-python, gtk4, gtk3, tty-clock, cmatrix, cava, gnome-camera${NC}"
echo -ne "${BOLD}Install these apps via yay? (y/n): ${NC}"
read -r app_confirm

if [[ "$app_confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${BLUE}Syncing with yay...${NC}"
    # 'snapshot' is the modern gnome-camera package name
    yay -S --needed python python-gobject gtk4 gtk3 tty-clock cmatrix cava snapshot
else
    echo -e "${RED}Skipping core apps.${NC}"
fi

# --- Step 5: Custom Apps ---
echo -e "\n${PURPLE}${BOLD}[3/3] Customization${NC}"
echo -ne "${BOLD}Would you like to install any additional apps? (y/n): ${NC}"
read -r extra_confirm

if [[ "$extra_confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${CYAN}Enter the package names separated by space:${NC}"
    read -r user_apps
    if [ -n "$user_apps" ]; then
        echo -e "${BLUE}Installing: $user_apps${NC}"
        yay -S --needed $user_apps
    fi
fi

# --- Final Step: Completion & Reboot ---
echo -e "\n${CYAN}${BOLD}==========================================${NC}"
echo -e "${GREEN}${BOLD}        INSTALLATION 100% COMPLETE        ${NC}"
echo -e "${CYAN}${BOLD}==========================================${NC}"
echo ""
echo -e "${YELLOW}${BOLD}The system needs a reboot to apply all OmGlass changes.${NC}"
echo -ne "${BOLD}Reboot now? (y/n): ${NC}"
read -r reboot_answer

if [[ "$reboot_answer" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${RED}Rebooting system in 3 seconds...${NC}"
    sleep 3
    reboot
else
    echo -e "${GREEN}Installation finished. Please remember to reboot later!${NC}"
fi
