# ============================================================
#  FULLY FIXED SCRIPT — XBOX CONTROLLER MOUSE + KEYBOARD
#  - Mouse movement works
#  - A button = mouse hold
#  - X, Y, B work
#  - D-Pad keyboard navigation
#  - No crashes
# ============================================================

import threading
import tkinter as tk
from inputs import get_gamepad
import ctypes
import time

# -------------------------
# GLOBAL STATE
# -------------------------
running = False
keyboard_open = False

SENSITIVITY = 0.25
DEADZONE = 2500

keyboard_window = None
keyboard_mode = "letters"
keyboard_buttons = []
keyboard_row = 0
keyboard_col = 0

# -------------------------
# WINDOWS API CONSTANTS
# -------------------------
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

VK_MENU = 0x12
VK_F4   = 0x73
VK_BACK = 0x08

# -------------------------
# WINDOWS API STRUCTURES
# -------------------------
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def move_mouse(dx, dy):
    if keyboard_open:
        return
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    ctypes.windll.user32.SetCursorPos(pt.x + int(dx), pt.y + int(dy))

def mouse_down():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

def mouse_up():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def alt_f4():
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_F4, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_F4, 0, 2, 0)
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 2, 0)

def send_vk(vk_code):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

def send_char(char):
    vk = ctypes.windll.user32.VkKeyScanW(ord(char))
    if vk == -1:
        return
    vk_code = vk & 0xFF
    shift_state = (vk >> 8) & 0xFF

    if shift_state & 1:
        ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)

    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

    if shift_state & 1:
        ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)

# -------------------------
# KEYBOARD UI COLORS
# -------------------------
KEY_BG        = "#202020"
KEY_FG        = "#FFFFFF"
KEY_HL_BG     = "#00FF00"
KEY_HL_FG     = "#000000"
BAR_BG        = "#303030"
WINDOW_BG     = "#000000"

# -------------------------
# KEYBOARD LAYOUTS
# -------------------------
def get_layout_for_mode():
    if keyboard_mode == "caps":
        return [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM"),
        ]
    elif keyboard_mode == "numbers":
        return [
            list("1234567890"),
            list("-/:;()$&@"),
            list(".,?!'\""),
        ]
    return [
        list("qwertyuiop"),
        list("asdfghjkl"),
        list("zxcvbnm"),
    ]

# -------------------------
# THREAD-SAFE HIGHLIGHT
# -------------------------
def highlight_current_key():
    if not keyboard_open or keyboard_window is None:
        return

    def _update():
        if not keyboard_open or keyboard_window is None:
            return
        for r, row in enumerate(keyboard_buttons):
            for c, btn in enumerate(row):
                try:
                    if r == keyboard_row and c == keyboard_col:
                        btn.config(bg=KEY_HL_BG, fg=KEY_HL_FG)
                    else:
                        btn.config(bg=KEY_BG, fg=KEY_FG)
                except tk.TclError:
                    pass

    root.after(0, _update)

# -------------------------
# KEYBOARD MODE SWITCHING
# -------------------------
def set_keyboard_mode(new_mode):
    global keyboard_mode, keyboard_row, keyboard_col
    keyboard_mode = new_mode
    keyboard_row = 0
    keyboard_col = 0
    build_keyboard_keys()

def on_key_press(char):
    if char == "SPACE":
        send_char(" ")
    elif char == "BACK":
        send_vk(VK_BACK)
    else:
        send_char(char)

# -------------------------
# BUILD KEYBOARD UI
# -------------------------
def build_keyboard_keys():
    global keyboard_buttons
    if keyboard_window is None:
        return

    for child in keyboard_window.grid_slaves():
        child.destroy()

    keyboard_window.configure(bg=WINDOW_BG)

    rows = get_layout_for_mode()
    keyboard_buttons = []

    keys_frame = tk.Frame(keyboard_window, bg=WINDOW_BG)
    keys_frame.grid(row=0, column=0, sticky="ew")

    for r, row_chars in enumerate(rows):
        row_buttons = []
        for c, ch in enumerate(row_chars):
            btn = tk.Button(keys_frame, text=ch, width=3,
                            bg=KEY_BG, fg=KEY_FG,
                            activebackground=KEY_HL_BG,
                            activeforeground=KEY_HL_FG,
                            command=lambda ch=ch: on_key_press(ch))
            btn.grid(row=r, column=c, padx=2, pady=2)
            row_buttons.append(btn)
        keyboard_buttons.append(row_buttons)

    highlight_current_key()

# -------------------------
# OPEN/CLOSE KEYBOARD
# -------------------------
def open_keyboard(root):
    global keyboard_window, keyboard_open, keyboard_row, keyboard_col
    if keyboard_open:
        return
    keyboard_open = True
    keyboard_row = 0
    keyboard_col = 0

    keyboard_window = tk.Toplevel(root)
    keyboard_window.title("Virtual Keyboard")
    keyboard_window.configure(bg=WINDOW_BG)
    keyboard_window.attributes("-topmost", True)

    screen_w = keyboard_window.winfo_screenwidth()
    screen_h = keyboard_window.winfo_screenheight()
    height = int(screen_h * 0.35)
    keyboard_window.geometry(f"{screen_w}x{height}+0+{screen_h - height}")

    build_keyboard_keys()

