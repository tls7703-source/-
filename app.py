import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, time, timedelta

# ---------------------------------------------------------
# 마미톡(MomiTalk) 스타일 감성 모바일 UI 테마 적용
# ---------------------------------------------------------
st.set_page_config(
    page_title="우리 아이 육아 기록 & 맞춤 놀이",
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
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(255, 142, 158, 0.25);
        margin-bottom: 15px;
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
        margin-bottom: 18px;
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
        padding: 15px 18px;
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
    
    /* 발달 놀이 카드 */
    .play-box {
        background: white;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
        border-left: 6px solid #FF8E9E;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
    
    div.stButton > button:first-child {
        border-radius: 12px;
        font-weight: 600;
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
# 2. 메인 화면 상단: 아기 생년월일 & 프로필 설정 영역
# ---------------------------------------------------------
with st.expander("⚙️ 아기 프로필 설정 (생년월일 / 알레르기 수정)", expanded=False):
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        birth_date = st.date_input("아기 생년월일", value=date(2025, 12, 1), key="main_birth_date")
    with c_b2:
        allergies = st.text_input("알레르기 / 주의 음식", value="밀가루, 계란", placeholder="예: 계란, 우유", key="main_allergies")

today = date.today()
days_passed = (today - birth_date).days
months_passed = max(0, days_passed // 30)

# 마미톡 스타일 메인 프로필 배너
st.markdown(f"""
<div class="baby-profile-card">
    <h2>🍼 우리 아이</h2>
    <p><strong>생후 {days_passed}일차</strong> ({months_passed}개월)</p>
    {f'<p style="font-size:13px; margin-top:6px; background:rgba(0,0,0,0.12); border-radius:10px; padding:3px 8px; display:inline-block;">⚠️ 알레르기 주의: {allergies}</p>' if allergies else ''}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 월령별 맞춤 놀이 & 발달 가이드 DB
# ---------------------------------------------------------
PLAY_RECOMMENDATIONS = {
    (0, 3): {
        "title": "감각 발달 & 터미타임 단계 (0~3개월)",
        "activities": [
            ("👀 흑백 초점책 & 모빌 놀이", "시각 초점을 맞추는 연습을 도와주며, 좌우로 천천히 움직여 시선 추적을 유도합니다."),
            ("🐢 안전한 터미타임 (1~3분)", "수유 직후를 피해 엎드려 놓아 목과 등 근육을 강화합니다."),
            ("💆 베이비 오일 마사지", "팔다리를 가볍게 쓸어내리며 피부 접촉을 통한 정서적 안정감을 줍니다.")
        ]
    },
    (4, 6): {
        "title": "뒤집기 & 소근육 반응 단계 (4~6개월)",
        "activities": [
            ("🪞 거울 까꿍 놀이", "거울 속 자신을 보며 사회적 미소와 시각 인지 발달을 자극합니다."),
            ("🔔 딸랑이 쥐고 흔들기", "양손으로 물건을 잡고 흔들며 인과관계(흔들면 소리 남)를 배웁니다."),
            ("📖 촉감책 바스락 놀이", "부드러운 천, 바스락거리는 촉감책을 만지며 촉각 감각을 확장합니다.")
        ]
    },
    (7, 9): {
        "title": "되집기/기어가기 & 협응력 단계 (7~9개월)",
        "activities": [
            ("👏 짝짜꿍 & 잼잼 모방 놀이", "부모의 손동작을 따라 하며 모방 능력과 소근육 협응력을 키웁니다."),
            ("🔍 손수건 속 장난감 찾기", "물건을 손수건으로 살짝 가려 대상영속성(보이지 않아도 존재함)을 익힙니다."),
            ("🎾 볼풀공 잡고 굴리기", "배밀이나 기어가기를 유도하기 위해 좋아하는 공을 굴려줍니다.")
        ]
    },
    (10, 12): {
        "title": "잡고 서기 & 인지 확장 단계 (10~12개월)",
        "activities": [
            ("🧱 컵 쌓기 & 무너뜨리기", "컵을 높이 쌓아주고 아이가 손으로 무너뜨리며 쾌감과 원인-결과를 학습합니다."),
            ("📦 상자 속에 물건 넣고 빼기", "작은 공이나 블록을 바구니에 넣고 쏟는 반복 놀이를 진행합니다."),
            ("🧍 잡고 서서 발 떼기 연습", "소파나 안전 가드를 잡고 옆으로 걸어보는 크루징(Cruising)을 유도합니다.")
        ]
    },
    (13, 24): {
        "title": "걸음마 & 표현력 발달 단계 (13~24개월)",
        "activities": [
            ("🖍️ 안전 무독성 크레파스 낙서", "큰 종이 위에 자유롭게 선을 그으며 대소근육 조절력을 기릅니다."),
            ("🧩 도형 맞추기 & 꼭지 퍼즐", "원, 세모, 네모 기본 모양 맞추기로 공간지각력을 키웁니다."),
            ("⚽ 폭신한 공 주고받기", "발로 차거나 손으로 굴리며 신체 균형 감각을 발달시킵니다.")
        ]
    }
}

# 현재 월령에 맞는 추천 놀이 데이터 추출
current_play_data = None
for (s_m, e_m), p_data in PLAY_RECOMMENDATIONS.items():
    if s_m <= months_passed <= e_m:
        current_play_data = p_data
        break
if not current_play_data:
    current_play_data = PLAY_RECOMMENDATIONS[(13, 24)]

# ---------------------------------------------------------
# 4. 탭 구성
# ---------------------------------------------------------
tab_today, tab_input, tab_play = st.tabs(["📋 오늘 타임라인", "✏️ 기록하기", "🧸 오늘의 추천 놀이"])

df_records = load_records()

with tab_today:
    # 날짜 선택
    selected_date = st.date_input("📅 날짜 선택", value=today, label_visibility="collapsed")
    target_date_str = selected_date.strftime("%Y-%m-%d")

    day_df = pd.DataFrame()
    if not df_records.empty:
        day_df = df_records[df_records["date"] == target_date_str].copy()

    # 요약 통계
    sleep_cnt = len(day_df[day_df["type"] == "수면"]) if not day_df.empty else 0
    meal_cnt = len(day_df[day_df["type"] == "이유식"]) if not day_df.empty else 0
    milk_cnt = len(day_df[day_df["type"] == "모유 수유"]) if not day_df.empty else 0
    diaper_cnt = len(day_df[day_df["type"].isin(["소변", "대변"])]) if not day_df.empty else 0

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

    # 타임라인 리스트
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
                
        rec_memo = st.text_input("메모", placeholder="예: 140ml 완밥, 낮잠 잘 잠 등")
        
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
                    st.success("기록이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("저장 실패. 구글 시트 연결을 확인하세요.")

with tab_play:
    st.markdown(f"#### 🧸 {months_passed}개월 맞춤 발달 놀이")
    st.caption(f"현재 단계: **{current_play_data['title']}**")
    
    for title, desc in current_play_data["activities"]:
        st.markdown(f"""
        <div class="play-box">
            <div style="font-size:16px; font-weight:700; color:#333; margin-bottom:5px;">{title}</div>
            <div style="font-size:14px; color:#666; line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
