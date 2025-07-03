import subprocess
import time
import win32gui
import win32con


HWND_EDGE = None  # Biến toàn cục lưu handle cửa sổ Edge
URL = "https://www.messenger.com/requests/t/100000934364874/" # URL tin nhắn spam
msedge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


_ui_globals = {}                        #~~> _ui_globals.get("MESSAGE")
def set_global_toReadmess(ctx):
    global _ui_globals
    _ui_globals = ctx


def open_edge_new_window(url):
    cmd = [f"{msedge}", "--new-window", url]
    subprocess.Popen(cmd)


def find_hwnd_by_title(title_keywords):
    global HWND_EDGE
    HWND_EDGE = None

    def enum_windows(hwnd, _):
        global HWND_EDGE
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if any(keyword in title for keyword in title_keywords):
                HWND_EDGE = hwnd
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)  # Ẩn cửa sổ khi tìm thấy

    win32gui.EnumWindows(enum_windows, None)
    return HWND_EDGE is not None


def close_hwnd(hwnd):
    if hwnd and win32gui.IsWindow(hwnd):
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            MESSAGE.emit(f"[✓] Đã đóng [Messenger] {HWND_EDGE}", 3000) # type: ignore
        except Exception as e:
            print(f"Lỗi khi gửi WM_CLOSE: {e}")


def run():
    title_keywords = ["Messenger", 'loading...']

    # 1. Mở Edge
    open_edge_new_window(URL)

    # 2. Lặp lại quá trình tìm HWND mỗi 0.2s (tối đa 20 lần)
    for _ in range(20):
        if find_hwnd_by_title(title_keywords):
            print(f"Đã tìm thấy HWND: {HWND_EDGE}")
            break
        time.sleep(0.2)
    else:
        return f"Không tìm thấy hwnd [Messenger] {HWND_EDGE}"

    # 3. Sau 4 giây thì đóng nếu HWND_EDGE vẫn tồn tại
    time.sleep(10)
    if HWND_EDGE and win32gui.IsWindow(HWND_EDGE):
        close_hwnd(HWND_EDGE)
        return f"Đã đóng [Messenger] {HWND_EDGE}"


if __name__ == "__main__":
    run()
