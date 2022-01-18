from PyQt5 import QtCore, QtGui, QtWidgets
import qdarkstyle
from threading import Thread
from collections import deque
from datetime import datetime
import time
import sys
import cv2
import imutils
from PyQt5.QtCore import pyqtSlot
from browser import *


IP_ADDR = "0.0.0.0"
SDP = ""

class logindialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Login')
        self.resize(200, 200)
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.frame = QtWidgets.QFrame(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.ipEdit = QtWidgets.QLineEdit()
        self.ipEdit.setPlaceholderText("input ip")
        self.verticalLayout.addWidget(self.ipEdit)

        self.sdpEdit = QtWidgets.QLineEdit()
        self.sdpEdit.setPlaceholderText("input sdp")
        self.verticalLayout.addWidget(self.sdpEdit)

        self.pushButton_enter = QtWidgets.QPushButton()
        self.pushButton_enter.setText("Connect")
        self.verticalLayout.addWidget(self.pushButton_enter)
        self.pushButton_enter.clicked.connect(self.on_clicked)
        

    def on_clicked(self):
        global IP_ADDR, SDP
        IP_ADDR = self.ipEdit.text()
        SDP = self.sdpEdit.text()
        print(f'{IP_ADDR}, {SDP}')
        self.accept()

    

if __name__ == "__main__":
    mp.set_start_method('spawn')
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    dialog = logindialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        dialog.close()
        

        thd = mp.Process(target=watch_streaming, args=(IP_ADDR, "CONTROLLER",))
        thd.start()
        pc = RTCPeerConnection()
        coro = main(pc, SDP)
        try:
            asyncio.run(coro)
            thd.join()
        except KeyboardInterrupt:
            thd.terminate()
            pass
        sys.exit(app.exec_())

    
