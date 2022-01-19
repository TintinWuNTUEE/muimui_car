import json
import time
import logging
import threading
import argparse
import asyncio
import multiprocessing as mp


from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import object_to_string, object_from_string

from motor import MotorDriver,MotorForward,MotorBackward,MotorLeftward,MotorRightward,ResetMotor

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
endpoints = '192.168.122.97:8000/'
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

def onChange(message,Motor):
    global control
    if control!=message:
        control = message
        ResetMotor(Motor)
    return



def TimeOut(ws,loop,coro):
    global DURATION
    DURATION = 0 
    print("time out!!")
    ws.send("time out!!")
    loop.close()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(coro)

def on_message(ws, message):
    global DURATION,BROWSER_SDP
    tmp = message.split("\@/")
    message,time = tmp[0],tmp[1]
    time = int(time)
    BROWSER_SDP = message
    DURATION = time
def on_error(ws, error):
    print("error", error)
def on_close(ws, close_code, _):
    print("##close##")

async def step1_wait_for_browser_sdp(pc):
    string = BROWSER_SDP
    while string == "":
        asyncio.sleep(0.5)
    sdp = object_from_string(string)
    await pc.setRemoteDescription(sdp)

async def step2_running_loop():
    global RUNNING, HEALTHCHECKS
    while RUNNING and HEALTHCHECKS > 0:
        HEALTHCHECKS -= 1
        await asyncio.sleep(1)

async def main(pc,Motor,ws):

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
    obj = obj = json.dumps({
                "message": JETSON_SDP
            })
    ws.send(obj)
    print(object_to_string(pc.localDescription))
    print("===================================")
    await step1_wait_for_browser_sdp(pc)
    await step2_running_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true')
    args = vars(parser.parse_args())
    server_path = ws_start+endpoints+path_name
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(server_path,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    thd = threading.Thread(target=ws.run_forever)
    thd.start()

    VERBOSE = args['verbose']
    Motor = MotorDriver()
    # Run main event loop
    pc = RTCPeerConnection()
    coro = main(pc,Motor,ws)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
        timer = threading.Timer(DURATION,TimeOut,args=(ws,loop,coro))

    except KeyboardInterrupt:
        pass
