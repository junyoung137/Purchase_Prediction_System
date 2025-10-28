# ===============================================================
# 🚀 예측 API (실무형 구조) + MinIO 로그 비동기 저장
# ===============================================================
import os, json, joblib, asyncio
import pandas as pd, numpy as np
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import s3fs

# --------------------------------------------------
# 1️⃣ 환경 변수 / 설정
# --------------------------------------------------
MINIO_ENDPOINT = "http://localhost:9900"
ACCESS_KEY = os.getenv("MINIO_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET", "minioadmin")

MODEL_PATH = "s3://model-store/session-purchase/xgb_model.joblib"
META_PATH = "s3://model-store/session-purchase/model_meta.json"
LOG_PATH = "s3://model-logs/session-purchase/inference-logs.csv"

# --------------------------------------------------
# 2️⃣ MinIO 및 모델 초기화
# --------------------------------------------------
fs = s3fs.S3FileSystem(key=ACCESS_KEY, secret=SECRET_KEY,
                       client_kwargs={"endpoint_url": MINIO_ENDPOINT})

with fs.open(MODEL_PATH, "rb") as f:
    model = joblib.load(f)
with fs.open(META_PATH, "r") as f:
    model_meta = json.load(f)

used_features = model_meta["features"]
threshold = model_meta.get("threshold", 0.45)
model_version = model_meta.get("version", "v1")

app = FastAPI(title="Session Purchase Predictor")

# --------------------------------------------------
# 3️⃣ 데이터 구조 정의
# --------------------------------------------------
class SessionInput(BaseModel):
    features: dict

# --------------------------------------------------
# 4️⃣ 파생 피처 함수
# --------------------------------------------------
def compute_derived_features(df):
    df["cart_to_view_ratio"] = df["n_cart"] / (df["n_view"] + 1)
    df["event_per_session"] = df["total_events"] / (df["total_sessions"] + 1)
    df["session_activity_index"] = df["frequency"] * np.log1p(df["total_sessions"])
    df["recency_ratio"] = df["recent_days"] / (df["frequency"] + 1)
    df["cart_depth"] = np.log1p(df["n_cart"]) * (df["frequency"] + 1)
    df["recent_intensity"] = np.exp(-df["recent_days"] / (df["frequency"] + 1))
    df["event_diversity"] = np.log1p(df["total_sessions"]) / (df["recent_days"] + 1)
    return df

# --------------------------------------------------
# 5️⃣ 로그 저장 (비동기)
# --------------------------------------------------
async def append_log_async(new_row: pd.DataFrame):
    try:
        with fs.open(LOG_PATH, "rb") as f:
            prev = pd.read_csv(f)
        combined = pd.concat([prev, new_row], ignore_index=True)
    except FileNotFoundError:
        combined = new_row
    combined.to_csv("inference-logs.csv", index=False)
    await asyncio.to_thread(fs.put, "inference-logs.csv", LOG_PATH)

# --------------------------------------------------
# 6️⃣ 예측 엔드포인트
# --------------------------------------------------
@app.post("/predict")
async def predict(input: SessionInput):
    try:
        df = pd.DataFrame([input.features])
        df = compute_derived_features(df)

        for f in used_features:
            if f not in df.columns:
                df[f] = 0
        X = df[used_features]

        proba = model.predict_proba(X)[:, 1][0]
        pred = int(proba >= threshold)

        log_entry = X.copy()
        log_entry["probability"] = proba
        log_entry["prediction"] = pred
        log_entry["model_version"] = model_version
        log_entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 비동기로 로그 저장
        asyncio.create_task(append_log_async(log_entry))

        return {"probability": float(proba),
                "prediction": pred,
                "model_version": model_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
