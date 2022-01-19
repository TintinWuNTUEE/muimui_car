import json
import time
import logging
import threading
import argparse
import asyncio
import multiprocessing as mp


from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

from motor import MotorDriver

import socket
import websocket
import threading
import _thread as thread
import time

VERBOSE = False
RUNNING = True
HEALTHCHECKS = 100

HEALTH_INTERVAL = 1
INSTRUCTION_INTERVAL = 0.1

SERVER_IP="0.0.0.0"
PORT="9999"

JETSON_SDP =""
BROWSER_SDP=""
DURATION=0
control = ""

ws_start = 'ws://'
endpoints = 'localhost:8000/'
path_name = 'ws/chat/'

def Move(Motor):
    global control
    print("[Control]:{control}")
    if control =="w":
        MotorForward(Motor)
    elif control =="s":
        MotorBackward(Motor)
    elif control =="d":
        MotorLeftward(Motor)
    elif control =="a":
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

def on_message(ws, message):
    global DURATION,BROWSER_SDP
    message,time = message.split("\@/")
    time = int(time)
    BROWSER_SDP = message
    DURATION = time
def on_error(ws, error):
    print("error", error)
def on_close(ws, close_code, _):
    print("##close##")
def on_open(ws):
    # print("open connection")
    def run(*arg):
        while True:
            msg = JETSON_SDP
            obj = json.dumps({
                "sdp": msg
            })
            # print(obj)
            ws.send(obj)
    thread.start_new_thread(run, ())

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
        # move motor and stop
        Move(control,Motor)
        timer = threading.Timer(INSTRUCTION_INTERVAL, onChange, args=(message,Motor,))
        timer.start()
        # time.sleep(INSTRUCTION_INTERVAL)
        # ResetMotor(Motor)
    await pc.setLocalDescription(await pc.createOffer())
    #jetson sdp
    global JETSON_SDP 
    JETSON_SDP = object_to_string(pc.localDescription)
    print(object_to_string(pc.localDescription))
    print("===================================")
    await step1_wait_for_browser_sdp(pc)
    await step2_running_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    server_path = ws_start+endpoints+path_name
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(server_path,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    thd = mp.Process(target=ws.run_forever,args=None,name="socket")
    thd.start()

    VERBOSE = args['verbose']
    Motor = MotorDriver()
    # Run main event loop
    pc = RTCPeerConnection()
    coro = main(pc,Motor)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
        ws.close()
        ws = None

    except KeyboardInterrupt:
        pass
