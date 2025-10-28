import os
import pandas as pd
import s3fs
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import matplotlib.font_manager as fm

plt.rcParams['font.family'] = 'NanumGothic'  
plt.rcParams['axes.unicode_minus'] = False

# --------------------------------------------------
# 1️⃣ MinIO 연결 설정
# --------------------------------------------------
MINIO_ENDPOINTS = [
    "http://host.docker.internal:9900",  # Docker/WSL 환경
    "http://localhost:9900",             # 로컬 직접 실행
    "http://172.28.159.42:9900",         # 내부 네트워크 IP (FastAPI와 동일)
]

ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
LOG_PATH = "s3://model-logs/session-purchase/inference-logs.csv"
OUTPUT_DIR = "ml-pipeline/monitoring/plots"

os.makedirs(OUTPUT_DIR, exist_ok=True)

fs = None
for ep in MINIO_ENDPOINTS:
    try:
        print(f"🔗 Trying MinIO endpoint: {ep}")
        fs = s3fs.S3FileSystem(
            key=ACCESS_KEY,
            secret=SECRET_KEY,
            client_kwargs={"endpoint_url": ep}
        )
        fs.ls("s3://model-logs")
        print(f"✅ Connected to MinIO at {ep}")
        break
    except Exception as e:
        print(f"⚠️ Connection failed ({ep}): {e}")

if fs is None:
    raise RuntimeError("❌ 모든 MinIO endpoint 연결 실패. MinIO 서버가 실행 중인지 확인하세요.")

# --------------------------------------------------
# 2️⃣ 로그 파일 로드
# --------------------------------------------------
print("📦 Loading inference logs...")
try:
    with fs.open(LOG_PATH, "rb") as f:
        logs = pd.read_csv(f)
    print(f"✅ Loaded logs → {logs.shape[0]} rows, {logs.shape[1]} columns")
except FileNotFoundError:
    raise FileNotFoundError(f"❌ 로그 파일이 존재하지 않습니다: {LOG_PATH}")
except Exception as e:
    raise RuntimeError(f"❌ 로그 불러오기 실패: {e}")

# --------------------------------------------------
# 3️⃣ 기본 정보
# --------------------------------------------------
print("\n[🧾 로그 데이터 미리보기]")
print(logs.head(3))
print("\n[📋 데이터 타입 및 결측치]")
print(logs.info())
print(logs.isnull().sum())

# --------------------------------------------------
# 4️⃣ 기본 통계
# --------------------------------------------------
print("\n[📊 기본 통계 요약]")
print(logs.describe(include="all"))

# --------------------------------------------------
# 5️⃣ 예측 확률 분포 시각화 (저장)
# --------------------------------------------------
if "probability" in logs.columns:
    plt.figure(figsize=(7, 5))
    sns.histplot(logs["probability"], bins=30, kde=True, color="#6baed6")
    plt.title(" 예측 확률 분포", fontsize=13)
    plt.xlabel("예측 확률", fontsize=11)
    plt.ylabel("개수", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "예측확률_분포.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"✅ 그래프 저장 완료 → {save_path}")
    plt.close()
else:
    print("⚠️ 'probability' 컬럼이 로그에 존재하지 않습니다.")

# --------------------------------------------------
# 6️⃣ 예측 Label 비율 시각화 (저장)
# --------------------------------------------------
if "prediction" in logs.columns:
    label_ratio = logs["prediction"].value_counts(normalize=True) * 100
    label_names = {0: "비구매", 1: "구매"}
    label_ratio.index = label_ratio.index.map(lambda x: label_names.get(x, str(x)))

    plt.figure(figsize=(5, 5))
    plt.pie(
        label_ratio,
        labels=[f"{i} ({v:.1f}%)" for i, v in label_ratio.items()],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#fd8d3c", "#6baed6"]
    )
    plt.title(" 구매/비구매 비율", fontsize=13)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "구매비율_파이차트.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"✅ 그래프 저장 완료 → {save_path}")
    plt.close()
else:
    print("⚠️ 'prediction' 컬럼이 로그에 존재하지 않습니다.")

# --------------------------------------------------
# 7️⃣ 시간 흐름에 따른 확률 변화 (저장)
# --------------------------------------------------
if "timestamp" in logs.columns and "probability" in logs.columns:
    logs["timestamp"] = pd.to_datetime(logs["timestamp"], errors="coerce")
    logs = logs.dropna(subset=["timestamp"])
    logs = logs.sort_values("timestamp")

    plt.figure(figsize=(10, 4))
    sns.lineplot(x="timestamp", y="probability", data=logs, marker="o", color="#3182bd")
    plt.title(" 시간별 예측 확률 추이", fontsize=13)
    plt.xlabel("시간", fontsize=11)
    plt.ylabel("예측 확률", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    save_path = os.path.join(OUTPUT_DIR, "시간별_예측확률추이.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"✅ 그래프 저장 완료 → {save_path}")
    plt.close()
else:
    print("⚠️ 시간 기반 시각화를 위한 컬럼(timestamp, probability)이 누락되어 있습니다.")

# --------------------------------------------------
# 8️⃣ 최신 로그 10건
# --------------------------------------------------
print("\n[🕒 최근 10건 로그]")
print(logs.sort_values("timestamp", ascending=False).head(10))

# --------------------------------------------------
# 9️⃣ CSV 백업 저장 (선택)
# --------------------------------------------------
backup_path = os.path.join(OUTPUT_DIR, f"inference_logs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
logs.to_csv(backup_path, index=False)
print(f"📁 로그 백업 완료 → {backup_path}")

print("\n✅ 로그 분석 및 그래프 저장 완료!")
