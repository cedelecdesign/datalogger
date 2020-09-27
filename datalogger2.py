#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Ced electronics design

 Project     : The poorman's data logger.
 File        : datalogger.py
 Version     : 2.0
 Description : A simple Arduino based data logger.


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
import os
import math
import socket
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QLocale, QTranslator,
                          QLibraryInfo, QFileInfo, QSettings)
from PyQt5.QtWidgets import (QWidget, QMainWindow, QGridLayout, QHBoxLayout,
                             QVBoxLayout, QLabel, QRadioButton, QPushButton,
                             QMessageBox, QGroupBox, QFrame, QApplication,
                             QCheckBox, QSpinBox, QFileDialog, QAction,
                             QProgressBar)
from PyQt5.QtGui import QIcon, QColor
import numpy as np
import pyqtgraph as pg
import serial
from tools.settingsdialogs import (SerialSettingsDialog, PreferencesDialog,
                                   LangSelector, TCPConfigDialog)
from tools.helpdialogs import HelpHtmlDialog
from tools.CustomWidgets import EditorDialog, TicTimer
from tools.langtranslate import load_section
from tools.datafilters import datafilter
from tools.stats import StatsDialog


class MainWindow(QMainWindow):
    """
       Creates window and displays data
    """

    appsettings = QSettings("C.E.D", "datalogger")
    # a global list to store serial settings
    settingsList = []
    # is connection whith arduino established?
    isConnected = False
    # number of samples acquired
    count = 0
    chunk_size = 0
    # grabbing data?
    isRunning = False
    # min and max values for graph units
    pmin = 0
    pmax = 6
    # used to send the right unit to arduino
    units = ['m', 's', 'M']
    unitsel = 1
    # data buffer size
    buffersize = int(appsettings.value("Buffer", 1200))
    # data buffer
    data = np.zeros((buffersize,))
    # use internal filter function
    use_internal_filter = True
    # use tcp or serial
    use_tcp_flag = appsettings.value("UseTCP", False, type=bool)
    tcp_config = ["127.0.0.1", 0]

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setObjectName('MainWindow')

        # load translation
        self.langstr = load_section(self.appsettings.value("Lang",
                                    'translations/datalogger_en'),
                                    "datalogger")

        self.initUI()
        # self.setFixedSize(self.size()+QSize(0,30))
        # self.showMaximized()

        self.statsdlg = StatsDialog()

        # serial configuration dialog
        self.configdlg = SerialSettingsDialog(self)
        self.configdlg.setModal(True)
        self.configdlg.dataReady.connect(self.configure_data)

        # configuration dialog
        self.settingsdlg = PreferencesDialog(self)
        self.settingsdlg.setModal(True)
        self.settingsdlg.dataReady.connect(self.configure_app)

        # help dialog
        if QLocale.system().name() == 'fr_FR':
            self.helpdlg = HelpHtmlDialog(
                parent=self, filename=os.path.abspath(os.path.join(
                    os.path.dirname(__file__),
                    'resources/dataloggerhelp_fr.html')))
        else:
            self.helpdlg = HelpHtmlDialog(
                parent=self, filename=os.path.abspath(os.path.join(
                    os.path.dirname(__file__),
                    'resources/dataloggerhelp_en.html')))

        # Create serial object
        self.serport = serial.Serial()

        # create thread for reading data from serial port
        self.Thread = DataThread(self)
        self.Thread.dataReady.connect(self.update_data)

        # Create thread for reading from network
        self.tcp_thread = TCPThread(self)
        self.tcp_thread.dataReady.connect(self.update_data)

        # create plot
        self.create_graphs()

        # if no default settings stored, launch configuration
        if not self.appsettings.value('Init', False):
            reply = QMessageBox.question(self, "Configure",
                                         "Configure app now?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.settingsdlg.show()

        self.langSelector = LangSelector()
        self.langSelector.lang_selected.connect(self.new_lang)

    def initUI(self):
        """ Initialize widgets """

        # Create central widget for MainWindow
        self.widget = QWidget()
        self.grid = QGridLayout()
        self.widget.setLayout(self.grid)
        self.setCentralWidget(self.widget)

        # set window icon
        self.setWindowIcon(QIcon('resources/images/icon.png'))
        self.statusBar().showMessage(self.langstr[1])

        self.myeditor = EditorDialog(self)

        self.tcpdialog = TCPConfigDialog()
        self.tcpdialog.set_defaults("127.0.0.1", "5500")
        self.tcpdialog.ip_config.connect(self.config_tcp)

        # create a PlotWidget from pyqtgraph
        self.pw = pg.PlotWidget()
        self.pw.setLabel('left', self.appsettings.value(
            "YName", "Volts"), self.appsettings.value("YUnit", "V"))
        self.pw.setLabel('bottom', 'Samples')
        self.pw.showGrid(True, True)
        # self.pw.invertX()

        # label to store graph title
        self.mainlabel = QLabel(self.appsettings.value("Title", "My plot"))
        # get range values for graph from local settings
        self.pmin = self.appsettings.value("YMin", 0, type=float)
        self.pmax = self.appsettings.value("YMax", 6, type=float)

        # create menus
        self.exitAct = QAction(
            QIcon.fromTheme('application-exit'), self.langstr[2], self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.triggered.connect(self.close)

        self.saveAct = QAction(
            QIcon.fromTheme('document-save'), self.langstr[3], self)
        self.saveAct.setShortcut('Ctrl+S')
        self.saveAct.setEnabled(False)
        self.saveAct.triggered.connect(self.savefile)

        self.loadAct = QAction(
            QIcon.fromTheme('document-open'), self.langstr[4], self)
        self.loadAct.setShortcut('Ctrl+L')
        self.loadAct.triggered.connect(self.loadfile)
        # Serial configuration menu
        self.scanAct = QAction(
            QIcon.fromTheme('document-properties'), self.langstr[5], self)
        self.scanAct.setShortcut('Ctrl+N')
        self.scanAct.triggered.connect(self.showconfig)
        # tcp configuration menu
        self.tcp_act = QAction(
            QIcon.fromTheme('document-properties'), self.langstr[39], self)
        self.tcp_act.triggered.connect(self.showtcp)

        self.setAct = QAction(
            QIcon.fromTheme('document-properties'), self.langstr[6], self)
        self.setAct.setShortcut('Ctrl+P')
        self.setAct.triggered.connect(self.showprefs)

        self.lang_act = QAction(
            QIcon.fromTheme('document-language'), self.langstr[37], self)
        self.lang_act.triggered.connect(self.show_lang)

        self.conAct = QAction(
            QIcon.fromTheme('call-start'), self.langstr[7], self)
        self.conAct.setShortcut('Ctrl+C')
        self.conAct.setEnabled(False)
        self.conAct.triggered.connect(self.connect_serial)

        self.aboutAct = QAction(
            QIcon.fromTheme('help-about'), self.langstr[8], self)
        self.aboutAct.setShortcut('Ctrl+A')
        self.aboutAct.triggered.connect(self.about_app)

        self.aboutQtAct = QAction(
            QIcon.fromTheme('help-about'), self.langstr[9], self)
        self.aboutQtAct.setShortcut('Ctrl+A')
        self.aboutQtAct.triggered.connect(self.aboutqt_app)

        self.helpAct = QAction(
            QIcon.fromTheme('help-contents'), self.langstr[10], self)
        self.helpAct.setShortcut('Ctrl+H')
        self.helpAct.triggered.connect(self.help_app)

        self.editAct = QAction(
            QIcon.fromTheme('help-contents'), self.langstr[35], self)
        self.editAct.setShortcut('Ctrl+H')
        self.editAct.triggered.connect(self.showedit)

        self.filterAct = QAction(self.langstr[36], self, checkable=True)
        self.filterAct.setChecked(self.appsettings.value("UseFilter", True,
                                                         type=bool))
        self.filterAct.triggered.connect(self.use_filter)

        self.comAct = QAction(self.langstr[40], self, checkable=True)
        self.comAct.setChecked(self.appsettings.value("UseTCP", False,
                                                      type=bool))
        self.comAct.triggered.connect(self.use_tcp)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu(self.langstr[11])
        fileMenu.addAction(self.saveAct)
        fileMenu.addAction(self.loadAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAct)

        editMenu = menubar.addMenu(self.langstr[34])
        editMenu.addAction(self.setAct)
        editMenu.addAction(self.editAct)
        editMenu.addAction(self.filterAct)
        editMenu.addAction(self.lang_act)

        serialMenu = menubar.addMenu(self.langstr[12])
        serialMenu.addAction(self.scanAct)
        serialMenu.addAction(self.tcp_act)
        serialMenu.addAction(self.conAct)
        serialMenu.addAction(self.comAct)

        helpMenu = menubar.addMenu(self.langstr[13])
        helpMenu.addAction(self.helpAct)
        helpMenu.addAction(self.aboutAct)
        helpMenu.addAction(self.aboutQtAct)

        # create axis buttons and pack them into a groupbox
        self.xaxisgrid = QCheckBox('X Grid')
        self.xaxisgrid.setChecked(True)
        self.yaxisgrid = QCheckBox('Y Grid')
        self.yaxisgrid.setChecked(True)
        self.yaxisgrid.toggled.connect(self.set_axis_grid)
        self.xaxisgrid.toggled.connect(self.set_axis_grid)
        self.axisbox = QGroupBox(self.langstr[14])
        self.axislayout = QVBoxLayout()
        self.axislayout.setAlignment(Qt.AlignTop)
        self.axislayout.addWidget(self.xaxisgrid)
        self.axislayout.addWidget(self.yaxisgrid)
        self.axisbox.setLayout(self.axislayout)
        self.statbutton = QPushButton("Statistics")
        # self.statbutton.setEnabled(False)
        self.statbutton.clicked.connect(self.show_stats)
        self.axislayout.addWidget(self.statbutton)

        # create sample rate controls and pack them into a groupbox
        self.vallabel = QLabel(self.langstr[15])
        self.vallabel.setEnabled(False)
        self.sample_val = QSpinBox(self)
        self.sample_val.setEnabled(False)
        self.valslayout = QHBoxLayout()
        self.valslayout.setAlignment(Qt.AlignLeft)
        self.valslayout.addWidget(self.vallabel)
        self.valslayout.addWidget(self.sample_val)
        self.sample_ms = QRadioButton('ms')
        self.sample_ms.setEnabled(False)
        self.sample_ms.toggled.connect(self.setunit_ms)
        self.sample_s = QRadioButton('s')
        self.sample_s.toggled.connect(self.setunit_s)
        self.sample_s.setEnabled(False)
        self.sample_min = QRadioButton('min')
        self.sample_min.toggled.connect(self.setunit_min)
        self.sample_min.setEnabled(False)
        if self.appsettings.value("Unit") == 's':
            self.sample_s.setChecked(True)
            self.sample_val.setRange(1, 60)
        elif self.appsettings.value("Unit") == 'ms':
            self.sample_val.setRange(1, 1000)
            self.sample_ms.setChecked(True)
        elif self.appsettings.value("Unit") == 'min':
            self.sample_val.setRange(1, 60)
            self.sample_min.setChecked(True)
        self.sample_val.setValue(int(self.appsettings.value("UnitVal", 1)))
        self.samplebox = QGroupBox(self.langstr[16])
        self.samplelayout = QVBoxLayout()
        self.samplelayout.setAlignment(Qt.AlignTop)
        self.samplelayout.addWidget(self.sample_ms)
        self.samplelayout.addWidget(self.sample_s)
        self.samplelayout.addWidget(self.sample_min)
        self.samplelayout.addLayout(self.valslayout)
        self.samplebox.setLayout(self.samplelayout)

        # create measure controls and pack them into a groupbox
        self.btnstart = QPushButton(self.langstr[17])
        self.btnstart.setIcon(QIcon.fromTheme('media-playback-start'))
        self.btnstart.setEnabled(False)
        self.btnstart.clicked.connect(self.startlogging)
        self.btnsave = QPushButton(self.langstr[18])
        self.btnsave.setIcon(QIcon.fromTheme('document-save'))
        self.btnsave.clicked.connect(self.savefile)
        self.btnsave.setEnabled(False)
        self.btnload = QPushButton(self.langstr[19])
        self.btnload.setIcon(QIcon.fromTheme('document-open'))
        self.btnload.clicked.connect(self.loadfile)
        self.btnload.setEnabled(True)
        self.meslayout = QVBoxLayout()
        self.meslayout.addWidget(self.btnstart)
        self.meslayout.addWidget(self.btnsave)
        self.meslayout.addWidget(self.btnload)
        self.meslayout.setAlignment(Qt.AlignTop)
        self.mesbox = QGroupBox(self.langstr[20])
        self.mesbox.setLayout(self.meslayout)

        # create system controls and pack them into a groupbox
        self.confBtn = QPushButton(self.langstr[21])
        self.confBtn.setIcon(QIcon.fromTheme('document-properties'))
        self.confBtn.clicked.connect(self.showconfig)
        self.conbtn = QPushButton(self.langstr[7])
        self.conbtn.setIcon(QIcon.fromTheme('call-start'))
        self.conbtn.clicked.connect(self.connect_data)
        self.conbtn.setEnabled(False)
        self.exitbtn = QPushButton(self.langstr[2])
        self.exitbtn.setIcon(QIcon.fromTheme('application-exit'))
        self.exitbtn.clicked.connect(self.close)
        self.syslayout = QVBoxLayout()
        self.syslayout.setAlignment(Qt.AlignTop)
        self.syslayout.addWidget(self.confBtn)
        self.syslayout.addWidget(self.conbtn)
        self.syslayout.addWidget(self.exitbtn)
        self.sysbox = QGroupBox(self.langstr[22])
        self.sysbox.setLayout(self.syslayout)

        # using a frame as an horizontal line separator
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # add stuff to layout
        self.grid.addWidget(self.pw, 0, 0, 1, 4)
        self.grid.addWidget(self.mainlabel, 1, 0, 1, 4, Qt.AlignCenter)
        self.grid.addWidget(self.line, 2, 0, 1, 4)
        self.grid.addWidget(self.axisbox, 3, 0)
        self.grid.addWidget(self.samplebox, 3, 1)
        self.grid.addWidget(self.mesbox, 3, 2)
        self.grid.addWidget(self.sysbox, 3, 3)

        # Remaining time label
        self.time_label = QLabel(self.get_rem_time())
        self.statusBar().addPermanentWidget(self.time_label)
        # progress menuBar
        self.buffprogress = QProgressBar()
        self.buffprogress.setMaximum(100)
        self.buffprogress.setFixedSize(60, 10)
        self.buffprogress.setTextVisible(False)
        # label on status bar indicating buffer status
        self.statusLabel = QLabel('Buffer fill :')
        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusBar().addPermanentWidget(self.buffprogress)

        # show window
        self.move(300, 150)
        self.setWindowTitle('Data logger')
        self.show()

    def connect_data(self):
        if self.use_tcp_flag:
            self.connect_tcp()
        else:
            self.connect_serial()

    def config_data(self):
        if self.use_tcp_flag:
            self.tcpdialog.show()
        else:
            self.configdlg.show()

    def config_tcp(self, value):
        """ Get tcp info from configuration dialog and
            enable connection button
        """
        # if a valid tcp configuration is set
        if value[0]:
            self.tcp_config[0] = value[1]  # save address
            self.tcp_config[1] = value[2]  # save port
            self.conbtn.setEnabled(True)
            self.conAct.setEnabled(True)

    def use_tcp(self):
        """ Select serial port or network communication """
        if self.comAct.isChecked():
            self.use_tcp_flag = True
        else:
            self.use_tcp_flag = False

    def showtcp(self):
        self.tcpdialog.show()

    def show_stats(self):
        """ Show statistics dialog """
        raw_data = self.data[0:(self.buffersize -
                                (self.buffersize - self.chunk_size))]
        self.statsdlg.update(raw_data)
        self.statsdlg.show()

    def get_rem_time(self):
        multiplier = 1
        days = hours = mins = secs = msecs = 0

        # Time base
        if self.sample_ms.isChecked():
            multiplier = 1
        elif self.sample_s.isChecked():
            multiplier = 1000
        elif self.sample_min.isChecked():
            multiplier = 60000

        multiplier = multiplier * self.sample_val.value()
        max_time = (self.buffersize - self.count) * multiplier

        # more than 1 day
        if max_time > 864 * (10**5):
            days = math.floor(max_time / (864 * (10**5)))
            max_time = max_time % (864 * (10**5))
        # more than 1 hours
        if max_time > 36 * (10**5):
            hours = math.floor(max_time / (36 * (10**5)))
            max_time = max_time % (36 * (10**5))
        # more than 1 minutes
        if max_time > 60000:
            mins = math.floor(max_time / 60000)
            max_time = max_time % 60000
        # more than 1 second
        if max_time > 1000:
            secs = math.floor(max_time / 1000)
            max_time = max_time % 1000
        if max_time < 1000:
            msecs = max_time

        remaining_time = \
            f"Rem. time: {days}d : {hours:02}h : {mins:02}m : {secs:02}s : {msecs:03}ms  "
        return remaining_time

    def show_lang(self):
        """ Menu ->edit-> language callback, show dialog """
        self.langSelector.show()

    def new_lang(self, langue):
        """ save selected language """
        self.appsettings.setValue("Lang",
                                  f'translations/{langue[2].strip()}')
        QMessageBox.information(self, "Language", self.langstr[38])

    def use_filter(self):
        """ Menu->Edit->use filter callback """
        if self.filterAct.isChecked():
            self.use_internal_filter = True
        else:
            self.use_internal_filter = False

    def showedit(self):
        self.myeditor.show()
        self.myeditor.file_set('tools/datafilters.py')

    def startlogging(self):
        """ Start / stop button callback """
        sval = self.sample_val.value()
        multiplier = 1
        if self.sample_ms.isChecked():
            multiplier = 0.001
        elif self.sample_s.isChecked():
            multiplier = 1
        elif self.sample_min.isChecked():
            multiplier = 60
        self.tcp_thread.set_tic(multiplier * sval)
        self.chunk_size = self.count
        # temp string to store commands for arduino
        tmpstr = '{}{}'.format(str(sval), self.units[self.unitsel])
        tmpstr = tmpstr.encode()
        if not self.isRunning:              # not running ?
            reply = QMessageBox.question(self, self.langstr[23],
                                         self.langstr[24],
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.clear_data()
            self.isRunning = True
            self.btnstart.setText(self.langstr[25])
            self.btnstart.setIcon(QIcon.fromTheme('media-playback-pause'))
            self.btnload.setEnabled(False)
            self.loadAct.setEnabled(False)
            if not self.use_tcp_flag:
                # send configuration to arduino
                self.serport.write(bytes(tmpstr))
                # DO NOT REMOVE tHIS LINE
                self.serport.readline().decode('ascii')
                # send start command to arduino
                self.serport.write(bytes(b'R'))
                self.Thread.start()        # start reading values
                self.statusBar().showMessage(self.langstr[26])
            else:
                self.connect_tcp()
                self.tcp_thread.start()
        else:
            self.isRunning = False
            self.btnload.setEnabled(True)
            self.loadAct.setEnabled(True)
            self.btnstart.setText(self.langstr[17])
            self.btnstart.setIcon(QIcon.fromTheme('media-playback-start'))
            if not self.use_tcp_flag:
                self.serport.write(bytes(b'C'))  # send stop command to arduino
                self.Thread.stop()               # stop reading values
                self.statusBar().showMessage(self.langstr[27])
            else:
                self.isConnected = False
                self.socket.sendall("close".encode("utf-8"))
                self.tcp_thread.stop()

    def closeEvent(self, event):
        """ Custom handler when user tries to close the window
            Closes ports if needed and exits properly
        """
        self.statusBar().showMessage(self.langstr[28])
        reply = QMessageBox.question(self, self.langstr[28], self.langstr[29],
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            if self.isConnected:
                self.serport.close()
                if self.isRunning:
                    if not self.use_tcp_flag:
                        self.Thread.stop()
                        self.Thread.terminate()
                    else:
                        self.socket.sendall("close".encode("utf-8"))
                        self.tcp_thread.stop()
                        self.tcp_thread.terminate()

        else:
            event.ignore()
            self.statusBar().showMessage('')

    def help_app(self):
        """ launch help dialog """
        self.helpdlg.show()

    def about_app(self):
        """ About dialog box """
        about_msg =  """The poorman's data logger based on Arduino !!!\n
Copyright 2020 Cedric Pereira.
Released under GNU GPL license.\n
    Version 2.0.0"""
        QMessageBox.about(self, self.langstr[8], about_msg)

    def aboutqt_app(self):
        """ show About Qt dialog """
        QMessageBox.aboutQt(self)

    def setunit_s(self):
        """ set sample interval to seconds """
        self.unitsel = 1
        self.sample_val.setRange(1, 60)
        self.sample_val.setSingleStep(1)
        self.sample_val.setValue(0)

    def setunit_ms(self):
        """ set sample interval to millis """
        self.unitsel = 0
        self.sample_val.setRange(1, 1000)
        self.sample_val.setSingleStep(10)
        self.sample_val.setValue(0)

    def setunit_min(self):
        """ set sample interval to minutes """
        self.unitsel = 2
        self.sample_val.setRange(1, 60)
        self.sample_val.setSingleStep(1)
        self.sample_val.setValue(0)

    def showconfig(self):
        """ show serial configuration dialog """
        # using tcp communication
        if self.use_tcp_flag:
            # show tcp configuration unless serial is wanted
            if self.sender().text() == self.langstr[5]:
                self.configdlg.show()
            else:
                self.tcpdialog.show()
        else:
            self.configdlg.show()

    def showprefs(self):
        """ show preferences dialog """
        self.settingsdlg.show()

    def create_graphs(self):
        """ create a new plot inside the PlotWidget """
        self.p1 = self.pw.plot()     # create a new plot and set color to green
        color = self.appsettings.value("LineColor", QColor(100, 200, 100))
        self.p1.setPen(color)
        self.pw.setYRange(self.pmin, self.pmax, padding=0)
        self.p1.setData(self.data)

    def update_data(self, value):
        """
            slot for thread signal
            process and display data
        """
        if(self.count < self.buffersize):
            # process data - modify datafilter() in /tools/datafilters.py
            # to fit your needs
            # if value > 10000:
            #    value = 0
            if self.use_internal_filter:
                value = datafilter(value)
            self.count += 1
            self.chunk_size = self.count
            # shift data in the array one sample left
            self.data[:-1] = self.data[1:]
            self.data[-1] = value           # add new value
            self.p1.setData(self.data)      # update display
            percent = self.count / self.buffersize * 100
            self.statusLabel.setText('Buffer fill: {:04.2f}'
                                     .format(round(percent, 2)) + '%')
            self.buffprogress.setValue(int(round(percent, 2)))
            self.time_label.setText(self.get_rem_time())

        elif self.count == self.buffersize:
            self.btnstart.setText(self.langstr[17])
            self.btnstart.setIcon(QIcon.fromTheme('media-playback-start'))
            self.isRunning = False
            if not self.use_tcp_flag:
                # send stop command to arduino
                self.serport.write(bytes(b'C'))
                self.statusBar().showMessage(self.langstr[30])
                self.Thread.stop()
                self.tcp_thread.stop()
            else:
                self.isConnected = False
                self.tcp_thread.stop()
                self.Thread.stop()
                self.socket.sendall("close".encode("utf-8"))
            self.btnload.setEnabled((True))

    def set_axis_grid(self):
        """ display horizontal an vertical grids """
        xaxis = False
        yaxis = False

        if self.xaxisgrid.checkState():
            xaxis = True
        if self.yaxisgrid.checkState():
            yaxis = True
        self.pw.showGrid(xaxis, yaxis)

    def configure_app(self, conflist):
        """ parse data from preferences dialog """
        if conflist[0] == "Ok" or conflist[0] == "Save":
            self.data = np.zeros(conflist[1],)
            self.pw.setLabel('left', conflist[4], conflist[5])
            self.pmin = conflist[6]
            self.pmax = conflist[7]
            self.pw.setYRange(self.pmin, self.pmax, padding=0)
            self.mainlabel.setText(conflist[8])
            self.filterAct.setChecked(conflist[10])
            self.use_internal_filter = conflist[10]
            self.comAct.setChecked(conflist[11])
            self.use_tcp_flag = conflist[11]
            if conflist[2] == 's':
                self.sample_s.setChecked(True)
            elif conflist[2] == 'ms':
                self.sample_ms.setChecked(True)
            elif conflist[2] == 'min':
                self.sample_min.setChecked(True)
            self.sample_val.setValue(conflist[3])
            self.p1.setPen(conflist[9])
        elif conflist[0] == "Cancel":
            pass

    def configure_data(self, conflist):
        """ Get data from configuration dialog and parse it """
        # save a copy of settings list
        self.settingsList = conflist.copy()
        # conflist[0] is the exit status (ok = 1 or cancel = 0)
        if conflist[0] and (conflist[1] is not None and conflist[1] != ''):
            self.conbtn.setEnabled(True)
            self.conAct.setEnabled(True)

    def update_display(self):
        """ Update buttons and labels when connected """
        self.conbtn.setEnabled(False)
        self.confBtn.setEnabled(False)
        self.scanAct.setEnabled(False)
        self.conAct.setEnabled(False)
        self.sample_min.setEnabled(True)
        self.sample_ms.setEnabled(True)
        self.sample_s.setEnabled(True)
        self.sample_val.setEnabled(True)
        self.btnload.setEnabled(True)
        self.loadAct.setEnabled(True)
        self.btnsave.setEnabled(True)
        self.saveAct.setEnabled(True)
        self.btnstart.setEnabled(True)
        self.vallabel.setEnabled(True)

    def connect_tcp(self):
        # if not yet connected
        if not self.isConnected:
            # try to creat a new socket and connect it
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.tcp_config[0], self.tcp_config[1]))
                self.isConnected = True
                self.update_display()
                self.statusBar().showMessage(
                    f'Connection to {self.tcp_config[0]}:{self.tcp_config[1]} successfull!', 1000)
            except ConnectionRefusedError as e:
                QMessageBox.about(self, 'Big mistake!', "Network error: " + str(e) +
                "\nIs your server running ?")

    def connect_serial(self):
        """ Button conBtn clicked event handler
            Try to connect to selected serial port
        """
        # set serial configuration
        self.serport.port = self.settingsList[1]
        self.serport.baudrate = self.settingsList[2]
        self.serport.timeout = 1
        # not yet connected? -> try to connect
        if not self.isConnected:
            try:
                if not self.serport.isOpen():
                    self.serport.open()
                self.isConnected = True
                self.update_display()
                self.statusBar().showMessage(
                    f'Connection to {self.settingsList[1]} successfull!', 1000)
            # something is wrong
            except serial.serialutil.SerialException:
                QMessageBox.about(self, 'Big mistake!', """Error opening port.
                \nPlease check your connections!!!""")

    def savefile(self):
        """ Save data to file """
        self.Thread.stop()
        # open file selection dialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, self.langstr[18], "",
                                                  """Datalogger Files
                                                   (*.lfd);;All Files (*)""",
                                                  options=options)
        # if file can be created
        if fileName:
            # add lfd suffix if not in filename
            if not QFileInfo(fileName).suffix():
                fileName += '.lfd'
            with open(fileName, 'w')as file:
                # write app name and version
                file.write('Datalogger v1.0\r\n')
                # add dataset name
                file.write(self.mainlabel.text() + '\r\n')
                # write used buffersize
                file.write(str(self.buffersize) + '\r\n')
                # write delay unit and value
                file.write(str(self.sample_val.value()) + ',' + self.units[
                    self.unitsel] + '\r\n')
                # write values
                file.write(str(self.pmin) + ',' + str(self.pmax) + '\r\n')
                # write data
                for n in range(0, self.buffersize):
                    file.write(str(self.data[n]) + '\r\n')
                # ask for optional csv file
                reply = QMessageBox.question(self, self.langstr[31],
                                             self.langstr[32],
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.No)
                # create CSV file on demand
                if reply == QMessageBox.Yes:
                    # replace file suffix
                    fileName = fileName.replace('lfd', 'csv')
                    with open(fileName, 'w+') as file:
                        try:
                            header = "Samples,Values" + '\r\n'
                            file.write(header)
                            for n in range(0, self.buffersize):
                                val = str(n) + ',' + str(self.data[n]) + '\r\n'
                                file.write(val)
                        except():
                            print('File error')

        self.Thread.start()

    def loadfile(self):
        """ load data from file """
        # open file selection dialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, self.langstr[19],
                                                  "", """Datalogger Files
                                                   (*.lfd);;All Files (*)""",
                                                  options=options)
        if fileName == "":
            return
        # if file exists and is a datalogger file
        if fileName and QFileInfo(fileName).suffix() == 'lfd':
            with open(fileName, 'r') as file:
                # read app name : not used
                file.readline()
                # read dataset name
                self.mainlabel.setText(file.readline().strip())
                # read buffesize
                self.buffersize = int(file.readline().strip())
                # get delay unit
                val = file.readline().strip().split(',')
                if val[1] == 'm':
                    self.sample_ms.setChecked(True)
                elif val[1] == 's':
                    self.sample_s.setChecked(True)
                elif val[1] == 'M':
                    self.sample_min.setChecked(True)
                # read delay value
                self.sample_val.setValue(int(val[0]))
                # read values range and setup graph
                val = file.readline().strip().split(',')
                self.pmin = float(val[0])
                self.pmax = float(val[1])
                self.pw.setYRange(self.pmin, self.pmax, padding=0)
                # read data
                for n in range(0, self.buffersize):
                    self.data[n] = float(file.readline())
                self.p1.setData(self.data)      # update display
                self.statbutton.setEnabled(True)
                self.chunk_size = self.buffersize

        else:
            QMessageBox.about(self, self.langstr[33],
                              f"Can't load file {fileName}\nBad file type!")

    def clear_data(self):
        """ erase all data """
        # if not running, erase data and update display
        if self.btnstart.text() != self.langstr[25]:
            for n in range(0, self.buffersize):
                self.data[n] = 0
            self.p1.setData(self.data)
            self.count = self.chunk_size = 0


