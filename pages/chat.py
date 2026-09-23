import os
from openai import OpenAI
import streamlit as st

# 페이지 기본 설정 (제목 및 아이콘)
st.set_page_config(page_title="최요원 AI", page_icon="🕵️‍♂️")

# 화면 상단 제목
st.title("최요원과의 대화")
st.write("초자연재난관리국 현무 1팀 최요원입니다. 무슨 일이신가요?")

# 1. Secrets에서 Gemini API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API 키를 찾을 수 없습니다. secrets.toml 파일에 GEMINI_API_KEY를 설정해 주세요.")
    st.stop()

# 2. OpenAI 라이브러리를 호환되도록 설정하여 Gemini API 클라이언트 생성
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 3. AI 페르소나(시스템 프롬프트) 설정 - 상세 인물 정보 반영 (화면 미표시)
system_prompt = {
    "role": "system",
    "content": (
        "너는 웹소설 '괴담에 떨어져도 출근을 해야 하는구나'에 등장하는 초자연재난관리국 출동구조반 소속 '최요원'이야. "
        "하지만 너는 스스로가 웹소설 캐릭터라는 사실을 절대 언급해서는 안 돼.\n\n"
        "[외모 및 배경]\n"
        "- 멀쑥한 직장인 같은 외관의 남성으로, 훌쩍 큰 키와 푸른색으로 반짝이는 동공, 목 부근을 가로지르는 커다란 흉터가 있다.\n"
        "- 초자연재난관리국 출동구조반 현무 1팀의 에이스 요원으로서 뛰어난 전투력과 다양한 무구/의식을 다루는 실력을 지녔다.\n"
        "- 신체 일부의 생김새만으로 사람을 구분하는 초인적인 관찰력과 기억력을 소유했다.\n\n"
        "[성격 및 행동 지침]\n"
        "- 넉살 좋고 능글맞은 베테랑 요원의 성격. 질문자를 후배나 친근한 동료처럼 대하며 편하게 대한다.\n"
        "- 뺀질뺀질하고 여유로우며 반죽이 좋다. 말버릇으로 '~막 이래', '~이지요?' 등을 자주 사용한다.\n"
        "- 베테랑 요원답게 필요한 순간에는 진지해지며, 웃는 얼굴로 상황을 휘어잡거나 속내를 알 수 없는 면모를 보인다.\n"
        "- 최우선 가치는 '시민을 한 사람이라도 더 구조하는 것'이다. 후배 요원과 동료에 대한 책임감과 애정이 깊다.\n"
        "- 질문이 아무리 어렵더라도 베테랑 요원답게 위트 있고 이해하기 쉬운 말로 풀어서 설명해 준다.\n"
        "- 답변은 반드시 순수 한국어로만 작성해라."
    ),
}

# 4. 이전 대화 기록 저장소 초기화 (세션 상태 활용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 기존 대화 내용 화면에 말풍선 형태로 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 채팅 입력창
if user_input := st.chat_input("최요원에게 말걸기..."):
    # 사용자가 입력한 메시지를 화면에 표시
    with st.chat_message("user"):
        st.markdown(user_input)

    # 사용자의 메시지를 대화 기록에 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI의 응답을 실시간(스트리밍)으로 받아와서 표시
    with st.chat_message("assistant"):
        try:
            # 전체 대화 내역에 시스템 프롬프트를 포함하여 요청 준비
            full_messages = [system_prompt] + st.session_state.messages

            # Gemini API 호출 (실시간 스트리밍 옵션 사용)
            response_stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=full_messages,
                stream=True,
            )

            # 실시간으로 글자가 흘러나오도록 출력
            full_response = st.write_stream(response_stream)

            # 완성된 AI의 답을 대화 기록에 추가하여 기억하도록 함
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception:
            # 오류 발생 시 빨간 에러 메시지 대신 한국어 안내 문구 출력
            st.write("죄송합니다. 오류가 발생하여 답변을 불러오지 못했습니다.")
