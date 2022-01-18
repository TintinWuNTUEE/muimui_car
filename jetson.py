import json
import time
import logging
import threading
import argparse
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

from motor import MotorDriver

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

HEALTH_INTERVAL = 1
INSTRUCTION_INTERVAL = 0.1

control = ""
def Move(message,Motor):
    if message =="w":
        MotorForward(Motor)
    elif message =="s":
        MotorBackward(Motor)
    elif message =="d":
        MotorLeftward(Motor)
    elif message =="a":
        MotorRightward(Motor)

def ResetMotor(Motor):
    Motor.MotorStop(0)
    Motor.MotorStop(1)
    return
def onChange(message,Motor):
    global control
    if control!=message:
        control = message
        ResetMotor(Motor)
    return

def MotorForward(Motor):
    Motor.MotorRun(0, 'backward', 100)
    Motor.MotorRun(1, 'forward', 100)
    # time.sleep(0.01)
    # Motor.MotorStop(0)
    # Motor.MotorStop(1)
    return

def MotorLeftward(Motor):
    Motor.MotorRun(0, 'backward', 100)
    Motor.MotorRun(1, 'backward', 100)
    # time.sleep(0.01)
    # Motor.MotorStop(0)
    # Motor.MotorStop(1)
    return

def MotorRightward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'forward', 100)
    # time.sleep(0.01)
    # Motor.MotorStop(0)
    # Motor.MotorStop(1)
    return

def MotorBackward(Motor):
    Motor.MotorRun(0, 'forward', 100)
    Motor.MotorRun(1, 'backward', 100)
    # time.sleep(0.01)
    # Motor.MotorStop(0)
    # Motor.MotorStop(1)
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
                await asyncio.sleep(HEALTH_INTERVAL)
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
        # move motor and stop
        Move(control,Motor)
        timer = threading.Timer(INSTRUCTION_INTERVAL, onChange, args=(message,Motor,))
        timer.start()
        # time.sleep(INSTRUCTION_INTERVAL)
        # ResetMotor(Motor)
    await pc.setLocalDescription(await pc.createOffer())
    print(object_to_string(pc.localDescription))
    print("===================================")
    await step1_wait_for_browser_sdp(pc)
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
