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
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject
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

from modules.argumentDialog import argumentDialog
from modules.quickLog import quickLog
from modules.settingsDialog import settingsDialog
from modules.rePhauncherDialog import rePhauncherDialog
from modules.common import settingsPath
from modules.movableMenuBar import movableMenuBar

if REDIRECT_OUTPUT:
    from modules.outputWindow import OutputWindow, MyStream
    sys.stdout = MyStream(sys.stdout)
    sys.stderr = MyStream(sys.stderr)



current_OS = 'linux' if not sys.platform.lower().startswith('win') else 'windows'
print('Current OS:',current_OS)


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
realpath = os.path.realpath(__file__)
SCRIPT_PATH = realpath[:realpath.rfind('/')+1]


# data = '{"key1": {"subkey1": "value1"}}{"key2": {"subkey2": "value2"}}{"key3": "value3"}'

# Use JSONDecoder to parse multiple JSON objects
def parse_multiple_json(data):
    decoder = json.JSONDecoder()
    pos = 0
    objects = []
    while pos < len(data):
        json_obj, pos = decoder.raw_decode(data, pos)
        objects.append(json_obj)
        # Skip any whitespace between JSON objects
        while pos < len(data) and data[pos].isspace():
            pos += 1
    return objects



class PluginDisplay(QDialog):
    def __init__(self,mainwin,plugins):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400,200)
        # self.move(mainwin.pos().x()+500,mainwin.pos().y()+40)
        self.setWindowTitle("QuickLog")
        # self.setWindowFlag(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
        # self.setLayout(QGridLayout())
        # self.setLayout(QFormLayout())
        
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        buttonWidth = 70
        
        textMsg = [0,0,0,0,0,0,0,0,0]
        
        for i,plugin in enumerate(plugins.values()):
            print(plugin)
            
            buttonPing = QPushButton("Ping")
            buttonFocus = QPushButton("Focus")
            buttonKill = QPushButton("Kill")
            textMsg[i] = QLineEdit()
            buttonSend = QPushButton("Send")
            
            buttonSend.clicked.connect(partial(mainwin.send_command, textMsg[i].text(), plugin['ID']))
            buttonFocus.clicked.connect(partial(mainwin.send_command, "focus", plugin['ID']))
            
            buttonPing.setFixedWidth(buttonWidth)
            buttonFocus.setFixedWidth(buttonWidth)
            buttonKill.setFixedWidth(buttonWidth)
            buttonSend.setFixedWidth(buttonWidth)
            
            proc_status = 'running' if plugin['process'].poll() is None else 'halted'
            proc_status_lineedit = QLineEdit()
            proc_status_lineedit.setText(proc_status)
            
            layout.addWidget(QLabel(plugin['name']), i, 0)
            layout.addWidget(QLabel(str(plugin['handshake'])), i, 1)
            layout.addWidget(QLabel(" "), i, 2)
            layout.addWidget(buttonPing, i, 3)
            layout.addWidget(buttonFocus, i, 4)
            layout.addWidget(buttonKill, i, 5)
            layout.addWidget(textMsg[i], i, 6)
            layout.addWidget(buttonSend, i, 7)
            layout.addWidget(proc_status_lineedit, i, 8)
        

