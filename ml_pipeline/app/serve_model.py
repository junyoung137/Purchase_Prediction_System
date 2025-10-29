# ============================================================
# 🧠 serve_model.py — FastAPI 기반 구매 예측 API (7개 feature, 자동 매핑 포함)
# ============================================================
import os
import json
import joblib
from typing import Dict, Any
import boto3
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ============================================================
# 📍 경로 설정 (Render & Local 겸용)
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CACHE_DIR = os.path.join(BASE_DIR, "models_cache")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# ============================================================
# 📦 로컬 모델 로드 함수
# ============================================================
def load_local_models() -> tuple:
    """로컬 캐시에서 모델 로드 후 (models, meta) 튜플 반환"""
    print("💡 Loading models from local cache...")
    try:
        lgb_path = os.path.join(MODEL_CACHE_DIR, "lgb_model.joblib")
        xgb_path = os.path.join(MODEL_CACHE_DIR, "xgb_model.joblib")
        cat_path = os.path.join(MODEL_CACHE_DIR, "cat_model.joblib")
        meta_path = os.path.join(MODEL_CACHE_DIR, "model_meta.json")

        models = {
            "lgb_model": joblib.load(lgb_path),
            "xgb_model": joblib.load(xgb_path),
            "cat_model": joblib.load(cat_path) if os.path.exists(cat_path) else None
        }

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        print("✅ 로컬 모델 로드 완료")
        return models, meta
    except Exception as e:
        raise RuntimeError(f"❌ 로컬 모델 로드 실패: {e}")

# ============================================================
# ☁️ MinIO에서 모델 로드 함수
# ============================================================
def load_models_from_minio(endpoint: str, bucket: str, prefix: str, local_dir: str = MODEL_CACHE_DIR):
    """MinIO에서 모델 다운로드 후 (models, meta) 반환"""
    print("📥 MinIO에서 모델 다운로드 시도 중...")
    try:
        if not endpoint:
            print("⚠️ MinIO endpoint가 설정되지 않음 → 로컬 캐시 사용 예정")
            return load_local_models()

        s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            region_name="us-east-1",
        )

        model_files = ["lgb_model.joblib", "xgb_model.joblib", "cat_model.joblib", "model_meta.json"]
        for fname in model_files:
            s3_key = f"{prefix}/{fname}"
            local_path = os.path.join(local_dir, fname)
            try:
                s3_client.download_file(bucket, s3_key, local_path)
                print(f"✅ {fname} 다운로드 성공")
            except Exception as e:
                print(f"⚠️ {fname} 다운로드 실패 ({e}) → 로컬 캐시 사용 예정")

        return load_local_models()

    except Exception as e:
        print(f"❌ MinIO 로드 중 오류 발생: {e}")
        print("⚠️ 로컬 캐시 모델로 대체합니다.")
        return load_local_models()

# ============================================================
# 🧩 feature 이름 자동 매핑 함수
# ============================================================
def align_feature_names(df, meta):
    """
    입력 DataFrame 컬럼명을 meta['features']에 정의된 실제 학습 피처명으로 매핑
    """
    expected_features = meta.get("features")

    if expected_features and len(expected_features) == df.shape[1]:
        old_cols = list(df.columns)
        df.columns = expected_features
        print(f"✅ 입력 피처명 매핑 완료:\n   {old_cols} → {expected_features}")
    else:
        print("⚠️ meta['features'] 정보가 없거나 수 불일치로 rename 생략")

    return df

# ============================================================
# 🧠 예측 유틸리티
# ============================================================
def predict_proba(models: Dict[str, Any], meta: Dict[str, Any], df: pd.DataFrame):
    """
    여러 모델의 예측 확률 평균을 계산하고, threshold 기준으로 최종 레이블 반환
    """
    preds = []
    try:
        # ✅ 입력 컬럼명 자동 매핑
        df = align_feature_names(df, meta)

        print(f"[DEBUG] 모델 키: {list(models.keys())}")
        for name, m in models.items():
            print(f"[DEBUG] {name}: {'✅ 로드됨' if m else '❌ None'}")

        # 모델별 예측 확률 계산
        if models.get("lgb_model"):
            preds.append(models["lgb_model"].predict_proba(df)[:, 1])
        if models.get("xgb_model"):
            preds.append(models["xgb_model"].predict_proba(df)[:, 1])
        if models.get("cat_model"):
            preds.append(models["cat_model"].predict_proba(df)[:, 1])

        if not preds:
            raise ValueError("❌ 사용할 수 있는 모델이 없습니다.")

        avg_prob = sum(preds) / len(preds)
        threshold = meta.get("threshold", 0.5)
        pred_label = int(avg_prob[0] >= threshold)

        print(f"[DEBUG] 예측 성공: 확률={avg_prob[0]}, 라벨={pred_label}")
        return avg_prob[0], pred_label

    except Exception as e:
        print(f"❌ predict_proba 내부 오류: {e}")
        raise RuntimeError(f"❌ predict_proba 실행 중 오류 발생: {e}")

# ============================================================
# 🚀 FastAPI 서버 정의
# ============================================================
app = FastAPI(
    title="🛍️ Purchase Prediction API",
    description="LightGBM + XGBoost + CatBoost 앙상블 기반 구매 예측 API (7개 feature 자동 매핑)",
    version="1.0.0"
)

# ============================================================
# 🔹 요청 데이터 스키마 (feature_1 ~ feature_7)
# ============================================================
class SessionFeatures(BaseModel):
    feature_1: float
    feature_2: float
    feature_3: float
    feature_4: float
    feature_5: float
    feature_6: float
    feature_7: float

# ============================================================
# 🧩 모델 로드 (Render 환경 기준)
# ============================================================
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
BUCKET = os.getenv("BUCKET", "")
PREFIX = os.getenv("PREFIX", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

if ENVIRONMENT == "production":
    MODELS, META = load_models_from_minio(MINIO_ENDPOINT, BUCKET, PREFIX)
else:
    MODELS, META = load_local_models()

# ============================================================
# ✅ Health Check
# ============================================================
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Purchase Prediction API is running 🚀"}

# ============================================================
# 🧠 예측 엔드포인트
# ============================================================
@app.post("/predict")
def predict_purchase(features: SessionFeatures):
    """
    단일 고객 세션의 구매 확률 예측 (7개 feature)
    """
    try:
        df = pd.DataFrame([features.dict()])
        prob, pred = predict_proba(MODELS, META, df)
        return {
            "probability": prob,
            "prediction": int(pred),
            "threshold": META.get("threshold", 0.5)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# 🔍 로컬 실행용 진입점
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
