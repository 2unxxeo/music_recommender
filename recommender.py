import openai
import streamlit as st

from supabase import create_client


@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.markdown(
    """
<style>
footer {
    visibility: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)

supabase = init_connection()
openai.api_key = st.secrets.OPENAI_TOKEN
openai_model_version = "gpt-3.5-turbo-0613"

st.title("for your playlist 🎶")
st.subheader("AI가 추천하는 음악을 들어보세요!")
st.text(f"Powered by {openai_model_version}")
st.image("./data/festival.jpeg", use_column_width=True)


def generate_prompt(condition, description, keywords, genres, n=4):
    genres_str = ", ".join(genres) if genres else "장르 무관"
    prompt = f""" 
요청자의 상황에 적합한 음악을 {n}개 추천해주세요.
{genres_str} 장르 중에서 골라주세요.
빌보드 HOT 100 이외에서 골라주세요.
키워드가 주어질 경우, 반드시 키워드를 고려하여야 합니다.
이유를 함께 설명하되, 이유를 설명하는 부분에서는 제목과 가수를 다시 언급하지 말고 이유만 두 문장 이상으로 설명해주세요.
그 다음, 해당 음악의 뮤직비디오 유튜브 링크를 같이 첨부해주세요.

예시)
1. Sam Smith - Stay with Me
- 선택한 이유를 자세하게 설명하기
- https://www.youtube.com/watch?v=pB-5XG-DbAA
   
---
상황: {condition}
음악 분위기/느낌: {description}
키워드: {", ".join(keywords)} 
---
"""
    return prompt.strip()


def request_chat_completion(prompt):
    response = openai.ChatCompletion.create(
        model=openai_model_version,
        messages=[
            {"role": "system", "content": "당신은 음악 업계 종사자입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

def write_prompt_result(prompt, result):
    data = supabase.table("music_recommender")\
        .insert({"prompt": prompt, "result": result})\
        .execute()
    print(data)

with st.form("form"):
    condition = st.text_input("상황(필수)", placeholder="드라이브할 때")
    desc = st.text_input("음악 분위기/느낌(필수)", placeholder="시끄러운 음악")
    genres = st.multiselect("음악 장르(선택)", options=["K-pop", "pop", "rock", "heavy metal", "jazz", "ballad", "hip-hop", "EDM", "장르 무관"])
    st.text("키워드(최대 3개까지 허용)")
    col1, col2, col3 = st.columns(3)
    with col1:
        keyword_one = st.text_input(
            placeholder="키워드 1",
            label="keyword_1",
            key="keyword_1"
        )
    with col2:
        keyword_two = st.text_input(
            placeholder="키워드 2",
            label="keyword_2",
            key="keyword_2"
        )
    with col3:
        keyword_three = st.text_input(
            placeholder="키워드 3",
            label="keyword_3",
            key="keyword_3"
        )
    submitted = st.form_submit_button("Submit")
    if submitted:
        if not condition:
            st.error("상황을 입력해주세요")
        elif not desc:
            st.error("음악의 분위기/느낌을 입력해주세요")
        else:
            with st.spinner('당신의 음악을 찾고 있습니다!!!'):
                keywords = [keyword_one, keyword_two, keyword_three]
                keywords = [x for x in keywords if x]
                prompt = generate_prompt(condition, desc, keywords, genres)
                response = request_chat_completion(prompt)
                write_prompt_result(prompt, response)
                st.text_area(
                    label="당신의 선택을 받게 될 음악은?",
                    value=response,
                    placeholder="아직 추천된 음악이 없습니다.",
                    height=200
                )
