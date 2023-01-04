import sys
from PyQt5 import QtCore
import PyQt5.QtCore
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QLineEdit,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QVBoxLayout, QPlainTextEdit, QSpinBox,
)
import json
from subprocess import Popen,CREATE_NEW_CONSOLE

class quickLog(QDialog):
    def __init__(self,mainwin):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400,200)
        self.move(mainwin.pos().x()+500,mainwin.pos().y()+40)
        # self.setWindowFlag(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
        # self.setLayout(QGridLayout())
        # self.setLayout(QFormLayout())

        self.formGroupBox = QGroupBox("Send to olog:")
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


class settingsDialog(QDialog):
    def __init__(self,position):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(300,150)
        self.move(position.x(), position.y())

        self.data = json.load(open("settings.json"))

        self.formGroupBox = QGroupBox("Settings:")
        layout = QFormLayout()
        menufileinput = QLineEdit(self.data["defaultLayoutFile"])
        layout.addRow(QLabel("Default layout:"),menufileinput) # could also be a dropdown..
        spinbox = QSpinBox()
        spinbox.setValue(int(self.data["fontsize"]))
        spinbox.setMaximum(20)
        spinbox.setMinimum(6)
        layout.addRow(QLabel("Font size:"),spinbox)
        self.formGroupBox.setLayout(layout)

        okbutton = QDialogButtonBox.Ok
        # okbutton.pressed.connect(lambda: print("test"))
        buttonBox = QDialogButtonBox(okbutton | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.onClickOK)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def onClickOK(self):
        json.dump(self.data,open("settings.json","w"))
        self.accept()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.loadSettings()

        self.setWindowTitle("Launcher")
        self.resize(800,30)
        self.move(700,-3) # -3 makes mouse "all the way up" still hover menus. :)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: lightblue;border: 1px solid black;")

        self.pinOnTop = True
        self.onPinToggle(self.pinOnTop)

        self.menubar = self.menuBar()
        # self.menubar.setPalette(QPalette.Inactive.)

        self.generateMenus(self.menubar)

    def generateMenus(self, menubar):
        self.menubar.setFont(QFont('Times',self.fontSize))
        self.menubar.setMaximumWidth(750)
        q = QAction(QIcon("quit.png"), "", self)
        q.triggered.connect(self.onQuit)
        menubar.addAction(q)

        icon = QAction(QIcon("pin.png"),"",self)
        # icon = QPushButton(QIcon("quit.png"),"",self)
        # icon = QCheckBox("",self)
        # icon.setIcon(QIcon("quit.png"))
        icon.setCheckable(True)
        icon.setChecked(True)
        icon.triggered.connect(self.onPinToggle)
        menubar.addAction(icon)

        # Generate file menu
        newmenu = menubar.addMenu("File")
        newAction = QAction("Load layout...",self)
        newAction.triggered.connect(self.onLoadLayout)
        newmenu.addAction(newAction)
        newAction = QAction("Reload menus",self)
        newAction.triggered.connect(self.onReload)
        newmenu.addAction(newAction)
        newAction = QAction("Settings",self)
        newAction.triggered.connect(self.onSettings)
        newmenu.addAction(newAction)
        newmenu.addSeparator()
        newAction = QAction(QIcon("quit.png"),"Quit",self)
        newAction.triggered.connect(self.onQuit)
        newmenu.addAction(newAction)

        # Generate dynamic menus
        data = json.load(open(self.layoutFile))
        for menu in data['menus']:
            newmenu = menubar.addMenu(menu['name'])
            for each in menu['submenu']:
                if "separator" in each:
                    newmenu.addSeparator()
                    continue
                if "icon" in each:
                    newAction = QAction(QIcon(each["icon"]), each["name"], self)
                else:
                    newAction = QAction(each['name'],self)
                d = each['link']
                newAction.triggered.connect((lambda d: lambda: self.onMenuClick(d))(d)) # Just keep swimming...
                newmenu.addAction(newAction)

        menubar.addAction(QAction("-",self))

        for button in data['buttons']:
            newbutton = QAction(button['name'],self)
            d = button['link']
            newbutton.triggered.connect((lambda d: lambda: self.onMenuClick(d))(d)) # jesus christ.
            menubar.addAction(newbutton)

        qlog = QAction("QuickLog",self)
        qlog.triggered.connect(self.onQuickLog)
        menubar.addAction(qlog)

        searchBar = QLabel("asdf")
        searchContainer = QWidgetAction(self)
        searchContainer.setDefaultWidget(searchBar)
        menubar.addAction(searchContainer)

    def loadSettings(self):
        data = json.load(open("settings.json"))
        self.layoutFile = data["defaultLayoutFile"]
        self.fontSize = int(data["fontsize"])

    def onQuickLog(self):
        self.qlog = quickLog(self)
        self.qlog.show()

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.moveFlag:
            self.move(event.globalPos() - self.movePosition)
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moveFlag = True
            self.movePosition = event.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            event.accept()

    def onMenuClick(self, text):
        print("os command:", text)
        # os.system(text)
        try:
            Popen(text,creationflags=CREATE_NEW_CONSOLE)
        except FileNotFoundError as e:
            print('File not found')

    def onQuit(self):
        QApplication.quit()

    def onReload(self):
        self.menubar.clear()
        self.generateMenus(self.menubar)
        return

    def onLoadLayout(self):
        f, _ = QFileDialog.getOpenFileName(filter="*.json")
        if len(f) == 0:
            return
        try:
            str = json.loads(open(f).read())
        except ValueError as e:
            print('Invalid JSON file')
            return
        print(self.layoutFile)
        self.layoutFile = f
        self.onReload()
        return

    def onSettings(self):
        settings = settingsDialog(self.pos())
        if settings.exec():
            self.loadSettings()
        return

    def onPinToggle(self,e):
        if e:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.show()
        return

app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
