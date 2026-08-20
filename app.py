import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta

st.set_page_config(page_title="우리 아이 맞춤 스케줄러 & 기록장", page_icon="👶", layout="wide")

# ---------------------------------------------------------
# 세션 상태(Session State) 초기화 - 기록 저장용
# ---------------------------------------------------------
if "records" not in st.session_state:
    # 기본 더미 또는 빈 기록 리스트
    st.session_state.records = []

# ---------------------------------------------------------
# 1. 아기 기본 정보 및 패턴 정의
# ---------------------------------------------------------
st.sidebar.header("📋 아기 프로필")
birth_date = st.sidebar.date_input("생년월일", value=date(2025, 12, 1))
allergies = st.sidebar.text_input("못 먹는 음식 / 알레르기", placeholder="예: 계란, 우유, 밀가루")

today = date.today()
days_passed = (today - birth_date).days
months_passed = days_passed // 30

st.sidebar.markdown(f"**🌟 생후 {days_passed}일차 ({months_passed}개월)**")
if allergies:
    st.sidebar.warning(f"⚠️ 주의 음식: {allergies}")

# 월령별 놀이 DB
play_database = {
    (0, 3): ["초점책 보여주기", "모빌 보기", "터미타임 (1~2분)", "팔다리 마사지"],
    (4, 6): ["딸랑이 쥐어주기", "거울 놀이", "손수건 까꿍놀이", "촉감책 만지기"],
    (7, 9): ["짝짜꿍/잼잼 놀이", "장난감 숨겼다 찾기", "기어가기 유도 (터널/볼풀)", "이름 부르고 반응 보기"],
    (10, 12): ["컵 쌓기 놀이", "상자에 공 넣기", "잡고 서서 걷기 연습", "동물 소리 흉내내기"],
    (13, 24): ["낙서/크레파스 놀이", "간단한 퍼즐 맞추기", "블록 쌓기", "공 던지고 받기"]
}

current_plays = ["그림책 읽어주기", "자유 교감 놀이"]
for (start_m, end_m), plays in play_database.items():
    if start_m <= months_passed <= end_m:
        current_plays = plays
        break

# ---------------------------------------------------------
# 2. 사용자 입력 기본 일과 패턴 (상대 시간 간격 분 단위)
# 기준: 05:51 기상 (0분 기준)
# ---------------------------------------------------------
# 5:51 기상 (0분)
# 5:51~6:12 모유 (21분)
# 6:12~7:23 놀이 (71분) -> offset: 21, dur: 71
# 7:23~8:07 취침 (44분) -> offset: 92, dur: 44
# 8:07~8:30 놀이 (23분) -> offset: 136, dur: 23
# 8:30~9:00 이유식 (30분) -> offset: 159, dur: 30
# 9:00~10:30 놀이 (90분) -> offset: 189, dur: 90
# 10:30~11:10 취침 (40분) -> offset: 279, dur: 40
# 11:10~11:30 놀이 (20분) -> offset: 319, dur: 20
# 11:30~12:00 이유식 (30분) -> offset: 339, dur: 30
# 12:00~13:40 놀이 (100분) -> offset: 369, dur: 100
# 13:40~15:10 취침 (90분) -> offset: 469, dur: 90
# 15:10~15:30 놀이 (20분) -> offset: 559, dur: 20
# 15:30~15:40 모유 (10분) -> offset: 579, dur: 10
# 15:40~16:30 놀이 (50분) -> offset: 589, dur: 50
# 16:30~17:00 간식 (30분) -> offset: 639, dur: 30
# 17:00~18:00 놀이 (60분) -> offset: 669, dur: 60
# 18:00~18:30 이유식 (30분) -> offset: 729, dur: 30
# 18:30~19:10 놀이 (40분) -> offset: 759, dur: 40
# 19:10~19:20 목욕 (10분) -> offset: 799, dur: 10
# 19:20~19:30 모유 (10분) -> offset: 809, dur: 10
# 19:30~20:00 재우기 (30분) -> offset: 819, dur: 30
# 20:00 취침 (밤잠) -> offset: 849, dur: 0

DEFAULT_PATTERN = [
    {"offset": 0, "duration": 21, "title": "첫 모유 수유", "type": "모유 수유", "icon": "🤱"},
    {"offset": 21, "duration": 71, "title": "아침 놀이 1", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 92, "duration": 44, "title": "낮잠 1", "type": "수면", "icon": "💤"},
    {"offset": 136, "duration": 23, "title": "기상 후 놀이", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 159, "duration": 30, "title": "이유식 1차", "type": "이유식", "icon": "🥣"},
    {"offset": 189, "duration": 90, "title": "오전 놀이 2", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 279, "duration": 40, "title": "낮잠 2", "type": "수면", "icon": "💤"},
    {"offset": 319, "duration": 20, "title": "기상 후 놀이", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 339, "duration": 30, "title": "이유식 2차 (점심)", "type": "이유식", "icon": "🥣"},
    {"offset": 369, "duration": 100, "title": "오후 놀이 / 산책", "type": "놀이", "icon": "🛝", "is_play": True},
    {"offset": 469, "duration": 90, "title": "낮잠 3", "type": "수면", "icon": "💤"},
    {"offset": 559, "duration": 20, "title": "기상 후 놀이", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 579, "duration": 10, "title": "오후 모유 수유", "type": "모유 수유", "icon": "🤱"},
    {"offset": 589, "duration": 50, "title": "오후 놀이", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 639, "duration": 30, "title": "오후 간식", "type": "간식", "icon": "🍎"},
    {"offset": 669, "duration": 60, "title": "저녁 전 놀이", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 729, "duration": 30, "title": "이유식 3차 (저녁)", "type": "이유식", "icon": "🥣"},
    {"offset": 759, "duration": 40, "title": "저녁 놀이 및 정리", "type": "놀이", "icon": "🧸", "is_play": True},
    {"offset": 799, "duration": 10, "title": "목욕", "type": "목욕", "icon": "🛁"},
    {"offset": 809, "duration": 10, "title": "막수 (모유)", "type": "모유 수유", "icon": "🤱"},
    {"offset": 819, "duration": 30, "title": "수면 의식 / 재우기", "type": "수면준비", "icon": "📖"},
    {"offset": 849, "duration": 0, "title": "밤잠 취침", "type": "수면", "icon": "🌙"},
]

