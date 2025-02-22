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
        
        self.notifying = False # are we currently displaying a different icon (or something) to notify?
        self.menu_seen = False # ...and did we already see it
        
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
    
    #### --- Notify stuff ####
    
    def menu_clicked(self):
        self.menu_seen = True
        print('debugging stuff. clicked.')
        
    
    ######## 
    
    # from menu file json.
    def setData(self, data, flatmenu):
        self.data = data
        self.flatmenu = flatmenu
    
    def _get_item_by_path(self, path):
    
        pathlist = path.split('/')
        currentlevel = self.data['menu']
        for menu in pathlist[:-1]:
            found = False
            for i,each in enumerate(currentlevel):
                if each['name'] == menu:
                    currentlevel = currentlevel[i]['menu']
                    found = True
                    break
            if not found:
                print('did not find :(')
                return None
        
        for each in currentlevel:
            if each['name'] == pathlist[-1]:
                return each

        return None
        
    def notify_ID(self, ID):
        self.notifying = True
        self.flatmenu[ID]['QAction'].setIcon(QIcon('icons/quit.png'))
        
    # this one is probably obsolete...
    def notify(self, menuitem):
        item = self._get_item_by_path('[o]/rocket_launches/asdf')
        
        item['QAction'].setIcon(QIcon('icons/quit.png'))
        
        self.data['menu'][0]['menu'][0]['name'] = 'HURAY'
        self.data['menu'][0]['menu'][0]['QAction'].setText('HURAY')
        self.data['menu'][0]['menu'][0]['QAction'].setIcon(QIcon('icons\quit.png'))
        
    def changeMenuItem(self, path, **kw):
        pass
        
    # for the search function, to go through and able to run items directly
    def get_flat_menu(self):
        return self.flatmenu