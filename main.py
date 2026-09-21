
# -*- coding: utf-8 -*-
"""
어제의 영화 박스오피스를 보여주는 스트림릿(Streamlit) 앱입니다.
- KOBIS(영화진흥위원회) 공식 오픈API를 사용합니다.
- 스트림릿 클라우드(Community Cloud)에 배포하는 것을 전제로 작성했습니다.
"""

# ------------------------------------------------------------
# 1. 필요한 라이브러리 불러오기
# ------------------------------------------------------------
import streamlit as st          # 화면(웹앱)을 그려주는 라이브러리
import pandas as pd             # 표(데이터프레임) 형태로 데이터를 다루는 라이브러리
import requests                 # KOBIS API에 HTTP 요청을 보내기 위한 라이브러리
from datetime import datetime   # 날짜/시간 계산용
from zoneinfo import ZoneInfo   # 시간대(타임존)를 다루기 위한 라이브러리 (파이썬 기본 내장)


# ------------------------------------------------------------
# 2. 페이지 기본 설정
# ------------------------------------------------------------
# st.set_page_config는 스크립트에서 제일 먼저 실행되는 스트림릿 명령이어야 합니다.
st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide",
)


# ------------------------------------------------------------
# 3. '어제' 날짜를 한국 시간(KST) 기준으로 계산하기
# ------------------------------------------------------------
# 스트림릿 클라우드 서버의 시계는 한국 시간이 아닐 수 있습니다(주로 UTC).
# 그래서 반드시 "한국 시간대"를 명시해서 현재 시각을 구한 뒤, 하루를 빼야 합니다.
def get_yesterday_kst_str() -> str:
    """한국 시간(KST) 기준 '어제' 날짜를 yyyymmdd 형식의 문자열로 반환합니다."""
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))          # 한국 시간 기준 현재 시각
    yesterday_kst = now_kst - pd.Timedelta(days=1)           # 하루 전(어제)
    return yesterday_kst.strftime("%Y%m%d")                  # yyyymmdd 형태의 8자리 문자열로 변환


target_date_str = get_yesterday_kst_str()

# 화면에 보여줄 때는 읽기 좋은 형태(yyyy-mm-dd)로 바꿔줍니다.
target_date_display = f"{target_date_str[:4]}-{target_date_str[4:6]}-{target_date_str[6:]}"


# ------------------------------------------------------------
# 4. KOBIS API에서 박스오피스 데이터 가져오기
# ------------------------------------------------------------
KOBIS_URL = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"


