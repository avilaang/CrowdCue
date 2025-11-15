from ocr.screen_capture import capture_screen
from ocr.ocr_engine import extract_text
from ocr.ai_engine import get_engagement_suggestions
import time

def main():
    print("Starting continuous slide analysis...")
    region = None

    while True:
        image_with_box = capture_screen(region, draw_box=True)
        text = extract_text(image_with_box)
        print("\n===== EXTRACTED TEXT =====")
        print(text if text else "[No text detected]")

        if text.strip():
            print("\n===== AI SUGGESTIONS =====")
            suggestions = get_engagement_suggestions(text)
            print(suggestions)
        else:
            print("\n(No readable text detected.)")
            
        time.sleep(1)

if __name__ == "__main__":
    main()
