from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QFont, QCursor, QPalette, QStandardItem, QStandardItemModel
from PyQt5.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QLabel, QMainWindow, QStatusBar, QToolBar, QLineEdit, QSpinBox, QVBoxLayout,
    QFormLayout, QPushButton, QDialog, QFileDialog, QWidgetAction, QWidget, QGridLayout, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QMenu, QHBoxLayout, QTreeView, QAbstractItemView, QComboBox,
)

import sys
from functools import partial
import json
from pydantic import BaseModel, validators
from datetime import timedelta
import pprint
from copy import deepcopy

class itemData(BaseModel):
    separator: bool = False
    name: str = ''
    menu: list = []
    description: str = ''
    link: str = ''
    icon: str = ''
    cwd: str = ''
    arguments: str = ''
    help_arg: str = ''
    mandatory_arg: str = ''
    default_args: str = ''
    hidden: bool = False
    run_on_start: bool = False
    run_at_interval: str = '' # timedelta = None
    confirm: bool = False
    shortcut: str = ''
    checkable: bool = False
    checked: bool = False


class TreeView(QWidget):

    def json_recursive(self, menu, indent, currentmenu):
        for each in menu:
            if "menu" in each:
                newmenu = QStandardItem(each['name'])
                newmenu.setData(itemData().model_validate(each))
                currentmenu.appendRow(newmenu)
                self.json_recursive(each['menu'], indent + 1, newmenu)
            else:
                if "separator" in each:
                    newmenu = QStandardItem('----------------')
                    newmenu.setData(itemData().model_validate({'separator':True}))
                else:
                    newmenu = QStandardItem(each['name'])
                    newmenu.setData(itemData().model_validate(each))
                currentmenu.appendRow(newmenu)

    def json_create_recursive(self, menu_entry, depth=0):
        entrydata = menu_entry.data()

        jsonentry = {}
        if entrydata.separator:
            jsonentry['separator'] = True
            return jsonentry # early out, because a separator cannot have children, or any other data

        jsonentry['name'] = entrydata.name

        if menu_entry.hasChildren():
            jsonentry['menu'] = []
            for i in range(menu_entry.rowCount()):
                jsonentry['menu'].append(self.json_create_recursive(menu_entry.child(i), depth + 1))
            return jsonentry # If it has children, it only has a name, and another menu. No other data

        jsonentry['link'] = entrydata.link # required field for any entry except menus and separators

        # the rest is non-mandatory data
        if entrydata.description != '':
            jsonentry['description'] = entrydata.description
        if entrydata.icon != '':
            jsonentry['icon'] = entrydata.icon
        if entrydata.cwd != '':
            jsonentry['cwd'] = entrydata.cwd
        if entrydata.arguments != '':
            jsonentry['arguments'] = entrydata.arguments
            if entrydata.help_arg != '':
                jsonentry['help_arg'] = entrydata.help_arg
            if entrydata.mandatory_arg != '':
                jsonentry['mandatory_arg'] = entrydata.mandatory_arg
            if entrydata.default_args != '':
                jsonentry['default_args'] = entrydata.default_args
        if entrydata.checkable:
            jsonentry['checkable'] = True
            if entrydata.checked:
                jsonentry['checked'] = True
        if entrydata.hidden:
            jsonentry['hidden'] = True
        if entrydata.run_on_start:
            jsonentry['run_on_start'] = True
        if (entrydata.run_at_interval != '') and (entrydata.run_at_interval != 'None'):
            jsonentry['run_at_interval'] = entrydata.run_at_interval
        if entrydata.confirm:
            jsonentry['confirm'] = True
        if entrydata.shortcut != '':
            jsonentry['shortcut'] = entrydata.shortcut
        return jsonentry

    def create_json_from_model(self):
        d = []
        for i in range(self.model.item(0).rowCount()):
            d.append(self.json_create_recursive(self.model.item(0).child(i)))
        return {"menu":d}

    def expandAll(self):
        self.tree.expandAll()

    def collapseAll(self):
        self.tree.collapseAll()

    def clickedItem(self, index):
        item = self.model.itemFromIndex(index)
        self.parent.editQStandardItem(item)

    def initroot(self):
        """ when loading a new tree, set a root item. It will not be shown or saved """
        self.rootitem = QStandardItem('root')
        self.rootitem.setData(itemData())
        self.model.appendRow(self.rootitem)
        self.tree.setRootIndex(self.model.indexFromItem(self.rootitem))

    def __init__(self, json_file, parent):
        super().__init__()
        self.parent = parent
        self.setFixedWidth(400)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        self.model = QStandardItemModel()
        self.tree.setModel(self.model)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.openMenu)
        self.tree.clicked.connect(self.clickedItem)

        json_dict = json.load(open(json_file))['menu']
        self.initroot()
        self.json_recursive(json_dict, 0, self.rootitem)

        # Enable drag and drop functionality
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeView.InternalMove)

        self.collapseAll()

    def openMenu(self, position):

        indexes = self.sender().selectedIndexes()

        tree_index_pos = self.tree.indexAt(position)
        if not tree_index_pos.isValid():
            return
        item = self.model.itemFromIndex(tree_index_pos)


        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        else:
            level = 0

        right_click_menu = QMenu()
        act_add = right_click_menu.addAction(self.tr("Add Child Item"))
        act_add.triggered.connect(partial(self.TreeItem_Add, level, tree_index_pos))

        right_click_menu.addSeparator()

        if item.parent() != None:
            insert_up = right_click_menu.addAction(self.tr("Insert Item Above"))
            insert_up.triggered.connect(partial(self.TreeItem_InsertUp, level, tree_index_pos))

            insert_down = right_click_menu.addAction(self.tr("Insert Item Below"))
            insert_down.triggered.connect(partial(self.TreeItem_InsertDown, level, tree_index_pos))

            right_click_menu.addSeparator()

            duplicate_up = right_click_menu.addAction(self.tr("Duplicate Item Above"))
            duplicate_up.triggered.connect(partial(self.TreeItem_DuplicateUp, level, tree_index_pos))

            duplicate_down = right_click_menu.addAction(self.tr("Duplicate Item Below"))
            duplicate_down.triggered.connect(partial(self.TreeItem_DuplicateDown, level, tree_index_pos))

            right_click_menu.addSeparator()

            insert_up_separator = right_click_menu.addAction(self.tr("Insert Separator Above"))
            insert_up_separator.triggered.connect(partial(self.TreeItem_InsertUpSeparator, level, tree_index_pos))

            insert_down_separator = right_click_menu.addAction(self.tr("Insert Separator Below"))
            insert_down_separator.triggered.connect(partial(self.TreeItem_InsertDownSeparator, level, tree_index_pos))

            right_click_menu.addSeparator()

            act_del = right_click_menu.addAction(self.tr("Delete Item"))
            act_del.triggered.connect(partial(self.TreeItem_Delete, item))

        right_click_menu.exec_(self.sender().viewport().mapToGlobal(position))

    def TreeItem_Add(self, level, tree_index_pos):
        self.tree.setExpanded(tree_index_pos, True)
        temp_key = QStandardItem('xx')
        temp_key.setData(itemData())
        self.model.itemFromIndex(tree_index_pos).appendRow([temp_key])

    def TreeItem_InsertUp(self, level, tree_index_pos):
        current_row = self.model.itemFromIndex(tree_index_pos).row()
        temp_key = QStandardItem('xx')
        temp_key.setData(itemData())
        self.model.itemFromIndex(tree_index_pos).parent().insertRow(current_row, [temp_key])

    def TreeItem_InsertDown(self, level, tree_index_pos):
        temp_key = QStandardItem('xx')
        temp_key.setData(itemData())
        current_row = self.model.itemFromIndex(tree_index_pos).row()
        self.model.itemFromIndex(tree_index_pos).parent().insertRow(current_row + 1, [temp_key])

    def TreeItem_DuplicateUp(self, level, tree_index_pos):
        item = self.model.itemFromIndex(tree_index_pos)
        current_row = item.row()
        copied_item = QStandardItem(item.data().name)
        copied_item.setData(deepcopy(item.data()))
        self.model.itemFromIndex(tree_index_pos).parent().insertRow(current_row, [copied_item])

    def TreeItem_DuplicateDown(self, level, tree_index_pos):
        item = self.model.itemFromIndex(tree_index_pos)
        current_row = item.row()
        copied_item = QStandardItem(item.data().name)
        copied_item.setData(deepcopy(item.data()))
        self.model.itemFromIndex(tree_index_pos).parent().insertRow(current_row + 1, [copied_item])

    def TreeItem_InsertDownSeparator(self, level, tree_index_pos):
        temp_key = QStandardItem('----------------')
        temp_key.setData(itemData().model_validate({'separator':True}))
        current_row = self.model.itemFromIndex(tree_index_pos).row()
        self.model.itemFromIndex(tree_index_pos).parent().insertRow(current_row + 1, [temp_key])

    def TreeItem_InsertUpSeparator(self, level, tree_index_pos):
        temp_key = QStandardItem('----------------')
        temp_key.setData(itemData().model_validate({'separator':True}))
        current_row = self.model.itemFromIndex(tree_index_pos).row()
        self.model.itemFromIndex(tree_index_pos).parent().insertRow(current_row, [temp_key])

    def TreeItem_Delete(self, item):
        item.parent().removeRow(item.row())
        if item == self.parent.edit_menu_item:
            self.parent.edit_menu_item = None

