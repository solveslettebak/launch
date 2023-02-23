import json
import os

from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLineEdit, QLabel, QSpinBox, QDialogButtonBox, QVBoxLayout, QRadioButton, QCheckBox


class phauncherDialog(QDialog):
    def __init__(self, position):
        super().__init__()
        self.setWindowTitle("Phauncher")
        self.resize(300,150)
        self.move(position.x(), position.y())

        self.formGroupBox = QGroupBox("Compose Phoebus layout:")

        # strings to hold filenames of the single main window, and the list of side windows.
        self.mainwindow = ''
        self.sidewindows = []

        self.phauncherpath = '/nfs/Linacshare_controlroom/MCR/Solve/phauncher/'

        self.xml_start = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<memento show_menu="true" show_statusbar="true" show_tabs="true" show_toolbar="true">
'''

        self.xml_end = '</memento>'
        self.memento_path = '/home/operator-mcr/.phoebus/memento'

        self.helpRequest = False

        layout = QFormLayout()

        label = QLabel("Main window:")
        layout.addWidget(label)

        for each in os.scandir('../Solve/phauncher/mainwindows'):
            rb = QRadioButton(each.name.replace('_',' ').replace('.xml',''))
            rb.mainwin = each.name
            rb.toggled.connect(self.onClickedRadio)
            layout.addWidget(rb)

        label = QLabel("Side windows:")
        layout.addWidget(label)

        for each in os.scandir('../Solve/phauncher/sidewindows'):
            cb = QCheckBox(each.name.replace('_',' ').replace('.xml',''))
            cb.sidewin = each.name
            cb.toggled.connect(self.onClickedCheck)
            layout.addWidget(cb)


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
            output = self.xml_start
            output += self.readfile(self.phauncherpath+'mainwindows/'+self.mainwindow)
            for each in self.sidewindows:
                output += self.readfile(self.phauncherpath+'sidewindows/'+each)
            output += self.xml_end
            with open(self.memento_path,"w") as f:
                f.write(output)
            self.accept()

    def readfile(self,path):
        with open(path) as f:
            return f.read()

