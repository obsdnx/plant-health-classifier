import numpy as np
from PIL import Image
from pathlib import Path
from io import BytesIO

MODEL_PATH = Path(__file__).parent / "pumpkin.tflite"
LABELS_PATH = Path(__file__).parent / "labels.txt"

_interpreter = None
_inp = None
_out = None
INPUT_SIZE = (224, 224)


def _load():
    global _interpreter, _inp, _out, INPUT_SIZE

    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        try:
            from tflite_runtime.interpreter import Interpreter
        except ImportError:
            raise RuntimeError(
                "No TFLite runtime installed. Run:  pip install ai-edge-litert"
            )

    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Model file not found: {MODEL_PATH}\n"
            "Copy pumpkin.tflite into the computer/ folder."
        )

    labels_text = LABELS_PATH.read_text().strip().splitlines()

    interp = Interpreter(model_path=str(MODEL_PATH))
    interp.allocate_tensors()
    inp = interp.get_input_details()[0]
    out = interp.get_output_details()[0]
    shape = inp["shape"]
    INPUT_SIZE = (shape[1], shape[2])

    _interpreter = interp
    _inp = inp
    _out = out
    return labels_text


_labels = None


def classify(image_bytes: bytes) -> dict:
    global _interpreter, _labels

    if _interpreter is None:
        _labels = _load()

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
    }
