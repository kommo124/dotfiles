#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import os
import subprocess
import json

WALLPAPER_DIR = os.path.expanduser("~/Pictures")
HYPRPAPER_CONF = os.path.expanduser("~/.config/hypr/hyprpaper.conf")
THUMB_SIZE = 150

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')


def get_wallpapers():
    wallpapers = []
    for root, dirs, files in os.walk(WALLPAPER_DIR):
        for f in sorted(files):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                wallpapers.append(os.path.join(root, f))
    return sorted(wallpapers)


def create_thumbnail(filepath, size):
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filepath)
        w = pixbuf.get_width()
        h = pixbuf.get_height()
        
        scale = size / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        scaled = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.BILINEAR)
        return scaled
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def set_wallpaper(filepath):
    monitor = subprocess.check_output(
        ["hyprctl", "monitors", "-j"], text=True
    )
    monitors = json.loads(monitor)
    monitor_name = monitors[0]["name"] if monitors else "HDMI-A-1"
    
    wallpaper_dir = WALLPAPER_DIR
    
    with open(HYPRPAPER_CONF, 'w') as f:
        f.write(f"preload = {wallpaper_dir}\n")
        f.write(f"splash = false\n\n")
        f.write(f"wallpaper {{\n")
        f.write(f"    monitor = {monitor_name}\n")
        f.write(f"    path = {filepath}\n")
        f.write(f"    fit_mode = cover\n")
        f.write(f"}}\n")
    
    subprocess.run(["pkill", "hyprpaper"])
    subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        subprocess.run(["notify-send", "Wallpaper changed", os.path.basename(filepath)])
    except Exception:
        pass


class WallpaperPicker(Gtk.Window):
    def __init__(self):
        super().__init__(title="Select Wallpaper")
        self.set_default_size(800, 600)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Style
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(b"""
            * {
                background-color: #1a1a2e;
                color: #d8dee9;
            }
            window {
                background-color: #1a1a2e;
            }
            .wallpaper-btn {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 8px;
                padding: 4px;
            }
            .wallpaper-btn:hover {
                border-color: #33ccff;
            }
            label {
                color: #d8dee9;
                font-size: 11px;
            }
            scrollbar slider {
                background-color: #0f3460;
                border-radius: 4px;
                min-width: 8px;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.connect("destroy", Gtk.main_quit)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        self.add(main_box)
        
        # Title
        title = Gtk.Label()
        title.set_markup('<span size="large" color="#ffffff" weight="bold">Wallpaper Picker</span>')
        main_box.pack_start(title, False, False, 5)
        
        # Scrollable area
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scroll, True, True, 0)
        
        # Grid
        self.grid = Gtk.FlowBox()
        self.grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.grid.set_homogeneous(True)
        self.grid.set_max_children_per_line(20)
        self.grid.set_min_children_per_line(3)
        self.grid.set_row_spacing(10)
        self.grid.set_column_spacing(10)
        scroll.add(self.grid)
        
        # Load wallpapers
        self.load_wallpapers()
    
    def load_wallpapers(self):
        wallpapers = get_wallpapers()
        if not wallpapers:
            label = Gtk.Label()
            label.set_markup('<span color="#d8dee9">No wallpapers found in ~/Pictures</span>')
            main_box = self.get_children()[0]
            main_box.pack_start(label, False, False, 20)
            return
        
        for wp in wallpapers:
            thumb = create_thumbnail(wp, THUMB_SIZE)
            if thumb:
                btn = self.create_wallpaper_button(wp, thumb)
                self.grid.add(btn)
            else:
                btn = self.create_wallpaper_button(wp, None)
                self.grid.add(btn)
    
    def create_wallpaper_button(self, filepath, pixbuf):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.get_style_context().add_class("wallpaper-btn")
        box.set_size_request(THUMB_SIZE, THUMB_SIZE + 30)
        
        if pixbuf:
            image = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            image = Gtk.Image.new_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
            image.set_pixel_size(THUMB_SIZE - 20)
        
        box.pack_start(image, True, True, 0)
        
        label = Gtk.Label(os.path.basename(filepath))
        label.set_ellipsize(True)
        label.set_max_width_chars(15)
        box.pack_start(label, False, False, 0)
        
        box.connect("button-press-event", self.on_wallpaper_click, filepath)
        box.connect("button-release-event", self.on_wallpaper_click, filepath)
        box.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        
        return box
    
    def on_wallpaper_click(self, widget, event, filepath):
        set_wallpaper(filepath)
        Gtk.main_quit()


if __name__ == "__main__":
    win = WallpaperPicker()
    win.show_all()
    Gtk.main()
