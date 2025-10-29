# =====================================================
# dashboard.py (프리셋 개선 + 비율 자동 계산 + 정규화)
# =====================================================
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# =========================================
# 🔧 API 설정
# =========================================
API_URL = "https://purchase-prediction-system.onrender.com/predict"

st.set_page_config(page_title="🛍️ 구매 예측 대시보드", layout="wide")
st.title("🛍️ 구매 예측 대시보드")

# =========================================
# 📊 사이드바: 프리셋
# =========================================
st.sidebar.header("📊 빠른 분석")
st.sidebar.subheader("🎯 고객 프로필 프리셋")

preset_profiles = {
    "🔥 고관심 고객": {
        "event_count": 120, "n_view": 80, "n_cart": 20, "n_trans": 10
    },
    "⚠️ 이탈 위험 고객": {
        "event_count": 30, "n_view": 3, "n_cart": 0, "n_trans": 0
    },
    "💚 신규 방문자": {
        "event_count": 10, "n_view": 5, "n_cart": 0, "n_trans": 0
    },
    "🎁 재구매 고객": {
        "event_count": 200, "n_view": 120, "n_cart": 30, "n_trans": 15
    }
}

selected_preset = st.sidebar.selectbox("프로필 선택", ["선택 안함"] + list(preset_profiles.keys()))

if selected_preset != "선택 안함":
    if st.sidebar.button("📋 값 적용하기", use_container_width=True):
        for k, v in preset_profiles[selected_preset].items():
            st.session_state[k] = v
        st.sidebar.success(f"✅ '{selected_preset}' 값 적용 완료!")
        st.rerun()

st.sidebar.markdown("---")

# =========================================
# 1️⃣ 개별 예측
# =========================================
st.markdown("### 1️⃣ 개별 고객 구매 가능성 예측")
st.markdown("고객 세션 활동 정보를 입력하여 구매 확률을 예측합니다.")

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.number_input("전체 이벤트 발생 횟수 (event_count)", min_value=0.0, step=1.0, key="event_count")
    st.number_input("상품 조회 횟수 (n_view)", min_value=0.0, step=1.0, key="n_view")

with col2:
    st.number_input("장바구니 담기 횟수 (n_cart)", min_value=0.0, step=1.0, key="n_cart")
    st.number_input("결제 완료 횟수 (n_trans)", min_value=0.0, step=1.0, key="n_trans")

st.markdown("---")

if st.button("🔍 예측 실행", use_container_width=True):
    # ✅ 비율 자동 계산 + 정규화
    event_count = st.session_state.get("event_count", 0)
    n_view = st.session_state.get("n_view", 0)
    n_cart = st.session_state.get("n_cart", 0)
    n_trans = st.session_state.get("n_trans", 0)

    n_trans_ratio = (n_trans / event_count) if event_count > 0 else 0
    n_view_ratio = (n_view / event_count) if event_count > 0 else 0

    # 0~1 정규화
    n_trans_ratio = min(n_trans_ratio, 1.0)
    n_view_ratio = min(n_view_ratio, 1.0)

    payload = {
        "session_id": "manual_input",
        "event_count": event_count,
        "n_view": n_view,
        "n_cart": n_cart,
        "n_trans": n_trans,
        "n_trans_ratio": n_trans_ratio,
        "n_view_ratio": n_view_ratio,
    }

    try:
        with st.spinner("예측 중..."):
            res = requests.post(API_URL, json=payload, timeout=10)
            res.raise_for_status()
            result = res.json()

        prob = result.get("probability", 0)
        threshold = 0.6  # ✅ 조정된 기준값
        label = "✅ 구매 예상" if prob >= threshold else "❌ 비구매 예상"

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("예측 결과", label)
        col_b.metric("구매 확률", f"{prob:.2%}")
        col_c.metric("Threshold", f"{threshold:.2f}")
        st.success("✅ 예측 성공")

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
# 2️⃣ 배치 예측 (CSV)
# =========================================
st.markdown("---")
st.markdown("### 2️⃣ 대량 고객 구매 가능성 예측 (CSV 업로드)")

st.info("""
📋 **CSV 업로드 안내:**
- 각 행(row)은 1명의 고객 세션을 의미합니다.
- 고객별 주요 활동 데이터(이벤트 수, 조회 수, 전환율 등)를 포함해야 합니다.
- CSV는 UTF-8 인코딩 권장, 숫자(float) 형식이어야 합니다.
""")

uploaded = st.file_uploader("📂 CSV 파일 업로드", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    st.dataframe(df.head(), use_container_width=True)

    required_cols = [
        "session_id", "event_count", "n_view", "n_cart",
        "n_trans", "n_trans_ratio", "n_view_ratio"
    ]
    missing_cols = set(required_cols) - set(df.columns)

    if missing_cols:
        st.error(f"❌ 누락된 컬럼: {missing_cols}")
    else:
        if st.button("📈 배치 예측 실행", use_container_width=True):
            results = []
            progress = st.progress(0)

            for i, (_, row) in enumerate(df.iterrows()):
                payload = {col: float(row[col]) if col != "session_id" else str(row[col]) for col in required_cols}
                try:
                    r = requests.post(API_URL, json=payload, timeout=10)
                    r.raise_for_status()
                    result = r.json()
                    results.append({
                        "probability": result.get("probability"),
                        "prediction": result.get("prediction"),
                        "threshold": 0.6,
                        "timestamp": result.get("timestamp"),
                    })
                except Exception as e:
                    results.append({"error": str(e)})
                progress.progress((i + 1) / len(df))

            progress.empty()
            out = pd.DataFrame(results)
            st.success("✅ 배치 예측 완료")
            st.dataframe(out)

            if "probability" in out.columns:
                col1, col2, col3 = st.columns(3)
                total = len(out)
                purchase = (out["probability"] >= 0.6).sum()
                purchase_rate = (purchase / total * 100)
                avg_prob = out["probability"].mean()
                high_potential = (out["probability"] > 0.7).sum()

                col1.metric("전체 건수", f"{total:,}명")
                col2.metric("구매 예상", f"{purchase:,}명 ({purchase_rate:.1f}%)")
                col3.metric("평균 구매 확률", f"{avg_prob:.1%}")

                if high_potential > 0:
                    st.success(f"🎯 고확률 고객 (70% 이상): **{high_potential}명** 발견!")

            csv_data = out.to_csv(index=False).encode("utf-8")
            st.download_button("📥 결과 다운로드", csv_data, "predictions.csv", "text/csv")

# =========================================
# 푸터
# =========================================
st.markdown("---")
st.caption("🚀 고객 구매 예측 시스템 (v6.0)")

