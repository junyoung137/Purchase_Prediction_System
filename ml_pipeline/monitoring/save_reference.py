#!/usr/bin/env python3
# ======================================
# 기준(reference) 데이터 저장 - 파생 피처 포함 버전
# ======================================
import pandas as pd
import numpy as np
import s3fs
import os

print("=" * 70)
print("📦 기준 데이터 생성 및 저장")
print("=" * 70)

# MinIO 연결 설정
fs = s3fs.S3FileSystem(
    key="minioadmin",
    secret="minioadmin",
    client_kwargs={"endpoint_url": "http://localhost:9900"}
)

# --------------------------------------------------
# 1️⃣ 파생 피처 계산 함수
# --------------------------------------------------
def compute_derived_features(df):
    """원시 피처로부터 파생 피처 계산"""
    print("\n[피처 계산] 파생 피처 생성 중...")
    
    # cart_to_view_ratio = n_cart / (n_view + 1)
    if "n_cart" in df.columns and "n_view" in df.columns:
        df["cart_to_view_ratio"] = df["n_cart"] / (df["n_view"] + 1)
        print("   ✅ cart_to_view_ratio")
    
    # event_per_session = total_events / (total_sessions + 1)
    if "total_events" in df.columns and "total_sessions" in df.columns:
        df["event_per_session"] = df["total_events"] / (df["total_sessions"] + 1)
        print("   ✅ event_per_session")
    
    # session_activity_index = frequency * log1p(total_sessions)
    if "frequency" in df.columns and "total_sessions" in df.columns:
        df["session_activity_index"] = df["frequency"] * np.log1p(df["total_sessions"])
        print("   ✅ session_activity_index")
    
    # recency_ratio = recent_days / (frequency + 1)
    if "recent_days" in df.columns and "frequency" in df.columns:
        df["recency_ratio"] = df["recent_days"] / (df["frequency"] + 1)
        print("   ✅ recency_ratio")
    
    # cart_depth = log1p(n_cart) * (frequency + 1)
    if "n_cart" in df.columns and "frequency" in df.columns:
        df["cart_depth"] = np.log1p(df["n_cart"]) * (df["frequency"] + 1)
        print("   ✅ cart_depth")
    
    # recent_intensity = exp(-recent_days / (frequency + 1))
    if "recent_days" in df.columns and "frequency" in df.columns:
        df["recent_intensity"] = np.exp(-df["recent_days"] / (df["frequency"] + 1))
        print("   ✅ recent_intensity")
    
    # event_diversity = log1p(total_sessions) / (recent_days + 1)
    if "total_sessions" in df.columns and "recent_days" in df.columns:
        df["event_diversity"] = np.log1p(df["total_sessions"]) / (df["recent_days"] + 1)
        print("   ✅ event_diversity")
    
    return df

# --------------------------------------------------
# 2️⃣ 학습 데이터 로드
# --------------------------------------------------
print("\n[1/4] 학습 피처 데이터 로딩...")
feature_path = "s3://feature-data/session_features.parquet"

try:
    X = pd.read_parquet(feature_path, storage_options={
        "key": "minioadmin",
        "secret": "minioadmin",
        "client_kwargs": {"endpoint_url": "http://localhost:9900"}
    })
    print(f"   ✅ 데이터 로드 완료: {X.shape[0]:,}행 × {X.shape[1]}열")
except Exception as e:
    print(f"   ❌ 데이터 로드 실패: {e}")
    exit(1)

# --------------------------------------------------
# 3️⃣ Target 컬럼 제거
# --------------------------------------------------
print("\n[2/4] Target 컬럼 제거...")
if "has_transaction" in X.columns:
    X = X.drop(columns=["has_transaction"])
    print("   ✅ 'has_transaction' 컬럼 제거")

print(f"   📊 현재 컬럼: {X.shape[1]}개")

# --------------------------------------------------
# 4️⃣ 파생 피처 계산
# --------------------------------------------------
print("\n[3/4] 파생 피처 계산...")
X = compute_derived_features(X)

print(f"\n   📊 파생 피처 추가 후: {X.shape[1]}개 컬럼")

# 최종 선택할 피처 (예측 API와 동일한 10개)
final_features = [
    'total_sessions', 'recent_days', 'frequency',
    'cart_to_view_ratio', 'event_per_session', 'session_activity_index',
    'recency_ratio', 'cart_depth', 'recent_intensity', 'event_diversity'
]

# 존재하는 피처만 선택
available_features = [f for f in final_features if f in X.columns]
X_final = X[available_features]

print(f"   📋 최종 선택된 피처: {len(available_features)}개")
for f in available_features:
    print(f"      - {f}")

# --------------------------------------------------
# 5️⃣ 저장
# --------------------------------------------------
print("\n[4/4] MinIO 업로드 중...")
REFERENCE_PATH = "s3://model-logs/session-purchase/reference_data.csv"

try:
    # 로컬에 먼저 저장
    X_final.to_csv("reference_data.csv", index=False)
    print("   ✅ 로컬 저장 완료")
    
    # MinIO 업로드
    fs.put("reference_data.csv", REFERENCE_PATH)
    print(f"   ✅ MinIO 업로드 완료 → {REFERENCE_PATH}")
    
    # 로컬 파일 삭제
    os.remove("reference_data.csv")
    
except Exception as e:
    print(f"   ❌ 업로드 실패: {e}")
    exit(1)

# --------------------------------------------------
# 6️⃣ 검증
# --------------------------------------------------
print("\n[검증] 저장된 데이터 확인...")
try:
    with fs.open(REFERENCE_PATH, "rb") as f:
        saved_df = pd.read_csv(f)
    
    print(f"   ✅ Shape: {saved_df.shape[0]:,}행 × {saved_df.shape[1]}열")
    print(f"   ✅ 컬럼: {saved_df.columns.tolist()}")
    print(f"\n   📊 통계 요약:")
    print(saved_df.describe().to_string())
    
except Exception as e:
    print(f"   ❌ 검증 실패: {e}")

print("\n" + "=" * 70)
print("✅ 기준 데이터 생성 완료!")
print("=" * 70)
print("\n다음 단계:")
print("   python ml-pipeline/monitoring/monitor_data_drift.py")