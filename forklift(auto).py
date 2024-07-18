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
    df = pd.read_csv(url)
    
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

# 사이드바 설정
with st.sidebar:
    analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
    selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().tolist()))
    selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
    selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))
    selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
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
        agg_