class PluginHandler:
    

    def __init__(self):
        self.plugins = {}
        self.sockets = []
        
        self.server = QTcpServer()
        self.server.listen(QHostAddress("127.0.0.1"), 12345)
        self.server.newConnection.connect(self.handle_new_connection)        
        
    def handle_new_connection(self):
    
        # first check if we are expecting any incoming connection
    
        # client_socket = self.server.nextPendingConnection()
        client_socket = self.server.nextPendingConnection()
        
        # self.plugin_connection = PluginConnection(client_socket)
        # self.plugin_connection.message_received.connect(self.display_message)
        
        print("New connection received from port",client_socket.peerPort())
        # self.plugins[ID]['connected'] = True
        # self.plugins[ID]['conn'] = self.plugin_connection
        
        # newconnection = {'socket':client_socket, 'conn':plugin_connection}
        
        self.sockets.append(client_socket)
        
        client_socket.readyRead.connect(lambda: self.read_from_client(client_socket))
        
    def pong(self,ID):
        msg_json = {'ID':ID, 'command':'pong'}
        msg_text = json.dumps(msg_json)
        self.plugins[ID]['socket'].write(msg_text.encode())
        self.plugins[ID]['socket'].flush()
        
        
    def read_from_client(self, client_socket):
    
        msg_json = client_socket.readAll().data().decode()
        print('type msg_json:',type(msg_json))
        
        json_objects = parse_multiple_json(msg_json)

        print(json_objects)  

        for i in json_objects:
        
            #try:
            #    data = json.loads(i)
            #except json.JSONDecodeError as e:
            #    print('shit happened:',i)
            #    raise
            
            print('Read from client:',i)
            
            if i['command'] == 'handshake':
                ID = i['ID']
                if not ID in self.plugins:
                    print('ID not found in plugin list:',ID)
                    return
                self.plugins[ID]['handshake'] = True
                print('Handshake complete')
                self.plugins[ID]['socket'] = client_socket
                self.sockets.remove(client_socket)
            
            if i['ID'] not in self.plugins:
                print('Invalid ID')
                return
            
            if i['command'] == 'ping':
                self.pong(i['ID'])
        
        
    def send_command(self, command, ID):
        # command = command.text()
        msg_ID = {'ID':ID}
        msg_json = {'ID':ID, 'command':command}
        msg_else = msg_json
        msg = json.dumps(msg_json)
        print('Launcher sending:',msg)
        
        print(self.plugins[ID]['socket'])
        self.plugins[ID]['socket'].write(msg.encode())
        self.plugins[ID]['socket'].flush()        

    def send_message(self):
        if self.plugin_connection:
            self.plugin_connection.send_message("Hello from Launcher!")
        else:
            self.log("No plugin connected.")

    def display_message(self, msg_json): 
        msg_dict = json.loads(msg_json)
        print("Plugin:",msg_dict)

    def log(self, message):
        print('launcher log:',message)
        
    def runPlugin(self, name):
        pass
        
    def ping(ID=None):
        if ID is None:
            return
        
        
    def addPlugin(self, data):
        plug = {}
        plug['name'] = data['name']
        plug['location'] = str(Path(__file__).resolve().parent / "plugins" / (data['plugin_name'] + '.py'))
        plug['ID'] = str(uuid4())
        plug['handshake'] = False
        plug['pingInProgress'] = False
        
        self.plugins[plug['ID']] = plug        
   
        self.start(plug['ID'])
  
        # use self.running instead.. TODO
        print('process:','running' if plug['process'].poll() is None else 'unknown')
        
        # self.plugin_connection = None
        self.log("Waiting for plugin connection...")
        

        
    def start(self, ID):
        try:
            if current_OS == 'windows':
                self.plugins[ID]['process'] = Popen(['python',self.plugins[ID]['location'], ID]) #,creationflags=CREATE_NEW_CONSOLE)
            #else: # TODO: make this..
            #    Popen(splitlist, preexec_fn=os.setpgrp) #,creationflags=CREATE_NEW_CONSOLE)   
        except FileNotFoundError:
            pass
        except Exception as e:
            print('something bad happened. Could not start process. You see this shit?:',e)

        
    def running(self, ID):
        print('running:',ID)
        return self.plugins[ID]['process'].poll() is None
    
    def run(self, name):
        ID = None
        for each in self.plugins:
            print(self.plugins[each]['name'])
            
            if self.plugins[each]['name'] == name:
                ID = each
                break
        if ID == None:
            print('Plugin not found:',name)
            return
        if self.running(ID):
            self.send_command("focus", ID)
        else:
            self.start(ID)

    # create pyqt window with info on all plugins
    # todo: split if it makes sense, to separate data and GUI. only if it actually makes things easier though.
    def pluginInfo(self):
        self.qlog = PluginDisplay(self, self.plugins)
        self.qlog.show()    
        pprint(self.plugins)
        
        
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
        #self.move(200,3) # -3 makes mouse "all the way up" still hover menus. :)
        
        # These two lines seem to make the window frameless in any(?) OS, and also for whatever reason stay on top on linux/gnome
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.BypassWindowManagerHint) 
        
        with open('css.css', 'r') as f:
            stylesheet = f.read()

        # TODO instead of this stuff, check if "developer.txt" exists in folder, and then treat this instance as dev. Or add developer locations in settings.json. Then an option for that in settings dialog - "this launcher location is developer"
        if os.getcwd().endswith('Johanna/launcher') or os.getcwd().endswith('dev/launcher'):
            self.setStyleSheet(stylesheet + 'QMenu,QMenuBar,QMainWindow { background-color: lightgreen;border: 1px solid black; }') # hack to turn it green when run from my dev-location.. 
        else:
            self.setStyleSheet(stylesheet)

        if not current_OS == 'linux': # linux refuses to cooperate on this, so fuck it. Window somehow stays on top anyway, just not when told to.
            self.pinOnTop = True
            self.onPinToggle(self.pinOnTop)

        #self.menubar = self.menuBar()
        self.menubar = movableMenuBar()
        self.setMenuBar(self.menubar)
        self.menubar.setNativeMenuBar(False)

        if useShortCuts and current_OS == 'linux':
            self.keyboardlistener = KeyboardListener()
        
        if ALLOW_PLUGINS:
            self.plugins = PluginHandler()
	
        self.loadSettings()
        self.generateMenus(self.menubar)

        # Setup for remote update check.
        self.remoteUpdateTimer = QTimer()
        self.remoteUpdateTimer.start(4*1000)
        self.remoteUpdateTimer.timeout.connect(self.remoteUpdateCheck)
        self.updateInProgress = False
        self.updateFlag = False

