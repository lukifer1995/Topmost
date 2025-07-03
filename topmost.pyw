import sys, os, subprocess
import time
import ctypes
import threading


import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import logging
logging.getLogger().setLevel(logging.CRITICAL)
from PyQt5.QtCore import qInstallMessageHandler
def message_handler(mode, context, message):
    return # ~~> Chặn tất cả thông báo
qInstallMessageHandler(message_handler)


# Third-party
import keyboard

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QObject, QPoint
)
from PyQt5.QtGui import (
    QColor, QPixmap, QPainter,
    QMouseEvent, QWheelEvent, QKeyEvent
)

# Internal modules
from topmost_func import *
from Arange import *
from checkport import *
import ReadMessSpam
import Searchbar

#-----------------------------------------------------#
#region UI
class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("_")
        self.setGeometry(-100, -100, 0, 0)  # Vị trí và kích thước cửa sổ


class Overlay(QWidget):
    shiftSignal = pyqtSignal(int)
    selectSignal = pyqtSignal()
    closeSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.01)
        self.setFocusPolicy(Qt.StrongFocus)

        # > Hack :: cửa sổ bình thường phải luôn dc load trc lớp phủ trong suốt để qua mặt window
        welcome = WelcomeScreen()
        welcome.show()
        welcome.close()
        self.show()
        self.hide()

    def showEvent(self, event):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)
        super().showEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
            menu.hide()
            turn_off_capslock()
        elif event.key() in [Qt.Key_1, Qt.Key_2, Qt.Key_3]:
            self.selectSignal.emit()
            self.hide()
            turn_off_capslock()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.hide()
            menu.hide()
            turn_off_capslock()
        elif event.button() == Qt.LeftButton:
            self.selectSignal.emit()
            self.hide()
            turn_off_capslock()


    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        self.shiftSignal.emit(-1 if delta > 0 else 1)


