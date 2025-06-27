from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import sys
import os

class WebView(QMainWindow):
    def __init__(self, html_path):
        super().__init__()
        self.setWindowTitle("Weather Viewer")
        view = QWebEngineView()
        file_url = QUrl.fromLocalFile(os.path.abspath(html_path))
        view.load(file_url)
        self.setCentralWidget(view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebView("weather.html")
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())
