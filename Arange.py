import win32gui
import win32process
import win32con
import psutil
import json
import os



SAVE_FILE = "window_positions.json"

def load_saved_window_positions(filepath=SAVE_FILE):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def get_exe_name(pid):
    try:
        return psutil.Process(pid).name().lower()
    except psutil.Error:
        return "unknown.exe"

def is_main_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.IsIconic(hwnd):
        return False
    if win32gui.GetParent(hwnd):
        return False
    if not win32gui.GetWindowText(hwnd).strip():
        return False
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    return bool(style & win32con.WS_OVERLAPPEDWINDOW)

def enum_visible_windows():
    result = []
    def callback(hwnd, _):
        if is_main_window(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            exe = get_exe_name(pid)
            title = win32gui.GetWindowText(hwnd)
            result.append({
                "exe": exe,
                "pid": pid,
                "hwnd": hwnd,
                "title": title,
                "x": left,
                "y": top,
                "width": right - left,
                "height": bottom - top
            })
    win32gui.EnumWindows(callback, None)
    return result

def is_window_maximized(hwnd):
    placement = win32gui.GetWindowPlacement(hwnd)
    return placement[1] == win32con.SW_MAXIMIZE

IGNORE_LIST = ["python.exe", "applicationframehost.exe"]
def save_all_window_positions(filepath=SAVE_FILE):
    windows = enum_visible_windows()
    save_data = {}
    for win in windows:
        exe = win['exe']
        if exe in IGNORE_LIST:
            # print(f'[x] {exe}')
            continue
        
        hwnd = win["hwnd"]
        if "msedge" in exe:
            if is_window_maximized(hwnd):
                print(f"[INFO] Code window is maximized, restoring...")
                restore_all_window_positions()
                return

        if exe not in save_data:  # chỉ lưu 1 cửa sổ mỗi app
            save_data[exe] = {
                "x": win["x"],
                "y": win["y"],
                "width": win["width"],
                "height": win["height"]
            }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2)
    print(f"[✓] Saved {len(save_data)} window positions to {filepath}")


def restore_all_window_positions(filepath="window_positions.json"):
    if not os.path.exists(filepath):
        print("[-] No saved window positions found.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        saved = json.load(f)

    current = enum_visible_windows()

    # Kiểm tra trạng thái của msedge.exe
    APP_PIORNEER = "code.exe"
    Code_maximized = False
    for win in current:
        if win["exe"] == APP_PIORNEER:
            if is_window_maximized(win["hwnd"]):
                Code_maximized = True
            break  # chỉ cần kiểm tra 1 instance

    # === Nếu Edge đang maximize → khôi phục toàn bộ ===
    if Code_maximized:
        print(f"[✓] {APP_PIORNEER} is maximized → Restoring all window positions...")
        for win in current:
            exe = win["exe"]
            if exe in saved:
                pos = saved[exe]
                try:
                    win32gui.ShowWindow(win["hwnd"], win32con.SW_RESTORE)
                    win32gui.MoveWindow(
                        win["hwnd"],
                        pos["x"], pos["y"],
                        pos["width"], pos["height"],
                        True
                    )
                    print(f"[✓] Restored {exe}")
                except Exception as e:
                    print(f"[!] Failed to move {exe}: {e}")
    else:
        # === Nếu Edge không maximize → maximize tất cả cửa sổ ===
        print(f"[↥] {APP_PIORNEER} not maximized → Maximizing all windows...")
        for win in current:
            try:
                win32gui.ShowWindow(win["hwnd"], win32con.SW_MAXIMIZE)
                print(f"[↥] Maximized {win['exe']}")
            except Exception as e:
                print(f"[!] Failed to maximize {win['exe']}: {e}")




if __name__ == '__main__':
    save_all_window_positions(SAVE_FILE)