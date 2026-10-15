import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 데이터 로딩 (캐싱 적용)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="우리 동네 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="centered"
)

# 데이터 URL 정의
DATA_URL = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"

@st.cache_data
def load_data():
    """
    원격 ZIP 파일에서 인구 데이터를 읽어온 뒤 가장 최신 연도 데이터만 필터링합니다.
    st.cache_data를 사용하여 데이터 로딩 및 처리 속도를 최적화합니다.
    """
    # pandas는 zip 압축 파일을 자동으로 해제하여 CSV로 읽습니다.
    df = pd.read_csv(DATA_URL)
    
    # '연도' 컬럼을 숫자로 변환 후 가장 최신 연도(최대값)만 추출합니다.
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 앱 실행 시 타이틀 및 설명 표시
st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.write("지역을 선택하여 연령대별 남녀 인구 구성을 한눈에 확인해보세요.")

# 데이터 불러오기
try:
    data, latest_year = load_data()
    st.caption(f"기준 연도: **{latest_year}년**")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 2. 지역 선택 드롭다운 (시도 -> 시군구 -> 동)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")

# 1단계: 시도 선택
sido_list = sorted(data['시도'].dropna().unique())
selected_sido = st.selectbox("시·도 선택", sido_list)

# 선택된 시도에 해당하는 데이터 필터링
filtered_sido = data[data['시도'] == selected_sido]

# 2단계: 시군구 선택
sigungu_list = sorted(filtered_sido['시군구'].dropna().unique())
selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

# 선택된 시군구에 해당하는 데이터 필터링
filtered_sigungu = filtered_sido[filtered_sido['시군구'] == selected_sigungu]

# 3단계: 읍·면·동 선택
dong_list = sorted(filtered_sigungu['동'].dropna().unique())
selected_dong = st.selectbox("읍·면·동 선택", dong_list)

# 최종 선택된 동네의 1개 행 데이터 가져오기
target_row = filtered_sigungu[filtered_sigungu['동'] == selected_dong].iloc[0]

# -----------------------------------------------------------------------------
# 3. 나이대별 남/여 인구 데이터 정리
# -----------------------------------------------------------------------------
# 0세부터 99세까지 + 100세 이상 라벨 생성 (0세가 맨 아래, 100세 이상이 맨 위로 가게 순서 정의)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []

# 각 나이 라벨에 맞춰 해당 열의 인구수를 가져옵니다.
for age in age_labels:
    male_col = f"남_{age}"
    female_col = f"여_{age}"
    
    # 피라미드 그래프의 왼쪽(남자)은 음수로, 오른쪽(여자)은 양수로 설정합니다.
    m_val = target_row.get(male_col, 0)
    f_val = target_row.get(female_col, 0)
    
    male_pop.append(-int(m_val))  # 남자는 왼쪽 배치를 위해 음수
    female_pop.append(int(f_val))   # 여자는 오른쪽 배치를 위해 양수

# -----------------------------------------------------------------------------
# 4. Plotly 인구 피라미드 가로 막대그래프 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# 남자 막대 그래프 (왼쪽, 포근한 파란색 계열)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_pop,
    name="남자",
    orientation='h',
    marker=dict(color='#5B8FF9'),
    # 마우스 호버 시 음수 기호를 제거하고 정수로 보이게 설정
    customdata=[-x for x in male_pop],
    hovertemplate="남자 %{y}: %{customdata:,}명<extra></extra>"
))

# 여자 막대 그래프 (오른쪽, 따뜻한 핑크/코랄 계열)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name="여자",
    orientation='h',
    marker=dict(color='#FF7875'),
    hovertemplate="여자 %{y}: %{x:,}명<extra></extra>"
))

# X축 표시값의 최댓값을 구하여 좌우 대칭 범위를 설정
max_val = max(max([-x for x in male_pop]), max(female_pop))
# 여유 공간 10% 추가 (최소값 10명 설정)
limit = max(int(max_val * 1.1), 10)

# 그래프 레이아웃 및 축 설정
fig.update_layout(
    title=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드",
    title_font_size=20,
    barmode='overlay',  # 두 막대가 중앙 축 기준으로 나뉘도록 설정
    bargap=0.1,
    height=800,         # 100개 이상의 나이대를 명확히 보여주기 위해 높이 지정
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(245,247,250,0.5)',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    xaxis=dict(
        title="인구수 (명)",
        range=[-limit, limit],
        # X축 눈금에 음수 기호(-)를 없애고 양수로 표시
        tickvals=list(range(-limit, limit + 1, max(1, limit // 4))),
        ticktext=[f"{abs(v):,}" for v in range(-limit, limit + 1, max(1, limit // 4))]
    ),
    yaxis=dict(
        title="연령",
        # 축 뒤집기 옵션 없이, age_labels의 0번째(0세)가 맨 아래, 마지막(100세 이상)이 맨 위에 오도록 카테고리 순서 고정
        type='category',
        categoryorder='array',
        categoryarray=age_labels,
        dtick=5  # 눈금을 5세 단위로 표시하여 가독성 확보
    )
)

# Streamlit에 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# 하단 안내 문구
st.info("💡 **팁:** 그래프 위로 마우스를 올리면 각 나이별 정확한 인구수를 확인할 수 있습니다.")
