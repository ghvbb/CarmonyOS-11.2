#!/bin/bash
#OmGlass 6.2  Bro , install easy go lazy ! 

set -e

CONF="$HOME/.config"
OM_THEME="$HOME/.local/share/omarchy/default/themes/omarchy-default"

echo "Select Distribution:"
echo "1) Fedora"
echo "2) Kubuntu"
echo "3) Omarchy"
read -p "Choice [1-3]: " choice

case $choice in
    1)
        echo "Installing Fedora dependencies..."
        sudo dnf install -y hyprland waybar hyprlock grim slurp polkit-gnome wofi kitty btop gnome-clocks gnome-calculator xdg-desktop-portal-hyprland google-cascadia-code-fonts jetbrains-mono-fonts
        
        echo "Deploying Fedora configs..."
        mkdir -p "$CONF"
        cp -r fedora/* "$CONF/"
        ;;

    2)
        echo "Installing Kubuntu dependencies..."
        sudo add-apt-repository ppa:reback00/walker -y || true
        sudo apt update
        sudo apt install -y hyprland waybar hyprlock grim slurp polkit-gnome wofi kitty btop gnome-clocks gnome-calculator xdg-desktop-portal-hyprland fonts-cascadia-code fonts-jetbrains-mono walker
        
        echo "Deploying Kubuntu configs..."
        mkdir -p "$CONF"
        cp -r kubuntu/* "$CONF/"
        ;;

    3)
        echo "Installing Omarchy dependencies..."
        yay -S --needed --noconfirm hyprland waybar hyprlock grim slurp polkit-gnome wofi kitty obsidian chromium btop gnome-clocks gnome-calculator xdg-desktop-portal-hyprland ttf-cascadia-code ttf-jetbrains-mono ttf-nerd-fonts-symbols
        
        echo "Deploying Omarchy specific folders..."
        mkdir -p "$OM_THEME"
        cp -r themes/* "$OM_THEME/"
        
        mkdir -p "$CONF"
        [ -d "waybar" ] && cp -r waybar "$CONF/"
        [ -d "walker" ] && cp -r walker "$CONF/"
        [ -d "hypr" ] && cp -r hypr "$CONF/"
        ;;

    *)
        echo "Invalid selection."
        exit 1
        ;;
esac

echo "Work complete."
read -p "Reboot now? (y/n): " r
[[ "$r" =~ ^[yY]$ ]] && sudo reboot
