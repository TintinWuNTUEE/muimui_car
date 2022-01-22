from collections import deque
import json
# import time
# import logging
# import threading
import argparse
import multiprocessing as mp
import aiohttp

import cv2
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string
import os
import sys
from dotenv import load_dotenv
load_dotenv()

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

def exit_application():
    """Exit program event handler"""
    sys.exit(1)

async def step1_wait_for_jetson_sdp(pc, sdp):

    if sdp is not None:
        string = sdp
        dic = {'sdp':string,'type':'offer'}
        sdp = RTCSessionDescription(dic['sdp'],dic['type'])
    else:
        string = input("Jetson SDP:")
        print(string)
        sdp = object_from_string(string)
    
    if isinstance(sdp, RTCSessionDescription):
        await pc.setRemoteDescription(sdp)
        await pc.setLocalDescription(await pc.createAnswer())

async def step2_running_loop():
    global RUNNING, HEALTHCHECKS
    while RUNNING and HEALTHCHECKS != 0:
        HEALTHCHECKS -= 1
        await asyncio.sleep(1)
    RUNNING = False

async def send_answer(pc, carID):
    server_link = os.getenv('SERVER_LINK')
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
        @channel.on("message")
        def on_message(message):
            global RUNNING, HEALTHCHECKS, VERBOSE
            if message == 'active':
                HEALTHCHECKS = 100
                if VERBOSE:
                    print("[RENEW] Healthcheck")
            elif message == 'esc':
                print("getmessage esc")
                RUNNING = False

        async def report_health():
            """Send active message to jetson nano"""
            while True:
                channel.send("active")
                await asyncio.sleep(0.1)

        async def run_controller():
            """Send command to jetson nano"""
            global RUNNING
            cv2.namedWindow("CONTROLLER", cv2.WINDOW_GUI_EXPANDED)
            img = cv2.imread('controller/controller.jpg')
            while RUNNING:
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
                    channel.send(f"n")
                await asyncio.sleep(0.1)
            cv2.destroyAllWindows()
            RUNNING = False
            cv2.waitKey(1)
            # raise Exception("Controller exception")

        asyncio.ensure_future(report_health())
        asyncio.ensure_future(run_controller())

    await step1_wait_for_jetson_sdp(pc, sdp)
    print("===================================")
    print(object_to_string(pc.localDescription))
    await send_answer(pc, carID)
    await step2_running_loop()


def watch_streaming(url, previewName):
    print(f"start streaming from{url}")
    cv2.namedWindow(previewName, cv2.WINDOW_AUTOSIZE)
    cap = cv2.VideoCapture(f'rtmp://{url}/rtmp/live')
    while cap.isOpened():
        success, img = cap.read()
        if success:
            if cv2.waitKey(1) & 0xFF == 27:
                break
            img = cv2.flip(img,-1)
            cv2.imshow(previewName, img)   
    print("end...")
    cap.release()
    cv2.destroyAllWindows()
    # raise Exception("Video Exception")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    VERBOSE = args['verbose']
    
    # Run main event loop
    # thd = mp.Process(target=watch_streaming, args=("192.169.137.97:8000/rest/cars/", "CONTROLLER",))
    # thd.start()
    pc = RTCPeerConnection()
    coro = main(pc)
    
   
    try:

        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
        # thread.join()
    except KeyboardInterrupt:
        # thd.terminate()
        pass



