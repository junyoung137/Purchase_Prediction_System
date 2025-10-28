# ======================================
# ⚡ FastAPI + 구매 예측 API (Render 배포용 v4.0)
# ======================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import os
import sys
from datetime import datetime
from typing import Optional
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
    version="4.0",
    description="실시간 고객 구매 확률 예측 API (Render 배포용)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ✅ CORS 설정 (Streamlit Cloud에서 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 📌 환경 변수 설정
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
        print("❌ model_utils를 불러올 수 없어 모델 로드를 건너뜁니다.")
        return
    
    try:
        print("📥 MinIO에서 모델 다운로드 시도 중...")
        result = load_models_from_minio(
            endpoint=MINIO_ENDPOINT,
            bucket=BUCKET,
            prefix=PREFIX,
            local_dir=MODEL_DIR
        )
        
        if result is None or len(result) != 2:
            raise ValueError("load_models_from_minio가 잘못된 데이터를 반환했습니다.")

        models, meta = result

        # 메타 정보 출력
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
        print("⚠️ 서버는 시작되지만 예측 기능은 사용할 수 없습니다.")
        traceback.print_exc()
        models, meta = None, {}

# --------------------------------------------------
# 📥 입력 데이터 모델 정의
# --------------------------------------------------
class SessionFeatures(BaseModel):
    """고객 세션 특성 입력 모델"""
    feature_1: float = Field(..., ge=0, description="총 방문 횟수")
    feature_2: float = Field(..., ge=0, description="마지막 활동 후 경과일")
    feature_3: float = Field(..., ge=0, description="활동 빈도")
    feature_4: float = Field(..., ge=0, description="장바구니 담은 상품 수")
    feature_5: float = Field(..., ge=0, description="상품 조회 수")
    feature_6: float = Field(..., ge=0, description="세션 총 활동 횟수")
    feature_7: float = Field(..., ge=0, description="평균 세션 시간 (분)")
    feature_8: float = Field(..., ge=0, description="리뷰 작성 수")
    feature_9: float = Field(..., ge=0, description="할인 상품 조회")
    feature_10: float = Field(..., ge=0, description="결제 페이지 방문")

    class Config:
        json_schema_extra = {
            "example": {
                "feature_1": 15.0,
                "feature_2": 2.0,
                "feature_3": 20.0,
                "feature_4": 5.0,
                "feature_5": 30.0,
                "feature_6": 50.0,
                "feature_7": 12.0,
                "feature_8": 3.0,
                "feature_9": 10.0,
                "feature_10": 4.0
            }
        }

class PredictionResponse(BaseModel):
    """예측 결과 응답 모델"""
    probability: float = Field(..., description="구매 확률 (0~1)")
    prediction: int = Field(..., description="구매 예측 (0: 미구매, 1: 구매)")
    threshold: float = Field(..., description="분류 임계값")
    timestamp: str = Field(..., description="예측 시각")
    model_version: str = Field(..., description="모델 버전")

# --------------------------------------------------
# 🎯 예측 엔드포인트
# --------------------------------------------------
@app.post("/predict", response_model=PredictionResponse)
async def predict(input_data: SessionFeatures):
    """
    고객 세션 데이터를 받아 구매 확률을 예측합니다.
    
    - **feature_1~10**: 고객 활동 특성 값
    - **Returns**: 구매 확률, 예측 결과, 임계값 등
    """
    global request_count
    request_count += 1
    
    # 모델 로드 확인
    if models is None:
        raise HTTPException(
            status_code=503,
            detail="모델이 로드되지 않았습니다. 서버 로그를 확인하세요."
        )

    try:
        # 입력 데이터를 DataFrame으로 변환
        input_dict = input_data.model_dump()
        df = pd.DataFrame([input_dict])

        # 예측 수행
        prob, pred = predict_proba(models, meta, df)

        # 응답 생성
        response = PredictionResponse(
            probability=float(prob),
            prediction=int(pred),
            threshold=float(meta.get("threshold", 0.5)),
            timestamp=datetime.now().isoformat(),
            model_version=meta.get("version", "unknown")
        )

        print(f"[PREDICT #{request_count}] prob={prob:.4f}, pred={pred}")

        return response

    except Exception as e:
        print(f"❌ 예측 중 오류 발생: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"예측 실패: {str(e)}"
        )