@st.cache_data(ttl=60 * 60)  # 같은 날짜 요청은 1시간 동안 캐시해서, API를 매번 호출하지 않도록 합니다.
def fetch_box_office(target_dt: str):
    """
    KOBIS API를 호출해서 일별 박스오피스 목록을 가져옵니다.

    반환값은 (성공 여부, 데이터 또는 에러메시지) 형태의 튜플입니다.
    - 성공하면: (True, 영화 목록 리스트)
    - 실패하면: (False, 사람이 읽을 수 있는 한국어 에러 메시지)
    """
    # secrets에서 인증키를 불러옵니다. 코드에는 절대 키를 직접 적지 않습니다.
    # 스트림릿 클라우드의 'Settings > Secrets'에 아래처럼 등록해야 합니다.
    #   KOBIS_KEY = "발급받은_인증키"
    try:
        api_key = st.secrets["KOBIS_KEY"]
    except Exception:
        return False, (
            "인증키(KOBIS_KEY)를 찾을 수 없습니다.\n"
            "스트림릿 클라우드의 'Settings → Secrets'에 아래 형식으로 등록되어 있는지 확인해 주세요.\n\n"
            'KOBIS_KEY = "발급받은_인증키"'
        )

    params = {
        "key": api_key,
        "targetDt": target_dt,
    }

    # 4-1. 네트워크 요청 자체가 실패하는 경우 (인터넷 문제, 서버 다운, 타임아웃 등)
    try:
        response = requests.get(KOBIS_URL, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        return False, (
            "KOBIS 서버에 요청을 보내는 데 실패했습니다.\n"
            "인터넷 연결 상태나 KOBIS 서버 상태를 확인해 주세요.\n"
            f"(자세한 오류: {e})"
        )

    # 4-2. 응답은 왔지만 상태 코드가 200이 아닌 경우 (서버 오류 등)
    if response.status_code != 200:
        return False, (
            f"KOBIS 서버가 정상적이지 않은 응답을 반환했습니다. (상태 코드: {response.status_code})\n"
            "잠시 후 다시 시도하거나, KOBIS 서버 상태를 확인해 주세요."
        )

    # 4-3. 응답 내용이 JSON 형식이 아닌 경우
    try:
        data = response.json()
    except ValueError:
        return False, (
            "KOBIS 서버 응답을 해석할 수 없습니다(JSON 형식이 아님).\n"
            "요청 주소나 요청 변수가 올바른지 확인해 주세요."
        )

    # 4-4. 인증키가 틀린 경우 등: 상태코드는 200이지만 faultInfo 상자가 옴
    #      (KOBIS 공식 문서에 명시된 동작입니다.)
    if "faultInfo" in data:
        fault = data["faultInfo"]
        message = fault.get("message", "알 수 없는 오류")
        reason_code = fault.get("reasonCode", "코드 없음")
        return False, (
            "KOBIS API가 오류를 반환했습니다.\n"
            f"- 오류 메시지: {message}\n"
            f"- 오류 코드: {reason_code}\n"
            "인증키(KOBIS_KEY)가 올바르게 등록되어 있는지, 혹은 요청 변수가 맞는지 확인해 주세요."
        )

    # 4-5. 정상 응답이라면 boxOfficeResult 안의 목록을 꺼냅니다.
    try:
        movie_list = data["boxOfficeResult"]["dailyBoxOfficeList"]
    except KeyError:
        return False, (
            "응답 구조가 예상과 다릅니다(boxOfficeResult 또는 dailyBoxOfficeList가 없음).\n"
            "KOBIS API 문서가 변경되었는지 확인해 주세요."
        )

    # 4-6. 목록 자체는 있는데 비어 있는 경우 (예: 아직 해당 날짜 집계가 안 된 경우)
    if not movie_list:
        return False, (
            f"{target_date_display} 날짜의 박스오피스 데이터가 비어 있습니다.\n"
            "해당 날짜의 집계가 아직 완료되지 않았을 수 있습니다. 잠시 후 다시 시도해 주세요."
        )

    return True, movie_list


# ------------------------------------------------------------
# 5. 화면 제목 표시
# ------------------------------------------------------------
st.title("🎬 어제의 박스오피스")
st.caption(f"기준 날짜: {target_date_display} (한국 시간 기준 어제, KOBIS 제공)")

# 데이터 가져오기 시도
success, result = fetch_box_office(target_date_str)

# ------------------------------------------------------------
# 6. 실패했을 때: 빈 화면 대신 안내 문구 표시
# ------------------------------------------------------------
if not success:
    st.error("박스오피스 데이터를 불러오지 못했습니다.")
    st.warning(result)  # 위에서 만든, 무엇을 확인해야 하는지 알려주는 한국어 메시지
    st.stop()  # 여기서 스크립트 실행을 멈춰서, 아래 코드(표/그래프)가 실행되지 않도록 합니다.

movie_list = result  # 성공했다면 result는 영화 목록(list of dict)입니다.


# ------------------------------------------------------------
# 7. 데이터프레임으로 변환하고, 보여줄 컬럼만 정리하기
# ------------------------------------------------------------
df = pd.DataFrame(movie_list)

# KOBIS API의 숫자 값은 전부 문자열로 오기 때문에, 숫자 계산/정렬을 위해 형변환합니다.
numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")  # 변환 실패 시 NaN 처리

# 화면에 보여줄 컬럼만 골라서, 한국어 이름으로 바꿉니다.
display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
display_df.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

# 숫자에 천 단위 콤마를 넣어 읽기 좋게 만듭니다.
for col in ["관객수", "누적관객", "스크린수"]:
    display_df[col] = display_df[col].map(lambda x: f"{int(x):,}" if pd.notna(x) else "-")


# ------------------------------------------------------------
# 8. 1위 영화: 지표 카드 3장으로 크게 보여주기
# ------------------------------------------------------------
st.subheader("🏆 오늘의 1위")

top_movie = df.sort_values("rank").iloc[0]  # rank가 1인(가장 작은) 영화

col1, col2, col3 = st.columns(3)
col1.metric(label=f"{top_movie['movieNm']} · 관객수", value=f"{int(top_movie['audiCnt']):,}명")
col2.metric(label="누적관객", value=f"{int(top_movie['audiAcc']):,}명")
col3.metric(label="스크린수", value=f"{int(top_movie['scrnCnt']):,}개")


# ------------------------------------------------------------
# 9. 전체 순위표
# ------------------------------------------------------------
st.subheader("📋 전체 순위")
st.dataframe(display_df, use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# 10. 관객수 상위 5편 막대그래프
# ------------------------------------------------------------
st.subheader("📊 관객수 상위 5편")

top5_df = df.sort_values("audiCnt", ascending=False).head(5)
chart_df = top5_df.set_index("movieNm")[["audiCnt"]]
chart_df.columns = ["관객수"]

st.bar_chart(chart_df)
