import os
import json
import joblib
from typing import Dict, Any
import boto3

# ===========================
# 📍 경로 설정 (Render & Local 겸용)
# ===========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CACHE_DIR = os.path.join(BASE_DIR, "models_cache")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)


# ===========================
# 📦 로컬 모델 로드 함수
# ===========================
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
        return models, meta   # ✅ 튜플 반환으로 변경
    except Exception as e:
        raise RuntimeError(f"❌ 로컬 모델 로드 실패: {e}")


# ===========================
# ☁️ MinIO에서 모델 로드
# ===========================
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

        # ✅ 로컬 캐시로부터 다시 로드
        return load_local_models()  # (models, meta) 튜플 반환
    except Exception as e:
        print(f"❌ MinIO 로드 중 오류 발생: {e}")
        print("⚠️ 로컬 캐시 모델로 대체합니다.")
        return load_local_models()

# ===========================
# 🧠 개별 모델 예측 유틸
# ===========================
def predict_proba(models: Dict[str, Any], meta: Dict[str, Any], df):
    """
    여러 모델의 예측 확률 평균을 계산하고, threshold 기준으로 최종 레이블 반환
    FastAPI의 /predict 엔드포인트에서 사용
    """
    preds = []
    try:
        # ✅ 메타 정보에 있는 feature만 남기기 (중복/파생 변수 제거)
        if "features" in meta and isinstance(meta["features"], list):
            feature_cols = [f for f in meta["features"] if f in df.columns]
            df = df[feature_cols]
            print(f"[DEBUG] 사용된 feature 컬럼 ({len(df.columns)}개): {list(df.columns)}")
        else:
            print("⚠️ meta['features']가 정의되어 있지 않아 전체 feature 사용")

        # ✅ 모델별 예측 수행
        if "lgb_model" in models and models["lgb_model"]:
            preds.append(models["lgb_model"].predict_proba(df)[:, 1])
        if "xgb_model" in models and models["xgb_model"]:
            preds.append(models["xgb_model"].predict_proba(df)[:, 1])
        if "cat_model" in models and models["cat_model"]:
            preds.append(models["cat_model"].predict_proba(df)[:, 1])

        if not preds:
            raise ValueError("❌ 사용할 수 있는 모델이 없습니다.")

        # ✅ 평균 확률 계산 + threshold 비교
        avg_prob = sum(preds) / len(preds)
        threshold = meta.get("threshold", 0.5)
        pred_label = int(avg_prob[0] >= threshold)

        return avg_prob[0], pred_label

    except Exception as e:
        raise RuntimeError(f"❌ predict_proba 실행 중 오류 발생: {e}")
# ===========================
# 🧩 평균 확률 + 최종 예측 반환 (FastAPI용)
# ===========================
def predict_proba(models: Dict[str, Any], meta: Dict[str, Any], df):
    """
    여러 모델의 예측 확률 평균을 계산하고, threshold 기준으로 최종 레이블 반환
    FastAPI의 /predict 엔드포인트에서 사용
    """
    preds = []

    try:
        if "lgb_model" in models and models["lgb_model"]:
            preds.append(models["lgb_model"].predict_proba(df)[:, 1])
        if "xgb_model" in models and models["xgb_model"]:
            preds.append(models["xgb_model"].predict_proba(df)[:, 1])
        if "cat_model" in models and models["cat_model"]:
            preds.append(models["cat_model"].predict_proba(df)[:, 1])

        if not preds:
            raise ValueError("❌ 사용할 수 있는 모델이 없습니다.")

        # 평균 확률 계산
        avg_prob = sum(preds) / len(preds)
        threshold = meta.get("threshold", 0.5)
        pred_label = int(avg_prob[0] >= threshold)

        return avg_prob[0], pred_label

    except Exception as e:
        raise RuntimeError(f"❌ predict_proba 실행 중 오류 발생: {e}")
