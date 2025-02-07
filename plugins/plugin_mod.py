import sys
import json
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
import time

ID = None

class SelfContainedPlugin(QObject):

    message_received = pyqtSignal(str)  # Signal carrying the received message
    focus = pyqtSignal()

    def __init__(self, ID, loop=None, cb=None, quit=None, host="127.0.0.1", port=12345):
        super().__init__()
        self.socket = QTcpSocket(self)
        self.socket.connected.connect(self.on_connected)
        self.socket.readyRead.connect(self.read_message)
        self.socket.errorOccurred.connect(self.on_error)
        print('[TESTTEST] we are in init')
        self.ID = ID
        self.quit_call = quit
        self.pinging = False
        
        # Loop callback
        if loop is not None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.loopcaller)
            self.timer.start(1000)
            self.loopfunction = loop
            
        self.cb = cb

        # Connect to the launcher
        self.socket.connectToHost(host, port)
        
    def onQuit(self):
        if self.quit_call is not None:
            self.quit_call()
        QCoreApplication.quit()
        sys.exit()
        
    def loopcaller(self):
        code = self.loopfunction(self)
        print(code)
        if code == 0:
            self.onQuit()
            #QCoreApplication.quit()
        self.timer.start(5000)

    def on_connected(self):
        print("[Plugin] Connected to launcher. Attempting handshake")
        self.handshake()
        self.send_message("Hello from Self-Contained Plugin!")

    def read_message(self):
        while self.socket.bytesAvailable():
            message = self.socket.readAll().data().decode()
            print(f"[Plugin] Received: {message}")
            msg_dict = json.loads(message)
            print('ID check passed:',msg_dict['ID'] == self.ID)
            print('Command:',msg_dict['command'])
            if msg_dict['command'] == 'focus':
                self.focus.emit()
            elif msg_dict['command'] == 'pong':
                self.pong()
            elif msg_dict['command'] == 'die':
                self.onQuit()
            else:
                self.message_received.emit(msg_dict['command'])

    def send_message(self, message):
        if self.socket.state() == QTcpSocket.ConnectedState:
            msg_json = json.dumps({'ID':ID, 'command':'message', 'message':message}) 
            self.socket.write((msg_json + "\n").encode())
        else:
            print("[Plugin] Not connected to launcher.")

    def on_error(self, error):
        print(f"[Plugin] Socket error: {error}")
        
    def command(self, command, **kw):
        c = {'command':command, 'ID':ID}
        combined = {**c, **kw}
        self.socket.write(json.dumps(combined).encode())
            
    def handshake(self):
        self.command('handshake')

    def ping(self):
        self.pinging = True
        self.ping_start = time.perf_counter()
        self.command('ping')
        
    def pong(self):
        if self.pinging:
            self.pinging = False
            ping_end = time.perf_counter()
            elapsed = (ping_end - self.ping_start) * 1000
            print(f"Elapsed time: {elapsed:.6f} milliseconds")
        else:
            print('A wild pong appears!')
            
    def setMenu(self, menu_ID, name, link):
        self.command('setmenu', menu_ID = menu_ID, name = name, link = link)
        
    def saveSetting(self, setting, value):
        self.command('savesetting',value)
        
    def loadSetting(self, setting):
        pass

# for non-pyqt applications. Defines initialize function, loop function and a callback for messages
def start(ID, init, loop, quit, cb):
    #app = QCoreApplication(sys.argv)
    app = QApplication(sys.argv)
    print('[TEST] starting')
    plugin = SelfContainedPlugin(ID=ID, loop=loop, quit=quit, cb=cb)
    print('[TEST] plugin created')
    init()
    sys.exit(app.exec_())

# for pyqt applications, provide only access to plugin API
def start_pyqt(ID):
    plugin = SelfContainedPlugin(ID)
    return plugin
    
STANDALONE = False
if len(sys.argv) >= 2:
    ID = sys.argv[1]
else:
    STANDALONE = True