# -*- coding: utf-8 -*-

"""

 Project     : The poorman's data logger.
 File        : tools/settingsdialogs.py
 Version     : 1.0
 Description : Dialogs to set serial communication settings
                and application settings.


 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import glob
import sys
import re
from PyQt5.QtCore import (Qt, pyqtSignal, QLocale, pyqtSlot, QSettings,
                          QRegularExpression)
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLabel,
                             QHBoxLayout, QCheckBox, QSpinBox, QPushButton,
                             QRadioButton, QLineEdit, QComboBox, QGroupBox,
                             QVBoxLayout, QAbstractButton, QMessageBox,
                             QDoubleSpinBox, QColorDialog, QVBoxLayout, QFrame)
from PyQt5.QtGui import (QIcon, QColor, QRegularExpressionValidator,
                         QIntValidator)
import serial
from tools.langtranslate import loadLanguage, load_section


class SerialSettingsDialog(QDialog):
    """ Dialog to configure a serial connection """

    baudvalues = ['9600', '19200', '38400', '57600', '115200', '230400']
    dataReady = pyqtSignal(list)
    appsettings = QSettings("C.E.D", "datalogger")

    def __init__(self, parent=None):
        super(SerialSettingsDialog, self).__init__()

        # load translation
        self.langstr = load_section(self.appsettings.value("Lang",
                                    'translations/datalogger_en'),
                                    "serial")

        self.setWindowTitle(self.langstr[0])
        self.setupUI()

    def setupUI(self):
        """ init widgets """
        # set window icon
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ports list
        self.combobox = QComboBox()
        self.combobox.clear()
        self.combobox.addItems(self.serial_ports())

        # rescan ports button
        self.scanBtn = QPushButton(self.langstr[1])
        self.scanBtn.clicked.connect(self.rescan)

        # baud rate
        self.baudbox = QComboBox()
        for bauds in self.baudvalues:
            self.baudbox.addItem(bauds)
        self.baudbox.setCurrentIndex(3)

        # ok and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.submit_data)
        self.buttonBox.rejected.connect(self.reject_data)

        # some labels
        self.baudlabel = QLabel(self.langstr[2])
        self.bitslabel = QLabel(self.langstr[3])
        self.startlabel = QLabel(self.langstr[4])
        self.stoplabel = QLabel(self.langstr[5])

        # data bits
        self.dataspin = QSpinBox()
        self.dataspin.setValue(8)

        # parity combo
        self.parity = QComboBox()
        self.parity.addItems([self.langstr[6], self.langstr[7],
                             self.langstr[8]])

        # stop bits
        self.stopspin = QSpinBox()
        self.stopspin.setValue(1)

        # other serial stuff
        self.cts = QCheckBox('CTS')
        self.dtr = QCheckBox('DTR')
        self.xon = QCheckBox('XON')

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # put all the stuff together
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.baudlabel, 0, 1)
        self.grid.addWidget(self.bitslabel, 1, 1)
        self.grid.addWidget(self.startlabel, 2, 1)
        self.grid.addWidget(self.stoplabel, 3, 1)
        self.grid.addWidget(self.dataspin, 1, 2)
        self.grid.addWidget(self.parity, 2, 2)
        self.grid.addWidget(self.stopspin, 3, 2)
        self.grid.addWidget(self.cts, 4, 2)
        self.grid.addWidget(self.dtr, 5, 2)
        self.grid.addWidget(self.xon, 6, 2)
        self.grid.addWidget(self.baudbox, 0, 2)
        self.grid.addWidget(self.combobox, 0, 0)
        self.grid.addWidget(self.scanBtn, 1, 0)
        self.grid.addWidget(self.line, 7, 0, 1, 3)
        self.grid.addWidget(self.buttonBox, 8, 2)

    def submit_data(self):
        """ Ok button pressed : let's send values back and exit"""
        vallist = [True, self.combobox.currentText(),
                   int(self.baudbox.currentText()), self.dataspin.value(),
                   self.parity.currentText(), self.stopspin.value(),
                   self.cts.isChecked(), self.dtr.isChecked(),
                   self.xon.isChecked()]
        self.dataReady.emit(vallist)
        self.accept()

    def reject_data(self):
        """ Cancel button pressed : let's send defaulf values and exit"""
        vallist = [False, self.combobox.currentText(),
                   int(self.baudbox.currentText()), self.dataspin.value(),
                   self.parity.currentText(), self.stopspin.value(),
                   self.cts.isChecked(), self.dtr.isChecked(),
                   self.xon.isChecked()]
        self.dataReady.emit(vallist)
        self.reject()

    def rescan(self):
        """ Test if new ports are available """
        # clear list then try to populate it
        self.combobox.clear()
        self.combobox.addItems(self.serial_ports())

    @staticmethod
    def serial_ports():
        """ Get a list of available serial ports """

        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith(
                    'cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result


class PreferencesDialog(QDialog):
    """ Dialog to configure and save application settings """
    # list of values to return
    dataReady = pyqtSignal(list)
    settings = QSettings("C.E.D", "datalogger")
    color = settings.value("LineColor", QColor(100, 200, 100))
    appsettings = QSettings("C.E.D", "datalogger")

    def __init__(self, parent=None):
        super(PreferencesDialog, self).__init__()
        
        # load translation
        self.langstr = load_section(self.appsettings.value("Lang",
                                    'translations/datalogger_en'),
                                    "settings")

        self.setWindowTitle('Preferences')
        self.setupUI()

    def setupUI(self):
        """ init widgets """
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ok , save and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel
                                          | QDialogButtonBox.Save)
        self.buttonBox.clicked.connect(self._onButtonClicked)

        self.titlelabel = QLabel(self.langstr[0])
        self.titleval = QLineEdit()
        self.titleval.setText(self.settings.value("Title", "My graph"))

        self.bufflabel = QLabel(self.langstr[1])
        self.buffersize = QLineEdit()
        self.buffersize.setText(self.settings.value("Buffer", "1200"))

        self.yaxisname = QLabel(self.langstr[2])
        self.yaxisrange = QLabel(self.langstr[3])
        self.yaxisval = QLineEdit()
        self.yaxisval.setText(self.settings.value("YName", "Volts"))
        self.yaxisunit = QLineEdit()
        self.yaxisunit.setText(self.settings.value("YUnit", "V"))
        self.yaxismin = QDoubleSpinBox()
        self.yaxismin.setMinimum(-1000)
        self.yaxismin.setMaximum(1000)
        self.yaxismin.setValue(float(self.settings.value("YMin", "0")))
        self.yaxismax = QDoubleSpinBox()
        self.yaxismax.setMinimum(-1000.0)
        self.yaxismax.setMaximum(1000.0)
        self.yaxismax.setValue(float(self.settings.value("YMax", "1000")))

        # create sample rate controls
        self.vallabel = QLabel(self.langstr[4])
        self.sample_val = QSpinBox(self)
        self.sample_val.setValue(1)
        self.valslayout = QHBoxLayout()
        self.valslayout.setAlignment(Qt.AlignLeft)
        self.valslayout.addWidget(self.vallabel)
        self.valslayout.addWidget(self.sample_val)
        self.colorbtn = QPushButton(self.langstr[5])
        colorstr = "background-color: {}".format(self.color.name())
        self.colorbtn.setStyleSheet(colorstr)
        self.colorbtn.clicked.connect(self.pick_color)
        self.use_filter_btn = QCheckBox(self.langstr[6])
        self.use_filter_btn.setChecked(self.settings.value("UseFilter",
                                                           True, type=bool))
        # self.use_tcp_btn = QCheckBox(self.langstr[6])
        self.use_tcp_btn = QCheckBox(self.langstr[10])
        self.use_tcp_btn.setChecked(self.settings.value("UseTCP",
                                                        False, type=bool))
        self.use_layout = QVBoxLayout()
        self.use_layout.addWidget(self.use_filter_btn)
        self.use_layout.addWidget(self.use_tcp_btn)

        self.sample_ms = QRadioButton('ms')
        self.sample_ms.toggled.connect(self.setunitsrange)
        self.sample_s = QRadioButton('s')
        self.sample_s.toggled.connect(self.setunitsrange)
        self.sample_min = QRadioButton('min')
        self.sample_min.toggled.connect(self.setunitsrange)
        if self.settings.value("Unit") == 's':
            self.sample_s.setChecked(True)
        elif self.settings.value("Unit") == 'ms':
            self.sample_ms.setChecked(True)
        elif self.settings.value("Unit") == 'min':
            self.sample_min.setChecked(True)
        self.sample_val.setValue(int(self.settings.value("UnitVal", "1")))
        self.samplebox = QGroupBox(self.langstr[7])
        self.samplelayout = QVBoxLayout()
        self.samplelayout.setAlignment(Qt.AlignTop)
        self.samplelayout.addWidget(self.sample_ms)
        self.samplelayout.addWidget(self.sample_s)
        self.samplelayout.addWidget(self.sample_min)
        self.samplelayout.addLayout(self.valslayout)
        self.samplebox.setLayout(self.samplelayout)
        self.samplebox.setAlignment(Qt.AlignCenter)
        
        # create axis controls
        self.hbox1 = QHBoxLayout()
        self.hbox1.addWidget(self.yaxisname)
        self.hbox1.setAlignment(Qt.AlignLeft)
        self.hbox1.addWidget(self.yaxisval)
        self.hbox1.addWidget(self.yaxisunit)
        self.hbox2 = QHBoxLayout()
        self.hbox2.setAlignment(Qt.AlignLeft)
        self.hbox2.addWidget(self.yaxisrange)
        self.hbox2.addWidget(self.yaxismin)
        self.hbox2.addWidget(self.yaxismax)
        self.vbox1 = QVBoxLayout()
        self.vbox1.addLayout(self.hbox1)
        self.vbox1.addLayout(self.hbox2)
        self.vbox1.addWidget(self.colorbtn)
        self.vbox1.addLayout(self.use_layout)
        
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.bufflabel, 0, 0, Qt.AlignRight)
        self.grid.addWidget(self.buffersize, 0, 1)
        self.grid.addWidget(self.titlelabel, 1, 0, Qt.AlignRight)
        self.grid.addWidget(self.titleval, 1, 1)
        self.grid.addWidget(self.samplebox, 2, 0)
        self.grid.addLayout(self.vbox1, 2, 1, Qt.AlignVCenter)
        self.grid.addWidget(self.line, 3, 0, 1, 3)
        self.grid.addWidget(self.buttonBox, 4, 1)
        
    def pick_color(self):
        """ Color button callback, select color for graph """
        self.color = QColorDialog.getColor()
        if not self.color.isValid():
            self.color = QColor(100,200,100)
        else:
            colorstr = "background-color: {}".format(self.color.name())
            self.colorbtn.setStyleSheet(colorstr)

    def setunitsrange(self):
        """ set range for sample rate """
        if self.sample_min.isChecked() or self.sample_s.isChecked():
            self.sample_val.setRange(0, 60)
        else:
            self.sample_val.setRange(0, 1000)

    @pyqtSlot(QAbstractButton)
    def _onButtonClicked(self, button):
        """ manage save, cancel and yes buttons """
        # get sample rate unit
        val = 's'
        if self.sample_s.isChecked():
            val = 's'
        elif self.sample_ms.isChecked():
            val = 'ms'
        elif self.sample_min.isChecked():
            val = 'min'
        stButton = self.buttonBox.standardButton(button)
        # Save and exit
        if stButton == QDialogButtonBox.Save:
            reply = QMessageBox.question(self, self.langstr[8],
                                         self.langstr[9],
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.settings.setValue("Init", True)
                self.settings.setValue("Buffer", int(self.buffersize.text()))
                self.settings.setValue("Unit", val)
                self.settings.setValue("UnitVal", self.sample_val.value())
                self.settings.setValue("YName", self.yaxisval.text())
                self.settings.setValue("YUnit", self.yaxisunit.text())
                self.settings.setValue("YMin", self.yaxismin.value())
                self.settings.setValue("YMax", self.yaxismax.value())
                self.settings.setValue("Title", self.titleval.text())
                self.settings.setValue("LineColor", self.color)
                self.settings.setValue("UseFilter",
                                       self.use_filter_btn.isChecked())
                self.settings.setValue("UseTCP",
                                       self.use_tcp_btn.isChecked())
                vallist = ["Save", int(self.buffersize.text()), val,
                           self.sample_val.value(), self.yaxisval.text(),
                           self.yaxisunit.text(), self.yaxismin.value(),
                           self.yaxismax.value(), self.titleval.text(),
                           self.color, self.use_filter_btn.isChecked(),
                           self.use_filter_btn.isChecked()]
                self.dataReady.emit(vallist)
                self.accept()
        # Ok button pressed
        elif stButton == QDialogButtonBox.Ok:
            vallist = ["Ok", int(self.buffersize.text()), val,
                       self.sample_val.value(), self.yaxisval.text(),
                       self.yaxisunit.text(), self.yaxismin.value(),
                       self.yaxismax.value(), self.titleval.text(), self.color,
                       self.use_filter_btn.isChecked(),
                       self.use_filter_btn.isChecked()]
            self.dataReady.emit(vallist)
            self.accept()

        elif stButton == QDialogButtonBox.Cancel:
            vallist = ["Cancel"]
            self.dataReady.emit(vallist)
            self.reject()
        else:
            assert 0


class LangSelector(QDialog):
    """
    Select a language from the translations directory
    """
    lang_selected = pyqtSignal(list)
    lang_data = []

    def __init__(self, parent=None):
        super(LangSelector, self).__init__()

        self.setWindowTitle('Preferences')
        self.setupUI()
        self.populate_lang()

    def setupUI(self):
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ok , save and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.submit_data)
        self.buttonBox.rejected.connect(self.reject_data)

        self.lang_label = QLabel("Select a language")

        self.lang_list = QComboBox()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.lang_label)
        self.vlayout.addWidget(self.lang_list)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.addLayout(self.vlayout, 0, 0)
        self.grid.addWidget(self.line, 1, 0, 1,2)
        self.grid.addWidget(self.buttonBox, 2, 1)

    def populate_lang(self):
        try:
            with open("translations/lang.idx", "r") as reader:
                for line in reader:
                    name = line.split(",")
                    self.lang_data.append(name)
                    self.lang_list.addItem(name[0])

        except FileNotFoundError:
            self.lang_label.setText("No language index file found !")
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def submit_data(self):
        self.lang_selected.emit(self.lang_data[self.lang_list.currentIndex()])
        self.accept()

    def reject_data(self):
        self.reject()


