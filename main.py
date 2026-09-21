from pathlib import Path

main_py = r'''import html
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st
import streamlit.components.v1 as components


# ------------------------------------------------------------
# 1. 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="어제의 대한민국 박스오피스",
    page_icon="🎬",
    layout="wide",
)

KST = ZoneInfo("Asia/Seoul")

# 한국 시간 기준으로 "오늘"과 "어제"를 계산합니다.
today_kst = datetime.now(KST).date()
yesterday_kst = today_kst - timedelta(days=1)


# ------------------------------------------------------------
# 2. 영화관 느낌의 어두운 화면 꾸미기
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top, #2b2638 0%, #17151d 38%, #0d0c10 100%);
        color: #f5f2ea;
    }

    [data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0);
    }

    [data-testid="stSidebar"] {
        background: #121117;
        border-right: 1px solid #332f3c;
    }

    h1, h2, h3 {
        color: #fff8dc;
        letter-spacing: -0.03em;
    }

    .cinema-subtitle {
        color: #c8c2d0;
        font-size: 1.02rem;
        margin-top: -0.4rem;
        margin-bottom: 1.5rem;
    }

    .top-card {
        background: linear-gradient(145deg, rgba(48,44,58,.98), rgba(26,24,31,.98));
        border: 1px solid #514a5d;
        border-radius: 18px;
        padding: 20px 22px;
        min-height: 145px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, .28);
    }

    .top-card-label {
        color: #b9b0c5;
        font-size: .88rem;
        margin-bottom: 10px;
    }

    .top-card-value {
        color: #fff5cc;
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.18;
        word-break: keep-all;
    }

    .top-card-small {
        color: #d9d2df;
        font-size: .88rem;
        margin-top: 8px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #3b3643;
        border-radius: 14px;
        overflow: hidden;
    }

    .notice-box {
        background: #211f27;
        border: 1px solid #4c4657;
        border-radius: 14px;
        padding: 16px 18px;
        color: #ddd6e5;
        margin: 10px 0 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# 3. 첫 방문 때만 팝콘 알갱이가 터지는 애니메이션
# ------------------------------------------------------------
def show_popcorn_burst():
    """브라우저 화면 위에서 팝콘 알갱이가 터지는 간단한 애니메이션입니다."""
    components.html(
        """
        <div id="popcorn-stage"></div>
        <script>
        const stage = document.getElementById("popcorn-stage");

        // 팝콘 한 알처럼 보이는 SVG 이미지를 코드 안에서 생성합니다.
        const popcornSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
          <defs>
            <radialGradient id="g" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stop-color="#fffdf5"/>
              <stop offset="72%" stop-color="#f5e8b8"/>
              <stop offset="100%" stop-color="#d9bd68"/>
            </radialGradient>
          </defs>
          <path d="M12 28c-6-2-7-10-2-14 2-2 5-2 7-1 1-6 9-8 13-3 5-3 11 1 10 7 5 1 7 7 4 11-2 3-5 4-8 4-2 8-18 10-22 2-1-2-2-4-2-6z"
                fill="url(#g)" stroke="#c79e45" stroke-width="1.4"/>
          <circle cx="26" cy="19" r="3" fill="#f4c84e" opacity=".72"/>
        </svg>`;
        const popcornUrl = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(popcornSvg);

        const style = document.createElement("style");
        style.textContent = `
          #popcorn-stage {
            position: fixed;
            inset: 0;
            pointer-events: none;
            overflow: hidden;
            z-index: 999999;
          }
          .kernel {
            position: absolute;
            left: 50%;
            top: 22%;
            width: 34px;
            height: 34px;
            background-image: url("${popcornUrl}");
            background-size: contain;
            background-repeat: no-repeat;
            opacity: 0;
            animation: pop 1.35s cubic-bezier(.15,.65,.25,1) forwards;
            filter: drop-shadow(0 4px 5px rgba(0,0,0,.28));
          }
          @keyframes pop {
            0% {
              transform: translate(-50%, -50%) scale(.35) rotate(0deg);
              opacity: 0;
            }
            12% { opacity: 1; }
            100% {
              transform:
                translate(
                  calc(-50% + var(--x)),
                  calc(-50% + var(--y))
                )
                scale(var(--s))
                rotate(var(--r));
              opacity: 0;
            }
          }
        `;
        document.head.appendChild(style);

        for (let i = 0; i < 34; i++) {
          const kernel = document.createElement("div");
          kernel.className = "kernel";

          const angle = Math.random() * Math.PI * 2;
          const distance = 180 + Math.random() * 420;
          const x = Math.cos(angle) * distance;
          const y = Math.sin(angle) * distance + 160;

          kernel.style.setProperty("--x", `${x}px`);
          kernel.style.setProperty("--y", `${y}px`);
          kernel.style.setProperty("--s", `${0.65 + Math.random() * 0.8}`);
          kernel.style.setProperty("--r", `${-300 + Math.random() * 600}deg`);
          kernel.style.animationDelay = `${Math.random() * 0.22}s`;

          stage.appendChild(kernel);
        }

        setTimeout(() => {
          stage.remove();
          style.remove();
        }, 1900);
        </script>
        """,
        height=0,
        scrolling=False,
    )


if "popcorn_shown" not in st.session_state:
    st.session_state.popcorn_shown = True
    show_popcorn_burst()


# ------------------------------------------------------------
# 4. KOBIS 호출 도우미
# ------------------------------------------------------------
KOBIS_BASE = "https://www.kobis.or.kr/kobisopenapi/webservice/rest"
TIMEOUT = 12


class KobisError(Exception):
    """KOBIS 요청 중 생긴 오류를 한 곳에서 처리하기 위한 사용자 정의 오류입니다."""


def get_kobis_key():
    """Streamlit secrets에서 인증키를 가져옵니다."""
    try:
        key = st.secrets["KOBIS_KEY"]
    except Exception as exc:
        raise KobisError(
            "Streamlit 비밀 금고에 KOBIS_KEY가 없습니다."
        ) from exc

    if not str(key).strip():
        raise KobisError("KOBIS_KEY 값이 비어 있습니다.")

    return str(key).strip()


def kobis_get(path, params):
    """KOBIS JSON API를 안전하게 호출합니다."""
    key = get_kobis_key()
    url = f"{KOBIS_BASE}/{path}"

    request_params = {"key": key, **params}

    try:
        response = requests.get(url, params=request_params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout as exc:
        raise KobisError("KOBIS 서버 응답 시간이 초과되었습니다.") from exc
    except requests.exceptions.RequestException as exc:
        raise KobisError(f"KOBIS 요청에 실패했습니다: {exc}") from exc
    except ValueError as exc:
        raise KobisError("KOBIS가 올바른 JSON 형식으로 응답하지 않았습니다.") from exc

    # KOBIS는 인증키/파라미터 문제를 faultInfo로 돌려주는 경우가 있습니다.
    if "faultInfo" in data:
        message = data["faultInfo"].get("message", "알 수 없는 KOBIS 오류")
        raise KobisError(f"KOBIS 오류: {message}")

    return data


@st.cache_data(ttl=60 * 30, show_spinner=False)
def get_daily_boxoffice(target_date_str):
    """선택한 날짜의 일일 박스오피스를 가져옵니다."""
    data = kobis_get(
        "boxoffice/searchDailyBoxOfficeList.json",
        {"targetDt": target_date_str},
    )

    try:
        return data["boxOfficeResult"]["dailyBoxOfficeList"]
    except (KeyError, TypeError) as exc:
        raise KobisError("박스오피스 응답 구조를 확인할 수 없습니다.") from exc


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_movie_info(movie_cd):
    """영화 코드로 상세 정보를 가져옵니다."""
    data = kobis_get(
        "movie/searchMovieInfo.json",
        {"movieCd": movie_cd},
    )

    try:
        return data["movieInfoResult"]["movieInfo"]
    except (KeyError, TypeError) as exc:
        raise KobisError("영화 상세정보 응답 구조를 확인할 수 없습니다.") from exc


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def search_people(people_name, movie_name):
    """
    감독 이름만으로 동명이인이 생길 수 있으므로
    이름 + 해당 영화 필모그래피를 함께 검색합니다.
    """
    data = kobis_get(
        "people/searchPeopleList.json",
        {
            "peopleNm": people_name,
            "filmoNames": movie_name,
            "itemPerPage": 20,
        },
    )

    try:
        return data["peopleListResult"]["peopleList"]
    except (KeyError, TypeError):
        return []


@st.cache_data(ttl=60 * 60 * 24 * 7, show_spinner=False)
def get_director_nationality(people_cd):
    """
    KOBIS Open API의 영화인 상세 응답에는 국적 필드가 없습니다.
    그래서 같은 KOBIS의 공개 영화인 정보 페이지에서 '국적' 항목만 확인합니다.

    페이지 형식이 바뀌면 '확인 불가'를 반환하므로,
    잘못된 국적을 추측하지 않습니다.
    """
    url = (
        "https://www.kobis.or.kr/kobis/business/mast/peop/"
        "searchPeoplePrintList.do"
    )

    try:
        response = requests.get(
            url,
            params={"peopleCd": people_cd},
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        page = html.unescape(response.text)
    except requests.RequestException:
        return "확인 불가"

    # HTML 태그를 간단히 걷어내고 '국적 한국' 같은 문구를 찾습니다.
    text = re.sub(r"<[^>]+>", " ", page)
    text = re.sub(r"\s+", " ", text)

    match = re.search(r"국적\s*([가-힣A-Za-z·\-\s]+?)(?:관련 URL|소속|분야|필모그래피|$)", text)
    if not match:
        return "확인 불가"

    nationality = match.group(1).strip()

    # 너무 긴 문구가 잡히면 페이지 형식이 달라진 것으로 보고 안전하게 중단합니다.
    if len(nationality) > 40:
        return "확인 불가"

    return nationality


def movie_has_korean_director(movie_info):
    """
    '감독이 한국인'이라는 사용자의 기준을 적용합니다.
    공동감독 작품은 감독 중 한 명이라도 국적이 '한국'으로 확인되면 포함합니다.
    """
    movie_name = movie_info.get("movieNm", "")
    directors = movie_info.get("directors") or []

    if not directors:
        return False, []

    checked = []

    for director in directors:
        director_name = director.get("peopleNm", "").strip()
        if not director_name:
            continue

        candidates = search_people(director_name, movie_name)

        # 이름이 같고 대표 역할이 감독인 후보를 우선합니다.
        exact = [
            p for p in candidates
            if p.get("peopleNm") == director_name and "감독" in p.get("repRoleNm", "")
        ]

        # 대표 역할 표기가 다를 수 있으므로, 정확한 이름 후보도 보조로 사용합니다.
        if not exact:
            exact = [p for p in candidates if p.get("peopleNm") == director_name]

        for person in exact:
            people_cd = person.get("peopleCd")
            if not people_cd:
                continue

            nationality = get_director_nationality(people_cd)
            checked.append(f"{director_name}: {nationality}")

            if "한국" in nationality:
                return True, checked

    return False, checked


def format_open_date(raw):
    """YYYYMMDD 형식을 YYYY-MM-DD로 보기 좋게 바꿉니다."""
    if not raw:
        return "미상"

    try:
        return datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return raw


def int_or_zero(value):
    """숫자 문자열을 안전하게 정수로 바꿉니다."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def show_problem(message):
    """빈 화면 대신 사용자가 확인할 내용을 한국어로 안내합니다."""
    st.error(message)
    st.markdown(
        """
        <div class="notice-box">
        <b>다음을 확인해 주세요.</b><br>
        ① Streamlit Cloud의 <code>Settings → Secrets</code>에
        <code>KOBIS_KEY = "발급받은키"</code>가 있는지<br>
        ② KOBIS 인증키가 유효하고 일일 호출 한도를 넘지 않았는지<br>
        ③ 선택한 날짜가 오늘이 아닌 과거 날짜인지<br>
        ④ KOBIS 서비스 점검 또는 네트워크 장애가 없는지<br>
        ⑤ 해당 날짜에 실제 박스오피스 집계 영화가 있는지
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 5. 화면 상단
# ------------------------------------------------------------
st.title("🎬 어제의 대한민국 영화 박스오피스")
st.markdown(
    "KOBIS 일일 박스오피스를 바탕으로, **감독 국적이 한국으로 확인된 영화만** 보여줍니다.",
)
st.markdown(
    '<div class="cinema-subtitle">기본 조회일은 한국 시간 기준 어제이며, 원하는 과거 날짜로 바꿀 수 있습니다.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📅 조회 설정")
    selected_date = st.date_input(
        "박스오피스 날짜",
        value=yesterday_kst,
        max_value=yesterday_kst,
        help="오늘 데이터는 아직 집계 전일 수 있어 어제까지만 선택할 수 있습니다.",
    )
    st.caption(f"한국 시간 기준 오늘: {today_kst:%Y-%m-%d}")
    st.caption(f"기본 조회일(어제): {yesterday_kst:%Y-%m-%d}")

target_dt = selected_date.strftime("%Y%m%d")

st.caption(f"현재 조회: **{selected_date:%Y년 %m월 %d일}**")


# ------------------------------------------------------------
# 6. 데이터 가져오기 + 한국인 감독 기준 필터
# ------------------------------------------------------------
try:
    with st.spinner("KOBIS에서 박스오피스를 불러오는 중입니다..."):
        boxoffice = get_daily_boxoffice(target_dt)

    if not boxoffice:
        show_problem("선택한 날짜의 박스오피스 영화 목록이 비어 있습니다.")
        st.stop()

    rows = []
    unknown_director_movies = []

    progress = st.progress(0, text="감독 국적을 확인하고 있습니다...")

    for index, movie in enumerate(boxoffice):
        movie_cd = movie.get("movieCd", "")
        movie_name = movie.get("movieNm", "")

        try:
            movie_info = get_movie_info(movie_cd)
            is_korean, checked_directors = movie_has_korean_director(movie_info)
        except KobisError:
            # 특정 영화 상세 조회만 실패한 경우 전체 화면을 깨지 않고 넘어갑니다.
            unknown_director_movies.append(movie_name)
            progress.progress((index + 1) / len(boxoffice))
            continue

        if not checked_directors:
            unknown_director_movies.append(movie_name)

        if is_korean:
            rows.append(
                {
                    "영화명": movie_name,
                    "개봉일": format_open_date(movie.get("openDt", "")),
                    "관객수": int_or_zero(movie.get("audiCnt")),
                    "누적관객": int_or_zero(movie.get("audiAcc")),
                    "스크린 수": int_or_zero(movie.get("scrnCnt")),
                    # KOBIS Open API에는 평론가 평점 필드가 없습니다.
                    # 다른 평점 API를 연결하기 전까지는 사실대로 미제공으로 표시합니다.
                    "평론가 평점": "KOBIS 미제공",
                }
            )

        progress.progress((index + 1) / len(boxoffice))

    progress.empty()

except KobisError as exc:
    show_problem(str(exc))
    st.stop()
except Exception as exc:
    show_problem(f"예상하지 못한 오류가 발생했습니다: {exc}")
    st.stop()


if not rows:
    show_problem(
        "박스오피스 목록은 받았지만, 감독 국적이 한국으로 확인된 영화를 찾지 못했습니다."
    )
    if unknown_director_movies:
        st.info(
            "일부 영화는 감독 국적 확인에 실패했을 수 있습니다: "
            + ", ".join(unknown_director_movies)
        )
    st.stop()


# ------------------------------------------------------------
# 7. 대한민국 영화끼리 다시 순위를 매깁니다.
# ------------------------------------------------------------
rows.sort(key=lambda x: x["관객수"], reverse=True)

for rank, row in enumerate(rows, start=1):
    row["한국 영화 순위"] = rank

display_rows = [
    {
        "한국 영화 순위": row["한국 영화 순위"],
        "영화명": row["영화명"],
        "개봉일": row["개봉일"],
        "관객수": row["관객수"],
        "누적관객": row["누적관객"],
        "스크린 수": row["스크린 수"],
        "평론가 평점": row["평론가 평점"],
    }
    for row in rows
]


# ------------------------------------------------------------
# 8. 1위 영화 카드 3장
# ------------------------------------------------------------
top = rows[0]

st.subheader("🏆 대한민국 영화 1위")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
        <div class="top-card">
            <div class="top-card-label">영화명</div>
            <div class="top-card-value">{html.escape(top["영화명"])}</div>
            <div class="top-card-small">개봉일 {html.escape(top["개봉일"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="top-card">
            <div class="top-card-label">당일 관객수</div>
            <div class="top-card-value">{top["관객수"]:,}명</div>
            <div class="top-card-small">선택한 날짜 기준</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="top-card">
            <div class="top-card-label">누적 관객수</div>
            <div class="top-card-value">{top["누적관객"]:,}명</div>
            <div class="top-card-small">스크린 {top["스크린 수"]:,}개</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 9. 상위 5편 막대그래프
# ------------------------------------------------------------
st.subheader("🍿 관객수 상위 5편")

top5 = rows[:5]

# st.bar_chart가 읽기 쉬운 형태로 딕셔너리를 만듭니다.
chart_data = {
    row["영화명"]: row["관객수"]
    for row in top5
}

st.bar_chart(chart_data, horizontal=True)


# ------------------------------------------------------------
# 10. 전체 표
# ------------------------------------------------------------
st.subheader("📋 대한민국 영화 박스오피스")

st.dataframe(
    display_rows,
    use_container_width=True,
    hide_index=True,
    column_config={
        "한국 영화 순위": st.column_config.NumberColumn("한국 영화 순위", format="%d위"),
        "관객수": st.column_config.NumberColumn("관객수", format="%,d명"),
        "누적관객": st.column_config.NumberColumn("누적관객", format="%,d명"),
        "스크린 수": st.column_config.NumberColumn("스크린 수", format="%,d개"),
        "평론가 평점": st.column_config.TextColumn("평론가 평점"),
    },
)

st.caption(
    "※ KOBIS Open API에는 평론가 평점 항목이 없어 현재는 'KOBIS 미제공'으로 표시합니다. "
    "실제 평론가 점수를 자동 표시하려면 별도의 평점 데이터/API가 추가로 필요합니다."
)

if unknown_director_movies:
    with st.expander("감독 국적 확인이 완전하지 않았던 영화 보기"):
        st.write(", ".join(unknown_director_movies))
'''

requirements_txt = '''requests
'''

Path("/mnt/data/main.py").write_text(main_py, encoding="utf-8")
Path("/mnt/data/requirements.txt").write_text(requirements_txt, encoding="utf-8")

print("파일을 만들었습니다:")
print("/mnt/data/main.py")
print("/mnt/data/requirements.txt")
