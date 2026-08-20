import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, time, timedelta

# ---------------------------------------------------------
# 마미톡(MomiTalk) 스타일 감성 모바일 UI 테마 적용
# ---------------------------------------------------------
st.set_page_config(
    page_title="마미톡 스타일 우리 아이 기록장",
    page_icon="🍼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
        background-color: #F8F9FA;
    }
    
    /* 상단 아기 프로필 배너 */
    .baby-profile-card {
        background: linear-gradient(135deg, #FF8E9E 0%, #FFB6C1 100%);
        border-radius: 20px;
        padding: 22px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(255, 142, 158, 0.25);
        margin-bottom: 20px;
    }
    .baby-profile-card h2 {
        color: white;
        margin: 0;
        font-size: 24px;
        font-weight: 700;
    }
    .baby-profile-card p {
        margin: 5px 0 0 0;
        font-size: 15px;
        opacity: 0.95;
    }

    /* 오늘 요약 통계 대시보드 */
    .summary-container {
        display: flex;
        justify-content: space-between;
        background: white;
        border-radius: 16px;
        padding: 16px 12px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        text-align: center;
    }
    .summary-item {
        flex: 1;
        border-right: 1px solid #F0F0F0;
    }
    .summary-item:last-child {
        border-right: none;
    }
    .summary-val {
        font-size: 18px;
        font-weight: 700;
        color: #333;
    }
    .summary-lbl {
        font-size: 12px;
        color: #888;
        margin-top: 3px;
    }

    /* 타임라인 카드 디자인 */
    .timeline-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #F1F3F5;
    }
    .type-badge-sleep { background-color: #E8EEFF; color: #4A72FF; }
    .type-badge-meal { background-color: #FFF3E5; color: #FF922B; }
    .type-badge-milk { background-color: #E6FCF5; color: #20C997; }
    .type-badge-pee { background-color: #EBFBEE; color: #40C057; }
    .type-badge-poo { background-color: #F3F0FF; color: #7950F2; }

    .badge-icon {
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        margin-right: 14px;
    }
    
    /* 폼 입력 버튼 */
    div.stButton > button:first-child {
        border-radius: 14px;
        font-weight: 600;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 구글 시트 웹앱 API 연동
# ---------------------------------------------------------
API_URL = "https://script.google.com/macros/s/AKfycby3sVLC2WBVKgNWTmeSnuWa7G_P04FLFPi7PEic65Sg6xRy5YSS4P9SlyF6Nvq1cNXnzw/exec"

def load_records():
    """구글 시트에서 실시간 데이터 읽기"""
    try:
        res = requests.get(API_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                for col in ["date", "type", "start_time", "end_time", "memo", "created_at"]:
                    if col not in df.columns:
                        df[col] = "-"
                df["date"] = df["date"].astype(str).str.slice(0, 10)
                df["start_time"] = df["start_time"].astype(str).str.strip()
                df["end_time"] = df["end_time"].astype(str).str.strip()
                df["created_at"] = df["created_at"].astype(str).str.strip()
                return df
        return pd.DataFrame(columns=["date", "type", "start_time", "end_time", "memo", "created_at"])
    except Exception:
        return pd.DataFrame(columns=["date", "type", "start_time", "end_time", "memo", "created_at"])

def add_record(record_dict):
    """구글 시트에 새 기록 추가"""
    try:
        record_dict["action"] = "add"
        res = requests.post(API_URL, json=record_dict, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def delete_record(created_at_val):
    """구글 시트에서 기록 삭제"""
    try:
        payload = {"action": "delete", "created_at": created_at_val}
        res = requests.post(API_URL, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# 2. 아기 프로필 계산
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    birth_date = st.date_input("생년월일", value=date(2025, 12, 1))
    allergies = st.text_input("주의 음식 / 알레르기", placeholder="예: 계란, 우유, 복숭아")

today = date.today()
days_passed = (today - birth_date).days
months_passed = days_passed // 30

# 상단 마미톡 스타일 프로필 배너
st.markdown(f"""
<div class="baby-profile-card">
    <h2>🍼 우리 아이</h2>
    <p><strong>생후 {days_passed}일차</strong> ({months_passed}개월)</p>
    {f'<p style="font-size:13px; margin-top:6px; background:rgba(0,0,0,0.1); border-radius:10px; padding:3px 8px; display:inline-block;">⚠️ 알레르기: {allergies}</p>' if allergies else ''}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 마미톡 퀵 탭 UI
# ---------------------------------------------------------
tab_today, tab_input, tab_guide = st.tabs(["📋 오늘 타임라인", "✏️ 기록하기", "📖 권장 일과표"])

# 데이터 로드
df_records = load_records()
today_str = today.strftime("%Y-%m-%d")

with tab_today:
    # 날짜 이동/선택
    c_date, c_space = st.columns([1.5, 1])
    with c_date:
        selected_date = st.date_input("📅 날짜 선택", value=today, label_visibility="collapsed")
    target_date_str = selected_date.strftime("%Y-%m-%d")

    # 오늘 통계 집계
    day_df = pd.DataFrame()
    if not df_records.empty:
        day_df = df_records[df_records["date"] == target_date_str].copy()

    # 요약 통계 계산
    sleep_cnt = len(day_df[day_df["type"] == "수면"]) if not day_df.empty else 0
    meal_cnt = len(day_df[day_df["type"] == "이유식"]) if not day_df.empty else 0
    milk_cnt = len(day_df[day_df["type"] == "모유 수유"]) if not day_df.empty else 0
    diaper_cnt = len(day_df[day_df["type"].isin(["소변", "대변"])]) if not day_df.empty else 0

    # 마미톡 스타일 통계 요약 박스
    st.markdown(f"""
    <div class="summary-container">
        <div class="summary-item">
            <div class="summary-val" style="color:#4A72FF;">{sleep_cnt}회</div>
            <div class="summary-lbl">수면</div>
        </div>
        <div class="summary-item">
            <div class="summary-val" style="color:#FF922B;">{meal_cnt}회</div>
            <div class="summary-lbl">이유식</div>
        </div>
        <div class="summary-item">
            <div class="summary-val" style="color:#20C997;">{milk_cnt}회</div>
            <div class="summary-lbl">모유</div>
        </div>
        <div class="summary-item">
            <div class="summary-val" style="color:#7950F2;">{diaper_cnt}회</div>
            <div class="summary-lbl">기저귀</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 타임라인 리스트 렌더링
    if not day_df.empty:
        day_df = day_df.sort_values(by=["start_time"])
        
        type_meta = {
            "수면": {"icon": "💤", "badge": "type-badge-sleep"},
            "이유식": {"icon": "🥣", "badge": "type-badge-meal"},
            "모유 수유": {"icon": "🤱", "badge": "type-badge-milk"},
            "소변": {"icon": "💧", "badge": "type-badge-pee"},
            "대변": {"icon": "💩", "badge": "type-badge-poo"}
        }

        for idx, row in day_df.iterrows():
            meta = type_meta.get(row['type'], {"icon": "📝", "badge": "type-badge-sleep"})
            time_text = row['start_time']
            if row['end_time'] != "-":
                time_text += f" ~ {row['end_time']}"

            col_card, col_del = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
                <div class="timeline-card">
                    <div class="badge-icon {meta['badge']}">{meta['icon']}</div>
                    <div style="flex-grow:1;">
                        <div style="font-size:15px; font-weight:700; color:#212529;">
                            {row['type']} <span style="font-size:13px; font-weight:500; color:#868E96; margin-left:6px;">{time_text}</span>
                        </div>
                        <div style="font-size:13px; color:#495057; margin-top:3px;">
                            {row['memo']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                st.write("")
                st.write("")
                if st.button("삭제", key=f"del_{row['created_at']}_{idx}", use_container_width=True):
                    if delete_record(row['created_at']):
                        st.rerun()
    else:
        st.info(f"💡 {target_date_str}의 첫 기록을 남겨보세요!")

with tab_input:
    st.markdown("#### ✏️ 빠른 육아 기록")
    
    # 마미톡 감성의 직관적인 기록 폼
    with st.form("quick_record_form", clear_on_submit=True):
        record_type = st.radio(
            "기록 유형 선택",
            ["수면", "이유식", "모유 수유", "소변", "대변"],
            horizontal=True
        )
        
        c1, c2 = st.columns(2)
        with c1:
            rec_date = st.date_input("날짜", value=today)
            rec_start_time = st.time_input("시작(또는 발생) 시간", value=datetime.now().time())
        with c2:
            has_end_time = st.checkbox("종료 시간 입력", value=(record_type == "수면"))
            rec_end_time = st.time_input("종료 시간", value=(datetime.now() + timedelta(minutes=40)).time())
                
        rec_memo = st.text_input("메모", placeholder="예: 140ml 완밥, 낮잠 잘 잠, 상태 양호 등")
        
        submitted = st.form_submit_button("기록 저장하기 ✨", type="primary", use_container_width=True)
        if submitted:
            new_entry = {
                "date": rec_date.strftime("%Y-%m-%d"),
                "type": record_type,
                "start_time": rec_start_time.strftime("%H:%M"),
                "end_time": rec_end_time.strftime("%H:%M") if has_end_time else "-",
                "memo": rec_memo if rec_memo else "-",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with st.spinner("저장 중..."):
                if add_record(new_entry):
                    st.success("기록이 성공적으로 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("저장 실패. 구글 시트 연결을 확인하세요.")

with tab_guide:
    st.markdown("#### 📖 권장 24시간 일과 패턴")
    st.caption("우리 아이 기준 루틴 (5:51 기상 패턴)")
    
    STANDARD_ROUTINE = [
        ("05:51", "06:12", "첫 모유 수유", "🤱"),
        ("06:12", "07:23", "아침 놀이 1", "🧸"),
        ("07:23", "08:07", "낮잠 1", "💤"),
        ("08:07", "08:30", "기상 후 놀이", "🧸"),
        ("08:30", "09:00", "이유식 1차", "🥣"),
        ("09:00", "10:30", "오전 놀이 2", "🧸"),
        ("10:30", "11:10", "낮잠 2", "💤"),
        ("11:10", "11:30", "놀이", "🧸"),
        ("11:30", "12:00", "이유식 2차 (점심)", "🥣"),
        ("12:00", "13:40", "놀이 및 산책", "🛝"),
        ("13:40", "15:10", "낮잠 3", "💤"),
        ("15:10", "15:30", "놀이", "🧸"),
        ("15:30", "15:40", "모유 수유", "🤱"),
        ("15:40", "16:30", "놀이", "🧸"),
        ("16:30", "17:00", "오후 간식", "🍎"),
        ("17:00", "18:00", "놀이", "🧸"),
        ("18:00", "18:30", "이유식 3차 (저녁)", "🥣"),
        ("18:30", "19:10", "놀이 및 정리", "🧸"),
        ("19:10", "19:20", "목욕", "🛁"),
        ("19:20", "19:30", "막수 (모유)", "🤱"),
        ("19:30", "20:00", "수면 의식 / 재우기", "📖"),
        ("20:00", "-", "밤잠 취침", "🌙")
    ]
    
    routine_df = pd.DataFrame([
        {"시작": s, "종료": e, "활동": f"{icon} {title}"}
        for s, e, title, icon in STANDARD_ROUTINE
    ])
    st.dataframe(routine_df, use_container_width=True, hide_index=True)
