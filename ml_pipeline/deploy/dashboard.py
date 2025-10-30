# =====================================================
# dashboard.py 
# =====================================================
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

# =========================================
# 🔧 API 설정 (FastAPI 기준)
# =========================================
API_URL = "https://purchase-prediction-system.onrender.com/predict"

st.set_page_config(page_title="🛍️ 구매 예측 대시보드", layout="wide")
st.title("🛍️ 구매 예측 대시보드")

# 💡 초기 안내 메시지
st.info("💡 첫 실행 시 서버가 초기화 중일 수 있습니다. 최대 1분 정도 소요될 수 있습니다.")

# =========================================
# 📊 사이드바: 프리셋
# =========================================
st.sidebar.header("📊 빠른 분석")
st.sidebar.subheader("🎯 고객 프로필 프리셋")

preset_profiles = {
    "🔥 고관심 고객": {
        "total_visits": 15.0,
        "total_events": 50.0,
        "product_views": 30.0,
        "cart_adds": 5.0,
        "purchases": 4.0,
        "last_activity_days": 2.0,
        "activity_freq": 20.0,
        "avg_session_time": 12.0,
        "review_count": 3.0,
        "discount_views": 10.0,
    },
    "⚠️ 이탈 위험 고객": {
        "total_visits": 3.0,
        "total_events": 8.0,
        "product_views": 5.0,
        "cart_adds": 0.0,
        "purchases": 0.0,
        "last_activity_days": 30.0,
        "activity_freq": 2.0,
        "avg_session_time": 2.0,
        "review_count": 0.0,
        "discount_views": 1.0,
    },
    "💚 신규 방문자": {
        "total_visits": 1.0,
        "total_events": 12.0,
        "product_views": 8.0,
        "cart_adds": 1.0,
        "purchases": 0.0,
        "last_activity_days": 0.0,
        "activity_freq": 3.0,
        "avg_session_time": 5.0,
        "review_count": 0.0,
        "discount_views": 2.0,
    },
    "🎁 재구매 고객": {
        "total_visits": 25.0,
        "total_events": 40.0,
        "product_views": 20.0,
        "cart_adds": 3.0,
        "purchases": 3.0,
        "last_activity_days": 7.0,
        "activity_freq": 15.0,
        "avg_session_time": 10.0,
        "review_count": 5.0,
        "discount_views": 8.0,
    }
}

selected_preset = st.sidebar.selectbox(
    "프로필 선택",
    ["선택 안함"] + list(preset_profiles.keys())
)

# ✅ 프리셋 적용
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
st.markdown("고객 세션의 주요 활동 정보를 입력하여 구매 확률을 예측합니다.")

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.number_input("총 방문 횟수", min_value=0.0, step=0.1, key="total_visits")
    st.number_input("전체 이벤트 수", min_value=0.0, step=0.1, key="total_events")
    st.number_input("상품 조회 수", min_value=0.0, step=0.1, key="product_views")
    st.number_input("장바구니 담기 수", min_value=0.0, step=0.1, key="cart_adds")

with col2:
    st.number_input("결제 완료 수", min_value=0.0, step=0.1, key="purchases")
    st.number_input("마지막 활동 후 경과일", min_value=0.0, step=0.1, key="last_activity_days")
    st.number_input("활동 빈도", min_value=0.0, step=0.1, key="activity_freq")

with col3:
    st.number_input("평균 세션 시간 (분)", min_value=0.0, step=0.1, key="avg_session_time")
    st.number_input("리뷰 작성 수", min_value=0.0, step=0.1, key="review_count")
    st.number_input("할인 상품 조회", min_value=0.0, step=0.1, key="discount_views")

st.markdown("---")

# =========================================
# 🔍 예측 실행 버튼 (자동 재시도 포함)
# =========================================
if st.button("🔍 예측 실행", use_container_width=True):
    total_visits = float(st.session_state.get("total_visits", 0))
    total_events = max(float(st.session_state.get("total_events", 0)), 1.0)
    product_views = float(st.session_state.get("product_views", 0))
    cart_adds = float(st.session_state.get("cart_adds", 0))
    purchases = float(st.session_state.get("purchases", 0))

    payload = {
        "feature_1": total_visits,
        "feature_2": total_events,
        "feature_3": product_views,
        "feature_4": cart_adds,
        "feature_5": purchases,
        "feature_6": purchases / total_events,
        "feature_7": product_views / total_events,
    }

    max_retries = 3
    delay_sec = 10
    result = None
    success = False

    for attempt in range(1, max_retries + 1):
        try:
            with st.spinner(f"⏳ 서버와 통신 중... (시도 {attempt}/{max_retries})"):
                res = requests.post(API_URL, json=payload, timeout=10)
                res.raise_for_status()
                result = res.json()
                success = True
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < max_retries:
                st.info(f"⚙️ 서버가 아직 준비 중입니다. {delay_sec}초 후 다시 시도합니다...")
                time.sleep(delay_sec)
            else:
                st.warning("🚀 서버 초기화 중입니다. 잠시 후 다시 시도해주세요. (약 30~60초 소요될 수 있음)")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 서버 요청 중 오류가 발생했습니다: {e}")
            break
        except Exception as e:
            st.error(f"❌ 예측 실행 중 알 수 없는 오류가 발생했습니다: {e}")
            break

    # ✅ 예측 성공 시 결과 표시
    if success and result:
        prob = result.get("probability", 0)
        pred = result.get("prediction", 0)
        threshold = result.get("threshold", 0.5)
        label = "✅ 구매 예상" if pred == 1 else "❌ 비구매 예상"

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("예측 결과", label)
        col_b.metric("구매 확률", f"{prob:.2%}")
        col_c.metric("Threshold", f"{threshold:.2f}")
        st.success("✅ 예측이 성공적으로 완료되었습니다!")

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

with st.expander("📘 자세한 컬럼 정의 보기"):
    st.markdown("""
    | 컬럼명 | 설명 |
    |:--------|:--------------------------------------------|
    | `session_id` | 고객 세션 ID (총 방문 횟수) |
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
                payload = {
                    "feature_1": float(row["session_id"]),
                    "feature_2": float(row["event_count"]),
                    "feature_3": float(row["n_view"]),
                    "feature_4": float(row["n_cart"]),
                    "feature_5": float(row["n_trans"]),
                    "feature_6": float(row["n_trans_ratio"]),
                    "feature_7": float(row["n_view_ratio"])
                }
                try:
                    r = requests.post(API_URL, json=payload, timeout=10)
                    r.raise_for_status()
                    result = r.json()
                    results.append({
                        "probability": result.get("probability"),
                        "prediction": result.get("prediction"),
                        "threshold": result.get("threshold"),
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
st.caption("🚀 고객 구매 예측 시스템 (Production v5.0)")
