import json

from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLineEdit, QLabel, QSpinBox, QDialogButtonBox, QVBoxLayout, QRadioButton, QCheckBox


class phauncherDialog(QDialog):
    def __init__(self, position):
        super().__init__()
        self.setWindowTitle("Phauncher")
        self.resize(300,150)
        self.move(position.x(), position.y())

        self.formGroupBox = QGroupBox("Compose Phoebus layout:")

        layout = QFormLayout()

        label = QLabel("Main window:")
        layout.addWidget(label)

        rb = QRadioButton("SL default")
        rb.mainwin = 'testwindow.xml'
        rb.toggled.connect(self.onClickedRadio)
        layout.addWidget(rb)

        rb = QRadioButton("Bunchers")
        rb.mainwin = 'somethingelse.xml'
        rb.toggled.connect(self.onClickedRadio)
        layout.addWidget(rb)

        label = QLabel("Side windows:")
        layout.addWidget(label)

        cb = QCheckBox("Annunciate/log")
        cb.sidewin = 'test'
        cb.toggled.connect(self.onClickedCheck)
        layout.addWidget(cb)

        cb = QCheckBox("DTL overviews")
        cb.sidewin = 'test2'
        cb.toggled.connect(self.onClickedCheck)
        layout.addWidget(cb)
        



        self.formGroupBox.setLayout(layout)

        okbutton = QDialogButtonBox.Ok
        # okbutton.pressed.connect(lambda: print("test"))
        buttonBox = QDialogButtonBox(okbutton | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.onClickOK)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def onClickedRadio(self):
        rb = self.sender()
        if rb.isChecked():
            print(rb.mainwin)

    def onClickedCheck(self):
        rb = self.sender()
        if rb.isChecked():
            print('checked:',rb.sidewin)
        else:
            print('unchecked:',rb.sidewin)

    def onClickOK(self):

        self.accept()

    def getParams(self):
        return('asdf')
