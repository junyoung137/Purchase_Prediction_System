# =====================================================
# dashboard.py 
# =====================================================
import streamlit as st
import pandas as pd
import requests
import json
import plotly.graph_objects as go

# =========================================
# 🔧 API 설정 (FastAPI 기준)
# =========================================
API_URL = "https://purchase-prediction-system.onrender.com/predict"
HEALTH_URL = "https://purchase-prediction-system.onrender.com/"

st.set_page_config(page_title="🛍️ 구매 예측 대시보드", layout="wide")
st.title("🛍️ 구매 예측 대시보드")

# =========================================
# 📊 사이드바: 실무 기능
# =========================================
st.sidebar.header("📊 빠른 분석")

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

# =========================================
# Feature 매핑
# =========================================
FEATURE_MAPPING = {
    "총 방문 횟수": "feature_1",
    "마지막 활동 후 경과일": "feature_2",
    "활동 빈도": "feature_3",
    "장바구니 담은 상품 수": "feature_4",
    "상품 조회 수": "feature_5",
    "세션 총 활동 횟수": "feature_6",
    "평균 세션 시간": "feature_7",
    "리뷰 작성 수": "feature_8",
    "할인 상품 조회": "feature_9",
    "결제 페이지 방문": "feature_10",
}

# =========================================
# 1️⃣ 개별 예측
# =========================================
st.markdown("### 1️⃣ 개별 고객 구매 가능성 예측")
st.markdown("고객 세션의 주요 활동 정보를 입력하여 구매 확률을 예측합니다.")

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
# 🔹 예측 실행 로직
# =========================================
if submit:
    if 'preset' in st.session_state:
        del st.session_state.preset

    # 🚀 모델은 feature_1~7만 사용
    payload = {
        "feature_1": float(f1),
        "feature_2": float(f2),
        "feature_3": float(f3),
        "feature_4": float(f4),
        "feature_5": float(f5),
        "feature_6": float(f6),
        "feature_7": float(f7)
    }

    try:
        with st.spinner("예측 중..."):
            res = requests.post(API_URL, json=payload, timeout=10)
            res.raise_for_status()
            result = res.json()

        prob = result.get("probability", 0)
        pred = result.get("prediction", 0)
        threshold = result.get("threshold", 0.5)

        label = "✅ 구매 예상" if pred == 1 else "❌ 비구매 예상"

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("예측 결과", label)
        col_b.metric("구매 확률", f"{prob:.2%}")
        col_c.metric("Threshold", f"{threshold:.2f}")

        st.success("✅ 예측 성공 — 결과가 MinIO 로그에 자동 저장되었습니다.")

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

        with st.expander("📋 응답 상세 정보"):
            st.json(result)

    except requests.exceptions.RequestException as e:
        st.error(f"❌ API 요청 실패: {e}")
    except Exception as e:
        st.error(f"❌ 예측 실패: {e}")

# =========================================
# 푸터
# =========================================
st.markdown("---")
st.caption("""
🚀 고객 구매 예측 시스템 (Production v5.0)
""")
