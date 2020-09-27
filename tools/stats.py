# -*- coding: utf-8 -*-

"""

 Project     : The poorman's data logger.
 File        : stats.py
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
import numpy as np
from statistics import fmean, median, pstdev, pvariance, StatisticsError
from PyQt5.QtCore import pyqtSignal, QLocale, Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLabel,
                             QCheckBox, QSpinBox, QPushButton, QComboBox,
                             QFrame)
from PyQt5.QtGui import QIcon
from tools.langtranslate import loadLanguage


class StatsDialog(QDialog):
    data = np.zeros((1,))
    size = 0

    def __init__(self, parent=None):
        super(StatsDialog, self).__init__()
        if QLocale.system().name() == 'fr_FR':
            self.langstr = loadLanguage('resources/sersettings_fr_FR')
        else:
            self.langstr = loadLanguage('resources/sersettings_en')
        self.setWindowTitle("Stats")
        self.setupUI()

    def setupUI(self):
        # set window icon
        self.setWindowIcon(QIcon('resources/images/icon.png'))
        self.setFixedSize(300, 200)

        # ok and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)

        # labels
        self.title_label = QLabel("Data statistics")
        self.title_label.setStyleSheet('color : blue; border: 1px solid back; padding:2px;')
        self.mean_label = QLabel("Mean value : ")
        self.mean_label.setStyleSheet('color : #D55; border: 1px solid black;')
        self.mean_label.setAlignment(Qt.AlignRight)
        self.median_label = QLabel("Median value : ")
        self.median_label.setStyleSheet('color : #55D; border: 1px solid black;')
        self.median_label.setAlignment(Qt.AlignRight)
        self.variance_label = QLabel("Variance : ")
        self.variance_label.setStyleSheet('color : #D55; border: 1px solid black;')
        self.variance_label.setAlignment(Qt.AlignRight)
        self.std_var_label = QLabel("Standard deviation : ")
        self.std_var_label.setStyleSheet('color : #55D; border: 1px solid black;')
        self.std_var_label.setAlignment(Qt.AlignRight)
        self.mean_val_label = QLabel("")
        self.mean_val_label.setStyleSheet('color : #D55; border: 1px solid black;')
        self.median_val_label = QLabel("")
        self.median_val_label.setStyleSheet('color : #55D; border: 1px solid black;')
        self.var_val_label = QLabel("")
        self.var_val_label.setStyleSheet('color : D55; border: 1px solid black;')
        self.std_var_val_label = QLabel("")
        self.std_var_val_label.setStyleSheet('color : #55D; border: 1px solid black;')

        # separator
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # put all the stuff together
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.title_label, 0, 0, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(self.mean_label, 1, 0)
        self.grid.addWidget(self.mean_val_label, 1, 1)
        self.grid.addWidget(self.median_label, 2, 0)
        self.grid.addWidget(self.median_val_label, 2, 1)
        self.grid.addWidget(self.variance_label, 3, 0)
        self.grid.addWidget(self.var_val_label, 3, 1)
        self.grid.addWidget(self.std_var_label, 4, 0)
        self.grid.addWidget(self.std_var_val_label, 4, 1)
        self.grid.addWidget(self.line, 5, 0, 1, 2)
        self.grid.addWidget(self.buttonBox, 6, 1)

    def update(self, data):
        self.data = data
        try:
            meanval = fmean(self.data)
            caption = f"{meanval:.3f}"
            self.mean_val_label.setText(caption)
            caption = f"{median(self.data):.3f}"
            self.median_val_label.setText(caption)
            caption = f"{pvariance(self.data, mu=meanval):.3f}"
            self.var_val_label.setText(caption)
            caption = f"{pstdev(self.data, mu=meanval):.3f}"
            self.std_var_val_label.setText(caption)
        except StatisticsError:
            pass
