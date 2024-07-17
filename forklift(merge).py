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

        # 파일 내용 확인 (디버깅을 위해)
        st.write("파일의 첫 5줄을 확인하세요:", df.head())

        # 시간대를 시간 형식으로 변환
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

        # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df['월'] = df['시작 날짜'].dt.month

        # 분석 유형 선택
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        
        # 월 드롭다운 추가
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].unique().tolist()))

        # 차대 분류 선택
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + df['차대 분류'].dropna().unique().tolist())
        
        # 부서 선택
        selected_department = st.selectbox('부서 선택:', ['전체'] + df['부서'].dropna().unique().tolist())
        
        # 공정 선택
        selected_process = st.selectbox('공정 선택:', ['전체'] + df['공정'].dropna().unique().tolist())

        graph_height = st.slider('Select graph height', 300, 1500, 900)

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals():
    def generate_pivot(department, forklift_class, process, month):
        filtered_df = df.copy()
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if process != '전체':
            filtered_df = filtered_df[filtered_df['공정'] == process]
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]

        if analysis_type == '운영 대수':
            index_name = '시작 날짜'
            value_name = '차대 코드'
            agg_func = 'nunique'
            title = '지게차 일자별 운영 대수'
            filtered_df['시작 날짜'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')  # 날짜 형식 변경
        else:
            index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'
            filtered_df['시작 날짜'] = filtered_df['시작 날짜'].dt.strftime('%Y-%m-%d')  # 날짜 형식 유지

        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, index_name

    pivot_table, title, index_name = generate_pivot(selected_department, selected_forklift_class, selected_process, selected_month)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=[[f' {analysis_type} {int(val)}대' if analysis_type == '운영 대수' else f' {analysis_type} {int(val)}번' for val in row] for row in pivot_table.values]
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
