import threading
from PyQt5 import QtCore, QtGui, QtWidgets
import qdarkstyle
from threading import Thread
from collections import deque
from datetime import datetime
import time
import sys
import cv2
import imutils
# import multiprocessing as mp

import qasync
from qasync import asyncSlot, asyncClose, QApplication


import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100
async def step1_wait_for_jetson_sdp(pc, sdp):
    # string = input("Jetson SDP:")
    string = sdp+'"type": "offer"}'
    sdp = object_from_string(string)
    if isinstance(sdp, RTCSessionDescription):
        await pc.setRemoteDescription(sdp)
        await pc.setLocalDescription(await pc.createAnswer())

async def step2_running_loop():
    global RUNNING, HEALTHCHECKS
    while RUNNING and HEALTHCHECKS != 0:
        HEALTHCHECKS -= 1
        await asyncio.sleep(1)


class ControllerWidget(QtWidgets.QWidget):

    def __init__(self, sdp):
        super(QtWidgets.QWidget, self).__init__()
        self.pc = RTCPeerConnection()
        self.sdp = sdp
        print(f"init {sdp}")
        self.thread = qasync.run(self.foo())
        # self.thread.start()


    @asyncSlot()
    async def step1(self, pc, sdp):
        await step1_wait_for_jetson_sdp(pc, sdp)
        print("===================================")
        print(object_to_string(pc.localDescription))

    def foo(self):
        # self.coro = self.main(self.pc, self.sdp)
        self.step1(self.pc, self.sdp)

    
    '''
    async def main(self, pc, sdp):
        @pc.on("datachannel")
        def on_datachannel(channel):

            @channel.on("message")
            def on_message(message):
                global RUNNING, HEALTHCHECKS, VERBOSE
                if message == 'active':
                    HEALTHCHECKS = 100
                    if VERBOSE:
                        print("[RENEW] Healthcheck")
                elif message == 'esc':
                    RUNNING = False

            async def report_health():
                """Send active message to jetson nano"""
                while True:
                    channel.send("active")
                    await asyncio.sleep(0.1)

            async def run_controller():
                """Send command to jetson nano"""
                global RUNNING
                
                img = cv2.imread('controller/controller.jpg')
                while True:
                    self.img = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
                    self.pix = QtGui.QPixmap.fromImage(self.img)
                    self.video_frame.setPixmap(self.pix)
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:
                        channel.send(f"esc")
                        break
                    elif (
                        key == ord('q')
                        or key == ord('w')
                        or key == ord('e')
                        or key == ord('a')
                        or key == ord('s')
                        or key == ord('d')
                        or key == ord('z')
                        or key == ord('x')
                        or key == ord('c')
                    ):
                        img = cv2.imread(f'controller/controller_{chr(key)}.jpg')
                        channel.send(f"{chr(key)}")
                    else:
                        img = cv2.imread(f'controller/controller.jpg')
                    await asyncio.sleep(0.05)
                cv2.destroyAllWindows()
                RUNNING = False

            asyncio.ensure_future(report_health())
            asyncio.ensure_future(run_controller())

        await step1_wait_for_jetson_sdp(pc, sdp)
        print("===================================")
        print(object_to_string(pc.localDescription))
        await step2_running_loop()
    '''

    
    def get_frame(self):
        print("get frame")
        return self.video_frame


if __name__ == "__main__":
    

    stream_ip = '192.168.0.109'
    camera = f'rtmp://{stream_ip}/rtmp/live'
    sdp = input("s:")
    print('fuck')

    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))

    mywid = ControllerWidget(sdp)
    mywid.resize(500,500)
    mywid.setWindowTitle("controller")
    mywid.show()
    def exit_application():
        """Exit program event handler"""

        sys.exit(1)
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop)  # NEW must set the event loop

    with loop:
        w = Example()
        w.show()
        loop.run_forever()

    QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), mywid, exit_application)
    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
    

    




