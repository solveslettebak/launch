from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu, QMenuBar, QMessageBox
)
from PyQt5.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

from modules.common import *

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

class PluginDisplay(QDialog):
    def __init__(self,mainwin,plugins):
        def c():
            if self.count is False:
                self.count = 0
                return 0
            else:
                self.count += 1
                return self.count
            
        super().__init__()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400,200)
        # self.move(mainwin.pos().x()+500,mainwin.pos().y()+40)
        self.setWindowTitle("Plugin overview")
        # self.setWindowFlag(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background-color: lightblue;border: 1px solid black;")
        # self.setLayout(QGridLayout())
        # self.setLayout(QFormLayout())
        
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        buttonWidth = 70
        
        self.textMsg = []
        
        for i,plugin in enumerate(plugins.values()):
            self.textMsg.append(None)
            
            buttonPing = QPushButton("Ping")
            pingTime = QLineEdit("-" if "lastPingTime" not in plugin else "{:.3f}".format(plugin['lastPingTime']))
            buttonFocus = QPushButton("Focus")
            buttonKill = QPushButton("Kill")
            self.textMsg[i] = QLineEdit()
            buttonSend = QPushButton("Send")
            
            # every day we stray further from God...
            buttonSend.clicked.connect(partial(lambda t, id: mainwin.send_command(t(), id), self.textMsg[i].text, plugin['ID']))
            
            buttonFocus.clicked.connect(partial(mainwin.send_command, "focus", plugin['ID']))
            buttonPing.clicked.connect(partial(mainwin.ping, plugin['ID']))
            buttonKill.clicked.connect(partial(mainwin.kill, plugin['ID']))
            
            buttonPing.setFixedWidth(buttonWidth)
            buttonFocus.setFixedWidth(buttonWidth)
            buttonKill.setFixedWidth(buttonWidth)
            buttonSend.setFixedWidth(buttonWidth)
            
            proc_status = 'running' if plugin['process'].poll() is None else 'halted'
            proc_status_lineedit = QLineEdit()
            proc_status_lineedit.setText(proc_status)
            
            self.count = False
            
            layout.addWidget(QLabel(plugin['name']), i, c())
            layout.addWidget(QLabel(str(plugin['handshake'])), i, c())
            layout.addWidget(QLabel(" "), i, c())
            layout.addWidget(buttonPing, i, c())
            layout.addWidget(pingTime, i, c())
            layout.addWidget(QLabel("ms"), i, c())
            layout.addWidget(buttonFocus, i, c())
            layout.addWidget(buttonKill, i, c())
            layout.addWidget(self.textMsg[i], i, c())
            layout.addWidget(buttonSend, i, c())
            layout.addWidget(proc_status_lineedit, i, c())
        




