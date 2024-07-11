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

        # 날짜 데이터 정제 및 필터링
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')  # 'coerce' 옵션을 사용해 오류가 있는 날짜는 NaT로 변환
        df = df[df['시작 날짜'].dt.month == 5]  # 5월 데이터만 필터링
        df['시작 날짜'] = df['시작 날짜'].dt.strftime('%d')  # 일자 포맷으로 변경

        df = df.sort_values(by=['시작 날짜', '시간대'])
        df.dropna(subset=['부서', '차대 분류', '시작 날짜'], inplace=True)  # '시작 날짜'도 결측치 제거 대상에 추가

        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_department = st.selectbox('부서 선택:', ['전체'] + df['부서'].dropna().unique().tolist())
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + df['차대 분류'].dropna().unique().tolist())

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals():
    def generate_pivot(department, forklift_class):
        filtered_df = df.copy()
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]

        if analysis_type == '운영 대수':
            value_name = '차대 코드'
            agg_func = 'nunique'
            title = '시작 날짜별 차대 코드 운영 대수 Heatmap'
        else:
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '시작 날짜별 운영 횟수 Heatmap'

        pivot_table = filtered_df.pivot_table(index='시간대', columns='시작 날짜', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title

    pivot_table, title = generate_pivot(selected_department, selected_forklift_class)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text'
    )
    fig.add_trace(heatmap)
    fig.update_layout(
        title=title,
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title='시작 날짜'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=100, b=50)
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
