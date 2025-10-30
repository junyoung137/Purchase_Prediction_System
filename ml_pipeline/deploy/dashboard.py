# =====================================================
# dashboard.py (확장 사이드바 버전)
# =====================================================
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time  

# =========================================
# 🔧 API 설정
# =========================================
API_URL = "https://purchase-prediction-system.onrender.com/predict"

st.set_page_config(page_title="🛍️ 실시간 구매 가능성 예측", layout="wide")
st.title("🛍️ 실시간 구매 가능성 예측")

# =========================================
# 📊 사이드바: 프리셋
# =========================================
st.sidebar.header("📊 빠른 분석")
st.sidebar.subheader("🎯 고객 프로필 프리셋")

preset_profiles = {
    "🔥 고관심 고객": {
        "total_visits": 15.0, "total_events": 50.0, "product_views": 30.0,
        "cart_adds": 5.0, "purchases": 4.0, "last_activity_days": 2.0,
        "activity_freq": 20.0, "avg_session_time": 12.0,
        "review_count": 3.0, "discount_views": 10.0,
    },
    "⚠️ 이탈 위험 고객": {
        "total_visits": 3.0, "total_events": 8.0, "product_views": 5.0,
        "cart_adds": 0.0, "purchases": 0.0, "last_activity_days": 30.0,
        "activity_freq": 2.0, "avg_session_time": 2.0,
        "review_count": 0.0, "discount_views": 1.0,
    },
    "💚 신규 방문자": {
        "total_visits": 1.0, "total_events": 12.0, "product_views": 8.0,
        "cart_adds": 1.0, "purchases": 0.0, "last_activity_days": 0.0,
        "activity_freq": 3.0, "avg_session_time": 5.0,
        "review_count": 0.0, "discount_views": 2.0,
    },
    "🎁 재구매 고객": {
        "total_visits": 25.0, "total_events": 40.0, "product_views": 20.0,
        "cart_adds": 3.0, "purchases": 3.0, "last_activity_days": 7.0,
        "activity_freq": 15.0, "avg_session_time": 10.0,
        "review_count": 5.0, "discount_views": 8.0,
    }
}

selected_preset = st.sidebar.selectbox(
    "프로필 선택", ["선택 안함"] + list(preset_profiles.keys())
)

# ✅ 프리셋 적용 버튼
if selected_preset != "선택 안함":
    if st.sidebar.button("📋 값 적용하기", use_container_width=True):
        for k, v in preset_profiles[selected_preset].items():
            st.session_state[k] = v
        st.sidebar.success(f"✅ '{selected_preset}' 값 적용 완료!")
        st.rerun()

st.sidebar.markdown("---")

# =========================================
# ⬆️ 추가됨: 프로필 요약 카드
# =========================================
if selected_preset != "선택 안함":
    preset = preset_profiles[selected_preset]
    st.sidebar.markdown("### 📌 현재 선택된 프로필 요약")
    st.sidebar.info(
        f"""
        - 🧭 총 방문: **{preset['total_visits']}회**  
        - 🛒 장바구니: **{preset['cart_adds']}회**  
        - 💳 결제 완료: **{preset['purchases']}회**  
        - ⏰ 최근 활동: **{preset['last_activity_days']}일 전**
        """
    )

# =========================================
# ⬆️ 추가됨: 세그먼트 배지
# =========================================
if selected_preset != "선택 안함":
    color_map = {
        "🔥 고관심 고객": "#f97316",
        "⚠️ 이탈 위험 고객": "#dc2626",
        "💚 신규 방문자": "#16a34a",
        "🎁 재구매 고객": "#2563eb"
    }
    color = color_map.get(selected_preset, "#6b7280")
    st.sidebar.markdown(
        f"<div style='background-color:{color}; padding:8px; border-radius:8px; text-align:center; color:white;'>"
        f"<b>{selected_preset}</b></div>", unsafe_allow_html=True
    )

# =========================================
# ⬆️ 추가됨: 서버 상태 표시
# =========================================
with st.sidebar.expander("🧠 시스템 상태"):
    st.write("모델 버전: **v5.0**")
    try:
        res = requests.get("https://purchase-prediction-system.onrender.com/health", timeout=3)
        if res.status_code == 200:
            st.success("✅ 서버 온라인")
        else:
            st.warning("⚠️ 서버 응답 지연")
    except:
        st.error("❌ 서버 오프라인")


# =========================================
# ⬆️ 추가됨: 최근 예측 로그
# =========================================
if "log" not in st.session_state:
    st.session_state["log"] = []

with st.sidebar.expander("🕒 최근 예측 기록"):
    if len(st.session_state["log"]) == 0:
        st.write("아직 예측 기록이 없습니다.")
    else:
        for entry in st.session_state["log"][-5:]:
            st.write(f"- {entry['time']} | {entry['preset']}")

st.sidebar.markdown("---")

# =========================================
# 🌙 라이트 모드 & 다크 모드
# =========================================
import streamlit as st

# ==========================================
# 🔹 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="실시간 구매 가능성 예측", page_icon="🛍️", layout="centered")

