import pytesseract
import cv2
import numpy as np

def extract_text(image):
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    text = pytesseract.image_to_string(cv_img)
    return text
