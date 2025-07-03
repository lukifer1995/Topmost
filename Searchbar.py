from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QHBoxLayout, QApplication,
    QGraphicsDropShadowEffect, QVBoxLayout
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QEvent, QTimer
import sys
from PyQt5.QtWidgets import QDesktopWidget

import psutil
import subprocess
import re
import processinfo

import subprocess
import re
import psutil
from checkport import getglobal_UnsafePort


def find_process_by_port(port: int):
    try:
        # Chạy netstat để lấy các dòng có chứa port
        result = subprocess.run(
            f'netstat -aon | findstr :{port}',
            capture_output=True,
            text=True,
            shell=True
        )

        if not result.stdout:
            return None

        pids = set()
        for line in result.stdout.strip().splitlines():
            parts = re.split(r'\s+', line)
            if len(parts) >= 5:
                pid = parts[-1]
                if pid.isdigit():
                    pids.add(int(pid))

        for pid in pids:
            try:
                proc = psutil.Process(pid)
                return proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None
    except Exception:
        return None


def find_process_by_pid(pid: int):
    try:
        proc = psutil.Process(pid)
        return proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def kill_process_by_name(process_name):
    if not process_name.endswith('exe'):
        process_name = f"{process_name}.exe".replace("..", ".")
    try:
        result = subprocess.run(
            ["taskkill", "/IM", process_name, "/F"],
            capture_output=True,
            text=True,
            shell=False
        )
        print("Kết quả:")
        print(result.stdout)
        if result.stderr:
            print("Lỗi:")
            print(result.stderr)
    except Exception as e:
        print("Lỗi khi chạy taskkill:", e)


def send_func_module(func):
    globals()["MESS"] = func


class TransparentSearchBar(QWidget):
    def __init__(self,  IMG_PIXMAPS=None):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setFixedSize(600, 80)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Neon style for main widget (self)
        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 50);
            border: 2px solid #47b2ff;
            border-radius: 30px;
        """)
        glow = QGraphicsDropShadowEffect(self)
        glow.setOffset(0,0)
        glow.setBlurRadius(0.8)
        glow.setColor(QColor("#47b2ff"))
        self.setGraphicsEffect(glow)


        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.process_text)

        # QLineEdit
        self.line_edit = QLineEdit()
        self.line_edit.setFont(QFont("Segoe UI", 20))
        self.line_edit.setFixedHeight(50)
        self.line_edit.setPlaceholderText("Process name or port")
        STYLE = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                border: none;
                padding-left: 36px;
                padding-right: 36px;
                color: #ffffff;
                font-size: 16px;
            }
        """
        self.line_edit.setStyleSheet(STYLE)
        self.line_edit.installEventFilter(self)
        self.line_edit.textChanged.connect(self.on_text_changed)

        # Avatar
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(50, 50)
        self.images = IMG_PIXMAPS
        self.img_index = 0
        self.set_avatar(self.img_index)


        # Widget trung gian để ngăn glow lan vào line_edit
        container = QWidget(self)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(16, 10, 16, 10)
        container_layout.setSpacing(10)
        container_layout.addWidget(self.icon_label)
        container_layout.addWidget(self.line_edit)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        self.hide()


    def move_to_center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2 + 200
        self.move(x, y)


    def ensure_focus(self):
        if not self.line_edit.hasFocus():
            self.raise_()
            self.activateWindow()
            self.line_edit.setFocus(Qt.OtherFocusReason)


    def on_text_changed(self, text):
        self.last_text = text  # Lưu lại nội dung để xử lý sau
        self.search_timer.start(400)  # Chờ 600ms không gõ thêm mới xử lý


    def process_text(self):
        text = self.last_text
        if not text:
            if "MESS" in globals():
                MESS.dismiss_manual_labels()                    # type: ignore
        else:
            if "MESS" in globals():
                MESS.dismiss_manual_labels()                    # type: ignore
                MESS.signal.send_bottom_left.emit('\t\tLoading ...\n\n\n', 3000) # type: ignore


        if len(text) > 3:
            if text.isdigit():
                self.img_index = 3
                rs = find_process_by_port(text)
                if not rs:  
                    rs = find_process_by_pid(text)
                if rs:
                    detail = processinfo.analyze_process_by_name(rs)
            else:
                self.img_index = 0
                detail = processinfo.analyze_process_by_name(text)
            
            if detail:  
                if "MESS" in globals():
                    MESS.dismiss_manual_labels()                    # type: ignore
                    MESS.signal.send_bottom_left.emit(detail, 3000) # type: ignore
                else:
                    print(detail)

            self.set_avatar(self.img_index)


    def set_avatar(self, index):
        pixmap = self.images[index % len(self.images)]
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            scaled = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled)
        else:
            self.icon_label.clear()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            text = self.line_edit.text()
            self.line_edit.clear()
            if text:
                if "MESS" in globals():
                    MESS.dismiss_manual_labels()                    # type: ignore
                self.img_index = 2
                if text.isdigit():
                    name = find_process_by_port(text.strip())
                    kill_process_by_name(name)
                else:
                    kill_process_by_name(text.strip())
                self.set_avatar(self.img_index)

        else:
            super().keyPressEvent(event)


    def eventFilter(self, source, event):
        if source == self.line_edit and event.type() == QEvent.Wheel:
            delta = event.angleDelta().y()
            self.img_index += 1 if delta > 0 else -1
            self.set_avatar(self.img_index)
            return True
        return super().eventFilter(source, event)


    def showEvent(self, event):
        global UNSAFEPORT
        super().showEvent(event)
        UNSAFEPORT = getglobal_UnsafePort()
        self.move_to_center()
        self.activateWindow()
        self.raise_()
        self.line_edit.setFocus(Qt.OtherFocusReason)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    img1 = QPixmap(r"D:\Data\Code Resource\circuit.png")
    img2 = QPixmap(r"D:\Data\Code Resource\Download Circuit logo design for free.ico")
    img3 = QPixmap(r"D:\Data\Code Resource\mess.png")
    img4 = QPixmap(r"D:\Code\itachi.ico")
    IMG_PIXMAPS = [img1, img2, img3, img4]


    bar = TransparentSearchBar(IMG_PIXMAPS)
    bar.move(400, 300)
    bar.show()
    sys.exit(app.exec_())