# --- Remote update of application stuff. TODO: Move to separate class/file
# This stuff allows one instance of launcher to set a "relaunch flag" in a file in the launcher directory, in order to restart all running instances of launcher. It's pretty ugly, but.. it works.

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

        # q = QAction(QIcon("icons/quit.png"), "", self)
        # q.triggered.connect(self.onQuit)
        # menubar.addAction(q)

        # TODO: one day... make this work. 
        #drag = QAction(QIcon("icons/drag.png"), "", self)
        #menubar.addAction(drag)

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
                        self.plugins.addPlugin(each)
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
                    elif link == '_updateall':
                        newAction.triggered.connect(self.onInitiateUpdate)
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
                    else:

                        # Still here? Then we have a regular menu link on our hands.

                        if "cwd" in each: # if menu item specifies a different working directory, add it to the data sent to onMenuClick
                            link = {"cwd":each['cwd'], "link":each['link']}
                        newAction.triggered.connect(partial(self.onMenuClick, link)) 

                    # At last, add the new item to the menu.
                    currentmenu.addAction(newAction)

        recursive_read(data['menu'], 0, menubar)

#        searchBar = QLabel("asdf")
#        searchContainer = QWidgetAction(self)
#        searchContainer.setDefaultWidget(searchBar)
#        menubar.addAction(searchContainer)

    # TODO: Implement. This is called when launcher loads, so start keyboard monitoring from here, not in __init__ - also, this should be shortcuts in general, not autoramp.
    def autoramp_shortcut(self):
        pass
        
    def showSearch(self):
        print('search')
        self.search = SearchBox(self)
        self.search.show()
        print('showed search')

    # Triggered by internal function "_test". For development use only.
    def codeTest(self):
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
        print(text)
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

    def changeSetting(self, field, value):
        data = json.load(open(settingsPath))
        data[field] = value
        json.dump(data,open(settingsPath,"w"))

    def loadSettings(self):
        print(settingsPath)
        if not os.path.isfile(settingsPath):
            print('Settings file not found, creating it with default values')
            open(settingsPath,'w+').write(open('default_settings.json','r').read())
        try:
            data = json.load(open(settingsPath))
        except json.decoder.JSONDecodeError:
            print('Could not read JSON settings file. Loading default settings instead.')
            data = json.load(open('default_settings.json','r').read())
        self.layoutFile = 'menus/' + data["defaultLayoutFile"]
        self.fontSize = int(data["fontsize"])
        self.move(int(data['xpos']),int(data['ypos']))
        self.menubar.setFont(QFont('Arial',self.fontSize))
        print(data)

    def onQuickLog(self):
        self.qlog = quickLog(self)
        self.qlog.show()

    def onQuit(self):
        #if useShortCuts:
        #    self.keyboardlistener.stoplistening()
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
    msg = 'Unhandled exception: '+str(exc_value)+'\n\n'
    if REDIRECT_OUTPUT:
        msg += 'See File -> Output, or ~/launcher_output.log'
    QMessageBox.critical(None, 'Launcher: Shit happened',msg)



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

    

