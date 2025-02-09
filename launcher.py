#!/usr/bin/env python


# todo
# search bar, integrated in launcher as internal function. Add optional shortcut.
    # fix shortcuts on windows
# Menu editor GUI: don't modify unknown fields.
# Manage todo list better. maybe in git repo.. 

menu_type = 'JSON' # YAML / JSON

# When true, stdout and stderr from launcher (not launched applications) are caught and redirected to output.log.
# TODO: allow both options, not just either option.
REDIRECT_OUTPUT = False

ALLOW_PLUGINS = True
ALLOW_SHORTCUTS = True

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject, QEvent
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu, QMenuBar, QMessageBox
)
from PyQt5.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

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
from functools import partial
from pathlib import Path
from uuid import uuid4
from pprint import pprint
import time

from modules.argumentDialog import argumentDialog
from modules.quickLog import quickLog
from modules.settingsDialog import settingsDialog
from modules.rePhauncherDialog import rePhauncherDialog
from modules.common import *
from modules.movableMenuBar import movableMenuBar
from modules.PluginHandler import PluginHandler, PluginDisplay

if REDIRECT_OUTPUT:
    from modules.outputWindow import OutputWindow, MyStream
    sys.stdout = MyStream(sys.stdout)
    sys.stderr = MyStream(sys.stderr)

useShortCuts = False
if ALLOW_SHORTCUTS and current_OS == 'linux':
    try:
        import pyxhook
    except ModuleNotFoundError:
        logging.info('pyxhook module not found. Ignoring keyboard shortcut functionality.')
        useShortCuts = False
    else:
        useShortCuts = True
        from modules.KeyboardListener import KeyboardListener


if ALLOW_SHORTCUTS and current_OS == 'windows':
    try:
        import keyboard
    except ModuleNotFoundError:
        logging.info('keyboard module not found. Ignoring keyboard shortcut functionality.')
        useShortCuts = False
    else:
        useShortCuts = True
        #from modules.KeyboardListener import KeyboardListener
    

# TODO replace this with pathlib. Is this used anywhere..? 🤔
# also put it in common
realpath = os.path.realpath(__file__)
SCRIPT_PATH = realpath[:realpath.rfind('/')+1]

        
        
