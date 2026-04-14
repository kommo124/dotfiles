#!/bin/bash

WALLPAPER_DIR="$HOME/Pictures"
HYPRPAPER_CONF="$HOME/.config/hypr/hyprpaper.conf"

# Find all images
WALLPAPERS=$(find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" -o -iname "*.bmp" -o -iname "*.webp" \) | sort)

if [ -z "$WALLPAPERS" ]; then
    notify-send "Wallpaper Picker" "No wallpapers found in $WALLPAPER_DIR"
    exit 1
fi

# Show rofi with basename for display, but keep full path
SELECTED=$(echo "$WALLPAPERS" | while read -r path; do
    echo "$(basename "$path")|$path"
done | rofi -dmenu -i -p "Select wallpaper" -selected-row 0 | cut -d'|' -f2)

if [ -z "$SELECTED" ]; then
    exit 0
fi

# Update hyprpaper config
# Get current monitor
MONITOR=$(hyprctl monitors -j | jq -r '.[0].name')

# Create new config
cat > "$HYPRPAPER_CONF" << EOF
preload = $WALLPAPER_DIR
splash = false

wallpaper {
    monitor = $MONITOR
    path = $SELECTED
    fit_mode = cover
}
EOF

# Reload hyprpaper
pkill hyprpaper
nohup hyprpaper &>/dev/null &

notify-send "Wallpaper changed" "$(basename "$SELECTED")"
