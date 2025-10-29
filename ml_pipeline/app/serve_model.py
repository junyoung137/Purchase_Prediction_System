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
        return models, meta
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

        # ✅ 로컬 캐시에서 다시 로드
        return load_local_models()

    except Exception as e:
        print(f"❌ MinIO 로드 중 오류 발생: {e}")
        print("⚠️ 로컬 캐시 모델로 대체합니다.")
        return load_local_models()


# ===========================
# 🧩 입력 피처 이름 자동 매핑
# ===========================
def align_feature_names(df, meta):
    """
    입력 DataFrame의 컬럼명을 모델 학습 시 사용된 feature 이름으로 자동 변경.
    meta.json 내 "features" 키를 기준으로 매핑 수행.
    """
    expected_features = meta.get("features")

    if expected_features and len(expected_features) == df.shape[1]:
        old_cols = list(df.columns)
        df.columns = expected_features
        print(f"✅ 입력 피처명을 모델 학습 피처명으로 매핑 완료:\n   {old_cols} → {expected_features}")
    else:
        print("⚠️ meta['features'] 정보가 없거나 feature 수가 일치하지 않아 rename 생략됨")

    return df


# ===========================
# 🧠 개별 모델 예측 유틸
# ===========================
def predict(models: Dict[str, Any], features: Any) -> Dict[str, float]:
    """3개 모델의 개별 확률 예측"""
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
        # ✅ 컬럼명 자동 정렬
        df = align_feature_names(df, meta)

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
