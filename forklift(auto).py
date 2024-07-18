import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# CSV 파일 URL
csv_url = "https://raw.githubusercontent.com/HliB8113/01Table/main/fl.csv"

# 데이터 불러오기
@st.cache_data
def load_data(url):
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
    except pd.errors.ParserError as e:
        st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None
    
    # 시간대를 시간 형식으로 변환
    try:
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
    except ValueError:
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M')

    # 시작 날짜를 날짜 형식으로 변환
    df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
    df['월'] = df['시작 날짜'].dt.month

    # 12월 데이터 제외
    df = df[df['월'] != 12]

    return df

df = load_data(csv_url)

if df is not None:
    # 필터링 가능한 드롭다운 메뉴를 생성하기 전에 열이 존재하는지 확인
    def get_unique_values(column_name):
        if column_name in df.columns:
            return sorted(df[column_name].dropna().unique().tolist())
        else:
            return []

    # 사이드바 설정
    with st.sidebar:
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_month = st.selectbox('월 선택:', ['전체'] + get_unique_values('월'))
        selected_department = st.selectbox('부서 선택:', ['전체'] + get_unique_values('부서'))
        selected_process = st.selectbox('공정 선택:', ['전체'] + get_unique_values('공정'))
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + get_unique_values('차대 분류'))
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

    # 변수 초기화
    title = "분석 대기 중..."
    index_name = "데이터 선택"

    def generate_pivot(month, department, process, forklift_class):
        filtered_df = df.copy()
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if process != '전체':
            filtered_df = filtered_df[filtered_df['공정'] == process]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]

        if analysis_type == '운영 대수':
            index_name = '시작 날짜'
            value_name = '차대 코드'
            agg_func = 'nunique'
            title = '지게차 일자별 운영 대수'
        else:
            index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'

        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, index_name

    pivot_table, title, index_name = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    tooltip_texts = [[f'{analysis_type} {int(val)}{"대" if analysis_type == "운영 대수" else "번"}' for val in row] for row in pivot_table.values]
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=tooltip_texts
    )
    fig.add_trace(heatmap)
    fig.update_layout(
        title=title,
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title=index_name),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=100, b=50),
        width=900,  # 고정된 너비
        height=graph_height  # 조정 가능한 높이
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("데이터를 불러오는 데 실패했습니다.")
