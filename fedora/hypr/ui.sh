#!/bin/bash

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

hide_cursor() { tput civis; }
show_cursor() { tput cnorm; }

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
    local delay=0.08
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while :; do
        local temp=${spinstr#?}
        printf "${C}[${P}%c${C}]${NC}" "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b"
    done
}

clear
hide_cursor

echo -e "${B}"
center_text "    ____  __  ______  ___    __________  _______  __"
center_text "   / __ \/  |/  / __ \/ _ \  / ____/ / / /  _/ \/ /"
center_text "  / / / / /|_/ / /| / /_/ / / /   / /_/ // // / / "
center_text " / /_/ / /  / / ___ / _, _// /___/ __  // // /_/ /"
center_text " \____/_/  /_/_/  |_/_/ |_| \____/_/ /_/___/\____/"
echo -e "${NC}"

echo -e "${W}$(center_text "OMGLASS UPDATE ENGINE v6.2")${NC}"
echo
draw_line
echo

center_text "${Y}${BOLD}System Integrity Check In Progress${NC}"
echo
center_text "${DIM}Synchronizing package layers across OmGlass${NC}"
echo
center_text "${C}This window will close automatically if no updates are found${NC}"
echo
draw_line
echo

center_text "${P}Monitoring repositories...${NC}"
echo
center_text "${C}Awaiting signal from update core${NC}"
echo

spinner &
SPIN_PID=$!

sleep 2

kill $SPIN_PID >/dev/null 2>&1
wait $SPIN_PID 2>/dev/null

echo -e "\n"
draw_line
echo
center_text "${G}${BOLD}Updater Ready${NC}"
center_text "${DIM}Handing control to update process${NC}"
echo

show_cursor
