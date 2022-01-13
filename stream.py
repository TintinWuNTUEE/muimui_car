import cv2
import multiprocessing as mp
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
    queue = mp.Queue(maxsize=1)
    reader = mp.Process(target=gstreamer_camera, args=(queue,))
    reader.start()
    writer = mp.Process(target=gstreamer_rtmpstream, args=(queue,))
    writer.start()
    try:
        reader.join()
        writer.join()

    except KeyboardInterrupt:
        reader.terminate()
        writer.terminate()
