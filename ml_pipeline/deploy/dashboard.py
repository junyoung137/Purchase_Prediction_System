# =====================================================
# dashboard.py (v6.1 - Streamlit Cloud 독립 실행 버전)
# =====================================================
import streamlit as st

# ⚠️ CRITICAL: set_page_config은 가장 먼저 실행되어야 함!
st.set_page_config(page_title="🛍️ 구매 예측 대시보드", layout="wide")

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
from datetime import datetime
import os

# =========================================
# 🔧 모델 로드 (캐싱)
# =========================================
@st.cache_resource
def load_model():
    """모델 파일 로드 (GitHub에 포함되어야 함)"""
    try:
        # 모델 파일 경로 시도
        possible_paths = [
            'models/xgboost_model.pkl',
            'models/model.pkl',
            'ml_pipeline/models/xgboost_model.pkl',
            'model.pkl',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                model = joblib.load(path)
                return model, path
        
        # 모델 파일이 없으면 더미 모델 사용
        return None, "더미 모델"
        
    except Exception as e:
        return None, f"오류: {str(e)}"

model, model_info = load_model()

# =========================================
# 🎯 예측 함수
# =========================================
def predict(features_dict):
    """
    입력 features로 예측 수행
    Args:
        features_dict: {'feature_1': value, 'feature_2': value, ...}
    Returns:
        {'prediction': 0/1, 'probability': float, 'threshold': float}
    """
    try:
        # DataFrame 생성
        df = pd.DataFrame([features_dict])
        
        # 모델이 있으면 실제 예측
        if model is not None:
            proba = model.predict_proba(df)[0][1]  # 클래스 1의 확률
            threshold = 0.5
            pred = 1 if proba >= threshold else 0
        else:
            # 더미 예측 (간단한 규칙 기반)
            # feature_1(방문횟수) + feature_4(장바구니) + feature_10(결제페이지) 기반
            score = (
                features_dict.get('feature_1', 0) * 0.03 +
                features_dict.get('feature_4', 0) * 0.15 +
                features_dict.get('feature_10', 0) * 0.25 +
                features_dict.get('feature_5', 0) * 0.01
            )
            proba = min(max(score / 10, 0.05), 0.95)  # 0.05~0.95 사이로 정규화
            threshold = 0.5
            pred = 1 if proba >= threshold else 0
        
        return {
            'prediction': pred,
            'probability': proba,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        st.error(f"예측 중 오류 발생: {e}")
        return None

# =========================================
# 🎨 UI 시작
# =========================================
st.title("🛍️ 구매 예측 대시보드")

# =========================================
# 📊 사이드바: 실무 기능
# =========================================
st.sidebar.header("📊 빠른 분석")

# 모델 상태 표시
if model is not None:
    st.sidebar.success(f"✅ 모델 로드 성공\n`{model_info}`")
else:
    st.sidebar.warning(f"⚠️ 더미 모델 사용 중\n(실제 모델 파일을 업로드하면 정확한 예측 가능)")

st.sidebar.markdown("---")

# 고위험/고가치 고객 프리셋
st.sidebar.subheader("🎯 고객 프로필 프리셋")

preset_profiles = {
    "🔥 고관심 고객": {
        "feature_1": 15.0, "feature_2": 2.0, "feature_3": 20.0,
        "feature_4": 5.0, "feature_5": 30.0, "feature_6": 50.0,
        "feature_7": 12.0, "feature_8": 3.0, "feature_9": 10.0, "feature_10": 4.0
    },
    "⚠️ 이탈 위험 고객": {
        "feature_1": 3.0, "feature_2": 30.0, "feature_3": 2.0,
        "feature_4": 0.0, "feature_5": 5.0, "feature_6": 8.0,
        "feature_7": 2.0, "feature_8": 0.0, "feature_9": 1.0, "feature_10": 0.0
    },
    "💚 신규 방문자": {
        "feature_1": 1.0, "feature_2": 0.0, "feature_3": 3.0,
        "feature_4": 1.0, "feature_5": 8.0, "feature_6": 12.0,
        "feature_7": 5.0, "feature_8": 0.0, "feature_9": 2.0, "feature_10": 0.0
    },
    "🎁 재구매 고객": {
        "feature_1": 25.0, "feature_2": 7.0, "feature_3": 15.0,
        "feature_4": 3.0, "feature_5": 20.0, "feature_6": 40.0,
        "feature_7": 10.0, "feature_8": 5.0, "feature_9": 8.0, "feature_10": 3.0
    }
}

selected_preset = st.sidebar.selectbox(
    "프로필 선택",
    ["선택 안함"] + list(preset_profiles.keys())
)

if selected_preset != "선택 안함":
    if st.sidebar.button("📋 값 적용하기", use_container_width=True):
        st.session_state.preset = preset_profiles[selected_preset]
        st.rerun()

st.sidebar.markdown("---")

# 통계 대시보드 (배치 예측 후 표시)
if 'batch_stats' in st.session_state:
    st.sidebar.subheader("📈 최근 배치 분석 결과")
    stats = st.session_state.batch_stats
    
    st.sidebar.metric("전체 고객 수", f"{stats['total']:,}명")
    st.sidebar.metric("구매 예상", f"{stats['purchase']:,}명 ({stats['purchase_rate']:.1f}%)")
    st.sidebar.metric("평균 구매 확률", f"{stats['avg_prob']:.1%}")
    
    if stats['high_potential'] > 0:
        st.sidebar.success(f"🎯 고확률 고객: {stats['high_potential']}명")

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **사용 가이드**
- **개별 예측**: 특정 고객의 구매 가능성 분석
- **배치 예측**: 다수 고객 일괄 분석
- **프리셋**: 대표 고객 프로필로 빠른 테스트
""")

# =========================================
# 1️⃣ 개별 예측 실행
# =========================================
st.markdown("### 1️⃣ 개별 고객 구매 가능성 예측")
st.markdown("고객 세션의 주요 활동 정보를 입력하여 구매 확률을 예측합니다.")

st.markdown("#### ✏️ 고객 활동 상세 입력")

# 프리셋 적용된 경우 초기값 설정
if 'preset' in st.session_state:
    preset = st.session_state.preset
    init_values = [preset[f"feature_{i}"] for i in range(1, 11)]
else:
    init_values = [5.0, 10.0, 8.0, 2.0, 10.0, 20.0, 5.0, 0.0, 3.0, 1.0]

with st.form("single_prediction_form"):
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        f1 = st.number_input("총 방문 횟수", min_value=0.0, value=init_values[0], step=0.1)
        f2 = st.number_input("마지막 활동 후 경과일", min_value=0.0, value=init_values[1], step=0.1)
        f3 = st.number_input("활동 빈도", min_value=0.0, value=init_values[2], step=0.1)
        f4 = st.number_input("장바구니 담은 상품 수", min_value=0.0, value=init_values[3], step=0.1)
    
    with col2:
        f5 = st.number_input("상품 조회 수", min_value=0.0, value=init_values[4], step=0.1)
        f6 = st.number_input("세션 총 활동 횟수", min_value=0.0, value=init_values[5], step=0.1)
        f7 = st.number_input("평균 세션 시간 (분)", min_value=0.0, value=init_values[6], step=0.1)
    
    with col3:
        f8 = st.number_input("리뷰 작성 수", min_value=0.0, value=init_values[7], step=0.1)
        f9 = st.number_input("할인 상품 조회", min_value=0.0, value=init_values[8], step=0.1)
        f10 = st.number_input("결제 페이지 방문", min_value=0.0, value=init_values[9], step=0.1)

    st.markdown("---")
    submit = st.form_submit_button("🔍 예측 실행", use_container_width=True)

# =========================================
# 🔹 예측 로직
# =========================================
if submit:
    # 프리셋 세션 상태 초기화
    if 'preset' in st.session_state:
        del st.session_state.preset
    
    # Features 딕셔너리 생성
    features = {
        "feature_1": float(f1),
        "feature_2": float(f2),
        "feature_3": float(f3),
        "feature_4": float(f4),
        "feature_5": float(f5),
        "feature_6": float(f6),
        "feature_7": float(f7),
        "feature_8": float(f8),
        "feature_9": float(f9),
        "feature_10": float(f10),
    }

    with st.spinner("예측 중..."):
        result = predict(features)

    if result:
        prob = result.get("probability", 0)
        pred = result.get("prediction", 0)
        threshold = result.get("threshold", 0.5)

        label = "✅ 구매 예상" if pred == 1 else "❌ 비구매 예상"

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("예측 결과", label)
        col_b.metric("구매 확률", f"{prob:.2%}")
        col_c.metric("Threshold", f"{threshold:.2f}")

        st.success("✅ 예측 완료!")

        # 게이지 차트
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=prob * 100,
            delta={'reference': threshold * 100},
            title={'text': "구매 확률 (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2b6cb0"},
                'steps': [
                    {'range': [0, 30], 'color': "#f7fafc"},
                    {'range': [30, 60], 'color': "#cbd5e0"},
                    {'range': [60, 100], 'color': "#9ae6b4"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'value': threshold * 100}
            }
        ))
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)

        # 응답 상세 정보
        with st.expander("📋 예측 상세 정보"):
            st.json(result)
            st.write("**입력 Features:**")
            st.json(features)

# =========================================
# 2️⃣ 배치 예측 (CSV)
# =========================================
st.markdown("---")
st.markdown("### 2️⃣ 대량 고객 구매 가능성 예측 (CSV 업로드)")

st.info("""
📋 **CSV 파일 형식 요구사항:**
- 컬럼명: `feature_1` ~ `feature_10` (정확히 10개)
- 모든 값은 숫자(float)여야 합니다
- 예시: `feature_1,feature_2,...,feature_10`
""")

uploaded = st.file_uploader("📂 CSV 업로드", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    st.write("**업로드된 데이터 미리보기:**")
    st.dataframe(df.head(), use_container_width=True)

    # 컬럼 검증
    required_cols = [f"feature_{i}" for i in range(1, 11)]
    missing_cols = set(required_cols) - set(df.columns)
    
    if missing_cols:
        st.error(f"❌ 누락된 컬럼: {missing_cols}")
    else:
        if st.button("📈 배치 예측 실행", use_container_width=True):
            results = []
            progress = st.progress(0)

            for i, (_, row) in enumerate(df.iterrows()):
                features = {f"feature_{j}": float(row[f"feature_{j}"]) for j in range(1, 11)}
                result = predict(features)
                
                if result:
                    results.append(result)
                else:
                    results.append({"error": "예측 실패"})
                
                progress.progress((i + 1) / len(df))

            progress.empty()
            out = pd.DataFrame(results)
            st.success("✅ 배치 예측 완료")
            st.dataframe(out, use_container_width=True)

            # 통계 요약 및 세션 상태 저장
            if "prediction" in out.columns:
                col1, col2, col3 = st.columns(3)
                total = len(out)
                purchase = (out["prediction"] == 1).sum()
                purchase_rate = (purchase / total * 100) if total > 0 else 0
                avg_prob = out["probability"].mean() if "probability" in out.columns else 0
                high_potential = (out["probability"] > 0.7).sum() if "probability" in out.columns else 0
                
                col1.metric("전체 건수", f"{total:,}명")
                col2.metric("구매 예상", f"{purchase:,}명 ({purchase_rate:.1f}%)")
                col3.metric("평균 구매 확률", f"{avg_prob:.1%}")
                
                # 사이드바에 표시할 통계 저장
                st.session_state.batch_stats = {
                    'total': total,
                    'purchase': purchase,
                    'purchase_rate': purchase_rate,
                    'avg_prob': avg_prob,
                    'high_potential': high_potential
                }
                
                # 고확률 고객 하이라이트
                if high_potential > 0:
                    st.success(f"🎯 고확률 고객 (70% 이상): **{high_potential}명** 발견!")
                
                # 분포 시각화
                fig = px.histogram(
                    out, 
                    x="probability", 
                    nbins=20,
                    title="구매 확률 분포",
                    labels={"probability": "구매 확률", "count": "고객 수"}
                )
                st.plotly_chart(fig, use_container_width=True)

            csv_data = out.to_csv(index=False).encode("utf-8")
            st.download_button("📥 결과 다운로드 (CSV)", csv_data, "predictions.csv", "text/csv")

# =========================================
# 3️⃣ 샘플 데이터 생성기
# =========================================
st.markdown("---")
st.markdown("### 3️⃣ 테스트용 샘플 데이터 생성")

col_sample1, col_sample2 = st.columns(2)

with col_sample1:
    num_samples = st.number_input("생성할 샘플 수", min_value=10, max_value=1000, value=100, step=10)

with col_sample2:
    if st.button("🎲 랜덤 샘플 생성", use_container_width=True):
        np.random.seed(42)
        sample_data = pd.DataFrame({
            f"feature_{i}": np.random.uniform(0, 30, num_samples) for i in range(1, 11)
        })
        
        st.session_state.sample_data = sample_data
        st.success(f"✅ {num_samples}개 샘플 데이터 생성 완료!")

if 'sample_data' in st.session_state:
    st.dataframe(st.session_state.sample_data.head(10), use_container_width=True)
    
    csv_sample = st.session_state.sample_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 샘플 데이터 다운로드 (CSV)", 
        csv_sample, 
        "sample_customers.csv", 
        "text/csv",
        use_container_width=True
    )

# =========================================
# 푸터
# =========================================
st.markdown("---")
st.caption("""
🚀 고객 구매 예측 시스템 (Streamlit Cloud v6.1)  
✨ 모델 독립 실행 버전 - API 불필요
""")
