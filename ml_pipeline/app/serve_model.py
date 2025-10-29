# ======================================
# ⚡ FastAPI + 구매 예측 API (Render 배포용 v4.1 - Feature 7개 호환)
# ======================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import os
import sys
from datetime import datetime
import traceback

# ✅ 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ✅ model_utils 임포트
try:
    from app.model_utils import load_models_from_minio, predict_proba
    UTILS_LOADED = True
except ImportError as e:
    print(f"⚠️ model_utils 임포트 실패: {e}")
    UTILS_LOADED = False

# ✅ FastAPI 초기화
app = FastAPI(
    title="🛍️ E-Commerce Purchase Prediction API",
    version="4.1",
    description="실시간 고객 구매 확률 예측 API (Render 배포용)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 📌 환경 변수
# --------------------------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")
BUCKET = os.getenv("BUCKET", "model-store")
PREFIX = os.getenv("PREFIX", "session-purchase")
MODEL_DIR = os.getenv("MODEL_DIR", "models_cache")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# --------------------------------------------------
# 🌍 전역 변수
# --------------------------------------------------
models = None
meta = {}
startup_time = datetime.now()
request_count = 0


# --------------------------------------------------
# 🔧 서버 시작 시 모델 로드
# --------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 초기화"""
    global models, meta
    
    print("=" * 60)
    print("🚀 FastAPI 서버 시작 중...")
    print(f"📍 Environment: {ENVIRONMENT}")
    print(f"📍 MinIO Endpoint: {MINIO_ENDPOINT}")
    print(f"📍 Bucket: {BUCKET}")
    print(f"📍 Prefix: {PREFIX}")
    print("=" * 60)
    
    if not UTILS_LOADED:
        print("❌ model_utils 불러오기 실패 — 모델 로드 스킵")
        return

    try:
        result = load_models_from_minio(
            endpoint=MINIO_ENDPOINT,
            bucket=BUCKET,
            prefix=PREFIX,
            local_dir=MODEL_DIR
        )

        if result is None or len(result) != 2:
            raise ValueError("load_models_from_minio 결과가 잘못됨")

        models, meta = result

        version = meta.get('version', 'unknown')
        threshold = meta.get('threshold', 0.5)
        feature_count = len(meta.get('features', []))

        print("✅ 모델 로드 완료!")
        print(f"   - Version: {version}")
        print(f"   - Threshold: {threshold}")
        print(f"   - Feature Count: {feature_count}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        traceback.print_exc()
        models, meta = None, {}


# --------------------------------------------------
# 📥 입력 데이터 모델 정의 (7개 Feature 기준)
# --------------------------------------------------
class SessionFeatures(BaseModel):
    """고객 세션 입력 피처 (7개 버전)"""
    feature_1: float = Field(..., ge=0, description="총 방문 횟수")
    feature_2: float = Field(..., ge=0, description="마지막 활동 후 경과일")
    feature_3: float = Field(..., ge=0, description="활동 빈도")
    feature_4: float = Field(..., ge=0, description="장바구니 담은 상품 수")
    feature_5: float = Field(..., ge=0, description="상품 조회 수")
    feature_6: float = Field(..., ge=0, description="세션 총 활동 횟수")
    feature_7: float = Field(..., ge=0, description="평균 세션 시간 (분)")

    class Config:
        json_schema_extra = {
            "example": {
                "feature_1": 15.0,
                "feature_2": 2.0,
                "feature_3": 20.0,
                "feature_4": 5.0,
                "feature_5": 30.0,
                "feature_6": 50.0,
                "feature_7": 12.0
            }
        }


class PredictionResponse(BaseModel):
    """예측 결과 응답 모델"""
    probability: float
    prediction: int
    threshold: float
    timestamp: str
    model_version: str


# --------------------------------------------------
# 🎯 예측 엔드포인트
# --------------------------------------------------
@app.post("/predict", response_model=PredictionResponse)
async def predict(input_data: SessionFeatures):
    """고객 세션 데이터를 받아 구매 확률 예측"""
    global request_count
    request_count += 1

    if models is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다.")

    try:
        df = pd.DataFrame([input_data.model_dump()])
        prob, pred = predict_proba(models, meta, df)

        return PredictionResponse(
            probability=float(prob),
            prediction=int(pred),
            threshold=float(meta.get("threshold", 0.5)),
            timestamp=datetime.now().isoformat(),
            model_version=meta.get("version", "unknown")
        )
    except Exception as e:
        print(f"❌ 예측 중 오류 발생: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"예측 실패: {e}")


# --------------------------------------------------
# 🏥 헬스체크
# --------------------------------------------------
@app.get("/health")
async def health_check():
    uptime = (datetime.now() - startup_time).total_seconds()
    return {
        "status": "healthy" if models else "degraded",
        "models_loaded": models is not None,
        "model_version": meta.get("version", "unknown"),
        "threshold": meta.get("threshold", 0.5),
        "feature_count": len(meta.get("features", [])),
        "uptime_seconds": round(uptime, 2),
        "total_requests": request_count,
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    }


# --------------------------------------------------
# 🏠 루트
# --------------------------------------------------
@app.get("/")
async def root():
    uptime = (datetime.now() - startup_time).total_seconds()
    return {
        "message": "🛍️ E-Commerce Purchase Prediction API (7 features)",
        "version": "4.1",
        "status": "running",
        "models_loaded": models is not None,
        "feature_count": len(meta.get("features", [])),
        "uptime_seconds": round(uptime, 2),
        "environment": ENVIRONMENT
    }


# --------------------------------------------------
# 🧪 테스트 예측
# --------------------------------------------------
@app.get("/test")
async def test_prediction():
    """테스트용 샘플 예측"""
    if models is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다.")
    
    sample = SessionFeatures(
        feature_1=10.0,
        feature_2=1.0,
        feature_3=12.0,
        feature_4=3.0,
        feature_5=18.0,
        feature_6=30.0,
        feature_7=8.0
    )
    return await predict(sample)


# --------------------------------------------------
# 🚀 로컬 실행
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    print("=" * 60)
    print(f"🚀 FastAPI 서버를 포트 {PORT}에서 시작합니다...")
    print(f"📚 문서: http://localhost:{PORT}/docs")
    print("=" * 60)
    uvicorn.run("serve_model:app", host="0.0.0.0", port=PORT, reload=True)
