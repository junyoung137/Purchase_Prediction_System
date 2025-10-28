# =====================================================
# 🧠 FastAPI 모델 서빙 Dockerfile
# - Python 3.12 기반
# - non-root user 실행
# - FASTAPI_PORT 환경변수로 포트 제어
# =====================================================
FROM python:3.12-slim

# -- 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FASTAPI_PORT=8080

# 작업 디렉터리
WORKDIR /app

# 시스템 패키지 설치 (빌드용 툴 포함)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential gcc git curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# non-root 사용자 생성
RUN useradd --create-home --shell /bin/bash appuser \
  && mkdir -p /app/models_cache \
  && chown -R appuser:appuser /app /app/models_cache

# requirements 복사 및 의존성 설치 (가능하면 캐시 없이)
COPY --chown=appuser:appuser requirements.txt /app/requirements.txt

# pip 업그레이드 및 requirements 설치
RUN python -m pip install --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r /app/requirements.txt

# 앱 소스 복사 (최종)
COPY --chown=appuser:appuser . /app

# 작업 유저 전환
USER appuser

# 컨테이너 노출 포트 (기본값은 8080)
EXPOSE ${FASTAPI_PORT}

# 기본 실행: FASTAPI_PORT 환경변수에 맞춰 uvicorn 실행
# (docker run -e FASTAPI_PORT=5000 ... 또는 docker-compose로 설정)
CMD ["sh", "-c", "uvicorn serve_model:app --host 0.0.0.0 --port ${FASTAPI_PORT} --workers 2"]
