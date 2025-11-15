import tkinter as tk
from tkinter import font
from ocr.screen_capture import capture_screen
from ocr.ocr_engine import extract_text
from ocr.ai_engine import get_engagement_suggestions

current_ai_suggestions = "Analyzing slide..."

def continuous_analysis():
    global current_ai_suggestions

    image = capture_screen()
    text = extract_text(image)

    if text.strip():
        current_ai_suggestions = get_engagement_suggestions(text)
    else:
        current_ai_suggestions = "No readable text detected."

    # Schedule this function to run again in 1 second
    root.after(10000, continuous_analysis)

# --- Placeholders for dynamic data ---
def get_engagement_percentage():
    # Replace with import or function call to your external Python script
    return 45  # Example value

def get_suggested_action():
    # Replace with import or function call to your external Python script
    return current_ai_suggestions

def get_audience_breakdown():
    # Replace with import/function call to your external Python script
    return {
        "Engaged": 45,
        "Neutral": 15,
        "Un-engaged": 30,
        "Confused": 10
    }


def show_overlays():
    # --- Top Right Overlay ---
    overlay_width = 320
    overlay_height = 160
    screen_width = root.winfo_screenwidth()
    x1 = screen_width - overlay_width
    y1 = 0

    overlay_topright = tk.Toplevel()
    overlay_topright.geometry(f"+{x1}+{y1}")
    overlay_topright.overrideredirect(True)
    overlay_topright.attributes('-topmost', True)
    overlay_topright.configure(bg="black")
    overlay_topright.attributes('-alpha', 0.85)  # Adjust for desired transparency

    title_font = font.Font(family="Avenir", size=12, weight="bold")
    percent_font = font.Font(family="Avenir", size=24, weight="bold")
    label_font = font.Font(family="Avenir", size=11)
    suggestion_font = font.Font(family="Avenir", size=10)

    tk.Label(overlay_topright, text="Live Insights", bg="black", fg="white", font=title_font).pack(anchor="w", padx=15, pady=(8, 0))
    tk.Frame(overlay_topright, bg="white", height=1).pack(fill="x", padx=10, pady=(2, 10))

    f = tk.Frame(overlay_topright, bg="black")
    f.pack(anchor="w", padx=18)
    tk.Label(f, text="Your audience is", bg="black", fg="white", font=label_font).pack(side="left")
    tk.Label(f, text=f"{get_engagement_percentage()}%", bg="black", fg="white", font=percent_font).pack(side="left", padx=(5, 5))
    tk.Label(f, text="engaged", bg="black", fg="white", font=label_font).pack(side="left")

    tk.Label(overlay_topright, text="Suggested Actions", bg="black", fg="white", font=title_font).pack(anchor="w", padx=15, pady=(18, 0))
    tk.Frame(overlay_topright, bg="white", height=1).pack(fill="x", padx=10, pady=(2, 7))
    global suggestion_label 
    suggestion_label = tk.Label(
        overlay_topright,
        text=current_ai_suggestions,
        bg="black",
        fg="white",
        font=suggestion_font,
        wraplength=280,
        justify="left"
    )
    suggestion_label.pack(anchor="w", padx=18)

    # --- Bottom Left Overlay ---
    overlay2_width = 320
    overlay2_height = 170
    screen_height = root.winfo_screenheight()
    x2 = 0
    y2 = screen_height - overlay2_height

    overlay_bottomleft = tk.Toplevel()
    overlay_bottomleft.geometry(f"{overlay2_width}x{overlay2_height}+{x2}+{y2}")
    overlay_bottomleft.overrideredirect(True)
    overlay_bottomleft.attributes('-topmost', True)
    overlay_bottomleft.configure(bg="black")
    overlay_bottomleft.attributes('-alpha', 0.85)

    tk.Label(overlay_bottomleft, text="Your Audience:", bg="black", fg="white", font=title_font).pack(anchor="w", padx=15, pady=(12, 2))
    tk.Frame(overlay_bottomleft, bg="white", height=1).pack(fill="x", padx=10, pady=(2, 14))

    data = get_audience_breakdown()
    bar_width = 150  # px for 100%

    for label, percent in data.items():
        f = tk.Frame(overlay_bottomleft, bg="black")
        f.pack(anchor="w", padx=20, pady=2)
        tk.Label(f, text=f"{label}:", font=label_font, bg="black", fg="white", width=12, anchor='w').pack(side="left")  # fixed width label
        canvas = tk.Canvas(f, width=bar_width, height=12, bg="black", highlightthickness=0)
        canvas.pack(side="left", padx=(6, 6))
        canvas.create_rectangle(0, 0, int(bar_width * percent / 100), 12, fill="#cfcfcf", width=0)
        tk.Label(f, text=f"{percent}%", font=label_font, bg="black", fg="white").pack(side="left")

    keep_on_top(overlay_bottomleft)
    keep_on_top(overlay_topright)
    update_suggestion_label()

def update_suggestion_label():
    suggestion_label.config(text=current_ai_suggestions)
    suggestion_label.after(1000, update_suggestion_label)

def keep_on_top(window):
    window.attributes('-topmost', True)
    window.lift()
    window.after(500, lambda: keep_on_top(window))  # Repeat every 500 ms

def start():
    continuous_analysis()
    show_overlays()

# --- Main Window ---

root = tk.Tk()
root.title("CrowdCue")
root.geometry("500x250")
tk.Label(root, text="CrowdCue", font=("Optima", 36, "bold")).pack(pady=(30, 10))
tk.Label(root, text="AI-Powered Insights That Elevate Every Presentation", font=("Optima", 14, "italic")).pack()
tk.Button(root, text="Launch CrowdCue",font=("Optima", 14),borderwidth=5,command=start).pack(pady=20)
root.mainloop() 
