try:
    import win32gui, win32con, win32api, win32process
except ImportError:
    os.system('pip install pywin32')
    import win32gui, win32con, win32api, win32process

import keyboard
import time
import ctypes
import os




hwnd = None         
ALPHA= 255
ISTOPMOST = False
topmost= win32con.HWND_TOPMOST
no_topmost= win32con.HWND_NOTOPMOST
onRUNNING_KEYSHORCUT = False
keycut = None

SW_HIDE = 0
SW_SHOW = 5
WINDOW_HIDE = None

def find_hwnd_by_pid(pid):
    hwnds = []

    def callback(hwnd, _):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        if found_pid == pid and win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return hwnds[0] if hwnds else None


def find_hwnd_by_title(keyword):
    def callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if keyword.lower() in title.lower():
                result.append(hwnd)
    result = []
    win32gui.EnumWindows(callback, result)
    return result[0] if result else None


def set_window_topmost(hwnd, boo):
    # Get the handle of the active window
    if boo:
        boo = win32con.HWND_TOPMOST
    else:
        boo = win32con.HWND_NOTOPMOST


    # hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        # Set the window to be always on top
        win32gui.SetWindowPos(hwnd, boo, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    else:
        print("No active window found.")


def _transparent_hwnd(hwnd, alpha, window_ontopmost):
    win32gui.SetWindowLong (hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong (hwnd, win32con.GWL_EXSTYLE ) | win32con.WS_EX_LAYERED )
    win32gui.SetLayeredWindowAttributes(    hwnd, 
                                            win32api.RGB(0,0,0), 
                                            alpha, 
                                            win32con.LWA_ALPHA)
    win32gui.SetWindowPos(  hwnd, 
                            window_ontopmost, 100,100,200,200,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def hide_window():
    global WINDOW_HIDE
    SW_HIDE = 0
    SW_SHOW = 5
    if WINDOW_HIDE:
        hwnd = WINDOW_HIDE
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)


        try: # ~~> Hiện trên cùng
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
        except: pass


        WINDOW_HIDE = None
        # PNGSHOW_SIGNAL.send(("crosshair.png", 0.75, 900, 500))
    else:
        hwnd = win32gui.GetForegroundWindow()
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
        WINDOW_HIDE = hwnd
        # PNGSHOW_SIGNAL.send(("crosshairRed.png", 0.9, 800, 400))


def killApp():
    hwnd = win32gui.GetForegroundWindow()
    _ ,pid = win32process.GetWindowThreadProcessId(hwnd)
    os.system('taskkill /f /pid %d' % pid)


def open_Search():
    path = r"C:\Eol\enol_script\Systray\chrome.lnk"
    print(path)
    cmd = "%s https://www.google.com" % (path)
    os.system(cmd)


def open_CMD():
    os.system('start')


def doTransparent():
    global initPNG
    hwnd = win32gui.GetForegroundWindow()
    # win32gui.SetWindowLong (hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong (hwnd, win32con.GWL_EXSTYLE ) | win32con.WS_EX_LAYERED )
    print(win32gui.GetWindowText(hwnd) ,':: ', hwnd)
    global ALPHA
    if ALPHA != 200 :
        ALPHA = 200
        print('alpha: ', ALPHA)
        _transparent_hwnd(hwnd, ALPHA, topmost)

    elif ALPHA == 200:
        ALPHA= 255
        print('alpha: ', ALPHA)
        _transparent_hwnd(hwnd, ALPHA, no_topmost)


def dotopmost():
    global ISTOPMOST
    hwnd = win32gui.GetForegroundWindow()
    print(win32gui.GetWindowText(hwnd) ,':: ', hwnd)
    if ISTOPMOST:
        set_window_topmost(hwnd, ISTOPMOST)
        ISTOPMOST = False
    else:
            set_window_topmost(hwnd, ISTOPMOST)
            ISTOPMOST = True


def doMinimized_hwnd():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)


#-------------------------------F6----------------------------#
def next_track():
    VK_MEDIA_NEXT_TRACK = 0xB0
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    # Phím xuống
    ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_EXTENDEDKEY, 0)
    # Phím nhả
    ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
#-------------------------------F6----------------------------#


# vars : mouse_position and current time event happened :
saveX = None
saveY = None
ctime_2mouse = None

def on_click_2button(x, y, button, pressed):
    global saveX, saveY, ctime_2mouse
    if str(button) == "Button.left" and pressed == True:     # Left Pressed
        saveX = x
        saveY = y
        ctime_2mouse = time.time()
    elif    str(button) == "Button.right" \
            and saveX is not None   \
            and pressed is False    \
            and (time.time() - ctime_2mouse) < 0.2 :        # Right Left

        if abs(saveX-x) <= 10 and abs(saveY-y) <= 10 :      # Escept big distances position click
            keyboard.press_and_release('win+tab')
            return

# def listenning_mouse_2button():
#     with mouse.Listener(on_click = on_click_2button) as listener:
#         listener.join()


#▢▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▢#
def get_window():
        global hwnd, ALPHA
        ALPHA = 255
        hwnd = win32gui.GetForegroundWindow()
        print(win32gui.GetWindowText(hwnd) ,':: ', hwnd)



def upTransparent():
    global ALPHA
    # print('alpha: ', alpha)
    if ALPHA <=245 :
        ALPHA += 10
        _transparent_hwnd(alpha=ALPHA, hwnd=hwnd, window_ontopmost=no_topmost)



def downTransparent():
    global ALPHA
    # print('alpha: ', alpha)
    if ALPHA > 70:
        ALPHA -= 10
        _transparent_hwnd(alpha=ALPHA, hwnd=hwnd, window_ontopmost=no_topmost)



#▢▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▢#



if __name__ == '__main__':

    # Gán hotkeys
    
    keyboard.add_hotkey('F6',           next_track,     suppress=True)
    keyboard.on_press_key('F7',         lambda:     hide_window())        
    keyboard.on_press_key('F8',         lambda:     doTransparent())            # Make window onTop and Transparent
    # keyboard.add_hotkey('F10',      lambda: cpupos()        )
    # keyboard.add_hotkey('Win+A',    lambda: assistant(), suppress=True)
    # [Alt]+[Scroll.mouse]                                                      # Transparent window
    # [Left.mouse]+[Right.mouse]                                                # Manager Desktop


    ## [WIN] + [TAB]
    # mouse2 = Thread(target=listenning_mouse_2button, daemon=True, name='Mouse2')
    # mouse2.start()

    # AltScroll.Listenning().start(   doPressed=get_window,
    #                                 doDown=downTransparent,
    #                                 doUP=upTransparent)
    keyboard.wait()