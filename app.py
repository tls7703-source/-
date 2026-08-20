import streamlit as st
import pandas as pd
import requests
import random
import uuid
from datetime import datetime, date, time, timedelta

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
        flex-shrink: 0;
    }
    
    .play-box {
        background: white;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
        border-left: 6px solid #FF8E9E;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
    .play-tag {
        display: inline-block;
        background: #FFF0F2;
        color: #FF6B8B;
        font-size: 12px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        margin-bottom: 6px;
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
API_URL = "https://script.google.com/macros/s/AKfycbyDXnOr2itIAXJVTSNiwx61aPtzYotu6V3wiI7mtpE-kOJZJX1o57gmAi7bE4CHDPTnJw/exec"

def normalize_time_str(val):
    val = str(val).strip()
    if not val or val in ["-", "None", "nan", ""]:
        return "-"
    if ":" in val:
        parts = val.split(":")
        try:
            h, m = int(parts[0]), int(parts[1])
            return f"{h:02d}:{m:02d}"
        except:
            return val
    return val

def load_records():
    try:
        res = requests.get(API_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                for col in ["date", "type", "start_time", "end_time", "end_date", "memo", "created_at"]:
                    if col not in df.columns:
                        df[col] = "-"
                df["date"] = df["date"].astype(str).str.slice(0, 10)
                df["start_time"] = df["start_time"].apply(normalize_time_str)
                df["end_time"] = df["end_time"].apply(normalize_time_str)
                df["end_date"] = df["end_date"].astype(str).str.slice(0, 10)
                df["created_at"] = df["created_at"].astype(str).str.strip()
                return df
        return pd.DataFrame(columns=["date", "type", "start_time", "end_time", "end_date", "memo", "created_at"])
    except Exception:
        return pd.DataFrame(columns=["date", "type", "start_time", "end_time", "end_date", "memo", "created_at"])

def add_record(record_dict):
    try:
        record_dict["action"] = "add"
        res = requests.post(API_URL, json=record_dict, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def update_record(record_dict):
    """구글 시트의 기존 기록 수정"""
    try:
        record_dict["action"] = "update"
        res = requests.post(API_URL, json=record_dict, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def delete_record(unique_id):
    if not unique_id or unique_id in ["-", "None", ""]:
        return False
    try:
        payload = {"action": "delete", "created_at": str(unique_id)}
        res = requests.post(API_URL, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# 2. 아기 프로필 & D-day
# ---------------------------------------------------------
with st.expander("⚙️ 아기 프로필 설정 (생년월일 / 알레르기)", expanded=False):
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        birth_date = st.date_input("생년월일", value=date(2025, 12, 1), key="main_birth_date")
    with c_b2:
        allergies = st.text_input("알레르기 / 주의 음식", placeholder="예: 계란, 우유", key="main_allergies")

today = date.today()
days_passed = (today - birth_date).days
months_passed = max(0, days_passed // 30)

st.markdown(f"""
<div class="baby-profile-card">
    <h2>🍼 우리 아이</h2>
    <p><strong>생후 {days_passed}일차</strong> ({months_passed}개월)</p>
    {f'<p style="font-size:13px; margin-top:6px; background:rgba(0,0,0,0.12); border-radius:10px; padding:3px 8px; display:inline-block;">⚠️ 알레르기: {allergies}</p>' if allergies else ''}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 0~72개월(만 6세) 발달 놀이 DB
# ---------------------------------------------------------
EXTENDED_PLAY_DB = {
    (0, 3): [
        ("시각/감각", "👀 흑백 초점책 & 모빌 추적 놀이", "시각 초점을 맞추는 연습을 도와주며, 좌우로 천천히 움직여 시선 추적을 유도합니다."),
        ("대근육", "🐢 안전한 터미타임 (1~3분)", "수유 직후를 피해 엎드려 놓아 목, 어깨, 등 근육을 강화합니다."),
        ("정서/스킨십", "💆 베이비 오일 마사지 & 자장가", "팔다리를 가볍게 쓸어내리며 피부 접촉을 통한 정서적 안정감과 수면 의식을 형성합니다."),
        ("청각", "🎶 딸랑이 소리 방향 찾기", "아이의 양옆에서 번갈아 소리를 내어 소리 나는 방향으로 고개를 돌리도록 자극합니다."),
        ("신체", "🚲 자전거 타기 다리 운동", "기저귀 갈 때 다리를 부드럽게 원형으로 굴려주어 가스 배출과 장운동을 돕습니다.")
    ],
    (4, 6): [
        ("소근육", "🔔 치발기 & 딸랑이 양손 쥐기", "양손으로 물건을 잡고 입으로 탐색하며 손과 눈의 협응력을 키웁니다."),
        ("사회성", "🪞 거울 속 내 모습 까꿍놀이", "거울 속 자신과 부모의 얼굴을 보며 사회적 미소와 자아 인식을 시작합니다."),
        ("촉각", "📖 촉감책 바스락 놀이", "부드러운 천, 바스락거리는 비닐 소리가 나는 촉감책을 만지며 촉각을 확장합니다."),
        ("대근육", "🤸 되집기 & 비행기 태우기", "배를 지지하고 살짝 들어 올려 공간 감각과 코어 근육을 단련합니다."),
        ("감각", "💦 따뜻한 물놀이 & 손장난", "목욕 시 미온수에서 물을 찰랑이며 손바닥 감각을 자극합니다.")
    ],
    (7, 9): [
        ("모방", "👏 짝짜꿍 & 잼잼 & 곤지곤지", "부모의 손동작을 따라 하며 모방 능력과 소근육 협응력을 키웁니다."),
        ("인지", "🔍 손수건 속 장난감 찾기", "물건을 손수건으로 살짝 가려 대상영속성을 익힙니다."),
        ("대근육", "🎾 굴러가는 공 잡으러 기어가기", "배밀이나 기어가기를 유도하기 위해 좋아하는 공이나 장난감을 굴려줍니다."),
        ("언어", "🗣️ 동물 소리 & 까꿍 대화", "엄마 아빠의 입 모양을 보여주며 음성 언어 모방을 유도합니다."),
        ("소근육", "🥣 핑거푸드(떡뻥) 집어먹기", "엄지와 검지로 작은 과자 조각을 집어먹으며 핀서 그립을 연습합니다.")
    ],
    (10, 12): [
        ("소근육/인지", "🧱 컵 쌓기 & 와르르 무너뜨리기", "컵을 높이 쌓아주고 아이가 손으로 무너뜨리며 성취감을 경험합니다."),
        ("분류/공간", "📦 상자 속에 공 넣고 쏟기", "작은 공이나 블록을 바구니에 넣고 다시 쏟는 반복 탐색 놀이를 진행합니다."),
        ("대근육", "🧍 소파 잡고 서서 꽃게걸음(크루징)", "소파나 안전 가드를 잡고 옆으로 걸어보는 균형 잡기 연습을 합니다."),
        ("소근육", "📄 부드러운 종이 찢기 놀이", "전단지나 신문지를 손으로 찢고 구기며 악력을 기릅니다."),
        ("언어/사회성", "👋 안녕! 바이바이 손인사", "외출 시나 헤어질 때 손을 흔드는 사회적 상호작용 제스처를 배웁니다.")
    ],
    (13, 18): [
        ("소근육/표현", "🖍️ 안전 무독성 크레파스 끄적이기", "큰 전지 위에 자유롭게 선을 그으며 손목 조절력을 기릅니다."),
        ("인지/공간", "🧩 꼭지 퍼즐 & 도형 맞추기", "동그라미, 세모, 네모 기본 도형을 제자리에 맞추는 공간지각력을 키웁니다."),
        ("대근육", "⚽ 거실 축구 & 공 굴려 주고받기", "발로 공을 차거나 손으로 굴리며 신체 균형 감각과 대근육을 발달시킵니다."),
        ("생활습관", "🧸 숟가락으로 인형 밥 먹이기", "소꿉놀이 도구로 인형에게 음식을 먹여주는 흉내 놀이를 진행합니다."),
        ("감각", "🌾 미역/쌀 튀밥 오감 촉감 놀이", "불린 미역이나 쌀 튀밥을 매트 위에서 만지고 으깨는 오감 자극을 줍니다.")
    ],
    (19, 24): [
        ("역할놀이", "🛒 마트 장보기 & 카트 밀기", "모형 과일과 장바구니를 활용해 물건을 사고파는 초기 상징 놀이를 진행합니다."),
        ("소근육", "🧵 굵은 빨대 실에 꿰기 놀이", "빨대를 2cm로 잘라 끈에 꿰며 눈-손 협응을 기릅니다."),
        ("대근육", "🪜 베개 징검다리 건너기", "바닥에 베개나 쿠션을 놓고 밟으며 중심을 잡는 장애물 놀이를 합니다."),
        ("언어", "📖 그림책 장면 속 사물 가리키기", "'멍멍이는 어디 있지?' 질문에 맞춰 손가락으로 가리키는 수용 언어를 확장합니다."),
        ("사회성", "🧼 손 씻기 & 거품 비누 거품 놀이", "거품을 만들고 손을 비비며 청결 습관을 배웁니다.")
    ],
    (25, 36): [
        ("인지/창의", "🧱 레고 듀플로 / 블록 구조물 만들기", "집, 터널, 기차역 등 상상하는 형태를 블록으로 조립합니다."),
        ("신체", "🛑 무궁화 꽃이 피었습니다 (얼음 놀이)", "정지 신호에 멈추는 연습을 통해 신체 조절력을 단련합니다."),
        ("언어", "🎭 역할극 (병원놀이 / 미용실 놀이)", "의사와 환자 역할을 번갈아 하며 사회적 대화 규칙을 확장합니다."),
        ("미술", "🎨 플레이도우 점토로 피자 만들기", "도우를 밀대로 밀고 모형 칼로 자르며 소근육을 발달시킵니다."),
        ("자연탐구", "🍂 나뭇잎 주워 색깔별 분류하기", "공원 산책 시 낙엽을 모아 색상별로 분류해 봅니다.")
    ],
    (37, 48): [
        ("소근육/가위질", "✂️ 안전 가위로 종이 선 따라 오리기", "직선, 곡선을 가위로 오려보며 양손 협응력을 키웁니다."),
        ("규칙/게임", "🎲 주사위 굴려 보드게임 칸 이동", "단순한 규칙을 지키고 차례를 기다리는 연습을 합니다."),
        ("신체", "🚲 세발자전거 페달 밟기", "페달을 밟아 앞으로 나아가는 협응 운동을 진행합니다."),
        ("과학/인지", "🧊 얼음 속에 갇힌 장난감 구출", "따뜻한 물이나 소금으로 얼음을 녹여봅니다."),
        ("음악", "🥁 냄비 뚜껑 & 컵 난타 연주", "주방 도구로 다양한 소리와 리듬을 만들어봅니다.")
    ],
    (49, 72): [
        ("논리/창의", "🗺️ 보물 지도 그리고 숨긴 물건 찾기", "집안 구조를 지도로 간단히 그리고 힌트를 찾아봅니다."),
        ("언어/문해", "📝 끝말잇기 & 초성 퀴즈", "소리와 글자의 관계를 익히고 어휘력을 높입니다."),
        ("신체/스포츠", "🏸 미니 배드민턴 & 줄넘기 기초", "도구를 활용한 스포츠를 통해 순발력을 증진합니다."),
        ("과학/실험", "🌋 베이킹소다 식초 화산 폭발", "탄산가스 발생 반응을 관찰하는 과학 탐구입니다."),
        ("정서/협동", "🧩 50~100피스 직소 퍼즐 완성하기", "목표를 끝까지 완수하는 끈기를 기릅니다.")
    ]
}

# ---------------------------------------------------------
# 4. 탭 화면
# ---------------------------------------------------------
tab_today, tab_input, tab_play = st.tabs(["📋 오늘 타임라인", "✏️ 기록하기", "🧸 오늘의 추천 놀이"])

df_records = load_records()

# 수정 모드 세션 상태 관리
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

with tab_today:
    selected_date = st.date_input("📅 날짜 선택", value=today, label_visibility="collapsed")
    target_date_str = selected_date.strftime("%Y-%m-%d")

    def get_record_effective_dates(row):
        start_d = str(row["date"]).strip()
        end_d = str(row.get("end_date", "-")).strip()
        st_t = str(row.get("start_time", "-")).strip()
        end_t = str(row.get("end_time", "-")).strip()
        
        if row["type"] == "수면" and st_t != "-" and end_t != "-":
            try:
                if end_d in ["-", "", "None", "nan"] or end_d == start_d:
                    if st_t > end_t:
                        s_date_obj = datetime.strptime(start_d, "%Y-%m-%d").date()
                        end_d = (s_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
            except:
                pass
        return start_d, end_d

    day_rows = []
    if not df_records.empty:
        for _, row in df_records.iterrows():
            st_d, ed_d = get_record_effective_dates(row)
            if st_d == target_date_str or ed_d == target_date_str:
                r_dict = row.to_dict()
                r_dict["effective_start_date"] = st_d
                r_dict["effective_end_date"] = ed_d
                day_rows.append(r_dict)

    day_df = pd.DataFrame(day_rows)

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

    if not day_df.empty:
        def make_sort_key(r):
            if r["effective_end_date"] == target_date_str and r["effective_start_date"] != target_date_str:
                return f"{target_date_str} {r['end_time']}"
            t_str = r["start_time"] if r["start_time"] != "-" else "00:00"
            return f"{r['effective_start_date']} {t_str}"
            
        day_df["sort_key"] = day_df.apply(make_sort_key, axis=1)
        day_df = day_df.sort_values(by="sort_key", ascending=True)

        type_meta = {
            "수면": {"icon": "💤", "badge": "type-badge-sleep"},
            "이유식": {"icon": "🥣", "badge": "type-badge-meal"},
            "모유 수유": {"icon": "🤱", "badge": "type-badge-milk"},
            "소변": {"icon": "💧", "badge": "type-badge-pee"},
            "대변": {"icon": "💩", "badge": "type-badge-poo"}
        }

        for idx, row in day_df.iterrows():
            unique_created_at = str(row.get('created_at', '')).strip()
            
            # 현재 항목이 수정 모드인 경우: 인라인 수정 폼 렌더링
            if st.session_state.editing_id == unique_created_at:
                with st.container():
                    st.info(f"✏️ **[{row['type']}] 기록 수정 중**")
                    with st.form(key=f"edit_form_{unique_created_at}"):
                        edit_type = st.selectbox("유형", ["수면", "이유식", "모유 수유", "소변", "대변"], 
                                                 index=["수면", "이유식", "모유 수유", "소변", "대변"].index(row['type']) if row['type'] in ["수면", "이유식", "모유 수유", "소변", "대변"] else 0)
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            try:
                                d_val = datetime.strptime(row['date'], "%Y-%m-%d").date()
                            except:
                                d_val = today
                            edit_date = st.date_input("시작 날짜", value=d_val)
                            
                            try:
                                h, m = map(int, row['start_time'].split(":"))
                                st_val = time(h, m)
                            except:
                                st_val = datetime.now().time()
                            edit_start_time = st.time_input("시작 시간", value=st_val)
                            
                        with col_e2:
                            is_edit_sleep = (edit_type == "수면")
                            edit_has_end = (row['end_time'] != "-") if is_edit_sleep else False
                            
                            if is_edit_sleep:
                                edit_has_end = st.checkbox("종료 시간 있음", value=edit_has_end)
                                try:
                                    eh, em = map(int, row['end_time'].split(":"))
                                    et_val = time(eh, em)
                                except:
                                    et_val = time(6, 0)
                                edit_end_time = st.time_input("종료 시간", value=et_val)
                                edit_next_day = st.checkbox("🌙 다음 날 기상 (밤잠)", value=(row['effective_end_date'] != row['effective_start_date']))
                            else:
                                edit_end_time = None
                                edit_next_day = False
                                
                        edit_memo = st.text_input("메모", value=row['memo'])
                        
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            save_edit = st.form_submit_button("수정 완료 💾", type="primary", use_container_width=True)
                        with btn_c2:
                            cancel_edit = st.form_submit_button("취소 ❌", use_container_width=True)
                            
                        if save_edit:
                            auto_cross = (is_edit_sleep and edit_has_end and edit_start_time > edit_end_time)
                            c_end_date = (edit_date + timedelta(days=1)) if (edit_next_day or auto_cross) else edit_date
                            
                            updated_payload = {
                                "date": edit_date.strftime("%Y-%m-%d"),
                                "type": edit_type,
                                "start_time": edit_start_time.strftime("%H:%M"),
                                "end_time": edit_end_time.strftime("%H:%M") if (is_edit_sleep and edit_has_end) else "-",
                                "end_date": c_end_date.strftime("%Y-%m-%d") if (is_edit_sleep and edit_has_end) else "-",
                                "memo": edit_memo if edit_memo else "-",
                                "created_at": unique_created_at
                            }
                            with st.spinner("수정 중..."):
                                if update_record(updated_payload):
                                    st.session_state.editing_id = None
                                    st.success("수정되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("수정 실패")
                                    
                        if cancel_edit:
                            st.session_state.editing_id = None
                            st.rerun()
                st.write("---")
                continue

            # 일반 보기 모드 카드
            meta = type_meta.get(row['type'], {"icon": "📝", "badge": "type-badge-sleep"})
            start_disp = row['start_time']
            end_disp = row['end_time']
            
            is_overnight = (row['effective_end_date'] != "-" and row['effective_end_date'] != row['effective_start_date'])
            
            if is_overnight:
                if row['effective_start_date'] == target_date_str:
                    time_text = f"{start_disp} ~ 익일 {end_disp} 취침 (밤잠 🌙)"
                else:
                    time_text = f"전일 {start_disp} ~ {end_disp} 기상 (밤잠 🌙)"
            else:
                time_text = start_disp
                if end_disp != "-":
                    time_text += f" ~ {end_disp}"

            col_card, col_edit, col_del = st.columns([4.2, 0.9, 0.9])
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
            with col_edit:
                st.write("")
                if st.button("✏️", key=f"btn_edit_{unique_created_at}_{idx}", use_container_width=True, help="기록 수정"):
                    st.session_state.editing_id = unique_created_at
                    st.rerun()
            with col_del:
                st.write("")
                if st.button("🗑️", key=f"btn_del_{unique_created_at}_{idx}", use_container_width=True, help="기록 삭제"):
                    with st.spinner("삭제 중..."):
                        if delete_record(unique_created_at):
                            st.rerun()
                        else:
                            st.error("삭제 실패")
    else:
        st.info(f"💡 {target_date_str}의 기록이 없습니다.")

with tab_input:
    st.markdown("#### ✏️ 빠른 육아 기록")
    
    record_type = st.radio(
        "기록 유형 선택",
        ["수면", "이유식", "모유 수유", "소변", "대변"],
        horizontal=True,
        key="selected_record_type"
    )
    
    is_sleep_type = (record_type == "수면")
    
    with st.form("quick_record_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            rec_date = st.date_input("시작 날짜", value=today)
            rec_start_time = st.time_input("시작(발생) 시간", value=time(19, 0) if is_sleep_type else datetime.now().time())
        with c2:
            if is_sleep_type:
                has_end_time = st.checkbox("종료 시간 입력", value=True, key="chk_sleep_end")
                rec_end_time = st.time_input("종료 시간", value=time(6, 0))
            else:
                has_end_time = False
                rec_end_time = None

        is_next_day = False
        if is_sleep_type and has_end_time:
            is_next_day = st.checkbox("🌙 다음 날 아침에 깸 (밤잠/날짜 넘어감)", value=False, key="chk_sleep_next_day")
                
        rec_memo = st.text_input("메모", placeholder="예: 140ml 완밥, 밤잠 푹 잘 잠 등")
        
        submitted = st.form_submit_button("기록 저장하기 ✨", type="primary", use_container_width=True)
        if submitted:
            auto_cross_midnight = (is_sleep_type and has_end_time and rec_start_time > rec_end_time)
            calc_end_date = (rec_date + timedelta(days=1)) if (is_next_day or auto_cross_midnight) else rec_date
            unique_timestamp_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:6]}"
            
            new_entry = {
                "date": rec_date.strftime("%Y-%m-%d"),
                "type": record_type,
                "start_time": rec_start_time.strftime("%H:%M"),
                "end_time": rec_end_time.strftime("%H:%M") if (has_end_time and rec_end_time) else "-",
                "end_date": calc_end_date.strftime("%Y-%m-%d") if (has_end_time and is_sleep_type) else "-",
                "memo": rec_memo if rec_memo else "-",
                "created_at": unique_timestamp_id
            }
            with st.spinner("저장 중..."):
                if add_record(new_entry):
                    st.success("기록이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("저장 실패. 구글 시트 연결을 확인하세요.")

with tab_play:
    matched_plays = []
    current_range_str = "영유아"
    for (s_m, e_m), plays in EXTENDED_PLAY_DB.items():
        if s_m <= months_passed <= e_m:
            matched_plays = plays
            current_range_str = f"{s_m}~{e_m}개월"
            break
    if not matched_plays:
        matched_plays = EXTENDED_PLAY_DB[(49, 72)]
        current_range_str = "49~72개월"

    c_p1, c_p2 = st.columns([3, 1])
    with c_p1:
        st.markdown(f"#### 🧸 {months_passed}개월 맞춤 놀이 ({current_range_str})")
    with c_p2:
        shuffle_btn = st.button("🎲 다른 놀이", use_container_width=True)

    if "play_seed" not in st.session_state or shuffle_btn:
        st.session_state.play_seed = random.randint(1, 1000)

    random.seed(st.session_state.play_seed)
    sampled_plays = random.sample(matched_plays, min(3, len(matched_plays)))

    for tag, title, desc in sampled_plays:
        st.markdown(f"""
        <div class="play-box">
            <span class="play-tag">{tag}</span>
            <div style="font-size:16px; font-weight:700; color:#212529; margin-bottom:6px;">{title}</div>
            <div style="font-size:14px; color:#495057; line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🌐 전문가 육아/놀이 백과 바로가기 (차이의 놀이 / 아이사랑)"):
        st.markdown(f"""
        - 🎈 **[차이의 놀이 (Havruta Play)](https://www.chaisplay.com):** 월령별 맞춤 놀이 팁 및 교구 놀이 백과
        - 👶 **[보건복지부 아이사랑 포털](https://www.childcare.go.kr):** 표준 영유아 발달 가이드 및 부모 코칭
        - 💡 **현재 {months_passed}개월 발달 팁:** "🎲 다른 놀이" 버튼을 누르면 같은 월령대의 다른 추천 놀이 카드로 즉시 새로고침됩니다.
        """)
