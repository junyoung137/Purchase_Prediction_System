# ======================================
# 🧩 모델 로드 / 예측 헬퍼 (model_utils.py)
# ======================================
import os
import joblib
import json
import pandas as pd
import s3fs


# --------------------------------------
# 1️⃣ 모델 로드 함수
# --------------------------------------
def load_models_from_minio(endpoint, bucket, prefix, local_dir="models_cache"):
    """
    MinIO에서 모델 파일을 다운로드 후 로드.
    MinIO 연결 실패 시 로컬 캐시에서 불러옵니다.
    반환 구조:
        ( (lgb_model, xgb_model, cat_model), meta )
    """
    os.makedirs(local_dir, exist_ok=True)

    files = [
        "lgb_model.joblib",
        "xgb_model.joblib",
        "cat_model.joblib",
        "model_meta.json",
    ]

    # --- 1. MinIO 연결 및 다운로드 시도 ---
    print(f"🔄 MinIO({endpoint})에서 모델 다운로드 시도...")
    fs = s3fs.S3FileSystem(
        key="minioadmin",
        secret="minioadmin",
        client_kwargs={"endpoint_url": endpoint},
    )

    for fname in files:
        remote = f"s3://{bucket}/{prefix}/{fname}"
        local = os.path.join(local_dir, fname)
        try:
            with fs.open(remote, "rb") as src, open(local, "wb") as dst:
                dst.write(src.read())
            print(f"☁️  Downloaded: {remote} → {local}")
        except Exception as e:
            print(f"⚠️  {fname} 다운로드 실패 ({e}) → 로컬 캐시 사용 예정")

    # --- 2. 로컬 캐시에서 모델 로드 ---
    try:
        lgb_model = joblib.load(os.path.join(local_dir, "lgb_model.joblib"))
        xgb_model = joblib.load(os.path.join(local_dir, "xgb_model.joblib"))
        cat_model = joblib.load(os.path.join(local_dir, "cat_model.joblib"))

        with open(os.path.join(local_dir, "model_meta.json"), "r") as f:
            meta = json.load(f)

        # ✅ 기본값 보완 (features가 None인 경우 처리)
        meta.setdefault("threshold", 0.5)
        meta.setdefault("weights", {"lgb": 0.4, "xgb": 0.3, "cat": 0.3})
        meta.setdefault("version", "unknown")
        
        # ✅ features가 None이면 빈 리스트로 변경
        if meta.get("features") is None:
            print("⚠️  model_meta.json의 features가 None입니다. 빈 리스트로 설정합니다.")
            meta["features"] = []
        elif not isinstance(meta.get("features"), list):
            print(f"⚠️  features 타입 오류: {type(meta.get('features'))}. 빈 리스트로 설정합니다.")
            meta["features"] = []

        feature_count = len(meta.get("features", []))
        print(f"✅ 모델 및 메타 로드 완료 (version={meta.get('version')}, features={feature_count})")

        # ✅ 일관된 구조로 반환
        return (lgb_model, xgb_model, cat_model), meta

    except Exception as e:
        raise RuntimeError(f"❌ 모델 로드 실패: {e}")


# --------------------------------------
# 2️⃣ 예측 함수
# --------------------------------------
def predict_proba(models, meta, input_df: pd.DataFrame):
    """
    다중 모델 앙상블 확률 예측 수행
    - models: (lgb_model, xgb_model, cat_model)
    - meta: model_meta.json 로드 결과
    - input_df: 입력 데이터 (DataFrame)
    """
    lgb_model, xgb_model, cat_model = models
    weights = meta.get("weights", {"lgb": 0.4, "xgb": 0.3, "cat": 0.3})

    # --- 예측 확률 계산 ---
    probs = (
        weights["lgb"] * lgb_model.predict_proba(input_df)[:, 1]
        + weights["xgb"] * xgb_model.predict_proba(input_df)[:, 1]
        + weights["cat"] * cat_model.predict_proba(input_df)[:, 1]
    )

    preds = (probs >= meta.get("threshold", 0.5)).astype(int)

    # 단일 입력일 경우 스칼라 반환
    if len(probs) == 1:
        return float(probs[0]), int(preds[0])
    else:
        return probs.tolist(), preds.tolist()