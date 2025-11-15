import cv2


def draw_label(frame, text, x, y, color=(0,255,0)):
   # Draw a filled background for readability
   (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
   pad = 6
   bx1, by1 = x - pad, y - pad - h
   bx2, by2 = x + w + pad, y + pad
   cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 0, 0), -1)
   cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)




def draw_confidence_bar(frame, x, y, width, height, confidence, bar_color=(0,255,0)):
   # Draw an outline bar then fill proportionally
   cv2.rectangle(frame, (x, y), (x+width, y+height), (50,50,50), 1)
   fill_w = int(max(0, min(1.0, confidence)) * width)
   if fill_w > 0:
       cv2.rectangle(frame, (x+1, y+1), (x+fill_w, y+height-1), bar_color, -1)


