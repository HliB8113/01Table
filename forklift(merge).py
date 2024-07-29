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
        try:
            df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
        except ValueError:
            df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M')

        # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df['월'] = df['시작 날짜'].dt.month

        # 12월 데이터 제외
        df = df[df['월'] != 12]

        # 드롭다운 메뉴 설정
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().tolist()))
        selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
        selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals():
    def generate_pivot(month, department, process, forklift_class, workplace):
        filtered_df = df.copy()
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if process != '전체':
            filtered_df = filtered_df[filtered_df['공정'] == process]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체':
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        if analysis_type == '운영 대수':
            filtered_df['시작 날짜'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
            index_name = '시작 날짜'
            value_name = '차대 코드'
            agg_func = 'nunique'
            title = '지게차 일자별 운영 대수'

            # 월 전체 운영 대수, 최소/최대 운영 대수 계산
            total_operation = filtered_df[value_name].nunique()
            daily_counts = filtered_df.groupby('시작 날짜')[value_name].nunique()
            min_operation = daily_counts.min()
            max_operation = daily_counts.max()
            min_operation_date = daily_counts.idxmin()
            max_operation_date = daily_counts.idxmax()

            metrics = f"""
            월 전체 운영 대수: {total_operation}대
            최소 운영 대수: {min_operation_date} {min_operation}대
            최대 운영 대수: {max_operation_date} {max_operation}대
            """

        else:
            index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'

            # 월 최소/최대 운영 횟수 및 시간 계산
            total_counts = filtered_df.groupby(['차대 코드', '시작 날짜']).size()
            min_operation = total_counts.min()
            max_operation = total_counts.max()
            min_operation_forklift = total_counts.idxmin()
            max_operation_forklift = total_counts.idxmax()

            filtered_df['운영 시간'] = pd.to_timedelta(filtered_df['운영 시간'], unit='s')
            total_times = filtered_df.groupby(['차대 코드', '시작 날짜'])['운영 시간'].sum()
            min_time = total_times.min()
            max_time = total_times.max()
            min_time_forklift = total_times.idxmin()
            max_time_forklift = total_times.idxmax()

            min_time_str = f"{min_time.components.minutes:02}:{min_time.components.seconds:02}"
            max_time_str = f"{max_time.components.minutes:02}:{max_time.components.seconds:02}"

            metrics = f"""
            최소 운영 횟수 지게차: {min_operation_forklift} {min_operation}번
            최대 운영 횟수 지게차: {max_operation_forklift} {max_operation}번
            최소 운영시간 지게차: {min_time_forklift} {min_time_str}
            최대 운영 시간 지게차: {max_time_forklift} {max_time_str}
            """

        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, index_name, metrics

    pivot_table, title, index_name, metrics = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    tooltip_texts = [[f'{analysis_type} {int(val)}{"대" if analysis_type == "운영 대수" else "번"}' for val in row] for row in pivot_table.values]
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=tooltip_texts,
        zmin=0,
        zmax=pivot_table.values.max()
    )
    fig.add_trace(heatmap)
    fig.update_layout(
        title=title,
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title=index_name, categoryorder='array', categoryarray=sorted(pivot_table.index)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=100, b=50),
        width=900,  # 고정된 너비
        height=graph_height  # 조정 가능한 높이
    )
    
    # 모든 '시작 날짜'를 세로축에 표시 (월일만 표시)
    if analysis_type == '운영 대수':
        fig.update_yaxes(type='category', tickmode='array', tickvals=sorted(pivot_table.index))

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)

    # 계산된 값들 출력
    st.markdown(metrics)