# ==========================================
# 🔹 스타일 커스터마이징 (버튼 포함)
# ==========================================
st.markdown("""
<style>
/* ==========================================
   🧭 전체 페이지 기본 스타일
   ========================================== */
body {
    background-color: #0e1525;
    color: #ffffff;
}

/* ==========================================
   🔍 예측 실행 버튼 스타일
   ========================================== */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important; /* 💙 파란색 그라데이션 */
    color: white !important; /* ✅ 텍스트 흰색 고정 */
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7em 2.5em !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 3px 10px rgba(37,99,235,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
}

div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #1e40af, #1d4ed8) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(37,99,235,0.5);
}

/* ==========================================
   🧾 제목 및 본문 스타일
   ========================================== */
h1, h2, h3 {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔹 앱 제목 및 설명
# ==========================================
st.markdown("### 🛍️ 실시간 구매 가능성 예측")
st.write("고객 세션의 주요 활동 정보를 입력하여 구매 확률을 예측합니다.")

# ==========================================
# 🔹 입력 폼 구성
# ==========================================
col1, col2 = st.columns(2)
with col1:
    visits = st.number_input("총 방문 횟수", min_value=0.0, step=1.0)
    events = st.number_input("전체 이벤트 수", min_value=0.0, step=1.0)
with col2:
    views = st.number_input("상품 조회 수", min_value=0.0, step=1.0)
    carts = st.number_input("장바구니 담기 수", min_value=0.0, step=1.0)

# ==========================================
# 🔹 예측 실행 버튼
# ==========================================
if st.button("🔍 예측 실행"):
    st.success("✅ 예측이 완료되었습니다! (샘플 결과: 구매 확률 78%)")

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
# 🔍 예측 실행
# =========================================
if st.button("🔍 예측 실행", use_container_width=True):
    payload = {
        "feature_1": float(st.session_state.get("total_visits", 0)),
        "feature_2": float(max(st.session_state.get("total_events", 1.0), 1.0)),
        "feature_3": float(st.session_state.get("product_views", 0)),
        "feature_4": float(st.session_state.get("cart_adds", 0)),
        "feature_5": float(st.session_state.get("purchases", 0)),
        "feature_6": float(st.session_state.get("purchases", 0)) / max(float(st.session_state.get("total_events", 1.0)), 1.0),
        "feature_7": float(st.session_state.get("product_views", 0)) / max(float(st.session_state.get("total_events", 1.0)), 1.0),
    }

    success, result = False, None
    for attempt in range(1, 4):
        try:
            with st.spinner(f"⏳ 서버와 통신 중... (시도 {attempt}/3)"):
                res = requests.post(API_URL, json=payload, timeout=10)
                res.raise_for_status()
                result = res.json()
                success = True
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < 3:
                st.info("⚙️ 서버 초기화 중... 10초 후 재시도합니다.")
                time.sleep(10)
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
            break

    if success and result:
        prob = result.get("probability", 0)
        pred = result.get("prediction", 0)
        threshold = result.get("threshold", 0.5)
        label = "✅ 구매 예상" if pred == 1 else "❌ 비구매 예상"

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("예측 결과", label)
        col_b.metric("구매 확률", f"{prob:.2%}")
        col_c.metric("Threshold", f"{threshold:.2f}")

        # ⬆️ 로그 저장
        st.session_state["log"].append({
            "preset": selected_preset,
            "time": time.strftime("%H:%M:%S")
        })

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
        st.success("✅ 예측 완료!")

st.caption("💡 첫 실행 시 서버 초기화로 1분가량 지연될 수 있습니다.")

# =========================================
# 2️⃣ 배치 예측 (CSV)
# =========================================
st.markdown("---")
st.markdown("### 2️⃣ 대량 고객 구매 가능성 예측 (CSV 업로드)")
st.info("""
📋 **CSV 업로드 안내:**
- 각 행은 1명의 고객 세션입니다.
- 고객별 주요 활동 데이터를 포함해야 합니다.
""")

with st.expander("📘 컬럼 정의"):
    st.markdown("""
    | 컬럼명 | 설명 |
    |:--------|:--------------------------------------------|
    | `session_id` | 고객 세션 ID |
    | `event_count` | 전체 이벤트 수 |
    | `n_view` | 상품 조회 수 |
    | `n_cart` | 장바구니 담기 수 |
    | `n_trans` | 결제 완료 수 |
    | `n_trans_ratio` | 결제 전환율 |
    | `n_view_ratio` | 조회 비율 |
    """)

uploaded = st.file_uploader("📂 CSV 파일 업로드", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.dataframe(df.head(), use_container_width=True)
    req_cols = ["session_id","event_count","n_view","n_cart","n_trans","n_trans_ratio","n_view_ratio"]
    miss = set(req_cols) - set(df.columns)
    if miss:
        st.error(f"❌ 누락된 컬럼: {miss}")
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
                rate = purchase / total * 100
                avg_prob = out["probability"].mean()
                high_p = (out["probability"] > 0.7).sum()
                col1.metric("전체 건수", f"{total:,}명")
                col2.metric("구매 예상", f"{purchase:,}명 ({rate:.1f}%)")
                col3.metric("평균 구매 확률", f"{avg_prob:.1%}")
                if high_p > 0:
                    st.success(f"🎯 고확률 고객(70% 이상): **{high_p}명**")
            csv_data = out.to_csv(index=False).encode("utf-8")
            st.download_button("📥 결과 다운로드", csv_data, "predictions.csv", "text/csv")

# =========================================
# 푸터
# =========================================
st.markdown("---")
st.caption("🚀 고객 구매 예측 시스템 (Production v5.0)")

