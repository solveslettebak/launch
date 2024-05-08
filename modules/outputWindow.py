from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu, QMenuBar, QMessageBox
)

from datetime import datetime

class OutputWindow(QWidget):
    def __init__(self, out_standard, out_error, pos):
        super().__init__()
        self.resize(950,400)
        self.move(pos.x(), pos.y() + 30)
        self.setWindowTitle('stderr + stdout')
        layout = QGridLayout()
        self.setLayout(layout)
        self.teOut = QPlainTextEdit()
        layout.addWidget(self.teOut, 0, 0)
        self.clearBtn = QPushButton("Clear")
        self.clearBtn.clicked.connect(self.clear)
        layout.addWidget(self.clearBtn, 1, 0)

        f = open('output.log','r')
        self.text = f.readlines()
        f.close()
        if len(self.text) > 100:
            self.teOut.insertPlainText('See output.log for full log\n\n')
        for line in self.text[-100:]:
            self.teOut.insertPlainText(line)

        out_standard.register_callback(self.callback)
        out_error.register_callback(self.callback)

    def __del__(self):
        pass

    def clear(self):
        self.teOut.clear()

    def callback(self, text):
        self.teOut.insertPlainText(text)

class MyStream(object):
    def __init__(self, original):
        self.reg_cb = None
        self.original = original

    def write(self, text):
        #self.original(text)
        if text in [' ','',None]:
            return
        if text == '\n':
            f = open('output.log', 'a')
            f.write('\n')
            f.close()
            if self.reg_cb != None:
                self.reg_cb('\n')
            return

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f = open('output.log', 'a')
        text_out = time_str + ' : ' + text
        f.write(text_out)
        f.close()

        if self.reg_cb != None:
            self.reg_cb(text_out)

    def register_callback(self, cb):
        self.reg_cb = cb

    def flush(self):
        pass