class TransparentMenu(QWidget):
    def __init__(self, pixmaps):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # | Qt.Tool : gây mất focus, dẫn đến event không nhận.
        # self.setAttribute(Qt.WA_TranslucentBackground)                      # Nếu bật sẽ nền trong suốt
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)                         # <~ dòng này để các event bàn phím (keyPressEvent) hoạt động

        self.pixmaps = pixmaps
        self.current_index = -1

        layout = QHBoxLayout()
        layout.setSpacing(SPACING)      
        layout.setContentsMargins(MARGINS, MARGINS, MARGINS, MARGINS)

        self.labels = []
        for pix in pixmaps:
            label = QLabel()
            label.setPixmap(pix)
            label.setFixedSize(IMG_SIZE, IMG_SIZE)
            label.setMouseTracking(True)    # <~~ Label phải class cha nên k có focus mouse tracking
            layout.addWidget(label, alignment=Qt.AlignCenter)
            self.labels.append(label)

        self.setLayout(layout)
        self.highlight_current()
        self.adjustSize()
        self.setStyleSheet("background-color: rgba(30, 30, 30, 0.8); border-radius: 12px;")


    #region Handle UI
    @staticmethod
    def prepare_pixmap(pixmap: QPixmap):
        canvas = QPixmap(IMG_SIZE, IMG_SIZE)
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(IMG_OPACITY)

        if pixmap:
            scaled = pixmap.scaled(IMG_SIZE, IMG_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (IMG_SIZE - scaled.width()) // 2
            y = (IMG_SIZE - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()
        return canvas


    def move_to_center(self, screen_rect):
        self.move(
            screen_rect.center().x() - self.width() // 2,
            screen_rect.center().y() - self.height() // 2
        )


    def shift_current(self, direction: int):
        self.current_index = max(0, min(len(self.labels) - 1, self.current_index + direction))
        self.highlight_current()


    def highlight_current(self):
        wait = 700
        for i, label in enumerate(self.labels):
            if i == self.current_index:
                label.setStyleSheet("border: 3px solid red; border-radius: 10px;")
                if i == 0: MESSAGE.emit('Arange', wait)
                if i == 1: MESSAGE.emit('Panel', wait)
                if i == 2: MESSAGE.emit('Kill py process', wait)
                if i == 3: MESSAGE.emit('Private Space', wait)
            else:
                label.setStyleSheet("border: none;")


    def excute_select_current(self):
        if self.current_index == 0:
            func_arange()
        elif self.current_index == 1:
            func_panel()
        elif self.current_index == 2:
            func_killpy()
        elif self.current_index == 3:
            func_private()

        self.hide()
    #endregion

    # ------------ Event ------------ #
    def __doany_and_hide(self):
        self.hide()
        overlay.hide()
        turn_off_capslock()


    def __excute_and_hide(self):
        self.excute_select_current()
        turn_off_capslock()


    def mouseMoveEvent(self, event):
        for i, label in enumerate(self.labels):
            # map vị trí chuột sang hệ toạ độ của label
            local_pos = label.mapFromParent(event.pos())
            if label.rect().contains(local_pos):
                if self.current_index != i:
                    self.current_index = i
                    self.highlight_current()
                break


    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.__doany_and_hide()
        elif event.button() == Qt.LeftButton:
            self.__excute_and_hide()


    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.__doany_and_hide()
        elif event.key() in [Qt.Key_1, Qt.Key_2, Qt.Key_3]:
            self.__excute_and_hide()


    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        self.shift_current(-1 if delta > 0 else 1)


    def showEvent(self, event):
        self.current_index = 0
        self.highlight_current()
        self.move_to_center(QApplication.primaryScreen().geometry())
        super().showEvent(event)


#endregion


#-----------------------------------------------------#
#region Notification
# =================== SIGNAL ======================

class NotificationSignal(QObject):
    send_text       = pyqtSignal(str, int)  # Góc phải dưới (mặc định)
    send_top_left   = pyqtSignal(str, int)  # Góc trái trên
    send_top_right  = pyqtSignal(str, int)  # Góc phải trên
    send_bottom_left = pyqtSignal(str, int) # Góc trái dưới
    dismiss_manual  = pyqtSignal()
# =================== LABEL =======================

class NotificationLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Click xuyên

        # Style sheet
        self.setStyleSheet(NOTIFY_STYLE)


        self.setWordWrap(True)
        self.is_manual = False  # default


        # Bóng đổ
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(1, 2)
        shadow.setColor(QColor(121, 121, 121, 250)) 
        self.setGraphicsEffect(shadow)


        # Animation xuất hiện
        self.setWindowOpacity(0.01)
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.OutQuad)

        # Animation biến mất
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(NOTIFY_FADE_DURATION)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_out_anim.finished.connect(self.deleteLater)

        # Hẹn giờ tự đóng
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)


    def apply_alignment(self, position: str):
        if position.endswith('left'):
            self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif position.endswith('right'):
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            self.setAlignment(Qt.AlignCenter)


    def show_with_timeout(self, pos: QPoint, timeout=10000):
        self.adjustSize()
        self.move(pos)
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_in.start()
        self.timer.start(timeout)


    def show_with_Notime(self, pos: QPoint, timeout=None):
        self.is_manual = True
        self.move(pos)
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_in.start()


    def fade_out(self):
        self.fade_out_anim.start()


    def dismiss(self):
        self.close()


# ================== MANAGER ======================

