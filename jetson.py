import json
import time
import logging
import threading
import argparse
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

from motor import Motor, MotorDriver

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

def Move(message,Motor):
    if message =="w":
        MotorForward(Motor)
    elif message =="s":
        MotorBackward(Motor)

def MotorForward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'backward', 100)
    time.sleep(0.01)
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return

def MotorLeftward(Motor):
    return

def MotorRightward(Motor):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    VERBOSE = args['verbose']
    Motor = MotorDriver()
    # Run main event loop
    pc = RTCPeerConnection()
    coro = main(pc,Motor)
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass