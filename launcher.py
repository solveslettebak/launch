#!/usr/bin/env python

menu_type = 'JSON' # YAML / JSON

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu
)

if menu_type == 'YAML':
    import yaml
    import json # for settings. Change it all to YAML later.
else:
    import json
    
import sys
import shlex
import os
import warnings
from subprocess import Popen# ,CREATE_NEW_CONSOLE
from datetime import datetime
import traceback
import logging

from modules.argumentDialog import argumentDialog
from modules.quickLog import quickLog
from modules.settingsDialog import settingsDialog
from modules.rePhauncherDialog import rePhauncherDialog
from modules.common import settingsPath

useShortCuts = True
try:
    #import pyperclip
    import pyxhook
except ModuleNotFoundError:
    logging.info('pyxhook module not found. Ignoring keyboard shortcut functionality.')
    useShortCuts = False

if useShortCuts:
    from modules.KeyboardListener import KeyboardListener

current_OS = sys.platform.lower()

realpath = os.path.realpath(__file__)
SCRIPT_PATH = realpath[:realpath.rfind('/')+1]

class OutputWindow(QWidget):
    def __init__(self, out_standard, out_error, pos):
        super().__init__()
        self.resize(800,400)
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
    def __init__(self):
        self.reg_cb = None

    def write(self, text):
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

#sys.stdout = MyStream()
#sys.stderr = MyStream()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.resize(950,1)
        #self.move(700,-3) # -3 makes mouse "all the way up" still hover menus. :)
        
        # These two lines seem to make the window frameless in any(?) OS, and also for whatever reason stay on top on linux/gnome
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.BypassWindowManagerHint) 
        
        with open('css.css', 'r') as f:
            stylesheet = f.read()

        if os.getcwd().endswith('Johanna/launcher') or os.getcwd().endswith('dev/launcher'):
            self.setStyleSheet(stylesheet + 'QMenu,QMenuBar,QMainWindow { background-color: lightgreen;border: 1px solid black; }') # hack to turn it green when run from my dev-location.. 
        else:
            self.setStyleSheet(stylesheet)

        if not current_OS == 'linux': # linux refuses to cooperate on this, so fuck it. Window somehow stays on top anyway, just not when told to.
            self.pinOnTop = True
            self.onPinToggle(self.pinOnTop)

        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)

        if useShortCuts:
            self.keyboardlistener = KeyboardListener()
	
        self.loadSettings()
        self.generateMenus(self.menubar)

        # Setup for remote update check.
        self.remoteUpdateTimer = QTimer()
        self.remoteUpdateTimer.start(4*1000)
        self.remoteUpdateTimer.timeout.connect(self.remoteUpdateCheck)
        self.updateInProgress = False
        self.updateFlag = False

# --- Remote update of application stuff. TODO: Move to separate class/file


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


# --- 


    def generateMenus(self, menubar):

        self.menubar.setMaximumWidth(900)

        q = QAction(QIcon("icons/quit.png"), "", self)
        q.triggered.connect(self.onQuit)
        menubar.addAction(q)

        # TODO: one day... make this work.
        # drag = dragable(QIcon("icons/drag.png"), "", self)
        # drag.hovered.connect(self.onMoveHover)
        # menubar.addAction(drag)

        icon = QAction(QIcon("icons/pin.png"),"",self)
        icon.setCheckable(True)
        icon.setChecked(True)
        icon.triggered.connect(self.onPinToggle)

        # Generate dynamic menus
        if menu_type == 'YAML':
            data = yaml.safe_load(open("SLconsole_menus.yaml",'r'))
        else:
            try:
                data = json.load(open(self.layoutFile))    
            except json.decoder.JSONDecodeError as e:
                print(self.layoutFile,': Invalid JSON - aborting')
                print('Running json.tool...')
                os.system('python -m json.tool '+self.layoutFile)
                self.onQuit()

        # read tree structured menus from menu file and produce pyqt menu structure.
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

                    if useShortCuts:
                        if "shortcut" in each:
                            link = each['link']
                            #self.keyboardlistener.registerShortcut(('Ctrl','F12'), (lambda link: lambda: self.onMenuClick(link))(link))
                            #self.keyboardlistener.registerShortcut(tuple(i for i in each['shortcut'].split(' ')), (lambda link: lambda: self.onMenuClick(link))(link))
                            
                            self.keyboardlistener.registerShortcut(tuple(i for i in each['shortcut'].split(' ')), self.onMenuClick, link)

                    newAction.setToolTip(each['description'] if "description" in each else "no description") 

                    link = each['link']
                    if "arguments" in each: # doesn't care about the value of arguments..
                        datapack = {}
                        datapack['h_arg'] = each['help_arg'] if "help_arg" in each else ""
                        datapack['m_arg'] = each['mandatory_arg'] if "mandatory_arg" in each else ""
                        datapack['descr'] = each['description'] if "description" in each else "You no get help! You figure out!"
                        datapack['default'] = each['default_args'] if "default_args" in each else ""
                        datapack['name'] = each['name']
                        datapack['link'] = link

                        newAction.triggered.connect((lambda datapack: lambda: self.onMenuClickCommandline(datapack))(datapack)) # not winning any awards with this code...
                    else:
