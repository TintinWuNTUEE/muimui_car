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
from app import * 

import asyncio
import aiohttp
from dotenv import load_dotenv
load_dotenv()


IP_ADDR = "0.0.0.0"
SDP = ""
TOKEN = ""
CAR_ID = ""
PIC_DIR = "pic/logo128.png"

from PyQt5 import  QtNetwork
from PyQt5.QtCore import QCoreApplication, QUrl
import sys


class logindialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Login')
        self.resize(200, 200)
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.frame = QtWidgets.QFrame(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)

        # self.ipEdit = QtWidgets.QLineEdit()
        # self.ipEdit.setPlaceholderText("input ip")
        # self.verticalLayout.addWidget(self.ipEdit)

        # self.sdpEdit = QtWidgets.QLineEdit()
        # self.sdpEdit.setPlaceholderText("input sdp")
        # self.verticalLayout.addWidget(self.sdpEdit)

        self.tokenEdit = QtWidgets.QLineEdit()
        self.tokenEdit.setPlaceholderText("input token")
        self.verticalLayout.addWidget(self.tokenEdit)

        self.pushButton_enter = QtWidgets.QPushButton()
        self.pushButton_enter.setText("Connect")
        self.verticalLayout.addWidget(self.pushButton_enter)
        self.pushButton_enter.clicked.connect(self.on_clicked)
        

    def on_clicked(self):
        global TOKEN
        TOKEN = self.tokenEdit.text()
        self.tokenEdit.setText("")
        # self.accept()
        self.doRequest()

    def doRequest(self):   
        server_link = os.getenv('SERVER_LINK')
        url = server_link + TOKEN + '/'
        # print(f"send to {url}")

        req = QtNetwork.QNetworkRequest(QUrl(url))
        self.nam = QtNetwork.QNetworkAccessManager()
        self.nam.finished.connect(self.handleResponse)
        self.nam.get(req)    

    def handleResponse(self, reply):
        global CAR_ID, IP_ADDR, SDP
        er = reply.error()
        bytes_string = reply.readAll()
        json_string = str(bytes_string, 'utf-8')
        res = json.loads(json_string) 
        # print("response", res)

        if er == QtNetwork.QNetworkReply.NoError:

            res = res[0]
            print(res['carID'])
            print(res['carIP'])
            print(res['sdp'])
            CAR_ID = res['carID']
            IP_ADDR = res['carIP']
            SDP = res['sdp']
            self.accept()
            
        else:
            print("Error occured: ", er)
            print(reply.errorString())
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(res.get('message', "unknow error occurred"))
            msg.setWindowTitle("Error")
            msg.exec_()



def test():
    """ test for app quit() """
    for i in range(10):
        print(i)
        time.sleep(0.02)   

if __name__ == "__main__":
    mp.set_start_method('spawn')
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    app.setWindowIcon(QtGui.QIcon(PIC_DIR))
    dialog = logindialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        dialog.close()
        # app.quit()
 
        # QCoreApplication.quit()
        pc = RTCPeerConnection()
        coro = main(pc, sdp=SDP, carID=CAR_ID)
        thd = mp.Process(target=watch_streaming, args=(IP_ADDR, "STREAMING",))
             
        try:
            thd.start()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro)
            asyncio.run(coro)           
            thd.terminate()
        except Exception as e:
            print(e)
            thd.terminate()
            # loop.close()
            # exit_application()

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Info")
        msg.setInformativeText("The time is over. Thank you")
        msg.setWindowTitle("End")
        msg.exec_()
    # sys.exit(app.exec_())

    
