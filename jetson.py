import json
import time
import logging
import threading
import argparse
import asyncio
import cv2
import argparse
import multiprocessing as mp

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

from motor import MotorDriver

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

def Move(message,Motor):
    if message =="w":
        MotorForward(Motor)
    elif message =="s":
        MotorBackward(Motor)
    elif message =="d":
        MotorLeftward(Motor)
    elif message =="a":
        MotorRightward(Motor)

def MotorForward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'backward', 100)
    time.sleep(0.01)
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return

def MotorLeftward(Motor):
    Motor.MotorRun(0, 'backward', 100)
    Motor.MotorRun(1, 'backward', 100)
    time.sleep(0.01)
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return

def MotorRightward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'forward', 100)
    time.sleep(0.01)
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return

def MotorBackward(Motor):
    Motor.MotorRun(0, 'backward', 100)
    Motor.MotorRun(1, 'forward', 100)
    time.sleep(0.01)
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return
    

async def step1_wait_for_browser_sdp(pc):
    string = input("Browser SDP:")
    sdp = object_from_string(string)
    await pc.setRemoteDescription(sdp)

async def step2_running_loop():
    global RUNNING, HEALTHCHECKS
    while RUNNING and HEALTHCHECKS > 0:
        HEALTHCHECKS -= 1
        await asyncio.sleep(1)

async def main(pc,Motor):

    channel = pc.createDataChannel("chat")

    @channel.on("open")
    def on_open():
        async def report_health():
            """Send active message to jetson nano"""
            while True:
                channel.send("active")
                await asyncio.sleep(0.1)
        asyncio.ensure_future(report_health())

    @channel.on("message")
    def on_message(message):
        global RUNNING, HEALTHCHECKS, VERBOSE
        if message == 'esc':
            RUNNING = False
            return
        elif message == 'active':
            HEALTHCHECKS = 10
            if VERBOSE:
                print("[RENEW] Healthcheck")
            return
        print(f"[RECV]: key '{message}'")
        Move(message,Motor)
    await pc.setLocalDescription(await pc.createOffer())
    print(object_to_string(pc.localDescription))
    print("===================================")
    await step1_wait_for_browser_sdp(pc);
    await step2_running_loop()






def gstreamer_camera(queue):
    pipeline = (
        "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)1920, height=(int)1080, "
            "format=(string)NV12, framerate=(fraction)30/1 ! "
        "queue ! "
            "nvvidconv flip-method=2 ! "
                "video/x-raw, "
                "width=(int)1920, height=(int)1080, "
                "format=(string)BGRx, framerate=(fraction)30/1 ! "
            "videoconvert ! "
                "video/x-raw, format=(string)BGR ! "
            "appsink"
        )

    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        queue.put(frame)
        print("[CAM] READ")


def gstreamer_rtmpstream(queue):
    pipeline = (
        "appsrc ! "
            "video/x-raw, format=(string)BGR ! "
        "queue ! "
            "videoconvert ! "
                "video/x-raw, format=RGBA ! "
            "nvvidconv ! "
            "nvv4l2h264enc bitrate=8000000 ! "
            "h264parse ! "
            "flvmux ! "
            'rtmpsink location="rtmp://0.0.0.0/rtmp/live live=1"'
        )

    writer = cv2.VideoWriter(pipeline, cv2.CAP_GSTREAMER, 0, 30.0, (1920, 1080))
    while True:
        frame = queue.get()
        if frame is None:
            break
        writer.write(frame)
        print("[RTMP] WRITE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    VERBOSE = args['verbose']
    Motor = MotorDriver()
    
    # Run main event loop
    pc = RTCPeerConnection()
    coro = main(pc,Motor)
    # === streaming ===
    queue = mp.Queue(maxsize=1)
    reader = mp.Process(target=gstreamer_camera, args=(queue,))
    reader.start()
    writer = mp.Process(target=gstreamer_rtmpstream, args=(queue,))
    writer.start()
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
        reader.join()
        writer.join()

    except KeyboardInterrupt:
        reader.terminate()
        writer.terminate()