class TCPThread(QThread):
    """
        Thread for reading data from the network
    """
    # custom signal to return data
    dataReady = pyqtSignal(float)
    timer = TicTimer()
    send_msg = "send".encode("utf-8")

    def __init__(self, parent=None):
        super(TCPThread, self).__init__(parent)
        self.threadactive = True
        self.parent = parent
        self.tic = 0.1
        self.timer.start(self.tic)

    def run(self):
        self.threadactive = True
        while self.threadactive:
            if self.timer.is_finished():
                self.parent.socket.sendall(self.send_msg)
                data = self.parent.socket.recv(1024)
                self.timer.start(self.tic)
                data = data.decode('utf-8')
                if data != '':
                    value = float(data)
                    self.dataReady.emit(value)

    def set_tic(self, tic):
        self.tic = tic
        self.timer.start(self.tic)

    def stop(self):
        """ stop sending data """
        self.threadactive = False
        self.wait()


class DataThread(QThread):
    """ Thread for reading serial data """

    # custom signal to return data
    dataReady = pyqtSignal(float)
    isOpen = True

    def __init__(self, parent=None):
        super(DataThread, self).__init__(parent)
        self.threadactive = True
        self.parent = parent
        self.values = -1

    def run(self):
        """code to execute """
        self.threadactive = True
        while self.threadactive:
            try:
                # read a string from serial and cast it to int
                self.values = int(
                    self.parent.serport.readline().decode('ascii'))
                # envoi d'une valeur à afficher
                self.dataReady.emit(self.values)
            except (TypeError, ValueError):
                # self.dataReady.emit(-1)
                pass

    def stop(self):
        """ stop sending data """
        self.threadactive = False
        self.wait()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    locale = QLocale.system().name()
    appTranslator = QTranslator(app)
    if appTranslator.load('qt_' + locale, QLibraryInfo.location(
            QLibraryInfo.TranslationsPath)):
        app.installTranslator(appTranslator)
    ex = MainWindow()
    sys.exit(app.exec_())
