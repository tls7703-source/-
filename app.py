import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, time, timedelta

st.set_page_config(page_title="우리 아이 맞춤 스케줄러 & 실시간 기록장", page_icon="👶", layout="wide")

# ---------------------------------------------------------
# 1. 구글 시트 웹앱 API 연동
# ---------------------------------------------------------
API_URL = "https://script.google.com/macros/s/AKfycby3sVLC2WBVKgNWTmeSnuWa7G_P04FLFPi7PEic65Sg6xRy5YSS4P9SlyF6Nvq1cNXnzw/exec"

def load_records():
    """구글 시트에서 실시간 데이터 읽어오기 및 정제"""
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
    """구글 시트에 새 기록 전송"""
    try:
        record_dict["action"] = "add"
        res = requests.post(API_URL, json=record_dict, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def delete_record(created_at_val):
    """구글 시트에서 특정 기록 삭제"""
    try:
        payload = {"action": "delete", "created_at": created_at_val}
        res = requests.post(API_URL, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# 2. 아기 프로필 & 패턴 설정
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

# 기본 24시간 상세 일과 템플릿 (기상 05:51 기준)
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
# 3. 화면 레이아웃
# ---------------------------------------------------------
col_left, col_right = st.columns([1.1, 1.2], gap="large")

# =========================================================
# 좌측: 실시간 기록 & 삭제 관리
# =========================================================
with col_left:
    st.header("📝 실시간 공유 육아 기록")
    
    with st.form("record_form", clear_on_submit=True):
        record_type = st.selectbox("기록 유형", ["수면", "이유식", "모유 수유", "소변", "대변"])
        
        c1, c2 = st.columns(2)
        with c1:
            rec_date = st.date_input("날짜", value=today)
            rec_start_time = st.time_input("시작(또는 발생) 시간", value=datetime.now().time())
        with c2:
            has_end_time = st.checkbox("종료 시간 있음", value=(record_type == "수면"))
            rec_end_time = st.time_input("종료 시간", value=(datetime.now() + timedelta(minutes=40)).time())
                
        rec_memo = st.text_input("메모 (용량, 특이사항)", placeholder="예: 140ml 완밥, 낮잠 잘 잠")
        submitted = st.form_submit_button("구글 시트에 기록 저장", type="primary", use_container_width=True)
        
        if submitted:
            new_entry = {
                "date": rec_date.strftime("%Y-%m-%d"),
                "type": record_type,
                "start_time": rec_start_time.strftime("%H:%M"),
                "end_time": rec_end_time.strftime("%H:%M") if has_end_time else "-",
                "memo": rec_memo if rec_memo else "-",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with st.spinner("구글 시트에 동기화 중..."):
                success = add_record(new_entry)
            if success:
                st.success("구글 시트에 저장 완료!")
                st.rerun()
            else:
                st.error("저장 중 오류가 발생했습니다. URL을 확인해 주세요.")

    # 구글 시트 데이터 로드 및 삭제 UI
    st.subheader("📋 최근 기록 및 삭제")
    df_records = load_records()
    
    if not df_records.empty:
        # 최근 등록된 역순으로 상위 5개 표시 및 삭제 버튼 제공
        recent_df = df_records.tail(8).iloc[::-1]
        
        for idx, row in recent_df.iterrows():
            c_info, c_del = st.columns([4, 1])
            with c_info:
                end_str = f" ~ {row['end_time']}" if row['end_time'] != '-' else ""
                st.markdown(f"**[{row['type']}]** {row['date']} {row['start_time']}{end_str} | `{row['memo']}`")
            with c_del:
                if st.button("🗑️ 삭제", key=f"del_{row['created_at']}_{idx}", use_container_width=True):
                    with st.spinner("삭제 중..."):
                        if delete_record(row['created_at']):
                            st.success("삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error("삭제 실패")
            st.write("<div style='margin-bottom: -8px;'></div>", unsafe_allow_html=True)
    else:
        st.info("기록이 없습니다. 첫 기록을 등록해 보세요!")

# =========================================================
# 우측: 구글 시트 기록 기반 동적 스케줄표
# =========================================================
with col_right:
    st.header("⏰ 맞춤 실시간 스케줄표")
    
    latest_wake = time(5, 51)
    found_sleep_time = None
    
    if not df_records.empty:
        sleep_records = df_records[df_records["type"] == "수면"]
        if not sleep_records.empty:
            last_sleep = sleep_records.iloc[-1]
            raw_time = str(last_sleep["end_time"]).strip()
            if raw_time in ["-", "", "None", "nan"]:
                raw_time = str(last_sleep["start_time"]).strip()
                
            try:
                t_parts = raw_time.split(":")
                if len(t_parts) >= 2:
                    h, m = int(t_parts[0]), int(t_parts[1])
                    latest_wake = time(h, m)
                    found_sleep_time = f"{h:02d}:{m:02d}"
            except Exception:
                pass

    st.markdown("##### ⚙️ 일정 기준 시간 설정")
    use_auto_sync = st.checkbox("구글 시트의 최근 수면/기상 기록 자동 연동", value=True)
    
    if use_auto_sync and found_sleep_time:
        st.info(f"🔄 최근 수면 기록({found_sleep_time})을 기준으로 전체 일정이 자동 조정되었습니다.")
        base_wake_time = latest_wake
    else:
        base_wake_time = st.time_input("오늘 시작(기상) 시간 직접 지정", value=time(5, 51))
        
    base_dt = datetime.combine(today, base_wake_time)
    
    st.write("---")
    st.subheader(f"📅 오늘 자동 재조정된 타임라인 (기준: {base_wake_time.strftime('%H:%M')})")
    
    play_idx = 0
    for idx, item in enumerate(DEFAULT_PATTERN):
        start_t = base_dt + timedelta(minutes=item["offset"])
        end_t = start_t + timedelta(minutes=item["duration"]) if item["duration"] > 0 else None
        
        t_str = start_t.strftime("%H:%M")
        if end_t:
            t_str += f" ~ {end_t.strftime('%H:%M')}"
            
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
