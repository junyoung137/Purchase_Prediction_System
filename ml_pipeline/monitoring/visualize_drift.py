# ===============================================================
# 데이터 드리프트 시각화 스크립트
# ===============================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import s3fs
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 70)
print("📊 데이터 드리프트 시각화")
print("=" * 70)

# MinIO 연결
fs = s3fs.S3FileSystem(
    key="minioadmin",
    secret="minioadmin",
    client_kwargs={"endpoint_url": "http://localhost:9900"}
)

# 출력 디렉토리 생성
OUTPUT_DIR = "ml-pipeline/monitoring/drift_plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 1️⃣ 데이터 로드 ---
print("\n[1/3] 데이터 로딩...")

reference_path = "s3://model-logs/session-purchase/reference_data.csv"
log_path = "s3://model-logs/session-purchase/inference-logs.csv"

with fs.open(reference_path, "rb") as f:
    ref_df = pd.read_csv(f)

with fs.open(log_path, "rb") as f:
    cur_df = pd.read_csv(f)

print(f"   ✅ 기준 데이터: {ref_df.shape[0]:,}행")
print(f"   ✅ 현재 데이터: {cur_df.shape[0]}행")

# 공통 피처 추출
exclude_cols = ['probability', 'prediction', 'threshold', 'model_version', 
                'used_features', 'timestamp', 'has_transaction']
feature_cols = [col for col in ref_df.columns if col not in exclude_cols]
common_cols = [col for col in cur_df.columns if col in feature_cols]

# 피처명 한글 매핑
feature_name_map = {
    'cart_depth': '장바구니 담은 상품 수',
    'cart_to_view_ratio': '장바구니 담기 비율',
    'recent_days': '마지막 활동 후 경과일',
    'event_per_session': '세션 총 활동 횟수',
    'total_sessions': '총 방문 횟수',
    'event_diversity': '활동 다양성',
    'recent_intensity': '최근 활동 강도',
    'recency_ratio': '재방문 비율',
    'session_activity_index': '활동 지수',
    'frequency': '활동 빈도'
}

print(f"   📋 분석 피처: {len(common_cols)}개")

# --- 2️⃣ 분포 비교 시각화 ---
print("\n[2/3] 분포 비교 시각화 생성 중...")

# 피처당 하나의 플롯 생성
fig, axes = plt.subplots(len(common_cols), 1, figsize=(12, 4 * len(common_cols)))
if len(common_cols) == 1:
    axes = [axes]

for idx, col in enumerate(common_cols):
    ax = axes[idx]
    
    # 기준 데이터 (샘플링하여 크기 맞추기)
    ref_sample = ref_df[col].sample(min(10000, len(ref_df)), random_state=42)
    
    # 히스토그램
    ax.hist(ref_sample, bins=50, alpha=0.5, label='학습 데이터', 
            color='blue', density=True)
    ax.hist(cur_df[col], bins=30, alpha=0.5, label='운영 데이터', 
            color='red', density=True)
    
    # 한글 피처명 사용
    korean_name = feature_name_map.get(col, col)
    ax.set_xlabel(korean_name, fontsize=10)
    ax.set_ylabel('밀도', fontsize=10)
    ax.set_title(f'분포 비교: {korean_name}', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 통계 정보 추가
    ref_mean = ref_df[col].mean()
    cur_mean = cur_df[col].mean()
    ref_std = ref_df[col].std()
    cur_std = cur_df[col].std()
    
    stats_text = f'학습: 평균={ref_mean:.2f}, 표준편차={ref_std:.2f}\n'
    stats_text += f'운영: 평균={cur_mean:.2f}, 표준편차={cur_std:.2f}'
    ax.text(0.98, 0.95, stats_text, transform=ax.transAxes,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=9)

plt.tight_layout()
save_path = os.path.join(OUTPUT_DIR, "feature_distribution_comparison.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"   ✅ 분포 비교 그래프 저장: {save_path}")
plt.close()

# --- 3️⃣ PSI 리포트 시각화 ---
print("\n[3/3] PSI 리포트 시각화 중...")

psi_path = "s3://model-logs/session-purchase/psi_report.csv"
with fs.open(psi_path, "rb") as f:
    psi_df = pd.read_csv(f)

# 피처명을 한글로 변경
psi_df['feature_kr'] = psi_df['feature'].map(feature_name_map).fillna(psi_df['feature'])

fig, ax = plt.subplots(figsize=(10, 6))

# PSI 값 바 차트
colors = psi_df['psi'].apply(
    lambda x: '#27ae60' if x < 0.1 else '#f39c12' if x < 0.25 else '#e74c3c'
)

bars = ax.barh(psi_df['feature_kr'], psi_df['psi'], color=colors)

# 기준선 추가
ax.axvline(x=0.1, color='green', linestyle='--', linewidth=2, 
           label='안정 (< 0.1)', alpha=0.7)
ax.axvline(x=0.25, color='orange', linestyle='--', linewidth=2, 
           label='보통 (< 0.25)', alpha=0.7)

ax.set_xlabel('PSI 값', fontsize=12, fontweight='bold')
ax.set_ylabel('피처', fontsize=12, fontweight='bold')
ax.set_title('피처별 모집단 안정성 지수 (PSI)', 
             fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, axis='x', alpha=0.3)

# 값 레이블 추가
for i, (feature, psi) in enumerate(zip(psi_df['feature_kr'], psi_df['psi'])):
    ax.text(psi + 0.3, i, f'{psi:.2f}', 
            va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
save_path = os.path.join(OUTPUT_DIR, "psi_report_chart.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"   ✅ PSI 차트 저장: {save_path}")
plt.close()

# --- 4️⃣ 통계 요약 테이블 ---
print("\n📈 통계 요약:")
print("=" * 70)

summary_data = []
for col in common_cols:
    summary_data.append({
        '피처': col,
        '학습 평균': f"{ref_df[col].mean():.2f}",
        '운영 평균': f"{cur_df[col].mean():.2f}",
        '학습 표준편차': f"{ref_df[col].std():.2f}",
        '운영 표준편차': f"{cur_df[col].std():.2f}",
        '평균 차이': f"{abs(ref_df[col].mean() - cur_df[col].mean()):.2f}"
    })

summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False))

print("\n" + "=" * 70)
print("✅ 시각화 완료!")
print("=" * 70)
print(f"\n📂 저장 위치: {OUTPUT_DIR}/")
print("   - feature_distribution_comparison.png")
print("   - psi_report_chart.png")