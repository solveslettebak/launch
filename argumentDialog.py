from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLabel, QPlainTextEdit, QDialogButtonBox, QVBoxLayout, \
    QLineEdit

from subprocess import Popen,PIPE
import shlex

class argumentDialog(QDialog):
    def __init__(self,mainwin,link,name,help_arg,mandatory_arg,description,def_arg):
        super().__init__()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.resize(900,350)
        self.move(mainwin.pos().x()+200,mainwin.pos().y()+40)
        self.setWindowTitle(name+" arguments")

        self.formGroupBox = QGroupBox(link.split('\\')[-1][:-1]+" "+mandatory_arg) # check out that slicing magic
        layout = QFormLayout()
        self.optionalParams = QLineEdit(def_arg)
        layout.addRow(QLabel("args: "+mandatory_arg),self.optionalParams)

        splitlist = shlex.split(link)
        splitlist.append(help_arg)
        process = Popen(splitlist[2:], stdout=PIPE, universal_newlines=True) # that :2 thing... that's a dirty hack. need nice solution for new terminal function.
        try:
            (output,err) = process.communicate(timeout=2)
        except TimeoutError:
            output = "Application timed out. No help for you..."
            process.kill()
        helptext = output
        exit_code = process.wait()

        textbox = QPlainTextEdit(helptext)
        textbox.setReadOnly(True)
        layout.addRow(QLabel(help_arg),textbox) # run app with help_arg and put output here. Have a timeout. And check if None is an ok type to pass to a QLabel... for some robustness.
        self.formGroupBox.setLayout(layout)

        okButton = QDialogButtonBox.Ok

        buttonBox = QDialogButtonBox(okButton | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.onAccepted)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def getParams(self):
        return self.optionalParams.text()

    def onAccepted(self):
        self.done(1)
