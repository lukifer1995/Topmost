from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QHBoxLayout, QApplication,
    QGraphicsDropShadowEffect, QVBoxLayout
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QEvent, QTimer


import sys, os
import psutil
import subprocess
import re
import processinfo
import traceback


from checkport import *




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
        proc = psutil.Process(int(pid))
        return proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def kill_process_by_name(process_name):
    """Kill all processing """
    if not process_name: return
    if not process_name.endswith('exe'):
        process_name = f"{process_name}.exe".replace("..", ".")
    try:
        print_on_screen()
        result = subprocess.run(
            ["taskkill", "/IM", process_name, "/F"],
            capture_output=True,
            text=True,
            shell=False
        )
        print_on_screen("----- KILLIG PROCESSING... ------")
        print_on_screen(result.stdout)
        if result.stderr:
            print_on_screen("----- ERROR ------")
            print(result.stderr)
        print_on_screen('----- DONE ----------------------')
    except Exception as e:
        print("Lỗi khi chạy kill_process_by_name:", e)


def send_func_module(func):
    globals()["MESS"] = func


def print_on_screen(fstring=None):
    if "MESS" in globals():
        if not fstring:
            MESS.dismiss_manual_labels()                        # type: ignore
        else:
            MESS.signal.send_bottom_left.emit(fstring, 3000)    # type: ignore    
    else:   print(f"{fstring}")



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
        self.search_timer.timeout.connect(self.process_info)

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
        if not text: print_on_screen()  # ~> xóa lúc clear
        self.last_text = text           # Lưu lại nội dung để xử lý sau
        self.Command = ""

        text = text.lower()
        # ~~> Command : Dừng lâu ms kích hoạt
        if text.startswith('/'):
            self.search_timer.start(10000)


        elif text.startswith('cls'):
            self.Command = "CLS"


        if text.startswith('/kill') or text.startswith('kill'):
            try:
                self.Command = "KILL"
                self.last_text = text.split(" ")[-1]
            except : pass


        elif text.startswith('/whe') or text.startswith('wher'):
            try:     
                self.last_text = text.split(" ")[-1]
                self.Command = "WHERE"
            except : pass


        elif text.startswith('/dir') or text.startswith('dir'):
            try:     
                self.last_text = text.split(" ")[-1]
                self.Command = "DIR"
            except : pass


        else:
            self.search_timer.start(1000)


    def process_info(self):
        print_on_screen()
        text = self.last_text
        if len(text) > 3:
            # > PID / PORT
            if text.isdigit():
                self.set_avatar(1) # Loading
                name = find_process_by_pid(text) or find_process_by_port(text)
                if name:    
                    detail = processinfo.analyze_process_by_name(name)
                    if detail:  print_on_screen(detail)
                    else:       print_on_screen(f'\tKhông đủ quyền truy cập: {name}'+'\n'*15)
                else:
                    # print_on_screen()
                    self.set_avatar(2) # Done
            # > NAME PROCESS
            else:
                self.set_avatar(1) # Loading
                detail = processinfo.analyze_process_by_name(text)         
                if detail:  print_on_screen(detail)
                else:       print_on_screen(f'Không đủ quyền truy cập: {text}'+'\n'*15)   
                self.set_avatar(2) # Done


    def call_command_process(self):
        print('test', self.Command)
        if self.Command == "CLS":
            setglobal_UnsafeList([])
            setglobal_UnsafeExe(set())
            setglobal_safeExe(set())
            self.line_edit.setText('')
            self.repaint()

        elif self.Command == "WHERE":
            # ~> PID
            if self.last_text.isdigit():
                try:
                    p = psutil.Process(int(self.last_text))
                    print_on_screen()
                    print_on_screen(p.exe())
                    self.search_timer.start(10000)
                except : pass
            # ~> NAME
            else:
                self.process_info()


        elif self.Command == "DIR":
            parts = self.last_text.strip().split()
            if len(parts) >= 2:
                target = parts[-1]
                pid = None

                if target.isdigit():
                    pid = int(target)
                else:
                    try:
                        # Lấy danh sách tiến trình từ tasklist
                        result = subprocess.check_output(
                            ['tasklist', '/fo', 'csv', '/nh'], text=True
                        )
                        for line in result.splitlines():
                            items = line.strip().strip('"').split('","')
                            if len(items) >= 2 and target.lower() in items[0].lower():
                                pid = int(items[1])
                                break
                    except Exception as e: pass

                if pid is not None:
                    try:
                        p = psutil.Process(pid)
                        exe_dir = os.path.dirname(p.exe())
                        subprocess.run(f'explorer "{exe_dir}"')
                        print_on_screen()
                        print_on_screen(f"Explorer opened: {exe_dir}")
                    except: pass
                else:
                    print_on_screen(f"Process '{target}' not found.")
            else:
                print_on_screen()


    def set_avatar(self, index):
        pixmap = self.images[index % len(self.images)]
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            scaled = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled)
            self.icon_label.repaint()
        else:
            self.icon_label.clear()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            text = self.line_edit.text()
            self.line_edit.clear()
            if len(text)>3:
                if not self.Command or self.Command=="KILL":
                    self.img_index = 2
                    if text.isdigit():
                        name = find_process_by_port(text)
                        kill_process_by_name(name)
                    else:
                        kill_process_by_name(text)
                    self.set_avatar(self.img_index)
                else:
                    self.call_command_process()
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
        UNSAFEPORT = getglobal_UnsafeExe()
        self.move_to_center()
        self.activateWindow()
        self.raise_()
        self.line_edit.setFocus(Qt.OtherFocusReason)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    img1 = QPixmap(r"resource\kill.png")
    img2 = QPixmap(r"resource\pid.png")
    img3 = QPixmap(r"resource\port.png")
    img4 = QPixmap(r"resource\load.png")
    img5 = QPixmap(r"resource\done.png")

    IMG_PIXMAPS = [img1, img2, img3, img4, img5]


    bar = TransparentSearchBar(IMG_PIXMAPS)
    bar.move(400, 300)
    bar.show()
    sys.exit(app.exec_())
