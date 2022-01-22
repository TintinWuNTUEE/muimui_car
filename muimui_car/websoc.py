import websocket
import _thread as thread
import json
# websocket-client==1.2.3

ws_start = 'ws://'
endpoints = 'localhost:8000/'
path_name = 'ws/chat/'

def on_message(ws, message):
    print("on message",message)
def on_error(ws, error):
    print("error", error)
def on_close(ws, close_code, _):
    print("##close##")
def on_open(ws):
# print("open connection")
    def run(*arg):
        while True:
            msg = input("your msg:\n")
            obj = json.dumps({
            "message": msg
        })
        # print(obj)
        ws.send(obj)
    thread.start_new_thread(run, ())

if __name__ == "__main__":
    server_path = ws_start+endpoints+path_name
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(server_path,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    try:
        ws.run_forever()
    except KeyboardInterrupt as e:
        pass
    ws.close()
    ws = None

