"""
  __  __                    _                 
 / /_/ /  _______ ___ ___  (_)__    ___  __ __
/ __/ _ \/ __/ -_) -_) _ \/ / _ \_ / _ \/ // /
\__/_//_/_/  \__/\__/ .__/_/\___(_) .__/\_, / 
                   /_/           /_/   /___/  

The helpful companion to the 40' telescope
Written with frustration by Shengjie, Isabel, and Finn

"""


from PyQt5 import QtCore, QtWidgets, QtGui, QtChart
from main_ui import Ui_MainWindow   # compiled PyQt main ui
from dialog_ui import Ui_Dialog     # compiled PyQt dialogue ui
from layout_legacy import Ui_Legacy # compiled legacy ui
from decimal import Decimal
import time, math, random

import tars

class Dialog(QtWidgets.QDialog):
    """New observation dialogue window"""
    def __init__(self, parent_window):
        QtWidgets.QWidget.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Threepio Dialogue")

        # get the window that spawned it
        self.parent_window = parent_window

        # what to do when press "ok"
        self.ui.dialog_button_box.clicked.connect(self.handle_ok)

    def handle_ok(self):
        # TODO: convert input to epoch time properly (not just assume everything is Jan 1 1970)
        pattern = "%H:%M:%S"
        start = int(time.mktime(time.strptime(self.ui.start_value.text(), pattern)))
        end = int(time.mktime(time.strptime(self.ui.end_value.text(), pattern)))

        self.parent_window.set_ra(start, end)

class SuperClock():
    """Clock object for encapsulation; keeps track of the time"""
    def __init__(self, starting_time = time.time()):
        self.starting_time = starting_time
    
    def get_time(self):
        return time.time()

    def get_elapsed_time(self):
        return time.time() - self.starting_time
    
    def get_time_until(self, time):
        return time.time() - time

class Threepio(QtWidgets.QMainWindow):
    """Main class for the app"""

    # basic time
    start_RA = 0
    end_RA = 0
    timer_rate = 10 # ms
    stripchart_display_ticks = 2048 # how many data points to draw to stripchart
    stripchart_offset = 0
    
    # decimal display formats
    TWOPLACES = Decimal('0.01')

    # test data
    ticker = 0
    other_ticker = 0

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # use main_ui for window setup
        self.ui = Ui_MainWindow()
        self.setStyleSheet(open('stylesheet.qss').read())
        self.ui.setupUi(self)
        self.setWindowTitle("Threepio")

        # connect buttons
        self.ui.speed_faster_radio.clicked.connect(self.update_speed)
        self.ui.speed_slower_radio.clicked.connect(self.update_speed)
        self.ui.speed_default_radio.clicked.connect(self.update_speed)

        self.ui.actionScan.triggered.connect(self.handle_scan)
        self.ui.actionSurvey.triggered.connect(self.handle_survey)
        self.ui.actionSpectrum.triggered.connect(self.handle_spectrum)

        self.ui.chart_clear_button.clicked.connect(self.clear_strip_chart)
        self.ui.chart_refresh_button.clicked.connect(self.clear_strip_chart)

        self.ui.actionLegacy.triggered.connect(self.legacy_mode)

        # store data in... an array; TODO: make this less terrible
        self.data = []

        # initialize stripchart
        self.stripchart_series = QtChart.QLineSeries()
        self.ui.stripchart.setRenderHint(QtGui.QPainter.Antialiasing)

        # DATAQ stuff
        # self.tars = tars.Tars(tars.discovery())
        # self.tars.init()
        # self.tars.start()
        
        #  clock
        self.clock = SuperClock(time.time())
        self.start_RA = time.time()
        self.end_RA = time.time() + 1

        # refresh timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick) # do everything
        self.timer.start(self.timer_rate) # set refresh rate

    def tick(self): # primary controller for each clock tick

        self.update_gui() # update gui

        self.ticker += 1 # for the test data
        # self.data.append(int(((math.sin((self.ticker / (8 * math.pi)))*300)**2))) # pretty sine wave
        self.other_ticker += random.randint(-2,2)
        self.data.append(int(self.other_ticker)) # random meander

        # self.data.append(self.tars.read_one(1)) # get data from DAQ

        self.update_strip_chart() # make the stripchart scroll

    def add_data(self, data):
        self.data.append(data)

    # def get_elapsed_time(self):
    #     return self.clock.get_time()
    
    def legacy_mode(self):
        f = open("stylesheet.qss", "w")
        f.write("background-color:#00ff00; color: #ff0000")
        self.setStyleSheet("background-color:#00ff00; color: #ff0000")
        self.setAutoFillBackground( True )

    def update_speed(self):
        if (self.ui.speed_faster_radio.isChecked()):
            self.stripchart_display_ticks = 1024
        elif (self.ui.speed_slower_radio.isChecked()):
            self.stripchart_display_ticks = 3072
        else:
            self.stripchart_display_ticks = 2048

    def set_ra(self, start_RA, end_RA):
        self.start_RA = start_RA
        self.end_RA = end_RA
        print(start_RA, end_RA)

    def update_gui(self): # TODO: make this display in human time
        current_time = str(Decimal(self.clock.get_elapsed_time()).quantize(self.TWOPLACES))
        self.ui.ra_value.setText("T+" + current_time + "s")
        
        # TODO: get data from declinometer
        
        # TODO: make this not crash on a /0
        self.ui.progressBar.setValue(int((self.clock.get_elapsed_time() / (self.end_RA - self.start_RA))*100 % 100))

    def handle_survey(self):
        self.new_observation("survey")

    def handle_scan(self):
        self.new_observation("scan")

    def handle_spectrum(self):
        self.new_observation("spectrum")

    def new_observation(self, type):
        dialog = Dialog(self)
        dialog.setWindowTitle("New " + type.capitalize())
        dialog.show()
        dialog.exec_()
    
    def update_strip_chart(self):

        self.stripchart_series.append(self.data[len(self.data) - 1], len(self.data))

        while (len(self.data) - self.stripchart_offset > self.stripchart_display_ticks):
            self.stripchart_series.remove(0)
            self.stripchart_offset += 1

        # TODO: make the stripchart fill in old data when slowed down

        chart = QtChart.QChart()
        chart.addSeries(self.stripchart_series)
        # chart.createDefaultAxes()
        chart.legend().hide()

        self.ui.stripchart.setChart(chart)
    
    def clear_strip_chart(self): # are clear and refresh supposed to be the same?
        while (len(self.data) - self.stripchart_offset > 0):
            self.stripchart_series.remove(0)
            self.stripchart_offset += 1


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Threepio()
    window.setMinimumSize(800,600)
    window.show()
    sys.exit(app.exec_())