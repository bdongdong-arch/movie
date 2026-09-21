# -*- coding: utf-8 -*-
"""
🍿 어제의 대한민국 박스오피스
--------------------------------
영화진흥위원회(KOBIS) 오픈API의 '일별 박스오피스' 정보를 가져와서
"감독이 한국인인 영화(대한민국 영화)"만 골라 순위/그래프로 보여주는 스트림릿 앱입니다.

[꼭 알아두세요 - 두 가지 한계점]
1) KOBIS API는 '감독의 국적'을 직접 알려주지 않습니다.
   그래서 이 앱은 ① 영화의 제작국가에 '한국'이 포함되어 있고,
   ② 감독 이름이 한글로만 되어 있는 경우(외국어 표기가 섞여있지 않은 경우)를
   '한국인 감독'으로 추정하는 방식(근사치)을 사용합니다. 100% 정확하지 않을 수 있습니다.
2) KOBIS API는 '평론가 평점'을 제공하지 않습니다.
   그래서 이 앱은 네이버 검색 결과 페이지를 참고(스크래핑)해서 평점을 최대한 가져오되,
   네이버 페이지 구조가 바뀌거나 검색 결과가 없으면 "정보 없음"으로 표시합니다.
   (공식 API가 아니므로 보장되는 기능이 아닙니다.)
"""

import re
import random
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from bs4 import BeautifulSoup


# ============================================================
# 1. 기본 설정 (페이지 정보, 다크 영화관 테마 CSS)
# ============================================================

st.set_page_config(
    page_title="어제의 대한민국 박스오피스",
    page_icon="🍿",
    layout="wide",
)

# 영화관처럼 어둡게 꾸미는 CSS입니다.
# st.markdown에 unsafe_allow_html=True를 주면 순수 HTML/CSS를 화면에 넣을 수 있어요.
DARK_CINEMA_CSS = """
<style>
/* 전체 배경 - 극장 상영관처럼 짙은 남색~검정 */
.stApp {
    background: radial-gradient(circle at 50% 0%, #241214 0%, #120a0d 45%, #0a0608 100%);
    color: #f1e9d8;
}

/* 제목, 소제목 색상 - 극장 조명 느낌의 금색 */
h1, h2, h3, h4 {
    color: #f3c969 !important;
}

/* 사이드바도 어둡게 */
section[data-testid="stSidebar"] {
    background-color: #150c0e;
    border-right: 1px solid #4a2126;
}

/* 표(데이터프레임) 배경 어둡게 */
[data-testid="stDataFrame"] {
    background-color: #1b1013;
    border: 1px solid #4a2126;
    border-radius: 8px;
}

/* 지표 카드(st.metric) 꾸미기 - 극장 티켓 느낌 */
[data-testid="stMetric"] {
    background-color: #1b1013;
    border: 1px solid #7a1f2b;
    border-radius: 10px;
    padding: 14px 10px;
}
[data-testid="stMetricLabel"] {
    color: #d8b463 !important;
}
[data-testid="stMetricValue"] {
    color: #f1e9d8 !important;
}

/* 버튼, 인풋류 색 */
.stDateInput input {
    color: #f1e9d8 !important;
}
</style>
"""
st.markdown(DARK_CINEMA_CSS, unsafe_allow_html=True)