class TCPConfigDialog(QDialog):
    """
    Configure an ip address and port number with validation
    arguments:
        adr=xxx.yyy.ttt.ddd
        port=integer
    """
    # Qt signal used to tranfer data
    ip_config = pyqtSignal(list)

    def __init__(self, parent=None, adr="", port=0):
        super(TCPConfigDialog, self).__init__()

        self.ip_adr = adr
        self.portnb = port

        self.setWindowTitle('TCP configuration')
        self.setupUI()

    def setupUI(self):
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ok , save and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.submit_data)
        self.buttonBox.rejected.connect(self.reject_data)

        # Labels
        self.dialog_label = QLabel("Configure Ip settings")
        self.ip_label = QLabel("Ip address:")
        self.port_label = QLabel("Port :    ")

        # input for ip address
        self.ip_text = QLineEdit()
        # Part of the regular expression for validating ip address
        ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        # Regular expression
        ipRegex = QRegularExpression("^" + ipRange + "\\." + ipRange + "\\."
                                     + ipRange + "\\." + ipRange + "$")
        # regex object to validate address
        self.pattern = re.compile("^" + ipRange + "\\." + ipRange + "\\."
                                      + ipRange + "\\." + ipRange + "$")
        ipValidator = QRegularExpressionValidator(ipRegex, self)   
        self.ip_text.setValidator(ipValidator)
        # an adress was passed as an argument
        if self.ip_adr != "":
            self.ip_text.setText(self.ip_adr)

        # input for port number
        self.port_text = QLineEdit()
        # only accepts integers !
        self.onlyints = QIntValidator()
        self.port_text.setValidator(self.onlyints)
        # a port number  was passed as an argument
        if self.portnb != 0:
            self.port_text.setText(str(self.portnb))
        # add stuff to layout
        self.grid = QGridLayout()
        self.grid.addWidget(self.dialog_label, 0, 0, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(self.ip_label, 1, 0)
        self.grid.addWidget(self.port_label, 2, 0)
        self.grid.addWidget(self.ip_text, 1, 1)
        self.grid.addWidget(self.port_text,2, 1)
        self.grid.addWidget(self.buttonBox, 3, 1)
        self.setLayout(self.grid)

    def submit_data(self):
        """ Ok button pressed """

        # validate ip adress
        if not self.pattern.match(self.ip_text.text()):
            QMessageBox.information(self, "Info",
                                    "Not a valid ip address!")
            return
        # validate port number
        try:
            configuration = [1, self.ip_text.text(), int(self.port_text.text())]
        except ValueError:
            QMessageBox.information(self, "Info",
                                    "Please enter a valid port number!")
            return
        # emit signal if everything is ok
        self.ip_config.emit(configuration)
        self.accept()

    def reject_data(self):
        """ Cancel button pressed """
        configuration = [0]
        self.ip_config.emit(configuration)
        self.reject()

    def set_defaults(self, addr, port):
        self.ip_text.setText(addr)
        self.port_text.setText(port)
