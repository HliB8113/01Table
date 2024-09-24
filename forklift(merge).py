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
        
        # 시간대를 시간 형식으로 변환
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M')
        
        # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df['월'] = df['시작 날짜'].dt.month

        # 12월 데이터 제외
        df = df[df['월'] != 12]

        # 분석 유형 및 필터 설정
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].unique().tolist()))
        selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].unique().tolist()))

# 데이터 분석 함수
def analyze_data(df, month, department):
    filtered_df = df.copy()
    if month != '전체':
        filtered_df = filtered_df[filtered_df['월'] == month]
    if department != '전체':
        filtered_df = filtered_df[filtered_df['부서'] == department]

    if analysis_type == '운영 대수':
        # 중복 부서 데이터 처리
        filtered_df = filtered_df.drop_duplicates(subset=['차대 코드', '부서'])
        pivot_data = filtered_df.pivot_table(index='시작 날짜', columns='시간대', values='차대 코드', aggfunc=pd.Series.nunique)
    else:
        pivot_data = filtered_df.pivot_table(index='차대 코드', columns='시간대', values='시작 날짜', aggfunc='count')

    return pivot_data

# 메인 페이지
if uploaded_file is not None:
    pivot_table = analyze_data(df, selected_month, selected_department)

    # 히트맵 생성
    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale='Viridis'
    ))
    fig.update_layout(title='운영 데이터 히트맵', xaxis_nticks=36)
    st.plotly_chart(fig, use_container_width=True)