class NotificationManager:
    def __init__(self):
        self.notifications = []
        self.signal = NotificationSignal()
        self.signal.send_text.connect(lambda text, t: self.add_notification(text, t, 'bottom_right'))
        self.signal.send_top_left.connect(lambda text, t: self.add_notification(text, t, 'top_left'))
        self.signal.send_top_right.connect(lambda text, t: self.add_notification(text, t, 'top_right'))
        self.signal.send_bottom_left.connect(lambda text, t: self.add_notification(text, t, 'bottom_left'))
        self.signal.dismiss_manual.connect(self.dismiss_manual_labels)


    def add_notification(self, text: str, timeout: int = 10000, position='bottom_right'):
        label = NotificationLabel(text)
        
        
        if any(s in text for s in ("Nguy hiểm", "🆘", "[!]")):
            label.setStyleSheet(RED)
        elif any(s in text for s in ("Cẩn thận", "🚩", "Error", "AccessDenied")):
            label.setStyleSheet(YELLOW)


        label.position = position
        label.apply_alignment(position)

        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()

        # ✅ Set chiều rộng tối đa (cho tất cả vị trí)
        max_width = screen_width - 2 * NOTIFY_MARGIN
        # label.setWordWrap(True)
        label.setFixedWidth(max_width)  # Giới hạn chiều rộng tối đa

        # Font nhỏ hơn nếu không phải bottom_right
        if position != 'bottom_right' and position != 'bottom_left':
            font = label.font()
            font.setPointSize(8)
            label.setFont(font)


        label.adjustSize()
        width, height = label.width(), label.height()

        # Tính vị trí
        relevant = [n for n in self.notifications if getattr(n, 'position', '') == position]
        index = len(relevant)

        if position == 'bottom_right':
            x = screen.right() - width - NOTIFY_MARGIN
            y = screen.bottom() - NOTIFY_MARGIN - (height + NOTIFY_SPACING) * index
            label.show_with_timeout(QPoint(x, y), timeout)
        elif position == 'top_left':
            x = screen.left() + NOTIFY_MARGIN
            y = screen.top() + NOTIFY_MARGIN + (height + NOTIFY_SPACING) * index
            label.show_with_Notime(QPoint(x, y))
        elif position == 'top_right':
            x = screen.right() - width - NOTIFY_MARGIN
            y = screen.top() + NOTIFY_MARGIN + (height + NOTIFY_SPACING) * index
            label.show_with_Notime(QPoint(x, y))
        elif position == 'bottom_left':
            x = screen.left() + NOTIFY_MARGIN
            y = screen.bottom() - NOTIFY_MARGIN - height - (NOTIFY_SPACING * index)
            label.show_with_Notime(QPoint(x, y))
        else:
            x, y = 0, 0
            label.show_with_Notime(QPoint(x, y))

        label.destroyed.connect(lambda: self._remove_label(label))
        self.notifications.append(label)


    def _remove_label(self, label):
        try:
            self.notifications.remove(label)
        except ValueError:
            pass

    def dismiss_manual_labels(self):
        for label in self.notifications[:]:
            if getattr(label, 'is_manual', False):
                label.dismiss()
                self._remove_label(label)  # ✅ cập nhật ngay danh sách

    def sent_notification_signal(self):
        return self.signal.send_text
#endregion


#-----------------------------------------------------# 
#region Keyboad
class KeyListener(QObject):
    capslock_toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.running = True

    def start(self):
        def loop():
            prev = self.is_capslock_on()
            while self.running:
                now = self.is_capslock_on()
                if now != prev:
                    self.capslock_toggled.emit(now)
                    prev = now
                time.sleep(0.05)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False

    def is_capslock_on(self):
        import ctypes
        return ctypes.WinDLL("User32.dll").GetKeyState(0x14) & 1 == 1


def turn_off_capslock():
    def isCapslock_ON():
        return ctypes.WinDLL("User32.dll").GetKeyState(0x14) & 1 == 1
    
    if isCapslock_ON():
        keyboard.send("caps lock")


def KB_show_ui():
    overlay.show()
    menu.show()
    searchbar.show()

    # > Trên trái -> kiểm port Unsafe
    unsafe_ports = list(getglobal_UnsafeSet() or [])
    if unsafe_ports:
        unsafe_ports.insert(0, "----- PORT ĐÃ MỞ -----")
        manager.signal.send_top_left.emit("\n".join(unsafe_ports), 3000)

    # > Trên phải -> kiểm port Safe
    safe_ports = list(getglobal_safeSet() or [])
    if safe_ports:
        manager.signal.send_top_right.emit("\n".join(safe_ports), 3000)

    # Focus vào khung nhập
    searchbar.ensure_focus()
    searchbar.line_edit.clear()


def KB_hide_ui():
    manager.dismiss_manual_labels()
    menu.hide()
    searchbar.hide()
    searchbar.line_edit.clear()
    overlay.hide()
#endregion


#-----------------------------------------------------#
#region FUNCTION
def func_private():
    file = r"D:\Data\Images\NameSpace\LocknoFile.exe"
    dir_path = r"D:\Data\Images\NameSpace"
    exe_name = os.path.basename(file)
    # ✅ Mở exe trực tiếp
    subprocess.Popen([file], cwd=dir_path)


def func_arange():
    SAVE_FILE = "window_positions.json"
    restore_all_window_positions(SAVE_FILE)
    # save_all_window_positions(SAVE_FILE)


