import numpy as np
from PIL import Image
from pathlib import Path

try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        raise SystemExit(
            "ERROR: No TFLite runtime found.\n"
            "Run:  pip3 install ai-edge-litert\n"
            "  or: pip3 install tflite-runtime"
        )

MODEL_PATH = Path(__file__).parent / "pumpkin.tflite"
LABELS_PATH = Path(__file__).parent / "labels.txt"

if not MODEL_PATH.exists():
    raise SystemExit(
        f"ERROR: Model file not found: {MODEL_PATH}\n"
        "Copy pumpkin.tflite into the computer/ folder."
    )

labels = LABELS_PATH.read_text().strip().splitlines()

interpreter = Interpreter(model_path=str(MODEL_PATH))
interpreter.allocate_tensors()
_inp = interpreter.get_input_details()[0]
_out = interpreter.get_output_details()[0]

# Derive expected image size from model metadata
_shape = _inp["shape"]  # e.g. [1, 224, 224, 3]
INPUT_SIZE = (_shape[1], _shape[2])


def classify(image_bytes: bytes) -> dict:
    """Return label, confidence (0–1), and all raw scores."""
    from io import BytesIO
    img = Image.open(BytesIO(image_bytes)).convert("RGB").resize(INPUT_SIZE)
    x = np.array(img, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)

    interpreter.set_tensor(_inp["index"], x)
    interpreter.invoke()
    scores = interpreter.get_tensor(_out["index"])[0]

    i = int(np.argmax(scores))
    return {
        "label": labels[i],
        "confidence": float(scores[i]),
        "all_scores": {labels[j]: float(scores[j]) for j in range(len(labels))},
    }
