#!/bin/bash
#OmGlass Installer V5.0
R='\033[0;31m'
G='\033[0;32m'
B='\033[0;34m'
Y='\033[1;33m'
C='\033[0;36m'
P='\033[0;35m'
W='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

OMGLASS_DIR="OmGlass"
TARGET_DIR="$HOME/.config"
THEME_SRC="themes/omarchy-default"
THEME_DEST_BASE="$HOME/.local/share/omarchy/default/walker/themes"
CORE_APPS=("python" "python-gobject" "gtk4" "gtk3" "python-pip" "tty-clock" "cmatrix" "cava" "snapshot")
FOLDERS_REQUIRED=("hypr" "waybar" "walker")

trap cleanup EXIT INT TERM

cleanup() {
    tput cnorm
    rm -f /tmp/om_spinner_pid
}

hide_cursor() {
    tput civis
}

show_cursor() {
    tput cnorm
}

center_text() {
    local text="$1"
    local width=$(tput cols)
    local padding=$(( (width - ${#text}) / 2 ))
    printf "%${padding}s%s\n" "" "$text"
}

draw_line() {
    local width=$(tput cols)
    printf "${B}%*s${NC}\n" "$width" '' | tr ' ' '─'
}

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    echo -ne "  "
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c] " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

show_header() {
    clear
    echo -e "${B}"
    center_text "   ____  __  ______  ___    __________  _______  __"
    center_text "  / __ \/  |/  /   |/ _ \  / ____/ / / /  _/ \/ /"
    center_text " / / / / /|_/ / /| / /_/ / / /   / /_/ // // / / "
    center_text "/ /_/ / /  / / ___ / _, _// /___/ __  // // /_/ /  "
    center_text "\____/_/  /_/_/  |/_/ |_| \____/_/ /_/___/\____/   "
    echo -e "${NC}"
    echo -e "${C}$(center_text "OMGLASS MANAGER v5.0")${NC}"
    echo ""
    draw_line
    echo ""
}

show_progress() {
    local duration=${1}
    local width=40
    local progress=0
    
    echo -ne "${B}[${NC}"
    for ((i=0; i<=width; i++)); do
        echo -ne "${C}▓${NC}"
        sleep $(bc -l <<< "$duration / $width")
    done
    echo -e "${B}]${NC} ${G}Done!${NC}"
}

check_yay() {
    echo -ne "${Y}   [?] Checking system requirements...${NC}"
    sleep 0.5
    if ! command -v yay &> /dev/null; then
        echo -e "\n\n${R}   [!] Error: 'yay' is not installed.${NC}"
        echo -e "${DIM}       Please install yay to continue.${NC}"
        exit 1
    else
        echo -e "\r${G}   [✓] System requirements met.       ${NC}"
    fi
}

install_step() {
    local step_name="$1"
    local command="$2"
    
    echo -ne "${P}   :: $step_name...${NC}"
    eval "$command" > /dev/null 2>&1 &
    local pid=$!
    spinner $pid
    wait $pid
    
    if [ $? -eq 0 ]; then
        echo -e "${G}Success${NC}"
    else
        echo -e "${R}Failed${NC}"
    fi
}

hide_cursor
show_header

check_yay
echo ""

echo -e "${W}   Select an operation:${NC}"
echo -e "${B}   ┌──────────────────────────────────────────┐${NC}"
echo -e "${B}   │${NC} ${G}1.${NC} Install OmGlass                        ${B}│${NC}"
echo -e "${B}   │${NC} ${C}2.${NC} Update Omarchy                         ${B}│${NC}"
echo -e "${B}   │${NC} ${P}3.${NC} Upgrade OmGlass                        ${B}│${NC}"
echo -e "${B}   │${NC} ${R}4.${NC} Exit                                   ${B}│${NC}"
echo -e "${B}   └──────────────────────────────────────────┘${NC}"
echo ""
echo -ne "${BOLD}   >> Select Option [1-4]: ${NC}"
show_cursor
read -r main_choice
hide_cursor

case $main_choice in
    1) ACTION="Installing OmGlass"; BACKUP_REQ=true ;;
    2) ACTION="Updating Omarchy"; BACKUP_REQ=false ;;
    3) ACTION="Upgrading OmGlass"; BACKUP_REQ=true ;;
    4) echo -e "\n   ${Y}Goodbye!${NC}"; exit 0 ;;
    *) echo -e "\n   ${R}Invalid option.${NC}"; exit 1 ;;
