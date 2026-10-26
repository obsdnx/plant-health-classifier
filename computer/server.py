from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from classifier import classify
from explainer import explain

CONFIDENCE_THRESHOLD = 0.60

app = FastAPI(title="Plant Health Classifier")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify")
async def classify_leaf(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await image.read()

    try:
        result = classify(image_bytes)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)},
        )

    label = result["label"]
    confidence = result["confidence"]

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "label": label,
            "confidence": round(confidence, 4),
            "status": "unsure",
            "explanation": (
                f"Confidence too low ({confidence*100:.0f}%). "
                "Please retake the photo in better light, filling the frame with the leaf."
            ),
        }

    explanation = explain(label)

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "status": "ok",
        "explanation": explanation,
        "demo": result.get("demo", False),
    }


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
