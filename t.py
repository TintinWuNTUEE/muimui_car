
import cv2
cap = cv2.VideoCapture()
cv2.namedWindow("camCapture", cv2.WINDOW_AUTOSIZE)
cap.open('rtmp://192.168.50.185/rtmp/live')
# fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', '2')
# w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# size = (w,h)
# fps = cap.get(cv2.CAP_PROP_FPS)
# out = cv2.VideoWriter('vi.avi', fourcc, fps, size)
while cap.isOpened():
    success, img = cap.read()
    if success:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cv2.imshow("camCapture", img)      
cap.release()