class SearchBox(QDialog):
    def __init__(self,mainwin):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

        self.resize(100,50)
        self.move(mainwin.pos().x(),mainwin.pos().y()+40)
        self.setWindowTitle("QuickLog")
        # self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
            
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.inputfield = QLineEdit()
        self.inputfield.textChanged.connect(self._char_input)
        layout.addWidget(self.inputfield)
        
    def _char_input(self, text):
        print('text is',text)
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.resize(60,1)

        # These two lines seem to make the window frameless in any(?) OS, and also for whatever reason stay on top on linux/gnome
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.BypassWindowManagerHint) 
        self.setWindowFlag(Qt.WindowStaysOnTopHint)    # removed toggling of this. Never not needed, so.. here it is.   
        
        with open('css.css', 'r') as f:
            self.stylesheet = f.read()

        # TODO instead of this stuff, check if "developer.txt" exists in folder, and then treat this instance as dev. Or add developer locations in settings.json. Then an option for that in settings dialog - "this launcher location is developer"
        if os.getcwd().endswith('Johanna/launcher') or os.getcwd().endswith('dev/launcher'):
            self.setStyleSheet(self.stylesheet + 'QMenu,QMenuBar,QMainWindow { background-color: lightgreen;border: 1px solid black; }') # hack to turn it green when run from my dev-location.. 
        else:
            self.setStyleSheet(self.stylesheet)

        self.menubar = movableMenuBar()
        self.setMenuBar(self.menubar)
        self.menubar.setNativeMenuBar(False)

        if useShortCuts and current_OS == 'linux':
            self.keyboardlistener = KeyboardListener()
        
        if ALLOW_PLUGINS:
            self.plugins = PluginHandler(self)
        else:
            self.plugins = None
	
        self.loadSettings()
        self.generateMenus(self.menubar)
        
        self.notify_active = False
        

        
    # Function to grab attention about something. Should stop doing that once launcher is interacted with in any way.
    # if popup not False, then it is the string that should be displayed. Same with sound - give path to sound.
    # timeout can be None or given in seconds.
    # if called with ack=True, ignore all other parameters, and go back to normal mode (normal color, probably)
    # sound, if True, default sound to be used. If path, play that sound. if string, use system speech digitizer, if available.
    def notify(self, ack=False, start=True, timeout=None, changeColor = "#FF0000", popup = False, sound = False): 
        if ack:
            self.setStyleSheet(self.stylesheet)
            self.notify_active = False
            #self.notify_timer.stop()
            return
            
        if start:
            if changeColor is not False:
                self.setStyleSheet(self.stylesheet + 'QMenu,QMenuBar,QMainWindow { background-color: '+changeColor+';border: 1px solid black; }')
            self.notify_active = True
        else:
            self.setStyleSheet(self.stylesheet)
            self.notify_active = False
            return
        
        if timeout is not None:
            self.notify_timer = QTimer(self)  # Create a QTimer instance
            self.notify_timer.setSingleShot(True)  # Ensure it runs only once
            self.notify_timer.timeout.connect(partial(self.notify, start=False))  # Connect to function
            self.notify_timer.start(timeout * 1000)  # Start timer (5000 ms = 5 seconds)

    def generateMenus(self, menubar):

        # q = QAction(QIcon("icons/quit.png"), "", self)
        # q.triggered.connect(self.onQuit)
        # menubar.addAction(q)

        # TODO: one day... make this work. 
        #drag = QAction(QIcon("icons/drag.png"), "", self)
        #menubar.addAction(drag)

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

                # regular menu-item
                else:

                    # Separators
                    if 'separator' in each:
                        if indent == 0: # means the menu item is on the top-bar itself, not a sub-menu
                            currentmenu.addAction(QAction("-",self))
                        else:
                            currentmenu.addSeparator()
                        continue # no other checks needed for separators, so continue to next item.

                    # Required fields
                    assert ('name' in each) and ('link' in each)

                    # Create new QAction for the menu. With an icon if specified in the menu file.
                    if "icon" in each:
                        newAction = QAction(QIcon('icons/'+each["icon"]), each["name"], self)
                    else:                    
                        newAction = QAction(each['name'],self)
                        
                    # update existing menu structure with pyqt menu items
                    each['QAction'] = newAction

                    # Keyboard shortcut
                    if ("shortcut" in each) and useShortCuts:
                        link = each['link']
                        # TODO : re-add this functionality with true cross platform functionality
                        #self.keyboardlistener.registerShortcut(tuple(i for i in each['shortcut'].split(' ')), self.onMenuClick, link)

                    # Description
                    newAction.setToolTip(each['description'] if "description" in each else "no description") 

                    if "checkable" in each and each['checkable'] == True:
                        newAction.setCheckable(True)
                        if 'checked' in each:
                            newAction.setChecked(each['checked'] == True)
                        else:
                            newAction.setChecked(False)

                    # Command line arguments (all this can be improved by using functools partial, but... this stuff works.)
                    if "arguments" in each: # doesn't care about the value of arguments..
                        datapack = {}
                        datapack['h_arg'] = each['help_arg'] if "help_arg" in each else ""
                        datapack['m_arg'] = each['mandatory_arg'] if "mandatory_arg" in each else ""
                        datapack['descr'] = each['description'] if "description" in each else "You no get help! You figure out!"
                        datapack['default'] = each['default_args'] if "default_args" in each else ""
                        datapack['name'] = each['name']
                        datapack['link'] = each['link']

                        newAction.triggered.connect((lambda datapack: lambda: self.onMenuClickCommandline(datapack))(datapack)) # not winning any awards with this code...
                        currentmenu.addAction(newAction)
                        continue # and we're done. On to the next menu item.

                    link = each['link']
                    
                    if ALLOW_PLUGINS and "plugin" in each:
                        print('Plugin detected:',each['plugin_name'])
                        self.plugins.addPlugin(each, newAction)
                        # continue # this or not?

                    # Hard-coded internal functions.
                    if link == '_rephauncher':
                        newAction.triggered.connect(self.onRePhauncher) # there used to be a phauncher. It got updated -> rePhauncher.
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
                    #elif link == '_updateall':
                    #    newAction.triggered.connect(self.onInitiateUpdate)
                    elif link == '_autoramp_shortcut':
                        newAction.toggled.connect(self.autoramp_shortcut) # toggled. This assumes a checkbox.
                    elif link == '_output':
                        newAction.triggered.connect(self.showOutput)
                    elif link == '_test':
                        newAction.triggered.connect(self.codeTest)
                    elif link == '_search':
                        newAction.triggered.connect(self.showSearch)
                        if useShortCuts:
                            keyboard.add_hotkey('ctrl+alt+f12', self.showSearch)
                    elif link =='_plugin':
                        newAction.triggered.connect(partial(self.plugins.run, each['name']))
                    elif link == '_plugindata':
                        newAction.triggered.connect(self.showPluginData)
                    elif link.startswith('_plugin_command'):
                        plugname = link.split()[1]
                        command  = link.split()[2]
                        newAction.triggered.connect(partial(self.plugins.plugin_command, plugname, command))
                    else:

                        # Still here? Then we have a regular menu link on our hands.

                        if "cwd" in each: # if menu item specifies a different working directory, add it to the data sent to onMenuClick
                            link = {"cwd":each['cwd'], "link":each['link']}
                        newAction.triggered.connect(partial(self.onMenuClick, link)) 

                    # At last, add the new item to the menu.
                    currentmenu.addAction(newAction)


        menubar.setData(data) # hand it all over to the custom menu bar class
        recursive_read(data['menu'], 0, menubar)
        
        # self.menudata = data
        
        pprint(data['menu'][0]['menu'][0]['name'])
        #print(menubar)
        

    # TODO: Implement. This is called when launcher loads, so start keyboard monitoring from here, not in __init__ - also, this should be shortcuts in general, not autoramp.
    def autoramp_shortcut(self):
        pass
        
    
    def saveWindowPos(self):
        x = self.pos().x()
        y = self.pos().y()
        self.changeSetting('xpos',str(x))
        self.changeSetting('ypos',str(y))
        
    def showSearch(self):
        self.search = SearchBox(self)
        self.search.show()

    # Triggered by internal function "_test". For development use only.
    def codeTest(self):
        self.plugins.pluginInfo()
        #self.menudata['menu'][0]['menu'][0]['QAction'].setText('TEST')
        
    def showPluginData(self):
        self.plugins.pluginInfo()

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
    
        if self.plugins is not None:
            self.plugins.kill_all()
    
        if current_OS == 'linux':
            os.execv(__file__, sys.argv)
        elif current_OS == 'windows':
            os.execv(sys.executable, [sys.executable] + sys.argv)

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
               
                if current_OS == 'windows':
                    Popen(splitlist) #,creationflags=CREATE_NEW_CONSOLE)
                else:
                    Popen(splitlist, preexec_fn=os.setpgrp) #,creationflags=CREATE_NEW_CONSOLE)
            else:
                print('ASDF')
                splitlist = shlex.split(text['link'])
                logging.info(text['link'])
                print(current_OS)
                if current_OS == 'windows':
                    print(text['cwd'])
                    os.chdir(text['cwd'])
                    Popen(splitlist, cwd=text['cwd'])
                else:
                    Popen(splitlist, preexec_fn=os.setpgrp, cwd=text['cwd'])
        except FileNotFoundError as e:
            print('File not found',str(e))

    def changeSetting(self, field, value, owner='launcher'):
        data = json.load(open(newSettingsPath))
        if owner not in data:
            data[owner] = {}
        data[owner][field] = value
        json.dump(data,open(newSettingsPath,"w"), indent=4)

    def loadSettings(self, owner='launcher'):
        if not newSettingsPath.exists():
            print('Settings file not found, creating it with default values')
            open(newSettingsPath,'w+').write(open('default_settings.json','r').read())
        try:
            data = json.load(open(newSettingsPath))
        except json.decoder.JSONDecodeError:
            print('Could not read JSON settings file. Loading default settings instead.')
            data = json.load(open('default_settings.json','r').read())
            
        if owner in data:
            data = data[owner]
        else:
            data = {}
        
        # TODO: split this away, so loadSettings() is not performing anything on launcher
        if owner == 'launcher':
            self.layoutFile = 'menus/' + data["defaultLayoutFile"]
            self.fontSize = int(data["fontsize"])
            self.move(int(data['xpos']),int(data['ypos']))
            self.menubar.setFont(QFont('Arial',self.fontSize))
            
        return data

    def onQuickLog(self):
        self.qlog = quickLog(self)
        self.qlog.show()

    def onQuit(self):
        #if useShortCuts:
        #    self.keyboardlistener.stoplistening()
        self.saveWindowPos()
        if ALLOW_PLUGINS:
            self.plugins.kill_all()
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


def handle_exception(exc_type, exc_value, exc_traceback):
    s = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.exception('unhandled exception: %s',s)
    msg = 'Unhandled exception: '+str(exc_value)+'\n\n'
    if REDIRECT_OUTPUT:
        msg += 'See File -> Output, or ~/launcher_output.log'
    QMessageBox.critical(None, 'Launcher: Shit happened',msg)


# to intercept clicks and acknowledge notifications
class ClickInterceptor(QObject):
    def __init__(self, mainwin):
        super().__init__()
        self.mainwin = mainwin

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.mainwin.notify(ack=True)
        return super().eventFilter(obj, event)

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
    interceptor = ClickInterceptor(w)
    app.installEventFilter(interceptor)  # Global click detection
    w.show()
    app.exec()