def show_popcorn_burst():
    """
    처음 접속했을 때 딱 한 번 팝콘 알갱이(🍿)가 화면 중앙에서
    사방으로 터지듯 퍼지는 연출을 보여주는 함수입니다.

    원리: 팝콘 이모지를 여러 개 만들고, 각각에게 무작위 방향(각도)과
    거리(distance)를 CSS 변수(--tx, --ty)로 지정한 뒤,
    CSS 애니메이션으로 중앙에서 그 위치까지 날아가며 사라지게 만듭니다.
    """
    particles_html = ""
    particle_count = 26

    for i in range(particle_count):
        angle_deg = random.uniform(0, 360)
        distance = random.uniform(160, 480)
        # 각도와 거리를 이용해서 x, y 이동량을 계산합니다 (삼각함수).
        import math
        tx = round(distance * math.cos(math.radians(angle_deg)))
        ty = round(distance * math.sin(math.radians(angle_deg)))
        delay = round(random.uniform(0, 0.25), 2)
        size = round(random.uniform(20, 38))
        rotate = round(random.uniform(-180, 180))

        particles_html += f"""
        <span class="popcorn-particle"
              style="
                --tx: {tx}px;
                --ty: {ty}px;
                --rot: {rotate}deg;
                font-size: {size}px;
                animation-delay: {delay}s;
              ">🍿</span>
        """

    html = f"""
    <style>
    .popcorn-layer {{
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        pointer-events: none; /* 화면 클릭을 막지 않도록 함 */
        z-index: 9999;
        overflow: hidden;
    }}
    .popcorn-particle {{
        position: absolute;
        top: 40%;
        left: 50%;
        opacity: 1;
        transform: translate(-50%, -50%);
        animation: popcorn-burst 1.4s ease-out forwards;
    }}
    @keyframes popcorn-burst {{
        0% {{
            transform: translate(-50%, -50%) rotate(0deg) scale(0.4);
            opacity: 1;
        }}
        100% {{
            transform: translate(calc(-50% + var(--tx)), calc(-50% + var(--ty))) rotate(var(--rot)) scale(1.1);
            opacity: 0;
        }}
    }}
    </style>
    <div class="popcorn-layer">
        {particles_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# 세션당 딱 한 번만 팝콘이 터지도록 session_state로 확인합니다.
if "popcorn_shown" not in st.session_state:
    show_popcorn_burst()
    st.session_state["popcorn_shown"] = True


# ============================================================
# 2. 날짜 계산 (한국 시간 기준 '어제')
# ============================================================

KST = ZoneInfo("Asia/Seoul")


def get_yesterday_kst() -> date:
    """
    배포 서버의 시계는 한국 시간이 아닐 수 있으므로,
    반드시 Asia/Seoul 시간대로 '지금'을 계산한 뒤 하루를 빼서 '어제' 날짜를 구합니다.
    """
    now_kst = datetime.now(KST)
    return (now_kst - timedelta(days=1)).date()


yesterday_kst = get_yesterday_kst()


# ============================================================
# 3. KOBIS API 호출 함수들
# ============================================================

BOX_OFFICE_URL = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
MOVIE_INFO_URL = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_daily_box_office(api_key: str, target_date: date):
    """
    KOBIS 일별 박스오피스 API를 호출합니다.
    성공하면 (True, 영화리스트), 실패하면 (False, 에러메시지)를 반환합니다.
    """
    target_dt_str = target_date.strftime("%Y%m%d")
    params = {"key": api_key, "targetDt": target_dt_str}

    try:
        res = requests.get(BOX_OFFICE_URL, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        return False, f"KOBIS 서버에 연결하지 못했습니다. (네트워크 오류: {e})"

    if res.status_code != 200:
        return False, f"KOBIS 서버가 오류 응답(상태 코드 {res.status_code})을 반환했습니다."

    try:
        data = res.json()
    except ValueError:
        return False, "KOBIS 서버 응답을 JSON 형식으로 해석할 수 없습니다."

    # KOBIS는 인증키 오류 등 문제가 있으면 'faultInfo' 상자를 돌려줍니다.
    if "faultInfo" in data:
        message = data["faultInfo"].get("message", "알 수 없는 오류")
        return False, f"KOBIS API 오류: {message}"

    try:
        movie_list = data["boxOfficeResult"]["dailyBoxOfficeList"]
    except (KeyError, TypeError):
        return False, "응답에서 박스오피스 목록을 찾을 수 없습니다. (응답 형식이 예상과 다릅니다)"

    if not movie_list:
        return False, "해당 날짜의 박스오피스 목록이 비어 있습니다."

    return True, movie_list


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_movie_info(api_key: str, movie_cd: str):
    """
    KOBIS 영화 상세정보 API를 호출해서 감독 목록과 제작국가를 가져옵니다.
    실패하면 (False, None)을 반환합니다.
    """
    params = {"key": api_key, "movieCd": movie_cd}
    try:
        res = requests.get(MOVIE_INFO_URL, params=params, timeout=10)
        data = res.json()
        if "faultInfo" in data:
            return False, None
        info = data["movieInfoResult"]["movieInfo"]
        return True, info
    except Exception:
        return False, None


def is_korean_director_movie(movie_info: dict) -> bool:
    """
    '감독이 한국인인 영화'를 근사적으로 판정합니다.

    판정 방법(정확한 국적 정보가 없어서 쓰는 추정 방법입니다):
    1) 제작국가(nations) 중에 '한국'이 포함되어 있어야 하고,
    2) 감독(directors) 이름 중 하나라도 '한글로만' 적혀 있으면
       한국인 감독으로 추정합니다.
    """
    if not movie_info:
        return False

    nations = movie_info.get("nations", [])
    nation_names = [n.get("nationNm", "") for n in nations]
    if not any("한국" in n for n in nation_names):
        return False

    directors = movie_info.get("directors", [])
    hangul_only_pattern = re.compile(r"^[가-힣\s·]+$")
    for d in directors:
        name = d.get("peopleNm", "").strip()
        if name and hangul_only_pattern.match(name):
            return True

    return False


# ============================================================
# 4. 평론가 평점 (네이버 검색 결과 참고 - 비공식/최선 노력 기능)
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_critic_rating(movie_title: str):
    """
    네이버 통합검색 결과 페이지에서 '평론가 평점'으로 보이는 숫자를 찾아봅니다.
    공식 API가 아니라 페이지의 텍스트를 읽어서 추정하는 방식이라
    실패하거나 못 찾을 수 있습니다. 그런 경우 None을 반환합니다.
    """
    try:
        query = f"{movie_title} 평론가 평점"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(
            "https://search.naver.com/search.naver",
            params={"query": query},
            headers=headers,
            timeout=6,
        )
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        page_text = soup.get_text(separator=" ")

        # "평론가" 또는 "전문가"라는 글자 근처에 있는 소수점 숫자(예: 7.50)를 찾습니다.
        for keyword in ["평론가", "전문가"]:
            idx = page_text.find(keyword)
            if idx == -1:
                continue
            nearby_text = page_text[idx: idx + 60]
            match = re.search(r"(\d{1,2}\.\d{1,2})", nearby_text)
            if match:
                score = float(match.group(1))
                # 평점은 보통 0~10점 범위입니다. 범위를 벗어나면 잘못 찾은 것으로 보고 무시합니다.
                if 0 <= score <= 10:
                    return score

        return None
    except Exception:
        return None


# ============================================================
# 5. 사이드바 - 조회 날짜 선택
# ============================================================

st.sidebar.header("🎬 조회 설정")
selected_date = st.sidebar.date_input(
    "조회할 날짜를 선택하세요",
    value=yesterday_kst,
    min_value=date(2004, 1, 1),  # KOBIS 박스오피스 데이터가 대략 2004년부터 제공됩니다.
    max_value=yesterday_kst,      # 오늘/미래 날짜는 아직 집계되지 않았으므로 선택할 수 없게 막습니다.
    help="기본값은 한국 시간(KST) 기준 '어제'입니다. 오늘 날짜는 아직 집계 전이라 선택할 수 없습니다.",
)
st.sidebar.caption(f"⏰ 한국 시간 기준 '어제': {yesterday_kst.strftime('%Y-%m-%d')}")


# ============================================================
# 6. 메인 화면
# ============================================================

st.title("🍿 대한민국 박스오피스")
st.caption(f"조회 날짜: {selected_date.strftime('%Y년 %m월 %d일')} (기준: 감독이 한국인인 영화)")

# secrets에서 인증키를 불러옵니다. 코드에는 키 값을 절대 직접 쓰지 않습니다.
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    KOBIS_KEY = None

if not KOBIS_KEY:
    st.error(
        "🔑 KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "확인해주세요:\n"
        "1. 스트림릿 클라우드의 앱 설정 → Secrets 메뉴에서 KOBIS_KEY = \"발급받은키\" 형태로 등록했는지\n"
        "2. 키 이름 철자가 정확히 'KOBIS_KEY'인지 (대소문자 포함)\n"
        "3. 로컬에서 테스트 중이라면 .streamlit/secrets.toml 파일이 있는지"
    )
    st.stop()

with st.spinner("KOBIS에서 박스오피스 정보를 불러오는 중입니다..."):
    success, result = fetch_daily_box_office(KOBIS_KEY, selected_date)

if not success:
    st.error(
        f"😥 박스오피스 정보를 불러오지 못했습니다.\n\n"
        f"**오류 내용:** {result}\n\n"
        "다음을 확인해보세요:\n"
        "1. Secrets에 등록한 KOBIS_KEY가 정확하고 유효한지 (KOBIS 오픈API 사이트에서 키 상태 확인)\n"
        "2. 인터넷 연결 상태\n"
        "3. 선택한 날짜에 집계된 데이터가 있는지 (너무 오래된 날짜는 자료가 없을 수 있습니다)\n"
        "4. KOBIS 서버가 일시적으로 점검 중일 수 있으니 잠시 후 다시 시도"
    )
    st.stop()

raw_movie_list = result  # KOBIS가 준 전체 박스오피스 목록 (한국 영화 + 외국 영화 섞여 있음)


# ============================================================
# 7. '한국인 감독' 영화만 걸러내기
# ============================================================

korean_movies = []

with st.spinner("영화별 감독 정보를 확인하는 중입니다..."):
    for movie in raw_movie_list:
        movie_cd = movie.get("movieCd")
        ok, info = fetch_movie_info(KOBIS_KEY, movie_cd)
        if ok and is_korean_director_movie(info):
            korean_movies.append(movie)

if not korean_movies:
    st.warning(
        "이 날짜의 박스오피스 목록에서 '감독이 한국인'으로 추정되는 영화를 찾지 못했습니다.\n"
        "다른 날짜를 선택해 보세요. (감독 국적 판정은 근사치이므로 일부 영화가 누락될 수 있습니다)"
    )
    st.stop()


# ============================================================
# 8. 표로 보여주기 (한국 영화 순위 / 평론가 평점 포함)
# ============================================================

st.subheader("📋 한국 영화 박스오피스 순위")

table_rows = []
with st.spinner("평론가 평점 정보를 찾는 중입니다... (참고용 정보이며 시간이 조금 걸릴 수 있어요)"):
    for rank, movie in enumerate(korean_movies, start=1):
        title = movie.get("movieNm", "")
        rating = fetch_critic_rating(title)
        table_rows.append({
            "한국 영화 순위": rank,
            "영화명": title,
            "개봉일": movie.get("openDt", ""),
            "관객수": int(movie.get("audiCnt", 0)),
            "누적관객": int(movie.get("audiAcc", 0)),
            "스크린 수": int(movie.get("scrnCnt", 0)),
            "평론가 평점": rating if rating is not None else "정보 없음",
        })

df = pd.DataFrame(table_rows)

# 화면에 보여줄 때는 숫자를 천 단위 콤마로 보기 좋게 바꿉니다.
df_display = df.copy()
df_display["관객수"] = df_display["관객수"].apply(lambda x: f"{x:,}")
df_display["누적관객"] = df_display["누적관객"].apply(lambda x: f"{x:,}")
df_display["스크린 수"] = df_display["스크린 수"].apply(lambda x: f"{x:,}")

st.dataframe(df_display, use_container_width=True, hide_index=True)

st.caption(
    "※ '평론가 평점'은 KOBIS 공식 데이터가 아니라 네이버 검색 결과를 참고해 추정한 값으로, "
    "정확하지 않거나 '정보 없음'으로 표시될 수 있습니다."
)


# ============================================================
# 9. 1위 영화 - 지표 카드 3장
# ============================================================

top_movie = df.iloc[0]

st.subheader(f"🏆 오늘의 1위: {top_movie['영화명']}")

col1, col2, col3 = st.columns(3)
col1.metric("관객수", f"{top_movie['관객수']:,}명")
col2.metric("누적 관객수", f"{top_movie['누적관객']:,}명")
col3.metric("스크린 수", f"{top_movie['스크린 수']:,}개")


# ============================================================
# 10. 관객수 상위 5편 - 막대그래프
# ============================================================

st.subheader("📊 관객수 상위 5편")

top5_df = df.sort_values("관객수", ascending=False).head(5)

fig = go.Figure(
    data=[
        go.Bar(
            x=top5_df["영화명"],
            y=top5_df["관객수"],
            marker=dict(
                color="#c0392b",           # 극장 좌석같은 진한 빨강
                line=dict(color="#f3c969", width=1.5),  # 금색 테두리
            ),
            text=top5_df["관객수"].apply(lambda x: f"{x:,}명"),
            textposition="outside",
        )
    ]
)
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="영화명",
    yaxis_title="관객수 (명)",
    font=dict(color="#f1e9d8"),
    margin=dict(t=20, b=20),
)

st.plotly_chart(fig, use_container_width=True)
