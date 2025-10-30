# =========================================
# 🌙 라이트 모드 & 다크 모드
# =========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🎨 테마 설정")

# ✅ 기본값: 다크 모드
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# ✅ 토글 버튼
toggle_label = "🌞 라이트 모드로 전환" if st.session_state["theme"] == "dark" else "🌙 다크 모드로 전환"
if st.sidebar.button(toggle_label, use_container_width=True):
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
    st.rerun()

theme = st.session_state["theme"]

# =========================================
# 🌙 다크 / 라이트 모드 스타일 정의
# =========================================
if theme == "dark":
    st.markdown("""
        <style>
        /* ===== 전체 영역 ===== */
        .stApp {
            background-color: #1a1b1e !important;
            color: #f3f4f6 !important;
        }

        /* ===== 메인 컨텐츠 영역 배경 ===== */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            background-color: #1a1b1e !important;
        }

        /* ===== 입력 필드 컨테이너 (카드 스타일) ===== */
        [data-testid="stNumberInput"] {
            background-color: #25262b !important;
            padding: 12px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.2s ease-in-out !important;
        }

        [data-testid="stNumberInput"]:hover {
            border-color: rgba(59, 90, 214, 0.4) !important;
            box-shadow: 0 4px 12px rgba(59, 90, 214, 0.15) !important;
        }

        /* ===== 입력 필드 라벨 ===== */
        [data-testid="stNumberInput"] label {
            color: #e5e7eb !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            margin-bottom: 6px !important;
        }

        /* ===== 입력 필드 input ===== */
        [data-testid="stNumberInput"] input {
            background-color: #1a1b1e !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            font-size: 15px !important;
            font-weight: 500 !important;
        }

        [data-testid="stNumberInput"] input:focus {
            border-color: #3b5ad6 !important;
            box-shadow: 0 0 0 2px rgba(59, 90, 214, 0.2) !important;
        }

        /* ===== 입력 필드 버튼 (+/-) ===== */
        [data-testid="stNumberInput"] button {
            background-color: #2f323c !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 4px !important;
        }

        [data-testid="stNumberInput"] button:hover {
            background-color: #3a3d48 !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }

        /* ===== 파일 업로더 스타일링 ===== */
        [data-testid="stFileUploader"] {
            background-color: #25262b !important;
            border: 2px dashed rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            padding: 20px !important;
        }

        [data-testid="stFileUploader"] section {
            background-color: transparent !important;
            border: none !important;
        }

        [data-testid="stFileUploader"] label,
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploader"] p,
        [data-testid="stFileUploader"] span {
            color: #e5e7eb !important;
        }

        [data-testid="stFileUploader"] button {
            background-color: #3b5ad6 !important;
            color: #ffffff !important;
            border: none !important;
            padding: 8px 16px !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }

        [data-testid="stFileUploader"] button:hover {
            background-color: #4c6ef5 !important;
        }

        /* ===== 사이드바 ===== */
        section[data-testid="stSidebar"] {
            background-color: #1f2028 !important;
            color: #e5e7eb !important;
            border-right: 1px solid rgba(255,255,255,0.05) !important;
        }

        /* ===== 사이드바 배지 스타일 개선 ===== */
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="background-color"] {
            opacity: 0.9 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        }

        /* ===== Selectbox (드롭다운) - 전체 강제 스타일 ===== */
        
        /* 메인 selectbox 컨테이너 */
        [data-testid="stSelectbox"] div[data-baseweb="select"],
        div[data-baseweb="select"] {
            background-color: #2f323c !important;
        }
        
        /* selectbox 내부 div */
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-baseweb="select"] > div {
            background-color: #2f323c !important;
            color: #ffffff !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 6px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.25) !important;
        }

        /* 선택된 값 및 placeholder */
        [data-testid="stSelectbox"] [class*="ValueContainer"],
        [data-testid="stSelectbox"] [class*="singleValue"],
        [data-testid="stSelectbox"] [class*="placeholder"],
        div[data-baseweb="select"] [class*="ValueContainer"],
        div[data-baseweb="select"] [class*="singleValue"],
        div[data-baseweb="select"] [class*="placeholder"] {
            color: #ffffff !important;
        }

        /* 모든 하위 텍스트 강제 흰색 */
        [data-testid="stSelectbox"] *,
        div[data-baseweb="select"] * {
            color: #ffffff !important;
        }

        /* 드롭다운 메뉴 (열렸을 때) */
        ul[role="listbox"],
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        [data-baseweb="popover"] {
            background-color: #2f323c !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        }

        /* 드롭다운 각 항목 - 기본 */
        ul[role="listbox"] li,
        div[role="option"],
        [role="option"] {
            color: #ffffff !important;
            background-color: #2f323c !important;
            font-weight: 500 !important;
            padding: 8px 12px !important;
        }

        /* 항목 내 모든 텍스트 */
        ul[role="listbox"] li *,
        div[role="option"] *,
        [role="option"] * {
            color: #ffffff !important;
        }

        /* hover 상태 */
        ul[role="listbox"] li:hover,
        div[role="option"]:hover,
        [role="option"]:hover {
            background-color: #3a3d48 !important;
            color: #ffffff !important;
        }

        ul[role="listbox"] li:hover *,
        div[role="option"]:hover *,
        [role="option"]:hover * {
            color: #ffffff !important;
        }

        /* 선택된 항목 */
        ul[role="listbox"] li[aria-selected="true"],
        div[role="option"][aria-selected="true"],
        [role="option"][aria-selected="true"] {
            background-color: #4b5563 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        ul[role="listbox"] li[aria-selected="true"] *,
        div[role="option"][aria-selected="true"] *,
        [role="option"][aria-selected="true"] * {
            color: #ffffff !important;
        }

        /* 비활성 항목 */
        ul[role="listbox"] li[aria-disabled="true"],
        [role="option"][aria-disabled="true"] {
            color: #9ca3af !important;
            opacity: 0.6;
        }

        /* ===== 텍스트 ===== */
        h1, h2, h3, h4, h5, h6 {
            color: #f3f4f6 !important;
            font-weight: 700 !important;
        }
        
        p, span, label, li {
            color: #e5e7eb !important;
        }

        /* ===== Metric 카드 스타일링 ===== */
        [data-testid="stMetric"] {
            background-color: #25262b !important;
            padding: 16px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        }

        [data-testid="stMetric"] label {
            color: #9ca3af !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 24px !important;
            font-weight: 700 !important;
        }

        /* ===== Expander 스타일링 ===== */
        [data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
        }

        /* ===== 정보 박스 스타일링 ===== */
        .stInfo, [data-testid="stInfo"] {
            background-color: #eff6ff !important;
            border-left: 4px solid #3b82f6 !important;
            color: #1e40af !important;
        }

        .stSuccess, [data-testid="stSuccess"] {
            background-color: #f0fdf4 !important;
            border-left: 4px solid #22c55e !important;
            color: #15803d !important;
        }

        .stWarning, [data-testid="stWarning"] {
            background-color: #fffbeb !important;
            border-left: 4px solid #f59e0b !important;
            color: #92400e !important;
        }

        .stError, [data-testid="stError"] {
            background-color: #fef2f2 !important;
            border-left: 4px solid #ef4444 !important;
            color: #991b1b !important;
        }

        /* ===== Selectbox ===== */
        div.stButton > button {
            background-color: #3b5ad6 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            transition: background-color 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #4c6ef5 !important;
        }

        /* ✅ caption 텍스트는 밝은 회색으로 (경고 메시지 가독성) */
        .stCaption, 
        [data-testid="stCaption"],
        small {
            color: #e5e7eb !important;
            font-weight: 500 !important;
        }

        /* ===== Expander 스타일링 ===== */
        [data-testid="stExpander"] {
            background-color: #25262b !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
        }

        /* ===== 정보 박스 스타일링 ===== */
        .stInfo, [data-testid="stInfo"] {
            background-color: #1e3a5f !important;
            border-left: 4px solid #3b82f6 !important;
            color: #e0e7ff !important;
        }

        .stSuccess, [data-testid="stSuccess"] {
            background-color: #1e4620 !important;
            border-left: 4px solid #22c55e !important;
            color: #dcfce7 !important;
        }

        .stWarning, [data-testid="stWarning"] {
            background-color: #4a3510 !important;
            border-left: 4px solid #f59e0b !important;
            color: #fef3c7 !important;
        }

        .stError, [data-testid="stError"] {
            background-color: #4a1515 !important;
            border-left: 4px solid #ef4444 !important;
            color: #fee2e2 !important;
        }

        /* ✅ 사이드바 내 전환 버튼 (다크모드: 은은한 밝은 톤) */
        section[data-testid="stSidebar"] div.stButton > button {
            background-color: #4b5563 !important;
            color: #e5e7eb !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1px solid #6b7280 !important;
            transition: all 0.25s ease-in-out;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        section[data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #6b7280 !important;
            border-color: #9ca3af !important;
            color: #f9fafb !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.25);
        }
        
        /* 버튼 텍스트 강제 적용 */
        section[data-testid="stSidebar"] div.stButton > button * {
            color: #e5e7eb !important;
        }
        
        section[data-testid="stSidebar"] div.stButton > button:hover * {
            color: #f9fafb !important;
        }

        /* ===== 구분선 ===== */
        section[data-testid="stSidebar"] hr {
            border-top: 1px solid rgba(255,255,255,0.08) !important;
            margin: 1rem 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
        <style>
        /* ===== 전체 영역 ===== */
        .stApp {
            background-color: #f9fafb !important;
            color: #111827 !important;
            font-family: 'Pretendard', 'Inter', sans-serif;
        }

        /* ===== 메인 컨텐츠 영역 배경 ===== */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            background-color: #f9fafb !important;
        }

        /* ===== 입력 필드 컨테이너 (카드 스타일) ===== */
        [data-testid="stNumberInput"] {
            background-color: #ffffff !important;
            padding: 12px !important;
            border-radius: 8px !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.2s ease-in-out !important;
        }

        [data-testid="stNumberInput"]:hover {
            border-color: rgba(59, 130, 246, 0.3) !important;
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.1) !important;
        }

        /* ===== 입력 필드 라벨 ===== */
        [data-testid="stNumberInput"] label {
            color: #374151 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            margin-bottom: 6px !important;
        }

        /* ===== 입력 필드 input ===== */
        [data-testid="stNumberInput"] input {
            background-color: #f9fafb !important;
            color: #111827 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            font-size: 15px !important;
            font-weight: 500 !important;
        }

        [data-testid="stNumberInput"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
            background-color: #ffffff !important;
        }

        /* ===== 입력 필드 버튼 (+/-) ===== */
        [data-testid="stNumberInput"] button {
            background-color: #f3f4f6 !important;
            color: #374151 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 4px !important;
        }

        [data-testid="stNumberInput"] button:hover {
            background-color: #e5e7eb !important;
            border-color: #9ca3af !important;
            color: #111827 !important;
        }

        /* ===== 사이드바 ===== */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc !important;
            border-right: 1px solid #e5e7eb !important;
        }

        /* ===== 제목 및 텍스트 ===== */
        h1, h2, h3, h4, h5, h6, label, p, span, li {
            color: #111827 !important;
            font-weight: 600 !important;
        }

        /* ✅ caption 텍스트 (경고 메시지) */
        .stCaption, 
        [data-testid="stCaption"],
        small {
            color: #374151 !important;
            font-weight: 500 !important;
        }

        /* ===== Metric 카드 스타일링 ===== */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            padding: 16px !important;
            border-radius: 8px !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        }

        [data-testid="stMetric"] label {
            color: #6b7280 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #111827 !important;
            font-size: 24px !important;
            font-weight: 700 !important;
        }

        /* ===== 파일 업로더 스타일링 ===== */
        [data-testid="stFileUploader"] {
            background-color: #ffffff !important;
            border: 2px dashed #d1d5db !important;
            border-radius: 8px !important;
            padding: 20px !important;
        }

        [data-testid="stFileUploader"] section {
            background-color: transparent !important;
            border: none !important;
        }

        [data-testid="stFileUploader"] label,
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploader"] p,
        [data-testid="stFileUploader"] span {
            color: #374151 !important;
        }

        [data-testid="stFileUploader"] button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border: none !important;
            padding: 8px 16px !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }

        [data-testid="stFileUploader"] button:hover {
            background-color: #2563eb !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #111827 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        /* ✅ selectbox 내 모든 텍스트 */
        div[data-baseweb="select"] * {
            color: #111827 !important;
        }
        
        ul[role="listbox"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
        }
        ul[role="listbox"] li {
            color: #111827 !important;
        }
        ul[role="listbox"] li * {
            color: #111827 !important;
        }
        ul[role="listbox"] li:hover {
            background-color: #f3f4f6 !important;
        }

        /* ===== 일반 버튼 ===== */
        div.stButton > button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            transition: all 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #1e40af !important;
        }
        
        /* ✅ 버튼 텍스트 강제 흰색 */
        div.stButton > button * {
            color: #ffffff !important;
        }

        /* ✅ 사이드바 전환 버튼 (라이트모드: 적당한 다크 톤) */
        section[data-testid="stSidebar"] div.stButton > button {
            background-color: #374151 !important;
            color: #f3f4f6 !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1px solid #4b5563 !important;
            transition: all 0.25s ease-in-out;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        section[data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #4b5563 !important;
            border-color: #6b7280 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        
        /* 버튼 텍스트 강제 적용 */
        section[data-testid="stSidebar"] div.stButton > button * {
            color: #f3f4f6 !important;
        }
        
        section[data-testid="stSidebar"] div.stButton > button:hover * {
            color: #ffffff !important;
        }

        /* ===== 구분선 ===== */
        section[data-testid="stSidebar"] hr {
            border-top: 1px solid #e5e7eb !important;
            margin: 1rem 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