esac

echo ""
draw_line
echo -e "\n${B}   >> $ACTION...${NC}\n"

if [ -d "$OMGLASS_DIR" ]; then
    cd "$OMGLASS_DIR" || exit
fi

BACKUP_ENABLED="no"
if [ "$BACKUP_REQ" = true ]; then
    echo -ne "${Y}   [?] Create backup of existing config? (y/n): ${NC}"
    show_cursor
    read -r backup_ans
    hide_cursor
    if [[ "$backup_ans" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        BACKUP_ENABLED="yes"
    fi
fi

echo ""
echo -e "${C}${BOLD}   Phase 1: Configuration & Assets${NC}"

mkdir -p "$HOME/.local/share/applications"

for folder in "${FOLDERS_REQUIRED[@]}"; do
    if [ "$BACKUP_ENABLED" == "yes" ] && [ -d "$TARGET_DIR/$folder" ]; then
        install_step "Backing up $folder" "rm -rf $TARGET_DIR/${folder}.bak && mv $TARGET_DIR/$folder $TARGET_DIR/${folder}.bak"
    fi

    if [ -d "$folder" ]; then
        install_step "Syncing $folder config" "cp -r $folder $TARGET_DIR/"
    fi
done

if [ -d "$THEME_SRC" ]; then
    install_step "Preparing theme directories" "mkdir -p $THEME_DEST_BASE"
    install_step "Installing Omarchy Default Theme" "rm -rf $THEME_DEST_BASE/omarchy-default && cp -r $THEME_SRC $THEME_DEST_BASE/"
else
    echo -e "${Y}   [!] Warning: Theme source '$THEME_SRC' not found.${NC}"
fi

echo ""
echo -ne "${BOLD}   [?] Install GUI Applications & Dependencies? (y/n): ${NC}"
show_cursor
read -r app_confirm
hide_cursor

if [[ "$app_confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "\n${C}${BOLD}   Phase 2: System Integration${NC}"
    
    echo -ne "${P}   :: Installing Core Packages (This may take time)... ${NC}"
    yay -S --needed --noconfirm "${CORE_APPS[@]}" > /dev/null 2>&1 &
    spinner $!
    echo -e "${G}Done${NC}"
    
    if [ -f "omarchy-control.py" ]; then
        install_step "Installing Control Script" "cp omarchy-control.py $HOME/.config/hypr/ && chmod +x $HOME/.config/hypr/omarchy-control.py"
        
        cat <<EOF > "$HOME/.local/share/applications/omarchy-settings.desktop"
[Desktop Entry]
Type=Application
Name=Omarchy Settings
Comment=Configuration Manager
Exec=python3 $HOME/.config/hypr/omarchy-control.py
Icon=preferences-system
Categories=Settings;System;
Terminal=false
EOF
        install_step "Registering Desktop Entry" "update-desktop-database $HOME/.local/share/applications"
    fi
fi

echo ""
draw_line
echo -e "\n${G}${BOLD}$(center_text "INSTALLATION v5.0 COMPLETE")${NC}"
echo -e "${DIM}$(center_text "Your OmGlass system is ready")${NC}\n"

echo -ne "${B}   Would you like to reboot now? (y/n): ${NC}"
show_cursor
read -r reboot_answer
hide_cursor

if [[ "$reboot_answer" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "\n${R}   System is rebooting...${NC}"
    show_progress 2
    reboot
else
    echo -e "\n${G}   Okay. Please restart your session manually.${NC}"
    exit 0
fi