# ---------------------------------------------------------
# 레이아웃 구성 (좌측: 기록 입력 & 관리, 우측: 실시간 연동 타임라인)
# ---------------------------------------------------------
col_left, col_right = st.columns([1, 1.2], gap="large")

# =========================================================
# 좌측: 실시간 기록 및 데이터 관리
# =========================================================
with col_left:
    st.header("📝 실시간 육아 기록")
    
    with st.expander("➕ 새 기록 추가하기", expanded=True):
        record_type = st.selectbox("기록 유형", ["수면", "이유식", "모유 수유", "소변", "대변"])
        
        c1, c2 = st.columns(2)
        with c1:
            rec_date = st.date_input("날짜", value=today)
            rec_start_time = st.time_input("시작 시간 (또는 발생 시각)", value=datetime.now().time())
        with c2:
            # 수면이나 식사는 종료 시간이 있을 수 있음
            has_end_time = st.checkbox("종료 시간 있음 (수면/식사 등)", value=(record_type == "수면"))
            rec_end_time = None
            if has_end_time:
                rec_end_time = st.time_input("종료 시간", value=(datetime.now() + timedelta(minutes=40)).time())
                
        rec_memo = st.text_input("메모 (용량, 특이사항 등)", placeholder="예: 120ml 완밥, 대변 양호 등")
        
        if st.button("기록 저장하기", use_container_width=True, type="primary"):
            st.session_state.records.append({
                "date": rec_date,
                "type": record_type,
                "start_time": rec_start_time.strftime("%H:%M"),
                "end_time": rec_end_time.strftime("%H:%M") if (has_end_time and rec_end_time) else "-",
                "memo": rec_memo,
                "created_at": datetime.now()
            })
            st.success(f"{record_type} 기록이 저장되었습니다!")

    # 최근 기록 내역 표시
    st.subheader("📋 오늘의 기록 내역")
    if st.session_state.records:
        df_records = pd.DataFrame(st.session_state.records)
        st.dataframe(df_records[["type", "start_time", "end_time", "memo"]], use_container_width=True)
        if st.button("기록 전체 초기화"):
            st.session_state.records = []
            st.experimental_rerun()
    else:
        st.info("아직 등록된 기록이 없습니다. 위에서 기록을 남겨보세요.")

# =========================================================
# 우측: 기록 기반 동적 스케줄표 생성
# =========================================================
with col_right:
    st.header("⏰ 맞춤 실시간 스케줄표")
    
    # 1. 기준 기상 시간 설정 (가장 최근 수면 기록이 있다면 자동으로 반영할지 선택)
    latest_sleep = None
    for r in reversed(st.session_state.records):
        if r["type"] == "수면" and r["end_time"] != "-":
            latest_sleep = r
            break
            
    st.markdown("##### ⚙️ 일정 기준 시간 설정")
    use_auto_sync = st.checkbox("최근 수면/기상 기록으로 스케줄 자동 연동", value=True)
    
    default_wake = time(5, 51)
    if use_auto_sync and latest_sleep:
        try:
            h, m = map(int, latest_sleep["end_time"].split(":"))
            default_wake = time(h, m)
            st.info(f"🔄 최근 수면 종료 기록({latest_sleep['end_time']})을 기준으로 일정을 재계산합니다.")
        except:
            pass
            
    base_wake_time = st.time_input("오늘 시작(기상) 시간", value=default_wake)
    base_dt = datetime.combine(today, base_wake_time)
    
    st.write("---")
    st.subheader("📅 오늘 자동 재조정된 타임라인")
    
    play_idx = 0
    for idx, item in enumerate(DEFAULT_PATTERN):
        start_t = base_dt + timedelta(minutes=item["offset"])
        end_t = start_t + timedelta(minutes=item["duration"]) if item["duration"] > 0 else None
        
        t_str = start_t.strftime("%H:%M")
        if end_t:
            t_str += f" ~ {end_t.strftime('%H:%M')}"
            
        # UI 카드 스타일링
        with st.container():
            col_icon, col_content = st.columns([1, 8])
            with col_icon:
                st.markdown(f"### {item['icon']}")
            with col_content:
                st.markdown(f"**{t_str}** | **{item['title']}** ({item['type']})")
                if item.get("is_play", False) and current_plays:
                    play_tip = current_plays[play_idx % len(current_plays)]
                    st.caption(f"💡 **추천 발달 놀이:** {play_tip}")
                    play_idx += 1
            st.write("<div style='margin-bottom: -10px;'></div>", unsafe_allow_html=True)
