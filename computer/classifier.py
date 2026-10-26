import numpy as np
from PIL import Image
from pathlib import Path
from io import BytesIO
import random

MODEL_PATH = Path(__file__).parent / "pumpkin.tflite"
LABELS_PATH = Path(__file__).parent / "labels.txt"

_interpreter = None
_inp = None
_out = None
_labels = None
INPUT_SIZE = (224, 224)
DEMO_MODE = not MODEL_PATH.exists()


def _load_real():
    global _interpreter, _inp, _out, _labels, INPUT_SIZE

    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        try:
            from tflite_runtime.interpreter import Interpreter
        except ImportError:
            raise RuntimeError(
                "No TFLite runtime installed. Run:  pip install ai-edge-litert"
            )

    interp = Interpreter(model_path=str(MODEL_PATH))
    interp.allocate_tensors()
    inp = interp.get_input_details()[0]
    out = interp.get_output_details()[0]
    shape = inp["shape"]
    INPUT_SIZE = (shape[1], shape[2])

    _interpreter = interp
    _inp = inp
    _out = out
    _labels = LABELS_PATH.read_text().strip().splitlines()


def classify(image_bytes: bytes) -> dict:
    global _interpreter, _labels

    if DEMO_MODE:
        labels = LABELS_PATH.read_text().strip().splitlines()
        # Return a fake result so the pipeline can be tested without a model
        scores = [random.random() for _ in labels]
        total = sum(scores)
        scores = [s / total for s in scores]
        i = scores.index(max(scores))
        return {
            "label": labels[i],
            "confidence": round(scores[i], 4),
            "all_scores": {labels[j]: round(scores[j], 4) for j in range(len(labels))},
            "demo": True,
        }

    if _interpreter is None:
        _load_real()

    img = Image.open(BytesIO(image_bytes)).convert("RGB").resize(INPUT_SIZE)
    x = np.array(img, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)

    _interpreter.set_tensor(_inp["index"], x)
    _interpreter.invoke()
    scores = _interpreter.get_tensor(_out["index"])[0]

    i = int(np.argmax(scores))
    return {
        "label": _labels[i],
        "confidence": float(scores[i]),
        "all_scores": {_labels[j]: float(scores[j]) for j in range(len(_labels))},
        "demo": False,
    }
