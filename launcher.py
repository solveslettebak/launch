from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit,
)
import sys
import json
from subprocess import Popen,CREATE_NEW_CONSOLE

from quickLog import quickLog
from settingsDialog import settingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.resize(950,30)
        self.move(700,-3) # -3 makes mouse "all the way up" still hover menus. :)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: lightblue;border: 1px solid black;")

        self.pinOnTop = True
        self.onPinToggle(self.pinOnTop)

        self.menubar = self.menuBar()
        # self.menubar.setPalette(QPalette.Inactive.)

        self.loadSettings()
        self.generateMenus(self.menubar)

        # self.setFixedSize(self.layout.sizeHint())

    def generateMenus(self, menubar):

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
        try:
            data = json.load(open(self.layoutFile))
        except json.decoder.JSONDecodeError as e:
            print('Invalid JSON - aborting')
            self.onQuit()

        for menu in data['menus']:
            if not "name" in menu:
                print('Warning: Missing main menu name')
                continue
            newmenu = menubar.addMenu(menu['name'])
            for each in menu['submenu']:
                if "separator" in each:
                    newmenu.addSeparator()
                    continue
                if not "name" in each:
                    print('Warning: Missing name for menu item')
                    continue
                if "icon" in each:
                    newAction = QAction(QIcon(each["icon"]), each["name"], self)
                else:
                    newAction = QAction(each['name'],self)
                if not "link" in each:
                    d = "empty"
                else:
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
        self.menubar.setFont(QFont('Times',self.fontSize))

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
        sys.exit()

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
