# todo:
# - notifikasjonsmulighet med valgfrie notifikasjoner om alt sammen
# - plugin til launcher
# - update countdown and an "update now".
# - checsum of relevant data to detect updates perhaps.
# - inkluder aurora
#   - inkluder meteorsvermer
#   - og alt annet jeg kan komme på. Kometer? Halleys? "Time before Halley.." ..
#   - birthday reminder også. Men splitt det ut i sin egen app, men den blir vel nesten identisk. Kan jeg vurdere 1 app stort sett, men 2 ulike GUIs? nei, for mange forskjeller tror jeg. API på den ene, json på den andre. Kunne prøvd å lage en interface som da håndterer begge, men... blir litt far fetched tror jeg. Bare lag ulike apper.
#   - husk todo-appen også.


import re
import sys
import requests
import json
from datetime import datetime
import pytz
import time
from pprint import pprint
from functools import partial
from copy import deepcopy
from subprocess import call
import plugin_mod as pm


#from PyQt5.QtWidgets import (
#    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QDialog, QMessageBox
#)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMessageBox

BROWSER_PATH = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

def convert_to_localtime(iso_string, format_string="%Y-%m-%d %H:%M:%S"):
    """
    Converts an ISO 8601 UTC time string to a formatted local time string.

    Parameters:
        iso_string (str): The ISO 8601 formatted string (e.g., "2025-01-10T22:00Z").
        format_string (str): The desired output format (default: "%Y-%m-%d %H:%M:%S %Z").

    Returns:
        str: The local time string in the desired format.
    """
    try:
        # Parse the input string as a UTC datetime object
        utc_time = datetime.strptime(iso_string, "%Y-%m-%dT%H:%MZ")
        utc_time = utc_time.replace(tzinfo=pytz.utc)

        # Convert UTC time to local time
        local_time = utc_time.astimezone()

        # Format the local time
        return local_time.strftime(format_string)

    except ValueError as e:
        return f"Invalid input format: {e}"

class RocketLaunchApp(QMainWindow):
    def __init__(self, plug):
        super().__init__()
        
        self.plug = plug
        
        self.plug.message_received.connect(self.msg_received)
        self.plug.focus.connect(self.focus)
        
        self.standalone = pm.STANDALONE
            
        self.ID = plug.ID
        self.firstUpdate = True
        
        self.initUI()
        

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5 * 60 * 1000)  # milliseconds
        
    def msg_received(self, msg):
        print('Received command:',msg)
        
    def focus(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def log(self, message):
        print('rocket:',message)
        #self.text_edit.append(f"[Plugin] {message}")
   
        
        
    def show_test(self):
        self.show()
        
    def hide_test(self):
        self.hide()
        self.timertest = QTimer()
        self.timertest.timeout.connect(self.show_test)
        self.timertest.start(3 * 1000)  # milliseconds
        

    def initUI(self):
        self.setWindowTitle('Rocket Launch Viewer')
        # self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)        
        
        self.resize(650,270)

        self.layout = QVBoxLayout()
        
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.refresh_button = QPushButton('Refresh Now', self)
        self.refresh_button.clicked.connect(self.refresh_clicked)
        self.hide_button = QPushButton('Hide')
        self.hide_button.clicked.connect(self.hide)
        self.quit_button = QPushButton('Quit')  
        self.quit_button.clicked.connect(QApplication.instance().quit)
        
        self.buttonBar = QHBoxLayout()
        self.buttonBar.addWidget(self.refresh_button)
        self.buttonBar.addWidget(self.hide_button)
        self.buttonBar.addWidget(self.quit_button)
        
        self.statusLabel = QLabel("Last update:")

        self.table = QTableWidget()
        self.table.setRowCount(5)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Company", "Name", "URL",])      


        self.layout.addLayout(self.buttonBar)
        self.layout.addWidget(self.statusLabel)
        self.layout.addWidget(self.table)
        #self.layout.addWidget(self.textbox)
        
        self.data = [] # list of dicts with launch data

        self.setLayout(self.layout)
        self.update_data()
        
    def refresh_clicked(self):
        self.firstUpdate = True # to not generate a popup/notification when manually refreshing
        self.update_data()

    def update_data(self):
        data_updated = False
        try:
            response = requests.get('https://fdo.rocketlaunch.live/json/launches/next/5')
            if response.status_code == 200:
                rawdata = response.json()
                data_updated = True
            else:
                #self.textbox.setText(f"Failed to fetch data: HTTP {response.status_code}")
                print(f"Failed to fetch data: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            #self.textbox.setText(f"Error fetching data: {e}")
            print(e)
            
        if data_updated == False:
            self.statusLabel.setText("Update failed")
            return
            
        olddata = deepcopy(self.data)
        
        self.data = []
            
        for launch in rawdata['result']:
            data = {}
            data['ID'] = launch['id']
            data['name'] = launch['name'] if launch['name'] is not None else 'unknown'
            data['location'] = launch.get('location', {}).get('name', 'Unknown Location')
            data['company'] = launch['provider']['name']
            data['url'] = re.search("(?P<url>https?://[^\s]+)", launch['quicktext']).group("url")
            data['date'] = convert_to_localtime(launch['t0']) if launch['t0'] is not None else 'unknown'
            
            self.data.append(data)
            
        if hash(str(olddata)) != hash(str(self.data)):
            print('Data has changed!')
            if self.firstUpdate == False:
                self.notify()
                
        self.firstUpdate = False
            
        self.statusLabel.setText("Last update: "+str(datetime.now()))
                
        self.display_data()
            
    def onLinkPress(self, URL):
        call([BROWSER_PATH,URL])
        print(URL)
    
    def notify(self):
        if self.standalone:
            self.notify_dialog = QMessageBox()
            self.notify_dialog.setText("Things arent the way they used to be!")
            self.notify_dialog.show()
        else:
            self.plug.notify()

    def display_data(self):
        # print(data["result"][0]['t0'])
        
        font = QFont("Arial", 11)
        
        
        for row, data in enumerate(self.data):
            
            date = data['date']
            company = data['company']
            name = data['name']
            url = data['url']
            for col,key in enumerate([date, company, name]):
                
                item = QTableWidgetItem(key + "   ")
                item.setFont(font)
                self.table.setItem(row, col, item)
                
            linkBtn = QPushButton("link")
            linkBtn.setFixedWidth(50)
            linkBtn.clicked.connect(partial(self.onLinkPress, url))
            self.table.setCellWidget(row, 3, linkBtn)

        #self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)    
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    
    print('Rocketdata: Running standalone:',pm.STANDALONE)
    
    plug = pm.start_pyqt(pm.ID)
    
    ex = RocketLaunchApp(plug)
    ex.show()
    sys.exit(app.exec_())
