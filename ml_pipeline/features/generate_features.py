# ======================================
# 🧮 피처 생성 스크립트 (generate_features.py)
# ======================================
import pandas as pd
import s3fs
import os

print("\n🚀 Starting feature generation...")

# --- MinIO 연결 ---
fs = s3fs.S3FileSystem(
    client_kwargs={
        "endpoint_url": "http://host.docker.internal:9900",
        "aws_access_key_id": "minioadmin",
        "aws_secret_access_key": "minioadmin",
    }
)

RAW_PATH = "s3://raw-data/sessions.csv"  # 예시
OUTPUT_PATH = "s3://feature-data/session_features.parquet"

print("📦 Loading raw data from MinIO...")
df = pd.read_csv(fs.open(RAW_PATH))

# --- 간단한 피처 엔지니어링 ---
df["cart_to_view_ratio"] = df["cart_events"] / (df["view_events"] + 1)
df["session_activity_index"] = df["total_events"] / (df["session_length"] + 1)

print("✅ Feature engineering completed!")
df.to_parquet(OUTPUT_PATH, index=False)
print(f"✅ Features saved to {OUTPUT_PATH}")
