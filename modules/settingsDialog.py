import json

from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLineEdit, QLabel, QSpinBox, QDialogButtonBox, QVBoxLayout

from modules.common import settingsPath


class settingsDialog(QDialog):
    def __init__(self,position):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(300,150)
        self.move(position.x(), position.y())

        self.data = json.load(open(settingsPath))

        self.formGroupBox = QGroupBox("Settings:")
        layout = QFormLayout()
        self.menufileinput = QLineEdit(self.data["defaultLayoutFile"])
        layout.addRow(QLabel("Default layout:"),self.menufileinput) # could also be a dropdown..
        self.fontsizeSpinbox = QSpinBox()
        self.fontsizeSpinbox.setValue(int(self.data["fontsize"]))
        self.fontsizeSpinbox.setMaximum(20)
        self.fontsizeSpinbox.setMinimum(6)
        layout.addRow(QLabel("Font size:"),self.fontsizeSpinbox)
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

    def onClickOK(self):
        self.data["fontsize"] = str(self.fontsizeSpinbox.value())
        self.data["defaultLayoutFile"] = self.menufileinput.text()
        json.dump(self.data,open(settingsPath,"w"))
        self.accept()
