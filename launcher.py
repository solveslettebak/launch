#!/usr/bin/env python

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu
)
import sys
import json
import shlex
import os
from subprocess import Popen# ,CREATE_NEW_CONSOLE

from argumentDialog import argumentDialog
from quickLog import quickLog
from settingsDialog import settingsDialog
from phauncherDialog import phauncherDialog
from logCheck import logCheck

defaultSettings = {
  "fontsize":"16",
  "defaultLayoutFile":"SLconsole_menus.json",
  
}

# there is probably a better way to do this.. 
from common import settingsPath



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.resize(950,1)
        #self.move(700,-3) # -3 makes mouse "all the way up" still hover menus. :)
        
        # These two lines seem to make the window frameless in any(?) OS, and also for whatever reason stay on top on linux/gnome
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.BypassWindowManagerHint) 
        
        self.setStyleSheet("QMenu,QMenuBar,QMainWindow { background-color: lightblue;border: 1px solid black; } QMenu::item:selected { background-color: darkblue;}")

        # linux refuses to cooperate on this, so fuck it. Window somehow stays on top anyway, just not when told to.
        #self.pinOnTop = True
        #self.onPinToggle(self.pinOnTop)

        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        

        self.loadSettings()
        self.generateMenus(self.menubar)

        # self.setFixedSize(self.layout.sizeHint())

        # Logbook checker
        self.timer = QTimer()
        self.timer.start(1000)
        #self.timer.timeout.connect(self.logCheck)

        self.remoteUpdateTimer = QTimer()
        self.remoteUpdateTimer.start(4*1000)
        self.remoteUpdateTimer.timeout.connect(self.remoteUpdateCheck)
        self.updateInProgress = False
        self.updateFlag = False
        

    def remoteUpdateCheck(self):
        if self.updateFlag: # If this instance initiates the remote update, then we don't listen to that signal. 
            return
        try:
            data = open('update.flag','r').read()[0]
        except OSError:
            print('Problem reading update flag file. Giving up..')
            self.remoteUpdateTimer.stop()
        if data == '0' and self.updateInProgress: # perform the relaunch on a detected falling edge of the update flag.
            updateInProgress = False
            print('Remote update signal detected, relaunching..')
            self.onRelaunch()
        if data == '1' and not self.updateInProgress:
            print('Prepare update..')
            self.updateInProgress = True

    def clearUpdateFlag(self):
        print('qwer')
        self.updateFlag = False
        self.setRemoteUpdateTimer.stop()
        try:
            open('update.flag','w+').write('0')
        except OSError:
            print('Problem clearing update flag...')
        print('Relaunching this instance...')
        self.onRelaunch()
    

    def onInitiateUpdate(self):
        print('Initiating remote update of running instances of launcher')
        if self.updateFlag: # update already in progress.
            return
        self.updateFlag = True
        self.setRemoteUpdateTimer = QTimer()
        self.setRemoteUpdateTimer.start(10*1000)
        self.setRemoteUpdateTimer.timeout.connect(self.clearUpdateFlag)
        try:
            open('update.flag','w+').write('1')
        except OSError:
            print('Problem setting update flag. Giving up..')
            updateFlag = False
            self.setRemoteUpdateTimer.stop()
        print('done')

    def logCheck(self):
        self.qlog = logCheck(self)
        self.qlog.show()
        self.timer.stop()

    def parseMenus(file:str) -> dict:
        try:
            with open(file,'r') as file:
                data = file.read()
        except:
            print('well, shit') #ok, make this..better. later.
            return 
        
        

    def generateMenus(self, menubar):

        self.menubar.setMaximumWidth(900)


        q = QAction(QIcon("icons/quit.png"), "", self)
        q.triggered.connect(self.onQuit)
        menubar.addAction(q)

        # drag = dragable(QIcon("icons/drag.png"), "", self)
        # drag.hovered.connect(self.onMoveHover)

        # menubar.addAction(drag)

        icon = QAction(QIcon("icons/pin.png"),"",self)
        # icon = QPushButton(QIcon("quit.png"),"",self)
        # icon = QCheckBox("",self)
        # icon.setIcon(QIcon("quit.png"))
        icon.setCheckable(True)
        icon.setChecked(True)
        icon.triggered.connect(self.onPinToggle)
        # menubar.addAction(icon) # this doesn't work easily on linux, it seems.



        # Generate dynamic menus
        try:
            data = json.load(open(self.layoutFile))
        except json.decoder.JSONDecodeError as e:
            print(self.layoutFile,': Invalid JSON - aborting')
            print('Running json.tool...')
            os.system('python -m json.tool '+self.layoutFile)
            self.onQuit()

        # read tree structured menus from .json and produce pyqt menu structure.
        def recursive_read(menu, indent, currentmenu):
            for each in menu:

                # submenu
                if "menu" in each:
                    assert "name" in each
                    newmenu = currentmenu.addMenu(each['name'])
                    newmenu.setToolTipsVisible(True)
                    newmenu.setFont(QFont('Arial',self.fontSize - 2))
                    recursive_read(each['menu'], indent + 1, newmenu)

                # link/menu-item
                else:
                    if 'separator' in each:
                        if indent == 0:
                            currentmenu.addAction(QAction("-",self))
                        else:
                            currentmenu.addSeparator()
                        continue

                    assert 'name' in each and 'link' in each

                    # new terminal option? todo.. handle more arguments in same way as "datapack" for commandline

                    if "icon" in each:
                        newAction = QAction(QIcon('icons/'+each["icon"]), each["name"], self)
                    else:                    
                        newAction = QAction(each['name'],self)

                    newAction.setToolTip(each['description'] if "description" in each else "no description") 


                    link = each['link']
                    if "arguments" in each: #let's also check the value eventually...
                        datapack = {}
                        datapack['h_arg'] = each['help_arg'] if "help_arg" in each else ""
                        datapack['m_arg'] = each['mandatory_arg'] if "mandatory_arg" in each else ""
                        datapack['descr'] = each['description'] if "description" in each else "You no get help! You figure out!"
                        datapack['default'] = each['default_args'] if "default_args" in each else ""
                        datapack['name'] = each['name']
                        datapack['link'] = link

                        newAction.triggered.connect((lambda datapack: lambda: self.onMenuClickCommandline(datapack))(datapack)) # not winning any awards with this code...
                    else:
                        if link == '_phauncher':
                            newAction.triggered.connect(self.onPhauncher)
                        elif link == '_quit':
                            newAction.triggered.connect(self.onQuit)
                        elif link == '_reload':
                            newAction.triggered.connect(self.onReload)
                        elif link == '_settings':
                            newAction.triggered.connect(self.onSettings)
                        elif link == '_loadlayout':
                            newAction.triggered.connect(self.onLoadLayout)
                        elif link == '_quicklog':
                            newAction.triggered.connect(self.onQuickLog)
                        elif link == '_relaunch':
                            newAction.triggered.connect(self.onRelaunch)
                        elif link == '_updateall':
                            newAction.triggered.connect(self.onInitiateUpdate)
                        else:
                            if "cwd" in each:
                                link = {"cwd":each['cwd'], "link":each['link']}
                                print(link)
                            newAction.triggered.connect((lambda link: lambda: self.onMenuClick(link))(link)) # wtf

                    currentmenu.addAction(newAction)

        recursive_read(data['menu'], 0, menubar)

        searchBar = QLabel("asdf")
        searchContainer = QWidgetAction(self)
        searchContainer.setDefaultWidget(searchBar)
        menubar.addAction(searchContainer)

    # Shows dialog box for input of parameters to a commandline program, and executes it.
    def onMenuClickCommandline(self, d):

        link = d['link']
        name = d['name']
        help_arg = d['h_arg']
        mand_arg = d['m_arg']
        description = d['descr']
        default = d['default']

        self.argList = argumentDialog(self,link,name,help_arg,mand_arg,description, default)

        if self.argList.exec_() == 1:
            splitlist = shlex.split(link)
            splitlist += mand_arg.split()
            splitlist += self.argList.getParams().split()
            
            Popen(splitlist) #, creationflags=CREATE_NEW_CONSOLE)

    def onRelaunch(self):
        os.execv(__file__, sys.argv)

    def onPhauncher(self):
        phauncher = phauncherDialog(self.pos())
        if phauncher.exec_() == 1:
            if phauncher.helpRequest:
                self.onMenuClick("firefox https://confluence.esss.lu.se/display/~solveslettebak/Phauncher+help")
            else:
                self.onMenuClick("/usr/local/bin/phoebus")
        return

    def onMenuClick(self, text):
        print("os command:", text)
        # os.system(text)
        try:
            if type(text) is str:
                print(shlex.split(text))
                splitlist = shlex.split(text) # splits by spaces, but keeps quoted text unsplit. (on linux, maybe use posix=False option, to keep quotes)
                Popen(splitlist, preexec_fn=os.setpgrp) #,creationflags=CREATE_NEW_CONSOLE)
            else:
                splitlist = shlex.split(text['link'])
                Popen(splitlist, preexec_fn=os.setpgrp, cwd=text['cwd'])
        except FileNotFoundError as e:
            print('File not found')

    def changeSetting(self, field, value):
        data = json.load(open(settingsPath))
        data[field] = value
        json.dump(data,open(settingsPath,"w"))

    def loadSettings(self):
        if not os.path.isfile(settingsPath):
            open(settingsPath,'w+').write(open('default_settings.json','r').read())
        data = json.load(open(settingsPath))
        self.layoutFile = data["defaultLayoutFile"]
        self.fontSize = int(data["fontsize"])
        self.move(int(data['xpos']),int(data['ypos']))
        self.menubar.setFont(QFont('Arial',self.fontSize))

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

    def mouseReleaseEvent(self, event):
        print('mouse released')
        self.moveFlag = False
        self.changeSetting('xpos',str(self.pos().x()))
        self.changeSetting('ypos',str(self.pos().y()))
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

    # more work than it's worth to make this work on linux it seems. Putting on ice.
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
