import streamlit as st
import pandas as pd
from io import BytesIO
import requests

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# 파일 URL
FILE_URL = 'https://yourhost.com/yourfile.xlsx'  # Excel 파일의 URL을 입력하세요

# 비밀번호 입력
password = st.sidebar.text_input("파일 비밀번호를 입력하세요:", type="password")

if password:
    # 파일을 로드하는 함수
    def load_protected_excel(url, password):
        try:
            response = requests.get(url)
            file = BytesIO(response.content)
            return pd.read_excel(file, engine='openpyxl', password=password)
        except Exception as e:
            st.error(f'파일 로딩 중 오류가 발생했습니다: {e}')
            return None

    # 데이터프레임 로드
    df = load_protected_excel(FILE_URL, password)

    if df is not None:
        st.write('파일이 성공적으로 로드되었습니다.')
        # 데이터 처리 및 대시보드 로직 추가

        # 예를 들어, 데이터프레임을 화면에 출력
        st.dataframe(df)

import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# Streamlit 사이드바 설정
with st.sidebar:
    uploaded_file = st.file_uploader("파일을 업로드하세요.", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M').dt.strftime('%H:%M')

        # 날짜를 일자로 파싱하고 특정 월(예: 5월) 데이터만 필터링
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df = df[df['시작 날짜'].dt.month == 5]  # 5월 데이터만 선택
        df['시작 날짜'] = df['시작 날짜'].dt.strftime('%d')  # 일자 형식으로 변경

        df = df.sort_values(by=['시작 날짜', '시간대'])
        df.dropna(subset=['부서', '차대 분류'], inplace=True)

        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_department = st.selectbox('부서 선택:', ['전체'] + df['부서'].dropna().unique().tolist())
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + df['차대 분류'].dropna().unique().tolist())
        graph_height = st.slider('Select graph height', 300, 1500, 900)

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals():
    def generate_pivot(department, forklift_class):
        filtered_df = df.copy()
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
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

    pivot_table, title, index_name = generate_pivot(selected_department, selected_forklift_class)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=[[f' {analysis_type} {int(val)}번' for val in row] for row in pivot_table.values]
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