def func_panel():
    file = r"C:\Users\lukif\Desktop\FanSpam3\FanSpam3\__Server_Panel.py"
    dir_path = os.path.dirname(file)
    exe_name = os.path.basename(file)
    os.system(rf'C:\Windows\System32\cmd.exe /c "cd /d {dir_path} && start /b python {exe_name} && exit"')


def func_killpy():  # -> K dùng nữa
    os.system("taskkill /F /IM pythonw.exe")
    os.system("taskkill /F /IM python.exe")


def func_ReadMessSpam():
    global MESSAGE
    # ReadMessSpam._set_global_toReadmess(MESSAGE)
    result = ReadMessSpam.run()
    if result:
        MESSAGE.emit(f"[✓] {result}", 3000)
        return

#endregion


def wrap_mess(func, name=None, wait=None):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        MESSAGE.emit(f"[✓] Processed: {name or func.__name__}", wait or 3000)
        return result
    return wrapper


def wrap_checkport():
    while True:
        time.sleep(2)
        result = format_port_data()
        if result:
            for line in result:
                MESSAGE.emit(line, 3000)


if __name__ == "__main__":
    # === CONFIG MENU === #
    IMG_SIZE = 100
    IMG_OPACITY = 0.9
    IMG_COLOR = QColor("white")
    SPACING = 20
    MARGINS = 20

    # === CONFIG NOTIFICATION === #
    NOTIFY_MAX = 5                     # Tối đa số label hiển thị
    NOTIFY_TIMEOUT = 10000              # Thời gian tồn tại mỗi label (ms)
    NOTIFY_FADE_DURATION = 300         # Thời gian hiệu ứng mờ (ms)

    NOTIFY_MARGIN  = 50                 # Khoảng cách với mép màn hình
    NOTIFY_SPACING = 0                 # Khoảng cách giữa các label


    NOTIFY_STYLE = """
        QLabel {
            color: rgba(100, 225, 150, 1);
            font-size: 11pt;
            font-weight: bold;
            padding: 4px 6px;
        }
    """
    YELLOW = NOTIFY_STYLE.replace('color: rgba(100, 225, 150, 1)', 'color: rgba(213, 150, 0, 1)')
    RED    = NOTIFY_STYLE.replace('color: rgba(100, 225, 150, 1)', 'color: rgba(255, 0, 0, 0.9)')

    app = QApplication(sys.argv)
    img1 = QPixmap(r"D:\Data\Code Resource\circuit.png")
    img2 = QPixmap(r"D:\Data\Code Resource\Download Circuit logo design for free.ico")
    # img3 = QPixmap(r"D:\Data\Code Resource\mess.png")
    img4 = QPixmap(r"D:\Code\itachi.ico")
    IMG_PIXMAPS = [img1, img2, None, img4]
    IMG_PIXMAPS = [TransparentMenu.prepare_pixmap(p) for p in IMG_PIXMAPS]


    menu = TransparentMenu(IMG_PIXMAPS)
    searchbar = Searchbar.TransparentSearchBar(IMG_PIXMAPS)

    overlay = Overlay()
    overlay.shiftSignal.connect(lambda d: menu.shift_current(d))
    overlay.selectSignal.connect(lambda: menu.excute_select_current())


    keyListener = KeyListener()
    keyListener.capslock_toggled.connect(lambda on: KB_show_ui() if on else KB_hide_ui())
    keyListener.start() 

    keyboard.add_hotkey('F1',   lambda: keyboard.send('volume mute') ,                          suppress=True)
    keyboard.add_hotkey('F6',             wrap_mess(next_track,     "NEXT TRACK"    , 2000),    suppress=True)
    keyboard.on_press_key('F7', lambda _: wrap_mess(hide_window,    "HIDE"          , 3000)())
    keyboard.on_press_key('F8', lambda _: wrap_mess(doTransparent,  "TRANSPARENT"         )())


    manager = NotificationManager()
    MESSAGE = manager.sent_notification_signal()
    MESSAGE.emit("Ready", 1000)     # 1 giây
    Searchbar.send_func_module(manager)


    threading.Thread(target=wrap_checkport, daemon=True).start()
    # threading.Thread(target=func_ReadMessSpam, daemon=True).start()


    sys.exit(app.exec_())
