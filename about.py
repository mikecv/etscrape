#!/usr/bin/env python3

from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5 import QtGui

from utils import *

# *******************************************
# About dialog class.
# *******************************************
class AboutDialog(QDialog):
    def __init__(self, version):
        super(AboutDialog, self).__init__()
        uic.loadUi(res_path("about.ui"), self)

        self.showAbout(version)

    # *******************************************
    # Displays an "About" dialog box.
    # *******************************************
    def showAbout(self, version):
        # Set dialog window icon.
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(res_path("./resources/about.png")))
        self.setWindowIcon(icon)

        # Update version information.
        self.versionLbl.setText("Version : {0:s}".format(version))

        # Update dialog icon.
        self.aboutIcon.setPixmap(QtGui.QPixmap(res_path("./resources/about.png")))

        # Show dialog.
        self.exec_()