#                        if link == '_phauncher':
#                            newAction.triggered.connect(self.onPhauncher)

                        # Hard-coded internal functions.
                        if link == '_rephauncher':
                            newAction.triggered.connect(self.onRePhauncher)
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
                        elif link == '_autoramp_shortcut':
                            newAction.toggled.connect(self.autoramp_shortcut) # toggled. This assumes a checkbox.
                        elif link == '_output':
                            newAction.triggered.connect(self.showOutput)
                        else:
                            if "cwd" in each: # if menu item specifies a different working directory. Kind of a hack, needs to be handled nicer.
                                link = {"cwd":each['cwd'], "link":each['link']}
                            newAction.triggered.connect((lambda link: lambda: self.onMenuClick(link))(link)) # wtf

                    if "checkable" in each and each['checkable'] == True:
                        newAction.setCheckable(True)
                        if 'checked' in each:
                            newAction.setChecked(each['checked'] == True)
                        else:
                            newAction.setChecked(False)


                    # newAction.setCheckable(True)
                    # then just add a field to the function called, which will be bool - checked state.
                    currentmenu.addAction(newAction)

        recursive_read(data['menu'], 0, menubar)

#        searchBar = QLabel("asdf")
#        searchContainer = QWidgetAction(self)
#        searchContainer.setDefaultWidget(searchBar)
#        menubar.addAction(searchContainer)

    # TODO: Implement. This is called when launcher loads, so start keyboard monitoring from here, not in __init__ - also, this should be shortcuts in general, not autoramp.
    def autoramp_shortcut(self):
        pass

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

    def showOutput(self):
        self.out_win = OutputWindow(sys.stdout, sys.stderr, self.pos())
        self.out_win.show()
        

    def onRelaunch(self):
        os.execv(__file__, sys.argv)

    def onRePhauncher(self):
        phauncher = rePhauncherDialog(self.pos())
        if phauncher.exec_() == 1:
            if phauncher.helpRequest:
                self.onMenuClick("firefox https://confluence.esss.lu.se/display/~solveslettebak/Phauncher+help")
            else:
                self.onMenuClick("/usr/local/bin/phoebus")
        return

    def onMenuClick(self, text): # text is the command to send to OS
        try:
            if type(text) is str:
                logging.info(text)
                splitlist = shlex.split(text) # splits by spaces, but keeps quoted text unsplit. (on linux, maybe use posix=False option, to keep quotes)
                Popen(splitlist, preexec_fn=os.setpgrp) #,creationflags=CREATE_NEW_CONSOLE)
            else:
                splitlist = shlex.split(text['link'])
                logging.info(text['link'])
                Popen(splitlist, preexec_fn=os.setpgrp, cwd=text['cwd'])
        except FileNotFoundError as e:
            print('File not found')

    def changeSetting(self, field, value):
        data = json.load(open(settingsPath))
        data[field] = value
        json.dump(data,open(settingsPath,"w"))

    def loadSettings(self):
        if not os.path.isfile(settingsPath):
            print('Settings file not found, creating it with default values')
            open(settingsPath,'w+').write(open('default_settings.json','r').read())
        try:
            data = json.load(open(settingsPath))
        except JSONDecodeError:
            print('Could not read JSON settings file. Loading default settings instead.')
            data = json.load(open('default_settings.json','r').read())
        self.layoutFile = 'menus/' + data["defaultLayoutFile"]
        self.fontSize = int(data["fontsize"])
        self.move(int(data['xpos']),int(data['ypos']))
        self.menubar.setFont(QFont('Arial',self.fontSize))

    def onQuickLog(self):
        self.qlog = quickLog(self)
        self.qlog.show()

    # --- mouse moving stuff. Haven't figured out how to move the window from dragging the "move" icon yet.. work in progress.

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
        self.moveFlag = False
        self.changeSetting('xpos',str(self.pos().x()))
        self.changeSetting('ypos',str(self.pos().y()))
        event.accept()

    # // --- 


    def onQuit(self):
        if useShortCuts:
            self.keyboardlistener.stoplistening()
        QApplication.quit()
        sys.exit()

    def onReload(self):
        self.menubar.clear()
        self.generateMenus(self.menubar)
        return

    def onLoadLayout(self):
        filetype = '*.yaml' if menu_type == 'YAML' else '*.json'
        f, _ = QFileDialog.getOpenFileName(directory='menus', filter=filetype)
        if len(f) == 0:
            return
        try:
            if menu_type == 'YAML':
                str = yaml.safe_load(open(f).read())
            else:
                str = json.loads(open(f).read())
        except ValueError as e:
            print('Invalid menu format file')
            return
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


def handle_exception(exc_type, exc_value, exc_traceback):
    s = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.exception('unhandled exception: %s',s)
#    QMessageBox.critical(None, 'PVmon: Shit happened','Unhandled exception: '+str(exc_value)+'\n\nSee app.log')



if __name__ == "__main__":

    sys.excepthook = handle_exception

    logging.basicConfig(
        level=logging.DEBUG,
        #format = '%(asctime)s - %(levelname)s - %(message)s',
        format = '%(levelname)s - %(message)s',
        handlers = [
            #logging.FileHandler(SCRIPT_PATH + 'app.log'),
            logging.StreamHandler()
        ]
    )
    logging.info('Application started')

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()

    

