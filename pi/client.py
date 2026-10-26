import sys
import time
from pathlib import Path

import requests
from gpiozero import Button
from picamera2 import Picamera2

from config import BUTTON_PIN, PHOTO_PATH, REQUEST_TIMEOUT, SERVER_URL


def take_photo(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cam = Picamera2()
    cam.configure(cam.create_still_configuration())
    cam.start()
    time.sleep(1)          # let the sensor settle
    cam.capture_file(path)
    cam.stop()
    cam.close()


def send_photo(path: str) -> dict:
    with open(path, "rb") as f:
        response = requests.post(
            SERVER_URL,
            files={"image": ("leaf.jpg", f, "image/jpeg")},
            timeout=REQUEST_TIMEOUT,
        )
    response.raise_for_status()
    return response.json()


def show_verdict(result: dict) -> None:
    status = result.get("status", "error")
    label = result.get("label", "unknown")
    confidence = result.get("confidence", 0)
    explanation = result.get("explanation", "")

    print("\n" + "=" * 50)
    if status == "error":
        print(f"ERROR: {result.get('detail', 'Unknown error')}")
    elif status == "unsure":
        print(f"UNSURE ({confidence*100:.0f}%): {explanation}")
    else:
        print(f"RESULT: {label}  ({confidence*100:.0f}% confident)")
        print(f"\n{explanation}")
    print("=" * 50 + "\n")


def run_once() -> None:
    print("Taking photo...")
    try:
        take_photo(PHOTO_PATH)
    except Exception as e:
        print(f"Camera error: {e}")
        return

    print("Sending to server...")
    try:
        result = send_photo(PHOTO_PATH)
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot reach the server. Is the computer on the same Wi-Fi?")
        return
    except requests.exceptions.Timeout:
        print(f"ERROR: Server did not reply within {REQUEST_TIMEOUT} seconds.")
        return
    except Exception as e:
        print(f"ERROR: {e}")
        return

    show_verdict(result)


def main() -> None:
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.2)
    print(f"Ready. Press button on GPIO {BUTTON_PIN} to classify a leaf.")
    print("Ctrl-C to quit.\n")

    try:
        while True:
            button.wait_for_press()
            run_once()
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
