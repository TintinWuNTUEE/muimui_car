import cv2
import asyncio

async def myfun():
    """ test my keyboard """
    cv2.namedWindow("CONTROLLER", cv2.WINDOW_GUI_EXPANDED)
    img = cv2.imread('controller/controller.jpg')
    while True:
        cv2.imshow("CONTROLLER", img)
        key = cv2.waitKey(1) & 0xFF
        # print(key)
        if key == 27:
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
            print(f"{chr(key)}")
            # img = cv2.imread(f'controller/controller_{chr(key)}.jpg')
            # channel.send(f"{chr(key)}")
        else:
            pass
            # img = cv2.imread(f'controller/controller.jpg')
        await asyncio.sleep(0.03)

if __name__ == "__main__":
    
    try:
        asyncio.run(myfun())
    except KeyboardInterrupt as e:
        pass