from collections import deque
import json
import time
import logging
import threading
import argparse
import multiprocessing as mp
import aiohttp

import cv2
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string
import os
from dotenv import load_dotenv
load_dotenv()

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

async def step1_wait_for_jetson_sdp(pc, sdp):
    # string = input("Jetson SDP:")
    # string += ': "offer"}'
    if sdp is not None:
        string = sdp
        dic = {'sdp':string,'type':'offer'}
        sdp = RTCSessionDescription(dic['sdp'],dic['type'])
    else:
        string = input("Jetson SDP:") + 'fingerprint:sha-256 7D:4B:28:77:AF:E7:60:B1:F0:56:CE:CB:21:77:46:D7:06:9C:54:5F:E7:DC:1F:9A:CB:27:C1:25:AC:37:AE:A8\r\na=setup:actpass\r\n", "type": "offer"}'
        print(string)
        sdp = object_from_string(string)
    
    if isinstance(sdp, RTCSessionDescription):
        await pc.setRemoteDescription(sdp)
        await pc.setLocalDescription(await pc.createAnswer())

async def step2_running_loop():
    global RUNNING, HEALTHCHECKS
    while RUNNING and HEALTHCHECKS != 0:
        print("wait-1")
        HEALTHCHECKS -= 1
        await asyncio.sleep(1)

async def send_answer(pc, carID):
    server_link = os.getenv('SERVER_LINK')
    print("post")
    async with aiohttp.ClientSession() as session:
        async with session.post(server_link, 
            json=json.dumps({
                "carID": carID,
                "sdp":pc.localDescription.sdp,
                # "type":pc.localDescription.type,
            })
        ) as response:

            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            print(await response.json())

            if response.status == 200:
                print("success")
            else:
                print("error")

async def main(pc, sdp=None, carID=""):

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("on connect.....")
        @channel.on("message")
        def on_message(message):
            global RUNNING, HEALTHCHECKS, VERBOSE
            if message == 'active':
                print("getmessage active")
                HEALTHCHECKS = 100
                if VERBOSE:
                    print("[RENEW] Healthcheck")
            elif message == 'esc':
                print("getmessage esc")
                RUNNING = False

        async def report_health():
            """Send active message to jetson nano"""
            while True:
                print("send active")
                channel.send("active")
                await asyncio.sleep(0.1)

        async def run_controller():
            """Send command to jetson nano"""
            global RUNNING
            cv2.namedWindow("CONTROLLER", cv2.WINDOW_GUI_EXPANDED)
            img = cv2.imread('controller/controller.jpg')
            while True:
                cv2.imshow("CONTROLLER", img)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    channel.send(f"esc")
                    break
                elif (
                    key == ord('w')
                    # or key == ord('q')
                    # or key == ord('e')
                    or key == ord('a')
                    or key == ord('s')
                    or key == ord('d')
                    # or key == ord('z')
                    # or key == ord('x')
                    # or key == ord('c')
                ):
                    img = cv2.imread(f'controller/controller_{chr(key)}.jpg')
                    channel.send(f"{chr(key)}")
                else:
                    img = cv2.imread(f'controller/controller.jpg')
                    channel.send(f"")
                await asyncio.sleep(0.05)
            cv2.destroyAllWindows()
            RUNNING = False

        asyncio.ensure_future(report_health())
        asyncio.ensure_future(run_controller())

    await step1_wait_for_jetson_sdp(pc, sdp)
    print("===================================")
    print(object_to_string(pc.localDescription))
    await send_answer(pc, carID)
    await step2_running_loop()
'''
class controllerThread():
    def __init__(self, previewName):
        self.pc = RTCPeerConnection()
        self.coro = self.main(self.pc)
        asyncio.run(self.coro)

    def get_frame(self):
        return self.img
    
    async def main(self, pc):

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
                # cv2.namedWindow("CONTROLLER", cv2.WINDOW_GUI_EXPANDED)
                self.img = cv2.imread('controller/controller.jpg')
                while True:
                    # cv2.imshow("CONTROLLER", img)
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
                        self.img = cv2.imread(f'controller/controller_{chr(key)}.jpg')
                        channel.send(f"{chr(key)}")
                    else:
                        self.img = cv2.imread(f'controller/controller.jpg')
                    await asyncio.sleep(0.05)
                # cv2.destroyAllWindows()
                RUNNING = False

            asyncio.ensure_future(report_health())
            asyncio.ensure_future(run_controller())

        await step1_wait_for_jetson_sdp(pc)
        print("===================================")
        print(object_to_string(pc.localDescription))
        await step2_running_loop()

    
class camThread:
    def __init__(self, previewName, url, dequeSize = 1):
        self.previewName = previewName
        self.url = url
        self.deque = deque(maxlen=dequeSize)
        self.thread = threading.Thread(target=self.watch_streaming, args=())

        
    def watch_streaming(self):
        print(f"streaming from{self.url}")
        # cv2.namedWindow(self.previewName)
        cap = cv2.VideoCapture(f'rtmp://{self.url}/rtmp/live')
        while cap.isOpened():
            success, img = cap.read()
            if success:
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
                self.deque.append(img)      
        print("end...")
        cap.release()
        # cv2.destroyWindow(self.previewName)
    
    def get_frame(self):
        # return self.deque[-1]
        while len(self.deque)>0:
            cv2.imshow(self.previewName, self.deque[-1])
'''


def watch_streaming(url, previewName):
    print(url)
    cv2.namedWindow(previewName, cv2.WINDOW_AUTOSIZE)
    cap = cv2.VideoCapture(f'rtmp://{url}/rtmp/live')
    while cap.isOpened():
        success, img = cap.read()
        if success:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            cv2.imshow(previewName, img)   
    print("end...")
    cap.release()
    cv2.destroyWindow(previewName)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    VERBOSE = args['verbose']
    
    # Run main event loop
    # thd = mp.Process(target=watch_streaming, args=("192.169.137.97:8000/rest/cars/", "CONTROLLER",))
    # thd.start()
    # pc = RTCPeerConnection()
    # coro = main(pc)
    
   
    # try:

    #     loop = asyncio.get_event_loop()
    #     loop.run_until_complete(coro)
    #     # thread.join()
    # except KeyboardInterrupt:
    #     # thd.terminate()
    #     pass
    sdp = input("sdp:")
    car_id = input("carid:")
    pc = RTCPeerConnection()
    try:
        coro = main(pc, sdp=sdp, carID=car_id)
        asyncio.run(coro)
    except Exception as e:
        print(e)
        pass



