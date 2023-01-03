import sys
import os
from PyQt5 import QtCore
import PyQt5.QtCore
from PyQt5.QtGui import QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QLineEdit,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget,
)
import json

class settingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(500,300)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.defaultMenuFile = "menus.json"

        self.setWindowTitle("Launcher")
        self.resize(800,30)

        self.pinOnTop = True
        self.onPinToggle(self.pinOnTop)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
        #self.setStyleSheet("")


        self.menubar = self.menuBar()
        # self.menubar.setPalette(QPalette.Inactive.)
        self.menubar.setFont(QFont('Times',14))
        self.menubar.setMaximumWidth(750)

        self.generateMenus(self.menubar)

    def generateMenus(self, menubar):


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
        data = json.load(open(self.defaultMenuFile))
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
            newbutton.triggered.connect((lambda d: lambda: self.onMenuClick(d))(d)) # jesus christ.
            menubar.addAction(newbutton)


        searchBar = QLabel("asdf")
        searchContainer = QWidgetAction(self)
        searchContainer.setDefaultWidget(searchBar)
        menubar.addAction(searchContainer)



        # asdf = QFormLayout()
        # asdf.addItem(searchbar)
        # self.setLayout(asdf)

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
        os.system(text)

    def onQuit(self):
        QApplication.quit()

    def onReload(self):
        self.menubar.clear()
        self.generateMenus(self.menubar)
        return

    def onLoadLayout(self):
        self.defaultMenuFile, _ = QFileDialog.getOpenFileName(self)
        # todo: check it's json and valid here... otherwise revert to old. Crash otherwise.
        print(self.defaultMenuFile)
        self.onReload()
        return

    def onSettings(self):
        settings = settingsDialog()
        settings.exec()
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
w.move(700,-3) # -3 makes mouse "all the way up" still hover menus. :)
w.show()
app.exec()