class PluginHandler:
    

    def __init__(self, parent):
    
        self.parent = parent
    
        # For storing all plugins, whether running/connected or not
        self.plugins = {}
        
        # Temporarily stores incoming connections until they are verified
        self.sockets = []
        
        self.server = QTcpServer()
        self.server.listen(QHostAddress("127.0.0.1"), 12345)
        self.server.newConnection.connect(self.handle_new_connection)     
        
  
    def on_error(self, error):
        print('[Launcher] - there was an error:',error)

    # murderous function to ensure if we're going down, we're talking them all with us.
    def kill_all(self, double_tap = False):
        # suggest suicide, or kill. 
        for ID, values in self.plugins.items():
            self.send_command('die', ID)
            
        if double_tap:
            pass # kill processes
        
    def kill(self, ID, doble_tap = False):
        self.send_command('die', ID)
        
    def relaunch(self):
        self.kill_all()
        parent.onRelaunch()
               
    def handle_new_connection(self):
    
        # TODO: first check if we are expecting any incoming connection. For security etc..
        # TODO: Ensure connection comes from allowed peer host (localhost, per default, maybe exclusively)
    
        client_socket = self.server.nextPendingConnection()  
        print("New connection received from port",client_socket.peerPort())
        self.sockets.append(client_socket) 
        client_socket.readyRead.connect(lambda: self.read_from_client(client_socket))
        client_socket.errorOccurred.connect(self.on_error)
        
    def pong(self,ID):
        self.send_command('pong', ID)

    def read_from_client(self, client_socket):
    
        msg_json = client_socket.readAll().data().decode()
        json_objects = parse_multiple_json(msg_json)

        for i in json_objects:
    
            if i['command'] == 'handshake':
                ID = i['ID']
                if not ID in self.plugins:
                    print('ID not found in plugin list:',ID)
                    return
                self.plugins[ID]['handshake'] = True
                self.plugins[ID]['menuQAction'].setChecked(True)
                self.plugins[ID]['socket'] = client_socket
                self.sockets.remove(client_socket)
            
            if i['ID'] not in self.plugins:
                print('Invalid ID')
                return
                
            if self.plugins[i['ID']]['handshake'] == False:
                print('Handshake not complete.')
                return
                
            # Basic commands
            
            if i['command'] == 'ping':
                self.pong(i['ID'])
                
            elif i['command'] == 'pong':
                self.pong_received(i['ID'])
                
            # Launcher specific commands
                
            elif i['command'] == 'setmenu':
                print('set menu:',i['menu_ID'],':',i['name'])
                
            # general notify, should make launcher display something
            elif i['command'] == 'notify':
                self.parent.notify(menuitem=self.plugins[i['ID']]['name'])
                
            elif i['command'] == 'relaunch':
                self.parent.onRelaunch()
                
            elif i['command'] == 'save_parameter':
                try:
                    key = i['key']
                    value = i['value']
                except KeyError:
                    print('Received malformed key/value pair')
                else:
                    self.parent.changeSetting(key, value, self.plugins[i['ID']]['name'])
                
    def _name_to_ID(self, name):
        for ID,values in self.plugins.items():
            if values['name'] == name:
                return ID
        raise KeyError('Name not found: '+name)
        
        
    # todo: make it internal .. _send_command ..
    def send_command(self, command, ID):
        msg_json = {'ID':ID, 'command':command}
        msg = json.dumps(msg_json)

        self.plugins[ID]['socket'].write(msg.encode())
        self.plugins[ID]['socket'].flush()        

    # meant as external interface to this class, for custom communication to plugins via menu items.
    def plugin_command(self, name, command):
        ID = self._name_to_ID(name)
        self.send_command(command, ID)

    def ping(self, ID):
        self.plugins[ID]['pingInProgress'] = True
        self.plugins[ID]['ping_start_time'] = time.perf_counter()
        print('Launcher ->',self.plugins[ID]['name'],': Ping?')
        self.send_command('ping', ID)
    
    def pong_received(self, ID):
        if not self.plugins[ID]['pingInProgress']:
            print('[Launcher] A wild pong received from',self.plugins[ID]['name'])
            return
            
        elapsed = (time.perf_counter() - self.plugins[ID]['ping_start_time']) * 1000
        print(self.plugins[ID]['name'],'-> Launcher: Pong! .. in',elapsed,'ms')
        self.plugins[ID]['pingInProgres'] = False    
        self.plugins[ID]['lastPingTime'] = elapsed        
        
    def addPlugin(self, data, newAction):
        plug = {}
        plug['name'] = data['name']
        plug['location'] = str(Path(__file__).resolve().parent.parent / "plugins" / (data['plugin_name'] + '.py'))
        plug['ID'] = str(uuid4())
        plug['handshake'] = False
        plug['pingInProgress'] = False
        plug['menuQAction'] = newAction
        
        self.plugins[plug['ID']] = plug        
        self.start(plug['ID'])

    def start(self, ID):
        settings = self.parent.loadSettings(self.plugins[ID]['name'])
        params = [key+':'+value for key,value in settings.items()]
    
        try:
            if current_OS == 'windows':
                self.plugins[ID]['process'] = Popen(['python',self.plugins[ID]['location'], ID] + params) #,creationflags=CREATE_NEW_CONSOLE)
            #else: # TODO: make this..
            #    Popen(splitlist, preexec_fn=os.setpgrp) #,creationflags=CREATE_NEW_CONSOLE)   
        except FileNotFoundError:
            pass
        except Exception as e:
            print('something bad happened. Could not start process. You see this shit?:',e)

        
    def running(self, ID):
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