class MainWindow(QMainWindow):

    def __init__(self, filename):
        super().__init__()
        self.setWindowTitle("Launcher menu editor")
        self.resize(1200,650)
        self.filename = filename
        self._setupUI()
        self.edit_menu_item = None # which item we are currently editing. Used by the save entry functionality
        self.unsaved_changes_item = False
        self.unsaved_changes_file = False # TODO: this.


    def collapse(self):
        self.tree_view_widget.collapseAll()

    def expand(self):
        self.tree_view_widget.expandAll()

    def editQStandardItem(self, item):
        data = item.data()
        self.edit_menu_item = item
        self.saveBtn.setEnabled(False)
        self.saveBtn.setStyleSheet("")

        self.menudataLayout.itemAtPosition(0,1).widget().setText(data.name)
        self.menudataLayout.itemAtPosition(1,1).widget().setText(data.description)
        self.menudataLayout.itemAtPosition(2,1).widget().setText(data.link)
        self.menudataLayout.itemAtPosition(3,1).widget().setText(data.icon)
        self.menudataLayout.itemAtPosition(4,1).widget().setText(data.cwd)
        self.menudataLayout.itemAtPosition(5,1).widget().setChecked(True if data.arguments != '' else False)
        self.menudataLayout.itemAtPosition(6,1).widget().setText(data.help_arg)
        self.menudataLayout.itemAtPosition(7,1).widget().setText(data.mandatory_arg)
        self.menudataLayout.itemAtPosition(8,1).widget().setText(data.default_args)
        self.menudataLayout.itemAtPosition(9,1).widget().setChecked(data.hidden)
        self.menudataLayout.itemAtPosition(10,1).widget().setChecked(data.run_on_start)
        self.menudataLayout.itemAtPosition(11,1).widget().setText(str(data.run_at_interval))
        self.menudataLayout.itemAtPosition(12,1).widget().setChecked(data.confirm)
        self.menudataLayout.itemAtPosition(13,1).widget().setText(str(data.shortcut))
        self.menudataLayout.itemAtPosition(14,1).widget().setChecked(data.checkable)
        self.menudataLayout.itemAtPosition(15,1).widget().setChecked(data.checked)

        if data.separator:
            self.setEnabledRows([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], False)
        else:
            self.setEnabledRows([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], True)

            args = self.menudataLayout.itemAtPosition(5, 1).widget().isChecked()
            self.setEnabledRows([6, 7, 8], args)

            checkable = self.menudataLayout.itemAtPosition(14, 1).widget().isChecked()
            self.setEnabledRows([15], checkable)

        self.setEnabledRows([9,10,11,12],False) # these are yet to be implemented in launcher




    def saveEntry(self):
        if self.edit_menu_item == None:
            return

        data = self.edit_menu_item.data()
        data.name = self.menudataLayout.itemAtPosition(0,1).widget().text()
        data.description = self.menudataLayout.itemAtPosition(1,1).widget().text()
        data.link = self.menudataLayout.itemAtPosition(2,1).widget().text()
        data.icon = self.menudataLayout.itemAtPosition(3,1).widget().text()
        data.cwd = self.menudataLayout.itemAtPosition(4,1).widget().text()
        data.arguments = "True" if self.menudataLayout.itemAtPosition(5,1).widget().isChecked() else ""
        data.help_arg = self.menudataLayout.itemAtPosition(6,1).widget().text()
        data.mandatory_arg = self.menudataLayout.itemAtPosition(7,1).widget().text()
        data.default_args = self.menudataLayout.itemAtPosition(8,1).widget().text()
        data.hidden = self.menudataLayout.itemAtPosition(9,1).widget().isChecked()
        data.run_on_start = self.menudataLayout.itemAtPosition(10,1).widget().isChecked()
        data.run_at_interval = self.menudataLayout.itemAtPosition(11,1).widget().text()
        data.confirm = self.menudataLayout.itemAtPosition(12,1).widget().isChecked()
        data.shortcut = self.menudataLayout.itemAtPosition(13,1).widget().text()
        data.checkable = self.menudataLayout.itemAtPosition(14,1).widget().isChecked()
        data.checked = self.menudataLayout.itemAtPosition(15,1).widget().isChecked()

        self.edit_menu_item.setText(data.name)

        self.saveBtn.setEnabled(False)
        self.saveBtn.setStyleSheet("")

    def changes_made(self):
        self.changes_made_item = True
        self.saveBtn.setEnabled(True)
        self.saveBtn.setStyleSheet("background: red")
        

    def addRow(self, name, widget, descr='no description available'):
        label_name = QLabel(name)
        label_name.setToolTip(descr)
        widget.setToolTip(descr)
        self.menudataLayout.addWidget(label_name, self.row, 0)
        self.menudataLayout.addWidget(widget, self.row, 1)
        if isinstance(widget, QLineEdit):
            widget.textEdited.connect(self.changes_made)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(self.changes_made)
        self.row += 1
        return widget

    def setEnabledRows(self, rows:list, enabled):
        if enabled == None:
            s = self.sender()
            enabled = s.isChecked()
        for i in rows:
            self.menudataLayout.itemAtPosition(i,1).widget().setEnabled(enabled)

    def _setupEditMenu(self, layout):
        self.row = 0
        self.addRow('Name', QLineEdit(), 'Name of item as displayed in the menu')
        self.addRow('Description', QLineEdit(), 'Short description of the item')
        self.addRow('Link', QLineEdit(),'Command to run when item is clicked.')
        self.addRow('Icon', QLineEdit(),'Filename of icon, should be located in /launcher/icons/')
        self.addRow('CWD', QLineEdit(),'Current Working Directory. Launcher changes to this directory before running command.')
        argsCB = self.addRow('Arguments', QCheckBox(),'If true, a GUI popup is presented to the user, to input arguments for the command')
        argsCB.clicked.connect(partial(self.setEnabledRows, [6,7,8]))
        self.addRow('Help arg', QLineEdit(),'Argument to pass in order to get help text. Typically "-h" or similar')
        self.addRow('Mandatory arg', QLineEdit(),'Non-optional arguments')
        self.addRow('Default arg', QLineEdit(),'Default arguments, that can be changed by the user')
        self.addRow('Hidden', QCheckBox(),'Hide menu item from user. Typically together with "Run on start". Not implemented.').setEnabled(False)
        self.addRow('Run on start', QCheckBox(),'Run program when launcher starts. Not implemented').setEnabled(False)
        self.addRow('Run at interval', QLineEdit(),'Run at interval, given in minutes. Not implemented.').setEnabled(False)
        self.addRow('Confirm', QCheckBox(),'Give user a popup confirmation before running command. In case of sensitive comamnds. Not implemented.').setEnabled(False)
        self.addRow('Shortcut', QLineEdit(),'Currently accepts Ctrl, Alt, Shift and Fxx. Ensure shortcut is not taken. Requires pyxhook module.')
        checkableCB = self.addRow('Checkable', QCheckBox(),'Menu item as a check box. Currently only with internal commands.')
        checkableCB.clicked.connect(partial(self.setEnabledRows, [15]))
        self.addRow('Checked', QCheckBox(),'Default state of a checkable item.')

        self.editButtonBar = QHBoxLayout()
        self.menudataLayout.addLayout(self.editButtonBar, self.row, 0, 1, 2)
        self.saveBtn = QPushButton('Save')
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.saveEntry)
        self.editButtonBar.addWidget(self.saveBtn)

        self.helptext = QPlainTextEdit()
        self.helptext.setReadOnly(True)
        self.helptext.setEnabled(False)
        s  = '--HELP--\nName and link required\n\n'
        s += 'See existing menu items for examples. Any link starting with a "_" is a hard coded internal function. Otherwise, add any command that would run from shell. See also tooltips on all items.\n\n'
        s += 'CWD is current working directory. Sometimes needed to set this to location of script.\n\n'
        s += 'Some fields are disabled since they are not implemented in launcher yet.\n\n'
        self.helptext.setPlainText(s)
        self.menudataLayout.addWidget(self.helptext, self.row+1, 0, 1, 2)

    def loadFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'JSON files (*.json)')
        if filename:
            self.filename = filename
            self.update_file_label()
            self.tree_view_widget.model.clear()
            json_dict = json.load(open(filename))['menu']
            self.tree_view_widget.initroot()
            self.tree_view_widget.json_recursive(json_dict, 0, self.tree_view_widget.rootitem) #self.tree_view_widget.model)
            self.tree_view_widget.collapseAll()


    def saveFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'JSON files (*.json)')
        if filename:
            self.filename = filename
            self.update_file_label()
            d = self.tree_view_widget.create_json_from_model()
            json.dump(d, open(filename, 'w'), indent=4)

    def update_file_label(self):
        self.loaded_file_label.setText('Loaded file: ' + self.filename)

    def _setupUI(self):
        widget = QWidget()
        self.layout = QGridLayout()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)


        self.loaded_file_label = QLabel('Loaded file: ' + self.filename)
        self.loaded_file_label.setFixedHeight(15)
        self.layout.addWidget(self.loaded_file_label, 0, 0, 1, 2)

        self.tree_view_widget = TreeView(self.filename, self)
        self.layout.addWidget(self.tree_view_widget, 1, 0)

        self.menudataLayout = QGridLayout()
        self.layout.addLayout(self.menudataLayout, 1, 1, 2, 1)
        self._setupEditMenu(self.menudataLayout)

        self.buttonbar = QHBoxLayout()
        self.layout.addLayout(self.buttonbar, 2, 0)
        self.collapse_button = QPushButton('Collapse')
        self.collapse_button.clicked.connect(self.collapse)
        self.buttonbar.addWidget(self.collapse_button)
        self.expand_button = QPushButton('Expand')
        self.expand_button.clicked.connect(self.expand)
        self.buttonbar.addWidget(self.expand_button)
        self.load_file_button = QPushButton('Load file...')
        self.load_file_button.clicked.connect(self.loadFile)
        self.buttonbar.addWidget(self.load_file_button)
        self.save_file_button = QPushButton('Save as...')
        self.save_file_button.clicked.connect(self.saveFile)
        self.buttonbar.addWidget(self.save_file_button)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        filename = 'menus\winmenu.json'

    app = QApplication(sys.argv)
    w = MainWindow(filename)
    w.show()
    app.exec()