def close_keyboard():
    global keyboard_window, keyboard_open
    if keyboard_window is not None:
        try:
            keyboard_window.destroy()
        except:
            pass
        keyboard_window = None
    keyboard_open = False

# -------------------------
# CONTROLLER LOOP
# -------------------------
lx = 0
ly = 0
last_nav_time = 0
NAV_DELAY = 0.15

def move_keyboard_selection(dx, dy):
    global keyboard_row, keyboard_col
    if not keyboard_open or not keyboard_buttons:
        return

    rows = keyboard_buttons
    max_row = len(rows) - 1

    keyboard_row = max(0, min(max_row, keyboard_row + dy))
    max_col = len(rows[keyboard_row]) - 1
    keyboard_col = max(0, min(max_col, keyboard_col + dx))

    root.after(0, highlight_current_key)

def activate_current_key():
    if not keyboard_open or not keyboard_buttons:
        return
    try:
        btn = keyboard_buttons[keyboard_row][keyboard_col]
        text = btn.cget("text")
        on_key_press(text)
    except:
        pass

def controller_loop():
    global running, SENSITIVITY, lx, ly, last_nav_time

    while running:
        try:
            events = get_gamepad()
        except:
            time.sleep(0.01)
            continue

        now = time.time()

        for event in events:
            code = event.code
            state = event.state

            # Left stick
            if code == "ABS_X":
                lx = state
            elif code == "ABS_Y":
                ly = state

            # A button (mouse hold)
            if code == "BTN_SOUTH":
                if state == 1:  # pressed
                    if keyboard_open:
                        activate_current_key()
                    else:
                        mouse_down()

                if state == 0:  # released
                    if not keyboard_open:
                        mouse_up()

            # B button
            if code == "BTN_EAST" and state == 1:
                if keyboard_open:
                    close_keyboard()

            # X button
            if code == "BTN_NORTH" and state == 1:
                alt_f4()

            # Y button
            if code == "BTN_WEST" and state == 1:
                if not keyboard_open:
                    open_keyboard(root)

            # D-Pad Up/Down
            if code == "ABS_HAT0Y":
                if state == -1 and keyboard_open:
                    move_keyboard_selection(0, -1)
                elif state == 1 and keyboard_open:
                    move_keyboard_selection(0, 1)

            # D-Pad Left/Right
            if code == "ABS_HAT0X":
                if state == -1 and keyboard_open:
                    move_keyboard_selection(-1, 0)
                elif state == 1 and keyboard_open:
                    move_keyboard_selection(1, 0)

        # Keyboard navigation or mouse movement
        if keyboard_open:
            dx = dy = 0

            lx_out = 0 if abs(lx) < DEADZONE else lx / 32768
            ly_out = 0 if abs(ly) < DEADZONE else ly / 32768

            if lx_out > 0.5:
                dx = 1
            elif lx_out < -0.5:
                dx = -1

            if ly_out > 0.5:
                dy = 1
            elif ly_out < -0.5:
                dy = -1

            if (dx or dy) and (now - last_nav_time) > NAV_DELAY:
                move_keyboard_selection(dx, dy)
                last_nav_time = now

        else:
            lx_out = 0 if abs(lx) < DEADZONE else lx / 32768
            ly_out = 0 if abs(ly) < DEADZONE else ly / 32768

            move_mouse(lx_out * SENSITIVITY * 80,
                       -ly_out * SENSITIVITY * 80)

        time.sleep(0.001)

# -------------------------
# MAIN GUI
# -------------------------
def start_control():
    global running
    if not running:
        running = True
        status_label.config(text="Controller: ON", fg="green")
        threading.Thread(target=controller_loop, daemon=True).start()

def stop_control():
    global running
    running = False
    status_label.config(text="Controller: OFF", fg="red")

def update_sensitivity(value):
    global SENSITIVITY
    SENSITIVITY = float(value)

def on_textbox_click(event):
    if not keyboard_open:
        open_keyboard(root)

root = tk.Tk()
root.title("Xbox Controller Mouse + Virtual Keyboard")

status_label = tk.Label(root, text="Controller: OFF", font=("Arial", 16), fg="red")
status_label.pack(pady=10)

tk.Button(root, text="Start", font=("Arial", 14), command=start_control).pack(pady=5)
tk.Button(root, text="Stop", font=("Arial", 14), command=stop_control).pack(pady=5)

tk.Label(root, text="Mouse Sensitivity", font=("Arial", 14)).pack(pady=5)

sensitivity_slider = tk.Scale(root, from_=0.05, to=1.5, resolution=0.05,
                              orient="horizontal", length=250,
                              command=update_sensitivity)
sensitivity_slider.set(SENSITIVITY)
sensitivity_slider.pack(pady=10)

tk.Label(root, text="Click in this box to open keyboard:", font=("Arial", 12)).pack(pady=(15, 2))

demo_entry = tk.Entry(root, font=("Arial", 14), width=40)
demo_entry.pack(pady=5)
demo_entry.bind("<Button-1>", on_textbox_click)

root.mainloop()
