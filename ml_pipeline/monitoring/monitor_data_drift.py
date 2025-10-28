# ======================================
# 데이터 드리프트 감지 (PSI 기반) 
# ======================================
import pandas as pd
import numpy as np
import s3fs
from datetime import datetime

print("=" * 70)
print("📊 데이터 드리프트 모니터링 시작")
print("=" * 70)

# --- MinIO 연결 설정 ---
fs = s3fs.S3FileSystem(
    key="minioadmin",
    secret="minioadmin",
    client_kwargs={"endpoint_url": "http://localhost:9900"}
)

# --- 1️⃣ 기준(reference) 데이터 로드 ---
print("\n[1/5] 기준 데이터 로딩...")
reference_path = "s3://model-logs/session-purchase/reference_data.csv"

try:
    with fs.open(reference_path, "rb") as f:
        ref_df = pd.read_csv(f)
    print(f"   ✅ 기준 데이터: {ref_df.shape[0]}행 × {ref_df.shape[1]}열")
except FileNotFoundError:
    print(f"   ❌ 기준 데이터를 찾을 수 없습니다: {reference_path}")
    print(f"   💡 먼저 'python ml-pipeline/monitoring/save_reference.py'를 실행하세요")
    exit(1)
except Exception as e:
    print(f"   ❌ 기준 데이터 로드 실패: {e}")
    exit(1)

# --- 2️⃣ 최근 예측 로그 불러오기 ---
print("\n[2/5] 최근 예측 로그 로딩...")
log_path = "s3://model-logs/session-purchase/inference-logs.csv"

try:
    with fs.open(log_path, "rb") as f:
        cur_df = pd.read_csv(f)
    print(f"   ✅ 예측 로그: {cur_df.shape[0]}행 × {cur_df.shape[1]}열")
    print(f"   📅 로그 기간: {cur_df['timestamp'].min()} ~ {cur_df['timestamp'].max()}")
except FileNotFoundError:
    print(f"   ❌ 예측 로그를 찾을 수 없습니다: {log_path}")
    print(f"   💡 먼저 예측 API를 호출하여 로그를 생성하세요")
    exit(1)
except Exception as e:
    print(f"   ❌ 예측 로그 로드 실패: {e}")
    exit(1)

# --- 3️⃣ 피처 컬럼만 추출 (공통 컬럼 찾기) ---
print("\n[3/5] 피처 추출 및 정렬...")

# 예측 결과 컬럼 제외
exclude_cols = ['probability', 'prediction', 'threshold', 'model_version', 
                'used_features', 'timestamp', 'has_transaction']
feature_cols = [col for col in ref_df.columns if col not in exclude_cols]

# 현재 로그에서도 동일한 컬럼만 선택
cur_feature_cols = [col for col in cur_df.columns if col in feature_cols]

if not cur_feature_cols:
    print(f"   ❌ 공통 피처를 찾을 수 없습니다")
    print(f"   기준 데이터 컬럼: {ref_df.columns.tolist()[:5]}...")
    print(f"   예측 로그 컬럼: {cur_df.columns.tolist()[:5]}...")
    exit(1)

ref = ref_df[cur_feature_cols]
cur = cur_df[cur_feature_cols]

print(f"   ✅ 분석 대상 피처: {len(cur_feature_cols)}개")
print(f"   📋 피처 목록: {cur_feature_cols[:5]}{'...' if len(cur_feature_cols) > 5 else ''}")

# --- 4️⃣ PSI 계산 함수 ---
def calculate_psi(expected, actual, buckets=10):
    """
    Population Stability Index (PSI) 계산
    - PSI < 0.1: 안정적 (Stable)
    - 0.1 ≤ PSI < 0.25: 중간 드리프트 (Moderate Drift)
    - PSI ≥ 0.25: 심각한 드리프트 (Significant Drift)
    """
    # 결측치 제거
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    
    if len(expected) == 0 or len(actual) == 0:
        return np.nan
    
    # 구간 생성 (expected 기준)
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    breakpoints = np.unique(breakpoints)  # 중복 제거
    
    if len(breakpoints) < 2:
        return np.nan
    
    # 각 구간의 비율 계산
    expected_percents = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=breakpoints)[0] / len(actual)
    
    # PSI 계산 (0으로 나누기 방지)
    expected_percents = np.where(expected_percents == 0, 1e-6, expected_percents)
    actual_percents = np.where(actual_percents == 0, 1e-6, actual_percents)
    
    psi_value = np.sum((actual_percents - expected_percents) * 
                       np.log(actual_percents / expected_percents))
    
    return psi_value

# --- 5️⃣ 전체 피처에 대해 PSI 계산 ---
print("\n[4/5] PSI 계산 중...")
psi_results = {}

for col in cur_feature_cols:
    try:
        psi = calculate_psi(ref[col].values, cur[col].values)
        psi_results[col] = psi
    except Exception as e:
        print(f"   ⚠️ {col} 계산 실패: {e}")
        psi_results[col] = np.nan

psi_df = pd.DataFrame(list(psi_results.items()), columns=["feature", "psi"])
psi_df = psi_df.sort_values("psi", ascending=False)

# 안정성 분류
psi_df["stability"] = pd.cut(
    psi_df["psi"],
    bins=[-np.inf, 0.1, 0.25, np.inf],
    labels=["✅ Stable", "⚠️ Moderate Drift", "🚨 Significant Drift"]
)

print(f"   ✅ PSI 계산 완료")

# --- 6️⃣ 결과 출력 ---
print("\n" + "=" * 70)
print("📊 데이터 드리프트 감지 결과")
print("=" * 70)
print(psi_df.to_string(index=False))

# 요약 통계
print("\n" + "=" * 70)
print("📈 요약 통계")
print("=" * 70)
stability_counts = psi_df["stability"].value_counts()
for status, count in stability_counts.items():
    print(f"   {status}: {count}개 피처")

# 경고가 필요한 피처
drifted = psi_df[psi_df["psi"] >= 0.25]
if len(drifted) > 0:
    print("\n🚨 주의가 필요한 피처 (PSI ≥ 0.25):")
    for _, row in drifted.iterrows():
        print(f"   - {row['feature']}: PSI = {row['psi']:.4f}")
else:
    print("\n✅ 모든 피처가 안정적입니다!")

# --- 7️⃣ MinIO에 업로드 ---
print("\n[5/5] 결과 저장 중...")
result_path = "s3://model-logs/session-purchase/psi_report.csv"

try:
    psi_df.to_csv("psi_report.csv", index=False)
    fs.put("psi_report.csv", result_path)
    print(f"   ✅ PSI 리포트 저장 완료 → {result_path}")
except Exception as e:
    print(f"   ⚠️ MinIO 업로드 실패: {e}")
    print(f"   💾 로컬 파일로 저장됨: psi_report.csv")

print("\n" + "=" * 70)
print("✅ 데이터 드리프트 모니터링 완료!")
print("=" * 70)