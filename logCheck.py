from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLabel, QPlainTextEdit, QDialogButtonBox, QVBoxLayout

class logCheck(QDialog):
    def __init__(self,mainwin):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400,200)
        self.move(mainwin.pos().x()+500,mainwin.pos().y()+40)
        self.setWindowTitle("QuickLog")
        # self.setWindowFlag(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
        # self.setLayout(QGridLayout())
        # self.setLayout(QFormLayout())

        self.formGroupBox = QGroupBox("ASDF:")
        layout = QFormLayout()
        layout.addRow(QLabel("text:"),QPlainTextEdit())
        self.formGroupBox.setLayout(layout)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        #self.timer = QTimer()
        #self.timer.timeout.connect(self.accept)
        #self.timer.start(3000)
