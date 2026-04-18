from fastapi import FastAPI
import joblib

app = FastAPI()

model = joblib.load("multi_model.pkl")

@app.post("/predict")
def predict(hmr: float, avg: float):

    preds = model.predict([[hmr, avg]])[0]

    return {
        "oil": int(preds[0]),
        "afc": int(preds[1]),
        "afe": int(preds[2]),
        "mof": int(preds[3])
    }
