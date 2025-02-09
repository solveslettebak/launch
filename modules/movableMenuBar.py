from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu, QMenuBar, QMessageBox
)

# TODO: reimplement a QAction as "dragable", and then only trigger this stuff if mouse is over that class. Then use the standard 4-way "move" icon next to quit icon, and move launcher using this.
# This class implements QMenuBar, and adds functionality to drag and drop the application by dragging the menu bar itself.
class movableMenuBar(QMenuBar):
    def __init__(self):
        super().__init__()
        self.draggable = False
        self.offset = None
        
    #### --- Related to drag to move launcher stuff --- ####

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.draggable = False
        if event.button() == Qt.LeftButton:
            if (self.isOverMenuItem(event.pos()) == False) and (QtWidgets.qApp.activePopupWidget() is None):
                self.draggable = True
                self.offset = event.pos()
            else:
                self.draggable = False
                self.offset = None
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable:
            window = self.window()
            if window is not None:
                window.move(event.globalPos() - self.offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = False
            self.offset = None
        super().mouseReleaseEvent(event)

    def isOverMenuItem(self, pos):
        action = self.actionAt(pos)
        return isinstance(action, QAction)

    #### //// Related to drag to move launcher stuff --- ####
    
    # from menu file json.
    def setData(self, data):
        self.data = data
    
    # "[o]/rocket_launches/asdf"
    def _get_QAction_by_path(path):
    
        pathlist = path.split('/')
        currentlevel = self.data['menu']
        for menu in pathlist[:-1]:
            for each in currentlevel:
                pass
            currentlevel = currentlevel[menu]
        
        #if self.data['menu']
        
        #pass
        
    def changeMenuItem(path, **kw):
        pass
        
    # for the search function, to go through and able to run items directly
    def get_flat_list():
        pass
    