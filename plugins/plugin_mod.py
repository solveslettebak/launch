import sys
import json
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtCore import QTimer

ID = None

class SelfContainedPlugin:
    def __init__(self, ID, loop=None, cb=None, host="127.0.0.1", port=12345):
        self.socket = QTcpSocket()
        self.socket.connected.connect(self.on_connected)
        self.socket.readyRead.connect(self.read_message)
        self.socket.errorOccurred.connect(self.on_error)
        
        self.ID = ID
        
        # Loop callback
        if loop is not None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.loopcaller)
            self.timer.start(1000)
            self.loopfunction = loop
            
        self.cb = cb

        # Connect to the launcher
        self.socket.connectToHost(host, port)
        
    def loopcaller(self):
        code = self.loopfunction(self)
        print(code)
        if code == 0:
            QCoreApplication.quit()
        self.timer.start(1000)

    def on_connected(self):
        print("[Plugin] Connected to launcher.")
        self.handshake()
        self.send_message("Hello from Self-Contained Plugin!")

    def read_message(self):
        print('Reading message')
        while self.socket.bytesAvailable():
            message = self.socket.readAll().data().decode()
            print(f"[Plugin] Received: {message}")
            msg_dict = json.loads(message)
            print('ID check passed:',msg_dict['ID'] == self.ID)
            print('Command:',msg_dict['command'])

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
        # self.socket.write(json.dumps({'command':'handshake', 'ID':ID}).encode())

    def ping(self):
        self.command('ping')
        #self.socket.write(json.dumps({'command':'ping', 'ID':ID}).encode())

def start(ID, init, loop, cb):
    app = QCoreApplication(sys.argv)
    plugin = SelfContainedPlugin(ID=ID, loop=loop, cb=cb)
    init()
    sys.exit(app.exec_())


    
STANDALONE = False
if len(sys.argv) >= 2:
    ID = sys.argv[1]
else:
    STANDALONE = True