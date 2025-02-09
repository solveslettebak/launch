import sys
import json
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
import time

ID = None

loop_interval = 1000 # ms

class SelfContainedPlugin(QObject):

    message_received = pyqtSignal(str)  # Signal carrying the received message
    focus = pyqtSignal()

    def __init__(self, ID, loop=None, cb=None, quit=None, host="127.0.0.1", port=12345):
        super().__init__()
        self.socket = QTcpSocket(self)
        self.socket.connected.connect(self.on_connected)
        self.socket.readyRead.connect(self.read_message)
        self.socket.errorOccurred.connect(self.on_error)
        self.ID = ID
        self.quit_call = quit
        self.pinging = False
        
        # Loop callback
        if loop is not None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.loopcaller)
            self.timer.start(loop_interval)
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
        if code == 0:
            self.onQuit()
            #QCoreApplication.quit()
        self.timer.start(loop_interval)

    def on_connected(self):
        print("[Plugin] Connected to launcher. Attempting handshake")
        self.handshake()

    def read_message(self):
        while self.socket.bytesAvailable():
            message = self.socket.readAll().data().decode()
            msg_dict = json.loads(message)
            if not msg_dict['ID'] == self.ID:
                print('ID check failed')
                continue
            
            if msg_dict['command'] == 'focus':
                self.focus.emit()
            elif msg_dict['command'] == 'pong':
                self.pong()
            elif msg_dict['command'] == 'die':
                self.onQuit()
            elif msg_dict['command'] == 'ping':
                self.command('pong')
            elif msg_dict['command'] == 'test':
                self.command('relaunch')
            else:
                if USING_PYQT:
                    self.message_received.emit(msg_dict['command'])
                else:
                    self.cb(msg_dict['command'])

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
        
    # TODO: expand to match launcher's accepted parameters
    def notify(self):
        self.command('notify')

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

global plugin
plugin = None

# for non-pyqt applications. Defines initialize function, loop function and a callback for messages
def start(ID, init, loop, quit, cb):
    global plugin
    USING_PYQT = False
    #app = QCoreApplication(sys.argv)
    app = QApplication(sys.argv)
    plugin = SelfContainedPlugin(ID=ID, loop=loop, quit=quit, cb=cb)
    init()
    sys.exit(app.exec_())

# for pyqt applications, provide only access to plugin API
def start_pyqt(ID):
    USING_PYQT = True
    plugin = SelfContainedPlugin(ID)
    return plugin
    
def set_loop_interval(interval):
    global loop_interval
    loop_interval = interval
    
def saveParameter(key, value):
    if (plugin is not None) or STANDALONE:
        plugin.command('save_parameter',  key=key, value=value) #{'key':key, 'value':value}
    else:
        print('Cannot save parameter, plugin not connected')
    
def getParameter(key, default):
    return parameters[key] if key in parameters else str(default)

USING_PYQT = None    

STANDALONE = False
if len(sys.argv) >= 2:
    ID = sys.argv[1]
else:
    STANDALONE = True
    
parameters = {}
    
# TODO: implement passing of saved parameters for plugin on startup
for each in sys.argv[2:]:
    pair = each.split(':')
    key = pair[0]
    arg = pair[1]
    parameters[key] = arg