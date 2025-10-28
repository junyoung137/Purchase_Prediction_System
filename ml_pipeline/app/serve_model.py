# ======================================
# ⚡ FastAPI + Feast 통합 예측 API (v3.0)
# ======================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os
import sys
from feast import FeatureStore

# ✅ 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ✅ model_utils 임포트
from app.model_utils import load_models_from_minio, predict_proba

# ✅ FastAPI 초기화
app = FastAPI(
    title="E-Commerce Conversion Prediction API",
    version="3.0",
    description="🧠 Feast에서 직접 feature를 조회하여 실시간 구매 전환 확률을 예측합니다."
)

# --------------------------------------------------
# 1️⃣ Feast Store 초기화
# --------------------------------------------------
FEAST_REPO_PATH = os.getenv("FEAST_REPO_PATH", "/opt/airflow/feature_repo")
store = FeatureStore(repo_path=FEAST_REPO_PATH)

# --------------------------------------------------
# 2️⃣ MinIO 연결 설정
# --------------------------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9900")
BUCKET = os.getenv("BUCKET", "model-store")
PREFIX = os.getenv("PREFIX", "session-purchase")
MODEL_DIR = "models_cache"

# --------------------------------------------------
# 3️⃣ 전역 변수
# --------------------------------------------------
models = None
meta = {}

# --------------------------------------------------
# 4️⃣ 서버 시작 시 모델 로드
# --------------------------------------------------
@app.on_event("startup")
def startup_event():
    global models, meta
    try:
        result = load_models_from_minio(
            endpoint=MINIO_ENDPOINT,
            bucket=BUCKET,
            prefix=PREFIX,
            local_dir=MODEL_DIR
        )
        if result is None or len(result) != 2:
            raise ValueError("load_models_from_minio returned invalid data")

        models, meta = result

        print(f"✅ 모델 로드 완료: version={meta.get('version', 'unknown')} | threshold={meta.get('threshold', 0.5)}")

    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        models, meta = None, {}

# --------------------------------------------------
# 5️⃣ 입력 데이터 정의
# --------------------------------------------------
class UserInput(BaseModel):
    user_id: str

# --------------------------------------------------
# 6️⃣ 예측 엔드포인트 (Feast 사용)
# --------------------------------------------------
@app.post("/predict")
def predict(input_data: UserInput):
    """Feast에서 Feature를 조회해 구매 확률 예측"""
    if models is None:
        raise HTTPException(status_code=500, detail="모델이 로드되지 않았습니다.")

    try:
        # ✅ Feast 온라인 스토어에서 Feature 조회
        feature_response = store.get_online_features(
            features=[
                "session_features:cart_to_view_ratio",
                "session_features:session_activity_index",
                "session_features:recent_intensity",
                "session_features:event_diversity",
            ],
            entity_rows=[{"user_id": input_data.user_id}],
        ).to_dict()

        # ✅ DataFrame 변환
        df = pd.DataFrame([feature_response])

        # ✅ 예측 수행
        prob, pred = predict_proba(models, meta, df)

        print(f"[PREDICT] user_id={input_data.user_id} | prob={prob:.4f} | pred={pred}")

        return {
            "user_id": input_data.user_id,
            "probability": float(prob),
            "prediction": int(pred),
            "model_version": meta.get("version", "v1")
        }

    except Exception as e:
        print(f"❌ 예측 중 오류: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")

# --------------------------------------------------
# 7️⃣ 헬스체크
# --------------------------------------------------
@app.get("/health")
def health():
    feature_count = len(meta.get("features") or [])
    return {
        "status": "ok" if models else "not_loaded",
        "model_version": meta.get("version", "unknown"),
        "feature_count": feature_count
    }

# --------------------------------------------------
# 8️⃣ 기본 엔드포인트
# --------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "🚀 Feast-Integrated E-Commerce Prediction API is running!",
        "model_version": meta.get("version", "unknown"),
        "models_loaded": models is not None
    }