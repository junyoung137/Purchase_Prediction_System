import os
import json
import joblib
import tempfile
from io import BytesIO
from typing import Dict, Any
import boto3

# ===========================
# 📍 경로 설정 (Render & Local 겸용)
# ===========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CACHE_DIR = os.path.join(BASE_DIR, "models_cache")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)


# ===========================
# 📦 모델 로드 함수
# ===========================
def load_local_models() -> Dict[str, Any]:
    """로컬 캐시에서 모델 로드"""
    print("💡 Loading models from local cache...")

    models = {}
    try:
        lgb_path = os.path.join(MODEL_CACHE_DIR, "lgb_model.joblib")
        xgb_path = os.path.join(MODEL_CACHE_DIR, "xgb_model.joblib")
        cat_path = os.path.join(MODEL_CACHE_DIR, "cat_model.joblib")
        meta_path = os.path.join(MODEL_CACHE_DIR, "model_meta.json")

        models["lgb_model"] = joblib.load(lgb_path)
        models["xgb_model"] = joblib.load(xgb_path)
        models["cat_model"] = joblib.load(cat_path) if os.path.exists(cat_path) else None

        with open(meta_path, "r", encoding="utf-8") as f:
            models["meta"] = json.load(f)

        print("✅ 로컬 모델 로드 완료")
    except Exception as e:
        raise RuntimeError(f"❌ 로컬 모델 로드 실패: {e}")

    return models


# ===========================
# ☁️ MinIO에서 모델 로드
# ===========================
def load_models_from_minio(endpoint: str, bucket: str, prefix: str, local_dir: str = MODEL_CACHE_DIR):
    """MinIO에서 모델 다운로드, 실패 시 로컬 캐시 사용"""
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

        model_files = [
            "lgb_model.joblib",
            "xgb_model.joblib",
            "cat_model.joblib",
            "model_meta.json",
        ]

        for fname in model_files:
            s3_key = f"{prefix}/{fname}"
            local_path = os.path.join(local_dir, fname)
            try:
                s3_client.download_file(bucket, s3_key, local_path)
                print(f"✅ {fname} 다운로드 성공")
            except Exception as e:
                print(f"⚠️ {fname} 다운로드 실패 ({e}) → 로컬 캐시 사용 예정")

        # ✅ 다운로드 성공/실패 상관없이 캐시 로드 시도
        return load_local_models()

    except Exception as e:
        print(f"❌ MinIO 로드 중 오류 발생: {e}")
        print("⚠️ 로컬 캐시 모델로 대체합니다.")
        return load_local_models()


# ===========================
# 🧠 예측 유틸 (선택 사항)
# ===========================
def predict(models: Dict[str, Any], features: Any) -> Dict[str, float]:
    """3개 모델의 평균 예측"""
    preds = {}
    try:
        if "lgb_model" in models and models["lgb_model"]:
            preds["lgb"] = models["lgb_model"].predict_proba(features)[:, 1]
        if "xgb_model" in models and models["xgb_model"]:
            preds["xgb"] = models["xgb_model"].predict_proba(features)[:, 1]
        if "cat_model" in models and models["cat_model"]:
            preds["cat"] = models["cat_model"].predict_proba(features)[:, 1]
    except Exception as e:
        raise RuntimeError(f"❌ 예측 중 오류 발생: {e}")
    return preds
