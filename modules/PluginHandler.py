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
        
        self.parent = mainwin #mainwin makes no sense, change that
        
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400,200)
        # self.move(mainwin.pos().x()+500,mainwin.pos().y()+40)
        self.setWindowTitle("Plugin overview")

        layout = QGridLayout()
        self.setLayout(layout)
        
        buttonWidth = 70
        
        self.textMsg = []
        self.pingTimes = {}
        self.proc_status = {}
        
        for i,plugin in enumerate(plugins.values()):
            self.textMsg.append(None)
            
            buttonPing = QPushButton("Ping")
            self.pingTimes[plugin['ID']] = QLineEdit("-" if "lastPingTime" not in plugin else "{:.3f}".format(plugin['lastPingTime']))
            buttonFocus = QPushButton("Focus")
            buttonKill = QPushButton("Kill")
            self.textMsg[i] = QLineEdit()
            buttonSend = QPushButton("Send")
            
            # every day we stray further from God...
            buttonSend.clicked.connect(partial(lambda t, id: mainwin._send_command(t(), id), self.textMsg[i].text, plugin['ID']))
            
            buttonFocus.clicked.connect(partial(mainwin._send_command, "focus", plugin['ID']))
            buttonPing.clicked.connect(partial(mainwin.ping, plugin['ID']))
            buttonKill.clicked.connect(partial(mainwin.kill, plugin['ID']))
            
            buttonPing.setFixedWidth(buttonWidth)
            buttonFocus.setFixedWidth(buttonWidth)
            buttonKill.setFixedWidth(buttonWidth)
            buttonSend.setFixedWidth(buttonWidth)
            
            #proc_status = 'running' if plugin['process'].poll() is None else 'halted'
            self.proc_status[plugin['ID']] = QLineEdit()
            self.proc_status[plugin['ID']].setText('running' if plugin['process'].poll() is None else 'halted')
            
            self.count = False
            
            layout.addWidget(QLabel(plugin['name']), i, c())
            layout.addWidget(QLabel(str(plugin['handshake'])), i, c())
            layout.addWidget(QLabel(" "), i, c())
            layout.addWidget(buttonPing, i, c())
            layout.addWidget(self.pingTimes[plugin['ID']], i, c())
            layout.addWidget(QLabel("ms"), i, c())
            layout.addWidget(buttonFocus, i, c())
            layout.addWidget(buttonKill, i, c())
            layout.addWidget(self.textMsg[i], i, c())
            layout.addWidget(buttonSend, i, c())
            layout.addWidget(self.proc_status[plugin['ID']], i, c())
            
        self.parent.pong_received_signal.connect(self.pong_recv)
        self.parent.plugin_halted.connect(self.plugin_halted)
        
    def pong_recv(self, ID, ms):
        self.pingTimes[ID].setText("{:.3f}".format(ms))
        
    def plugin_halted(self, ID):
        self.proc_status[ID].setText("halted")
        




class PluginHandler(QObject):

    pong_received_signal = pyqtSignal(str, float) # ID, elapsed time in ms
    plugin_halted = pyqtSignal(str) # ID
    

    def __init__(self, parent):
    
        super().__init__()
    
        self.parent = parent
    
        # For storing all plugins, whether running/connected or not
        self.plugins = {}
        
        # Temporarily stores incoming connections until they are verified
        self.sockets = []
        
        self.server = QTcpServer()
        self.server.listen(QHostAddress("127.0.0.1"), 12345)
        self.server.newConnection.connect(self.handle_new_connection)     
        
    # on socket error. Which means lost connection. I think.
    def on_error(self, ID, error):
        print('[Launcher] - Lost connection to',self.plugins[ID]['name'],'. Error:',error)
        self.plugin_halted.emit(ID)
        

    #def kill_process(self, process):
    def kill_process(self, ID):
        process = self.plugins[ID].process
        print('killing',process)
        process.kill() # could also use terminate, but .. naah.
        process.wait()
        self.plugin_halted.emit(ID)
        
    # murderous function to ensure if we're going down, we're talking them all with us.
    def kill_all(self, double_tap = False):
        self.killtimers = [0,0,0,0]
        # suggest suicide, or kill. 
        for ID, values in self.plugins.items():
            self._send_command('die', ID)
            
            
            # TODO: get the timer stuff to work, so i give the application a chance to quit on its own
            # Will need some way to delay application exit probably. Because otherwise it quits before timers trigger
            # TODO: changed kill_process to take ID not process. update this section
            if double_tap:
                #self.kill_process(values['process'])
                print('Double tap: killing',values['name'])
                self.killtimers[i] = QTimer.singleShot(100, partial(self.kill_process, values['process']))
                #timer = QTimer.singleShot(100, lambda: self.kill_process(values['process']))
                self.killtimers.append(timer)
        
    def kill(self, ID, doble_tap = False):
        self._send_command('die', ID)
        
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
        
    def pong(self,ID):
        self._send_command('pong', ID)

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
                self.plugins[ID]['socket'].errorOccurred.connect(partial(self.on_error, ID))
                self.sockets.remove(client_socket)

            
            if i['ID'] not in self.plugins:
                print('Invalid ID')
                return
                
            if self.plugins[i['ID']]['handshake'] == False:
                print('Handshake not complete. Ignoring request.')
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
                #self.parent.notify(menuitem=self.plugins[i['ID']]['name'])
                self.parent.notify(item_ID=i['ID'])
                
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
        
    def _send_command(self, command, ID):
        msg_json = {'ID':ID, 'command':command}
        msg = json.dumps(msg_json)

        self.plugins[ID]['socket'].write(msg.encode())
        self.plugins[ID]['socket'].flush()        

    # meant as external interface to this class, for custom communication to plugins via menu items.
    def plugin_command(self, name, command):
        ID = self._name_to_ID(name)
        self._send_command(command, ID)

    def ping(self, ID):
        self.plugins[ID]['pingInProgress'] = True
        self.plugins[ID]['ping_start_time'] = time.perf_counter()
        print('Launcher ->',self.plugins[ID]['name'],': Ping?')
        self._send_command('ping', ID)
    
    def pong_received(self, ID):
        if not self.plugins[ID]['pingInProgress']:
            print('[Launcher] A wild pong received from',self.plugins[ID]['name'])
            return
            
        elapsed = (time.perf_counter() - self.plugins[ID]['ping_start_time']) * 1000
        print(self.plugins[ID]['name'],'-> Launcher: Pong! .. in',elapsed,'ms')
        self.plugins[ID]['pingInProgres'] = False    
        self.plugins[ID]['lastPingTime'] = elapsed    
        
        self.pong_received_signal.emit(ID, elapsed)
        
    def addPlugin(self, data, newAction):
    
        # dirty(?) way to make reload menus work
        for key,value in self.plugins.items():
            if value['name'] == data['name']:
                print('Plugin already registered. Skipping')
                return
    
        plug = {}
        plug['name'] = data['name']
        plug['location'] = str(Path(__file__).resolve().parent.parent / "plugins" / (data['plugin_name'] + '.py'))
        plug['ID'] = data['ID'] # str(uuid4())
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
            print('something bad happened. Could not start process:',e)

        
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
            self._send_command("focus", ID)
        else:
            self.start(ID)

    # create pyqt window with info on all plugins
    # todo: split if it makes sense, to separate data and GUI. only if it actually makes things easier though.
    def pluginInfo(self):
        self.qlog = PluginDisplay(self, self.plugins)
        self.qlog.show()