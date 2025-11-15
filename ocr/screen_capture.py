import mss
from PIL import Image

def capture_screen(region=None, draw_box=False):
    with mss.mss() as sct:
        monitor = sct.monitors[1] if not region else region
        sct_img = sct.grab(monitor)
        img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb)

        if draw_box and region:
            import cv2, numpy as np
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            x1, y1, x2, y2 = region['left'], region['top'], region['left']+region['width'], region['top']+region['height']
            cv2.rectangle(cv_img, (x1, y1), (x2, y2), (0,255,0), 3)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_img)
        return img
