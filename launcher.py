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
import shlex
from subprocess import Popen,CREATE_NEW_CONSOLE

from argumentDialog import argumentDialog
from quickLog import quickLog
from settingsDialog import settingsDialog

class dragable(QAction, QWidget):
    def __init__(self, icon, name, parent):
        super().__init__(icon, name, parent)
    def mouseMoveEvent(self, event):
        print('qwer')
        if Qt.LeftButton and self.moveFlag:
            self.move(event.globalPos() - self.movePosition)
            event.accept()

    def mousePressEvent(self, event):
        print('asdf')
        if event.button() == Qt.LeftButton:
            self.moveFlag = True
            self.movePosition = event.globalPos() - self.pos()
            # self.setCursor(QCursor(Qt.OpenHandCursor))
            event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.resize(950,1)
        self.move(700,-3) # -3 makes mouse "all the way up" still hover menus. :)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.BypassWindowManagerHint) # maybe fixes a linux issue...
        self.setStyleSheet("background-color: lightblue;border: 1px solid black;")

        self.pinOnTop = True
        self.onPinToggle(self.pinOnTop)

        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        # self.menubar.setPalette(QPalette.Inactive.)

        self.loadSettings()
        self.generateMenus(self.menubar)

        # self.setFixedSize(self.layout.sizeHint())

    def generateMenus(self, menubar):

        self.menubar.setMaximumWidth(850)

        q = QAction(QIcon("icons/quit.png"), "", self)
        q.triggered.connect(self.onQuit)
        menubar.addAction(q)

        drag = dragable(QIcon("icons/drag.png"), "", self)
        # drag.hovered.connect(self.onMoveHover)


        menubar.addAction(drag)

        icon = QAction(QIcon("icons/pin.png"),"",self)
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
        newAction = QAction(QIcon("icons/quit.png"),"Quit",self)
        newAction.triggered.connect(self.onQuit)
        newmenu.addAction(newAction)

        # Generate dynamic menus
        try:
            data = json.load(open(self.layoutFile))
        except json.decoder.JSONDecodeError as e:
            print(self.layoutFile,': Invalid JSON - aborting')
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

                if "arguments" in each: #let's also check the value eventually...
                    h_arg = each['help_arg'] if "help_arg" in each else ""
                    m_arg = each['mandatory_arg'] if "mandatory_arg" in each else ""
                    descr = each['description'] if "description" in each else "You no get help! You figure out!"
                    default = each['default_args'] if "default_args" in each else ""
                    name = each['name']
                    newAction.triggered.connect((lambda d: lambda: self.onMenuClickCommandline(d,name,h_arg,m_arg,descr,default))(d)) # this worked a bit too easily. Test with many items in menu etc.
                else:
                    newAction.triggered.connect((lambda d: lambda: self.onMenuClick(d))(d)) # wtf
                newmenu.addAction(newAction)

        menubar.addAction(QAction("-",self))

        for button in data['buttons']:
            newbutton = QAction(button['name'],self)
            d = button['link']
            newbutton.triggered.connect((lambda d: lambda: self.onMenuClick(d))(d))
            menubar.addAction(newbutton)

        qlog = QAction("QuickLog",self)
        qlog.triggered.connect(self.onQuickLog)
        menubar.addAction(qlog)

        searchBar = QLabel("asdf")
        searchContainer = QWidgetAction(self)
        searchContainer.setDefaultWidget(searchBar)
        menubar.addAction(searchContainer)

    # Shows dialog box for input of parameters to a commandline program, and executes it.
    def onMenuClickCommandline(self, link, name, help_arg, mand_arg, description, default):
        self.argList = argumentDialog(self,link,name,help_arg,mand_arg,description, default)

        if self.argList.exec_() == 1:
            splitlist = shlex.split(link)
            splitlist += mand_arg.split()
            splitlist += self.argList.getParams().split()
            Popen(splitlist, creationflags=CREATE_NEW_CONSOLE)

    def onMenuClick(self, text):
        print("os command:", text)
        # os.system(text)
        try:
            print(shlex.split(text))
            splitlist = shlex.split(text) # splits by spaces, but keeps quoted text unsplit. (on linux, maybe use posix=False option, to keep quotes)
            Popen(splitlist,creationflags=CREATE_NEW_CONSOLE)
        except FileNotFoundError as e:
            print('File not found')

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
            # self.setCursor(QCursor(Qt.OpenHandCursor))
            event.accept()
    #
    # def onMoveHover(self):
    #     self.moveHover = True
    #     print('qwerq')

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
