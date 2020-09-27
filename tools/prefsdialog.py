# -*- coding: utf-8 -*-

"""

 Project     : The poorman's frequency counter.
 File        : tools/sersettings.py
 Version     : 1.0
 Description : Dialog window to set serial communication settings.


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

import sys
from PyQt5.QtCore import pyqtSignal, QLocale
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLabel,
                             QCheckBox, QSpinBox, QPushButton, QComboBox)
from PyQt5.QtGui import QIcon
from tools.langtranslate import loadLanguage
import serial
import glob


class PrefsDialog(QDialog):
    baudvalues = ['9600', '19200', '38400', '57600', '115200', '230400']
    dataReady = pyqtSignal(list)

    def __init__(self, parent=None):
        super(PrefsDialog, self).__init__()
        if QLocale.system().name() == 'fr_FR':
            self.langstr = loadLanguage('resources/sersettings_fr_FR')
        else:
            self.langstr = loadLanguage('resources/sersettings_en')
        self.setWindowTitle(self.langstr[0])
        self.setupUI()

    def setupUI(self):
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
        for n in self.baudvalues:
            self.baudbox.addItem(n)
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
        self.grid.addWidget(self.buttonBox, 7, 2)

    def submit_data(self):
        """ Ok button pressed : let's send values back and exit"""
        self.vallist = ['1', self.combobox.currentText(),
                        self.baudbox.currentText(),
                        str(self.dataspin.value()), self.parity.currentText(),
                        str(self.stopspin.value()),
                        str(self.cts.isChecked()), str(self.dtr.isChecked()),
                        str(self.xon.isChecked())]
        self.dataReady.emit(self.vallist)
        self.accept()

    def reject_data(self):
        """ Cancel button pressed : let's send defaulf values and exit"""
        self.vallist = ['0', self.combobox.currentText(),
                        self.baudbox.currentText(),
                        str(self.dataspin.value()), self.parity.currentText(),
                        str(self.stopspin.value()),
                        str(self.cts.isChecked()), str(self.dtr.isChecked()),
                        str(self.xon.isChecked())]
        self.dataReady.emit(self.vallist)
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
