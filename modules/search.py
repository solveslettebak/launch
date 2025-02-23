from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject, QEvent
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu, QMenuBar, QMessageBox, QCompleter
)

# Known issue - will not handle items of the same name
class SearchBox(QDialog):
    def __init__(self,mainwin):
        super().__init__()
        #self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.resize(100,50)
        self.move(mainwin.pos().x() - 20,mainwin.pos().y()+20)
        self.setWindowTitle("Search")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
            
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        flatmenu = mainwin.menubar.get_flat_menu()
        self.keypairs = {i['name']:i['QAction'] for i in list(flatmenu.values())}
        self.word_list = list(self.keypairs.keys())

        self.completer = QCompleter(self.word_list, self)
        self.completer.setCaseSensitivity(False)  # Makes it case-insensitive
        self.completer.activated.connect(self._item_selected)
        self.completer.popup().setFixedWidth(150)
        
        self.inputfield = QLineEdit()
        self.inputfield.setCompleter(self.completer)
        self.inputfield.returnPressed.connect(self._enter_pressed)
        
        layout.addWidget(self.inputfield)
        

    def _item_selected(self, text):
        self.keypairs[text].trigger()
        self.accept()
        
    def _enter_pressed(self):
        text = self.inputfield.text().strip()

        matches = [word for word in self.word_list if word.lower().startswith(text.lower())]

        if len(matches) == 1:
            self.inputfield.setText(matches[0])  # Auto-fill the remaining text
            self._item_selected(matches[0])