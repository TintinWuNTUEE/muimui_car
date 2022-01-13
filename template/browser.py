import json
import time
import logging
import threading
import argparse

import cv2
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

async def step1_wait_for_jetson_sdp(pc):
    string = input("Jetson SDP:")
    sdp = object_from_string(string)
    if isinstance(sdp, RTCSessionDescription):
        await pc.setRemoteDescription(sdp)
        await pc.setLocalDescription(await pc.createAnswer())

async def step2_running_loop():
    global RUNNING, HEALTHCHECKS
    while RUNNING and HEALTHCHECKS != 0:
        HEALTHCHECKS -= 1
        await asyncio.sleep(1)

async def main(pc):

    @pc.on("datachannel")
    def on_datachannel(channel):

        @channel.on("message")
        def on_message(message):
            global RUNNING, HEALTHCHECKS, VERBOSE
            if message == 'active':
                HEALTHCHECKS = 10
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
            cv2.namedWindow("CONTROLLER", cv2.WINDOW_GUI_EXPANDED)
            img = cv2.imread('controller/controller.jpg')
            while True:
                cv2.imshow("CONTROLLER", img)
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
                await asyncio.sleep(0.01)
            cv2.destroyAllWindows()
            RUNNING = False

        asyncio.ensure_future(report_health())
        asyncio.ensure_future(run_controller())

    await step1_wait_for_jetson_sdp(pc);
    print("===================================")
    print(object_to_string(pc.localDescription))
    await step2_running_loop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    VERBOSE = args['verbose']

    # Run main event loop
    pc = RTCPeerConnection()
    coro = main(pc)
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
