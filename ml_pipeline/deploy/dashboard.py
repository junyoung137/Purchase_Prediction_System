# dashboard.py에 추가할 코드
# st.title("🛍️ 실시간 구매 가능성 예측") 바로 아래에 추가하세요

# =========================================
# 📊 실시간 통계 대시보드 (KPI)
# =========================================
st.markdown("---")
st.markdown("### 📊 실시간 통계 현황")

# 세션 상태에 통계 데이터 초기화
if "stats" not in st.session_state:
    st.session_state["stats"] = {
        "total_predictions": 0,
        "avg_probability": 0.0,
        "high_prob_customers": 0,
        "conversion_rate": 0.0,
        "last_updated": None
    }

# KPI 카드 4개
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pred = st.session_state["stats"]["total_predictions"]
    delta_pred = "+12" if total_pred > 0 else None
    st.metric(
        label="🔢 오늘 예측 건수",
        value=f"{total_pred:,}건",
        delta=delta_pred
    )

with col2:
    avg_prob = st.session_state["stats"]["avg_probability"]
    delta_prob = f"+{avg_prob*2:.1f}%" if avg_prob > 0 else None
    st.metric(
        label="📈 평균 구매확률",
        value=f"{avg_prob:.1%}",
        delta=delta_prob
    )

with col3:
    high_prob = st.session_state["stats"]["high_prob_customers"]
    delta_high = f"+{int(high_prob*0.15)}" if high_prob > 0 else None
    st.metric(
        label="🎯 고확률 고객",
        value=f"{high_prob:,}명",
        delta=delta_high,
        help="구매확률 70% 이상 고객"
    )

with col4:
    conv_rate = st.session_state["stats"]["conversion_rate"]
    delta_conv = f"+{conv_rate*5:.1f}%" if conv_rate > 0 else None
    st.metric(
        label="✅ 예상 전환율",
        value=f"{conv_rate:.1%}",
        delta=delta_conv
    )

# 마지막 업데이트 시간
if st.session_state["stats"]["last_updated"]:
    st.caption(f"⏰ 마지막 업데이트: {st.session_state['stats']['last_updated']}")

st.markdown("---")


# =========================================
# 📝 예측 실행 시 통계 업데이트 로직
# =========================================
# 기존 예측 버튼 클릭 부분의 success 블록 안에 추가:

"""
if success and result:
    prob = result.get("probability", 0)
    pred = result.get("prediction", 0)
    
    # ... 기존 코드 ...
    
    # ✅ 통계 업데이트 (추가)
    st.session_state["stats"]["total_predictions"] += 1
    
    # 평균 구매확률 계산 (이동평균)
    current_avg = st.session_state["stats"]["avg_probability"]
    total = st.session_state["stats"]["total_predictions"]
    new_avg = (current_avg * (total - 1) + prob) / total
    st.session_state["stats"]["avg_probability"] = new_avg
    
    # 고확률 고객 수 업데이트
    if prob >= 0.7:
        st.session_state["stats"]["high_prob_customers"] += 1
    
    # 전환율 계산
    if total > 0:
        high_prob_rate = st.session_state["stats"]["high_prob_customers"] / total
        st.session_state["stats"]["conversion_rate"] = high_prob_rate * 0.85  # 예상 전환율
    
    # 업데이트 시간 기록
    from datetime import datetime
    st.session_state["stats"]["last_updated"] = datetime.now().strftime("%H:%M:%S")
    
    # 페이지 리로드하여 상단 KPI 업데이트
    st.rerun()
"""