# --------------------------------------------------
# 🏥 헬스체크 엔드포인트
# --------------------------------------------------
@app.get("/health")
async def health_check():
    """서버 및 모델 상태 확인"""
    uptime = (datetime.now() - startup_time).total_seconds()
    
    return {
        "status": "healthy" if models is not None else "degraded",
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
# 🏠 루트 엔드포인트
# --------------------------------------------------
@app.get("/")
async def root():
    """API 정보 및 상태"""
    uptime = (datetime.now() - startup_time).total_seconds()
    
    return {
        "message": "🛍️ E-Commerce Purchase Prediction API",
        "version": "4.0",
        "status": "running",
        "models_loaded": models is not None,
        "model_version": meta.get("version", "unknown"),
        "uptime_seconds": round(uptime, 2),
        "total_requests": request_count,
        "docs_url": "/docs",
        "health_url": "/health",
        "environment": ENVIRONMENT
    }

# --------------------------------------------------
# 📊 통계 엔드포인트 (선택사항)
# --------------------------------------------------
@app.get("/stats")
async def get_stats():
    """API 사용 통계"""
    uptime = (datetime.now() - startup_time).total_seconds()
    
    return {
        "total_requests": request_count,
        "uptime_seconds": round(uptime, 2),
        "uptime_hours": round(uptime / 3600, 2),
        "requests_per_minute": round(request_count / (uptime / 60), 2) if uptime > 0 else 0,
        "model_info": {
            "version": meta.get("version", "unknown"),
            "threshold": meta.get("threshold", 0.5),
            "features": meta.get("features", []),
            "weights": meta.get("weights", {})
        },
        "timestamp": datetime.now().isoformat()
    }

# --------------------------------------------------
# 🧪 테스트 엔드포인트
# --------------------------------------------------
@app.get("/test")
async def test_prediction():
    """테스트 예측 실행 (샘플 데이터 사용)"""
    if models is None:
        raise HTTPException(
            status_code=503,
            detail="모델이 로드되지 않았습니다."
        )
    
    # 샘플 데이터
    sample_data = SessionFeatures(
        feature_1=15.0,
        feature_2=2.0,
        feature_3=20.0,
        feature_4=5.0,
        feature_5=30.0,
        feature_6=50.0,
        feature_7=12.0,
        feature_8=3.0,
        feature_9=10.0,
        feature_10=4.0
    )
    
    return await predict(sample_data)

# --------------------------------------------------
# 🔄 모델 재로드 엔드포인트 (관리용)
# --------------------------------------------------
@app.post("/reload")
async def reload_models():
    """모델을 다시 로드합니다 (관리자용)"""
    global models, meta
    
    if not UTILS_LOADED:
        raise HTTPException(
            status_code=503,
            detail="model_utils를 사용할 수 없습니다."
        )
    
    try:
        print("🔄 모델 재로드 시작...")
        result = load_models_from_minio(
            endpoint=MINIO_ENDPOINT,
            bucket=BUCKET,
            prefix=PREFIX,
            local_dir=MODEL_DIR
        )
        
        if result is None or len(result) != 2:
            raise ValueError("모델 로드 실패")

        models, meta = result
        
        print("✅ 모델 재로드 완료!")
        
        return {
            "status": "success",
            "message": "모델이 성공적으로 재로드되었습니다.",
            "model_version": meta.get("version", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 모델 재로드 실패: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"모델 재로드 실패: {str(e)}"
        )

# --------------------------------------------------
# 🚀 서버 실행 (로컬 테스트용)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    
    PORT = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print(f"🚀 FastAPI 서버를 포트 {PORT}에서 시작합니다...")
    print(f"📚 API 문서: http://localhost:{PORT}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "serve_model:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,  # 개발 모드에서만 사용
        log_level="info"
    )
