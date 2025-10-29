# =====================================================
# dashboard.py (프리셋 연동 완성 버전)
# =====================================================
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# =========================================
# 🔧 API 설정 (FastAPI 기준)
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

# ✅ 프리셋 클릭 시 세션 상태에 값 저장
if selected_preset != "선택 안함":
    if st.sidebar.button("📋 값 적용하기", use_container_width=True):
        for k, v in preset_profiles[selected_preset].items():
            st.session_state[k] = v
        st.sidebar.success(f"✅ '{selected_preset}' 값 적용 완료!")
        st.experimental_rerun()

st.sidebar.markdown("---")

# =========================================
# 1️⃣ 개별 예측
# =========================================
st.markdown("### 1️⃣ 개별 고객 구매 가능성 예측")
st.markdown("고객 세션의 주요 활동 정보를 입력하여 구매 확률을 예측합니다.")

# ✅ 각 입력창을 session_state에 직접 연결
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.number_input("총 방문 횟수", min_value=0.0, step=0.1, key="feature_1")
    st.number_input("마지막 활동 후 경과일", min_value=0.0, step=0.1, key="feature_2")
    st.number_input("활동 빈도", min_value=0.0, step=0.1, key="feature_3")
    st.number_input("장바구니 담은 상품 수", min_value=0.0, step=0.1, key="feature_4")

with col2:
    st.number_input("상품 조회 수", min_value=0.0, step=0.1, key="feature_5")
    st.number_input("세션 총 활동 횟수", min_value=0.0, step=0.1, key="feature_6")
    st.number_input("평균 세션 시간 (분)", min_value=0.0, step=0.1, key="feature_7")

with col3:
    st.number_input("리뷰 작성 수", min_value=0.0, step=0.1, key="feature_8")
    st.number_input("할인 상품 조회", min_value=0.0, step=0.1, key="feature_9")
    st.number_input("결제 페이지 방문", min_value=0.0, step=0.1, key="feature_10")

st.markdown("---")
if st.button("🔍 예측 실행", use_container_width=True):
    payload = {f"feature_{i}": float(st.session_state.get(f"feature_{i}", 0)) for i in range(1, 8)}

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
        st.success("✅ 예측 성공")

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

with st.expander("📘 자세한 컬럼 정의 보기 (운영자용)"):
    st.markdown("""
    | 컬럼명 | 설명 |
    |:--------|:------------------------------------------------|
    | `session_id` | 고객 세션 ID |
    | `event_count` | 전체 이벤트 발생 횟수 |
    | `n_view` | 상품 조회 횟수 |
    | `n_cart` | 장바구니 담기 횟수 |
    | `n_trans` | 결제 완료 횟수 |
    | `n_trans_ratio` | 결제 전환율 (n_trans / event_count) |
    | `n_view_ratio` | 조회 비율 (n_view / event_count) |
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
                payload = {col: float(row[col]) for col in required_cols}
                try:
                    r = requests.post(API_URL, json=payload, timeout=10)
                    r.raise_for_status()
                    result = r.json()
                    results.append({
                        "probability": result.get("probability"),
                        "prediction": result.get("prediction"),
                        "threshold": result.get("threshold"),
                        "timestamp": result.get("timestamp"),
                    })
                except Exception as e:
                    results.append({"error": str(e)})
                progress.progress((i + 1) / len(df))

            progress.empty()
            out = pd.DataFrame(results)
            st.success("✅ 배치 예측 완료")
            st.dataframe(out)

            if "prediction" in out.columns:
                col1, col2, col3 = st.columns(3)
                total = len(out)
                purchase = (out["prediction"] == 1).sum()
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
st.caption("🚀 고객 구매 예측 시스템 (Production v5.0, 프리셋 연동 버전)")
