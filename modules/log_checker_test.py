from PyQt5.QtWidgets import(QMainWindow,
QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QTextBrowser, QPushButton, QToolBar, QAction, QStatusBar, QButtonGroup, QToolButton)
from PyQt5.QtGui import QPixmap, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QThread,QSize,QTimer
import subprocess
import os


class AudioThread(QThread):
	def run(self):
		subprocess.call(["aplay", 'message.wav'])
		
class LogCheckerWindow(QMainWindow):
	def __init__(self, parent=None):	
		super().__init__()
		# Define the self of the parent window 		
		self.parent = parent
		
		# Define where to place the child window and set the size of the child window fixed
		self.setGeometry(self.parent.pos().x()+1845,self.parent.pos().y(),250,220)
		self.setFixedSize(250,220)
		self.setWindowFlag(Qt.FramelessWindowHint)
		self.setWindowFlag(Qt.BypassWindowManagerHint) 

		# Create toolbar 
		toolbar=QToolBar("tool bar")		
		self.addToolBar(toolbar)
		toolbar.setIconSize(QSize(12,12))
		
		# Create button group, only one button in this group can be checked
		group=QButtonGroup(self, exclusive=True)
		

		# The state of audio self.unmute=True means sound on		
		self.unmute=True
		
		# Add mute button to toolbar
		mute_button=QToolButton()
		mute_button.setIcon(QIcon("icons/mute.png"))
		mute_button.setToolTip('Sound OFF')
		mute_button.setCheckable(True)
		mute_button.clicked.connect(self.on_mute)
		toolbar.addWidget(mute_button)
		group.addButton(mute_button)				
		
		# Add unmute button to toolbar
		unmute_button=QToolButton()
		unmute_button.setIcon(QIcon("icons/unmute.png"))
		unmute_button.setToolTip('Sound ON')
		unmute_button.setCheckable(True)
		unmute_button.setChecked(True)
		unmute_button.clicked.connect(self.on_unmute)
		toolbar.addWidget(unmute_button)
		group.addButton(unmute_button)	
		
		# Add close button
		spacer=QLabel("                                          ")
		toolbar.addWidget(spacer)
		
		close_button=QToolButton()
		close_button.setIcon(QIcon("icons/close.png"))
		close_button.setIconSize(QSize(20,20))
		close_button.setToolTip('Close window')
		close_button.clicked.connect(self.on_close)
		toolbar.addWidget(close_button)
		
		# Add a central widget to the child window
		self.window=QWidget()
		self.setCentralWidget(self.window)
		self.window_layout=QVBoxLayout()
		self.window.setLayout(self.window_layout)

		# Make the whole window movable
		self.offset=None
	
	def on_mute(self):
		self.unmute=False
		print('on_mute pressed ', self.unmute)

	def on_unmute(self):
		self.unmute=True
		print('on_unmute pressed', self.unmute)

	def on_close(self):
		self.close()
		
	def display(self):
		
		# Make display green for 5s when message arrive
		self.setStyleSheet('QMainWindow {background-color: #C1FFC1;}')
		self.timer = QTimer()
		self.timer.start(5000)
		self.timer.timeout.connect(lambda: self.setStyleSheet(''))
		 	
	
		# Start thread for audio clip playing
		self.audio_worker=AudioThread()
		if self.unmute:
			self.audio_worker.start()

		# Get the new olog entry
		entry=self.parent.oplogbook.getLogEntry(self.parent.last_entry_id)[0]

		# Author
		lineAuthor=QHBoxLayout() 
		
		person_icon=QIcon("icons/person.png")
		pixmap_person=person_icon.pixmap(20,20)
		person_icon_label=QLabel(self)
		person_icon_label.setPixmap(pixmap_person)
		person_icon_label.setFixedWidth(24)
		
		self.person_label=QLabel(self)
		if len(entry.author)>25:
			author=entry.author[:25]+'...'
		else:
			author=entry.author
		self.person_label.setText(author)
		lineAuthor.addWidget(person_icon_label)
		lineAuthor.addWidget(self.person_label)
		self.window_layout.addLayout(lineAuthor)
		
		# Date 
		lineDate=QHBoxLayout()

		clock_icon=QIcon("icons/clock.png")
		pixmap_clock=clock_icon.pixmap(20,20)
		clock_icon_label=QLabel(self)
		clock_icon_label.setPixmap(pixmap_clock)
		clock_icon_label.setFixedWidth(24)
		
		self.clock_label=QLabel(self)
		self.clock_label.setText(str(entry.timestamp).split('.')[0])
		
		lineDate.addWidget(clock_icon_label)
		lineDate.addWidget(self.clock_label)
		self.window_layout.addLayout(lineDate)

		#Entry Title 
		if len(entry.subject)>25:
			title=entry.subject[:25]+'...'
		else:
			title=entry.subject
		self.title_label=QLabel(self)
		self.title_label.setText(f'Title: <b>{title}</b>')
		self.window_layout.addWidget(self.title_label)
		
		# Entry body
		self.body_label=QLabel(self)
		self.body_label.setText(entry.body)
		scroll_area=QScrollArea()
		scroll_area.setWidget(self.body_label)
		scroll_area.setWidgetResizable(True)
		self.body_label.setStyleSheet('QLabel {background-color: white;}')
		self.window_layout.addWidget(scroll_area) 
		
		# Link
		lineLink=QHBoxLayout()
		self.link=QLabel(self)
		link_text=f'<a href="https://olog.esss.lu.se/logs/{entry.id}"> Olog Link: {entry.id}</a>'
		self.link.setText(link_text)
		self.link.linkActivated.connect(self.open_link)		
		lineLink.addWidget(self.link)
		self.window_layout.addLayout(lineLink)
		
	def open_link(self, url):
		print('open link')	
		subprocess.Popen(['firefox', url])

	def update_display(self):
		
		# Make display green for 5s when message arrive
		self.setStyleSheet('QMainWindow {background-color: #C1FFC1;}')
		self.timer = QTimer()
		self.timer.start(5000)
		self.timer.timeout.connect(lambda: self.setStyleSheet(''))		
		
		# Start thread for audio clip playing
		self.audio_worker=AudioThread()
		if self.unmute:
			self.audio_worker.start()

		# Get the new olog entry
		entry=self.parent.oplogbook.getLogEntry(self.parent.last_entry_id)[0]
		
		# Update author
		if len(entry.author)>25:
			author=entry.author[:25]+'...'
		else:
			author=entry.author
		self.person_label.setText(author)	

		# Update date
		self.clock_label.setText(str(entry.timestamp).split('.')[0])	

		# Update title
		if len(entry.subject)>25:
			title=entry.subject[:25]+'...'
		else:
			title=entry.subject
		
		self.title_label.setText(f'Title: <b>{title}</b>')

		# Update entry
		self.body_label.setText(entry.body)

		# Update link
		link_text=f'<a href="https://olog.esss.lu.se/logs/{entry.id}"> Olog Link: {entry.id}</a>'
		self.link.setText(link_text)
	
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.offset=event.globalPos()-self.pos()

		elif event.button() == Qt.MidButton:
			self.close()

	def mouseMoveEvent(self, event):
		if self.offset and Qt.LeftButton:
			self.move(event.globalPos()-self.offset)

	def mouseReleaseEvent(self, event):
		if event.button()==Qt.LeftButton:
			self.offset=None
		

		









