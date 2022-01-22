
import cv2
if __name__ == "__main__":
    cap = cv2.VideoCapture()
    cv2.namedWindow("camCapture", cv2.WINDOW_AUTOSIZE)
    cap.open('rtmp://192.168.50.185/rtmp/live')

    while cap.isOpened():
        success, img = cap.read()
        if success:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            cv2.imshow("camCapture", img)      
    cap.release()
