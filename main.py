import pygetwindow as gw
import pyautogui
import keyboard
import tkinter as tk
from functools import partial
import queue
import threading
import argparse

class WindowClicker:
    def __init__(self, window_title):
        self.window_title = window_title
        self.hotkeys = {}
        self.overlay_root = None
        self.overlay_canvas = None
        self.dots = {}
        self.queue = queue.Queue()
        self.window = None
        self.persistent_dots = {}

    def click_in_window(self, abs_x, abs_y, show_clicked=False):
        original_x, original_y = pyautogui.position()
        self.overlay_root.withdraw()
        pyautogui.click(abs_x, abs_y)
        self.overlay_root.deiconify()
        pyautogui.moveTo(original_x, original_y)
        if show_clicked:
            self.queue.put(('click', abs_x - self.window.left, self.window.bottom - abs_y))

    def create_overlay(self):
        if self.overlay_root is None:
            self.overlay_root = tk.Tk()
            self.overlay_root.attributes('-topmost', True)
            self.overlay_root.overrideredirect(True)
            self.overlay_root.attributes('-transparentcolor', 'black')
            self.overlay_canvas = tk.Canvas(self.overlay_root, bg='black', highlightthickness=0)
            self.overlay_canvas.pack(fill=tk.BOTH, expand=True)
            self.overlay_root.after(100, self.check_queue)
            self.update_overlay_position()

    def update_overlay_position(self):
        if self.window:
            self.overlay_root.geometry(f"{self.window.width}x{self.window.height}+{self.window.left}+{self.window.top}")
        self.overlay_root.after(100, self.update_overlay_position)

    def check_queue(self):
        try:
            while True:
                action, x, y = self.queue.get_nowait()
                if action == 'click':
                    self.update_overlay(x, y, 'lime')
                elif action == 'show':
                    self.update_overlay(x, y, 'yellow', persistent=True)
        except queue.Empty:
            pass
        finally:
            self.overlay_root.after(100, self.check_queue)

    def update_overlay(self, x, y, color, persistent=False):
        adjusted_y = self.window.height - y
        if persistent:
            dot_id = self.overlay_canvas.create_oval(x-7, adjusted_y-7, x+7, adjusted_y+7, fill=color, width=2)
            self.persistent_dots[(x, y)] = dot_id
        else:
            dot_id = self.overlay_canvas.create_oval(x-7, adjusted_y-7, x+7, adjusted_y+7, fill=color, width=2)
            self.dots[dot_id] = self.overlay_root.after(250, lambda: self.remove_dot(dot_id))

    def remove_dot(self, dot_id):
        if self.overlay_canvas:
            self.overlay_canvas.delete(dot_id)
            self.dots.pop(dot_id, None)

    def add_hotkey(self, key, x_offset, y_offset, is_percentage=False, show_clicked=False, show_overlay=False):
        windows = gw.getWindowsWithTitle(self.window_title)
        self.window = next((w for w in windows if self.window_title == w.title), None)
        if self.window == None:
            raise ValueError(f"Window with name \"{self.window_title}\" not found!")
        
        if is_percentage:
            abs_x = self.window.left + int(self.window.width * x_offset / 100)
            abs_y = self.window.bottom - int(self.window.height * y_offset / 100)
        else:
            abs_x = self.window.left + x_offset
            abs_y = self.window.bottom - y_offset

        if show_overlay:
            self.queue.put(('show', abs_x - self.window.left, self.window.bottom - abs_y))
        
        self.hotkeys[key] = partial(self.click_in_window, abs_x, abs_y, show_clicked)
        keyboard.add_hotkey(key, self.hotkeys[key])

    def run(self):
        self.create_overlay()
        threading.Thread(target=self.wait_for_exit, daemon=True).start()
        self.overlay_root.mainloop()

    def wait_for_exit(self):
        keyboard.wait('shift+space')
        self.overlay_root.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add hotkeys to Arknights windows")

    parser.add_argument('-V', '--version', action='store_true', help="Show version information") 
    parser.add_argument('-O', '--show_overlay', action='store_true', help="Show where you will click") 
    parser.add_argument('-C', '--show_clicked', action='store_true', help="Show where you clicked") 
    parser.add_argument('-wn', '--windows_name', type=str, help="custom windows_name default is \"Arknights\"")

    args = parser.parse_args()

    if args.version:
        print("Arknights Shortcut Tool Version 1.0.0")

    if args.windows_name:
        clicker = WindowClicker(args.windows_name)
    else:
        clicker = WindowClicker("Arknights")

    show_overlay = False
    show_clicked = False
    if args.show_overlay:
        show_overlay = True
    if args.show_clicked:
        show_clicked = True
    clicker.add_hotkey('q', 46.5, 68.5, True,  show_clicked, show_overlay)
    clicker.add_hotkey('e', 68, 40, True, show_clicked, show_overlay)
    print("-"*20)
    print("ready")
    print("-"*20)
    clicker.run()
    print("-"*20)
    print("terminated successfully")
    print("-"*20)
    