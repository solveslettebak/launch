import json
import os

from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLineEdit, QLabel, QSpinBox, QDialogButtonBox, QVBoxLayout, QRadioButton, QCheckBox


class rePhauncherDialog(QDialog):
    def __init__(self, position):
        super().__init__()
        self.setWindowTitle("Phauncher")
        self.resize(300,150)
        self.move(position.x(), position.y())

        self.formGroupBox = QGroupBox("Compose Phoebus layout:")

        # strings to hold filenames of the single main window, and the list of side windows.
        self.mainwindow = ''
        self.sidewindows = []

        self.layoutpath = '/usr/local/share/cs-studio/layouts/'

        self.xml_start = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<memento show_menu="true" show_statusbar="true" show_tabs="true" show_toolbar="true">
'''

        self.xml_end = '</memento>'
        self.memento_path = '/home/operator-mcr/.phoebus/memento'

        self.helpRequest = False

        layout = QFormLayout()

        label = QLabel("Main window:")
        layout.addWidget(label)

        files = os.listdir(self.layoutpath)
        #sortedFiles.sort()
        sortedFiles = sorted(files, key=str.casefold)
        print(self.layoutpath)
        print(os.listdir(self.layoutpath))
        print(sortedFiles)
        
        for each in sortedFiles:
            if each.startswith('layout_'):
                rb = QRadioButton(each.replace('layout_','').replace('_',' ').replace('.memento',''))
                rb.mainwin = each
                rb.toggled.connect(self.onClickedRadio)
                layout.addWidget(rb)

        label = QLabel("Side windows:")
        layout.addWidget(label)

        for each in sortedFiles:
            if each.startswith('window_'):
                cb = QCheckBox(each.replace('window_','').replace('_',' ').replace('.memento',''))
                cb.sidewin = each
                cb.toggled.connect(self.onClickedCheck)
                layout.addWidget(cb)

#        for each in os.scandir(self.layoutpath):
#            if each.name.startswith('layout_'):




#        for each in os.scandir(self.layoutpath):
#            if each.name.startswith('window_'):



        self.formGroupBox.setLayout(layout)

        helpbutton = QDialogButtonBox.Help
        

        okbutton = QDialogButtonBox.Ok
        # okbutton.pressed.connect(lambda: print("test"))
        buttonBox = QDialogButtonBox(okbutton | QDialogButtonBox.Cancel | helpbutton)
        buttonBox.accepted.connect(self.onClickOK)
        buttonBox.rejected.connect(self.reject)
        buttonBox.helpRequested.connect(self.onHelp)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def onClickedRadio(self):
        rb = self.sender()
        if rb.isChecked():
            self.mainwindow = rb.mainwin

    def onClickedCheck(self):
        rb = self.sender()
        if rb.isChecked():
            print('checked:',rb.sidewin)
            self.sidewindows.append(rb.sidewin)
        else:
            print('unchecked:',rb.sidewin)
            self.sidewindows.remove(rb.sidewin)

    def onHelp(self):
        self.helpRequest = True
        self.accept()

    def onClickOK(self):
        if not self.mainwindow == '':
            output = self.readfile(self.layoutpath + self.mainwindow)
            output = output[:len(output) - len('</memento>') - 1]

            for each in self.sidewindows:
                a = self.readfile(self.layoutpath + each)
                a = a[:a.index('<')] + a[a.index('>')+1:]
                a = a[:a.index('<')] + a[a.index('>')+1:]
                a = a[:len(a) - len('</memento>') - 1]
                output += a

            output += self.xml_end
            with open(self.memento_path,"w") as f:
                f.write(output)
            self.accept()

    def readfile(self,path):
        with open(path) as f:
            return f.read()

