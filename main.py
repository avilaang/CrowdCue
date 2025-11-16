import tkinter as tk
from tkinter import font
import torch

from ocr.screen_capture import capture_screen
from ocr.ocr_engine import extract_text
from ocr.ai_engine import get_engagement_suggestions
from crowdcue_integration import initialize_detection, shutdown_detection

current_ai_suggestions = "Analyzing slide..."
metrics_provider = None
engagement_percent_label = None
audience_bar_canvases = {}
audience_percent_labels = {}


def continuous_analysis():
    global current_ai_suggestions

    try:
        image = capture_screen()
        text = extract_text(image)

        if text.strip():
            current_ai_suggestions = get_engagement_suggestions(text)
        else:
            current_ai_suggestions = "No readable text detected."
    except Exception:
        # keep previous suggestions on error
        pass

    # Schedule this function to run again in 10 seconds
    root.after(10000, continuous_analysis)

# --- Placeholders for dynamic data ---
def get_engagement_percentage():
    """Get live audience engagement score from detection engine."""
    if metrics_provider is None:
        return 0
    return int(metrics_provider.get_engagement_percentage())

def get_dominant_engagement_suggestion(dominant: str) -> str:
    """Map dominant engagement state to a suggestion."""
    suggestions = {
        'engaged': "Excellent! Keep the momentum going.",
        'neutral': "Good baseline. Consider adding an engaging element.",
        'bored': "Increase energy — ask a question or change pace.",
        'confused': "Clarify: restate key points or slow down.",
        'none': "Waiting for audience to appear...",
    }
    return suggestions.get(dominant, "Analyzing...")


def get_suggested_action():
    """Get suggestion from dominant engagement label."""
    if metrics_provider is None:
        return current_ai_suggestions

    # Get dominant engagement and map to suggestion
    dominant = metrics_provider.get_dominant_engagement()
    dominant_suggestion = get_dominant_engagement_suggestion(dominant)
    return dominant_suggestion

def get_audience_breakdown():
    if metrics_provider is None:
        return {
            "Engaged": 0,
            "Neutral": 0,
            "Un-engaged": 0,
            "Confused": 0,
        }

    data = metrics_provider.get_audience_breakdown()
    return {
        "Engaged": int(data.get('engaged', 0)),
        "Neutral": int(data.get('neutral', 0)),
        "Un-engaged": int(data.get('bored', 0)),
        "Confused": int(data.get('confused', 0)),
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
    global engagement_percent_label
    engagement_percent_label = tk.Label(f, text=f"{get_engagement_percentage()}%", bg="black", fg="white", font=percent_font)
    engagement_percent_label.pack(side="left", padx=(5, 5))
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
    
    global audience_bar_canvases, audience_percent_labels
    audience_bar_canvases = {}
    audience_percent_labels = {}

    for label, percent in data.items():
        f = tk.Frame(overlay_bottomleft, bg="black")
        f.pack(anchor="w", padx=20, pady=2)
        tk.Label(f, text=f"{label}:", font=label_font, bg="black", fg="white", width=12, anchor='w').pack(side="left")  # fixed width label
        canvas = tk.Canvas(f, width=bar_width, height=12, bg="black", highlightthickness=0)
        canvas.pack(side="left", padx=(6, 6))
        canvas.create_rectangle(0, 0, int(bar_width * percent / 100), 12, fill="#cfcfcf", width=0)
        audience_bar_canvases[label] = canvas
        percent_label = tk.Label(f, text=f"{percent}%", font=label_font, bg="black", fg="white")
        percent_label.pack(side="left")
        audience_percent_labels[label] = percent_label

    keep_on_top(overlay_bottomleft)
    keep_on_top(overlay_topright)
    update_suggestion_label()
    update_engagement_percentage()
    update_audience_bars()

def update_suggestion_label():
    suggestion_label.config(text=get_suggested_action())
    suggestion_label.after(1000, update_suggestion_label)

def update_engagement_percentage():
    """Update the engagement percentage label."""
    global engagement_percent_label
    try:
        if engagement_percent_label:
            engagement_percent_label.config(text=f"{get_engagement_percentage()}%")
            engagement_percent_label.after(1000, update_engagement_percentage)
    except (NameError, AttributeError):
        pass

def update_audience_bars():
    """Update the audience breakdown bars and percentages."""
    global audience_bar_canvases, audience_percent_labels
    try:
        if audience_bar_canvases and audience_percent_labels and len(audience_bar_canvases) > 0:
            data = get_audience_breakdown()
            bar_width = 150  # px for 100%
            
            for label, percent in data.items():
                if label in audience_bar_canvases and label in audience_percent_labels:
                    # Clear and redraw the bar
                    canvas = audience_bar_canvases[label]
                    canvas.delete("all")
                    fill_width = int(bar_width * percent / 100)
                    canvas.create_rectangle(0, 0, fill_width, 12, fill="#cfcfcf", width=0)
                    
                    # Update the percentage label
                    audience_percent_labels[label].config(text=f"{percent}%")
            
            # Schedule next update
            list(audience_bar_canvases.values())[0].after(1000, update_audience_bars)
    except (NameError, AttributeError, KeyError, IndexError):
        pass

def keep_on_top(window):
    window.attributes('-topmost', True)
    window.lift()
    window.after(500, lambda: keep_on_top(window))  # Repeat every 500 ms

def start():
    global metrics_provider
    # Initialize background detection engine when GUI starts
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        metrics_provider = initialize_detection(device=device, hf_token_selection=1, cam_index=0, debug=False)
    except Exception as e:
        print(f"Warning: could not start detection engine: {e}")

    continuous_analysis()
    show_overlays()

# --- Main Window ---

root = tk.Tk()
root.title("CrowdCue")
root.geometry("500x250")
tk.Label(root, text="CrowdCue", font=("Optima", 36, "bold")).pack(pady=(30, 10))
tk.Label(root, text="AI-Powered Insights That Elevate Every Presentation", font=("Optima", 14, "italic")).pack()
tk.Button(root, text="Launch CrowdCue",font=("Optima", 14),borderwidth=5,command=start).pack(pady=20)


def on_closing():
    try:
        shutdown_detection()
    except Exception:
        pass
    root.destroy()


# Ensure clean shutdown when the window is closed
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
