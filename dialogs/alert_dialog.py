"""dialogue box for alerting the user about something"""

from PyQt5 import QtCore, QtWidgets, QtGui
from layouts import alert_ui     # compiled PyQt dialogue ui


class AlertDialog(QtWidgets.QDialog):
    """Alert dialogue window"""

    def __init__(self, alert):
        QtWidgets.QWidget.__init__(self)
        self.ui = alert_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Alert")

        self.ui.alert.setText(alert)

        # connect okay button
        self.ui.buttonBox.accepted.connect(self.handle_ok)

    def handle_ok(self):
        pass
