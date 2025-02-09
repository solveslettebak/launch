import sys
import plugin_mod as pm

#from PyQt5.QtWidgets import (
#    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QDialog, QMessageBox
#)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit


class RocketLaunchApp(QMainWindow):
    def __init__(self, plug):
        super().__init__()
        
        self.plug = plug
        
        # custom signals from plugin module
        self.plug.message_received.connect(self.msg_received)
        self.plug.focus.connect(self.focus)
        
        self.standalone = pm.STANDALONE
            
        self.ID = plug.ID
        self.firstUpdate = True
        
        self.initUI()

        
    def msg_received(self, msg):
        print('Received command:',msg)
        
    def focus(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def log(self, message):
        print('rocket:',message)   
        
    def initUI(self):
        self.setWindowTitle('Rocket Launch Viewer')
        self.resize(300,100)
        self.layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
 
        self.command_input = QLineEdit()
        self.command_send  = QPushButton("send")
        
        self.command_send.clicked.connect(self.command)
        
        self.layout.addWidget(self.command_input)
        self.layout.addWidget(self.command_send)

        self.setLayout(self.layout)
        
    def command(self):
        self.plug.command(self.command_input.text())





if __name__ == '__main__':

    app = QApplication(sys.argv)
    
    print('Rocketdata: Running standalone:',pm.STANDALONE)
    
    plug = pm.start_pyqt(pm.ID)
    
    ex = RocketLaunchApp(plug)
    ex.show()
    sys.exit(app.exec_())
