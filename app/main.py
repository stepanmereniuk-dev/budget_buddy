
from PySide6.QtWidgets import QApplication,QMainWindow, QWidget, QPushButton
from PySide6.QtCore import QSize,Qt

from pages.login_page import LoginPage
#from pages.login_page import 

import sys
screen_resolution = ()
phone_resoulution = ()

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_self()
        pass
    
    def setup_self(self):
        self.setWindowTitle("Budget buddy")
        self.setFixedSize(QSize(400, 300))
        pass


app = QApplication(sys.argv)
window = App()
window.show()
app.exec()
