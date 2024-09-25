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
            
            # 월 전체 운영 대수 계산
            total_operating_units = filtered_df[value_name].nunique()
            
            # 월 최소 및 최대 운영 대수 계산
            daily_counts = filtered_df.groupby('시작 날짜')[value_name].nunique()
            min_operating_units = daily_counts.min()
            max_operating_units = daily_counts.max()
            min_operating_day = daily_counts.idxmin()
            max_operating_day = daily_counts.idxmax()
            avg_operating_units = round(daily_counts.mean())

            # 비율 계산
            min_operating_units_ratio = (min_operating_units / total_operating_units) * 100
            max_operating_units_ratio = (max_operating_units / total_operating_units) * 100
            avg_operating_units_ratio = (avg_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0

            summary = {
                'total_units': total_operating_units,
                'min_units': min_operating_units,
                'min_units_day': min_operating_day,
                'min_units_ratio': min_operating_units_ratio,
                'max_units': max_operating_units,
                'max_units_day': max_operating_day,
                'max_units_ratio': max_operating_units_ratio,
                'avg_units': avg_operating_units,
                'avg_units_ratio' : avg_operating_units_ratio
            }
        else:
            index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'
            
            # 월 최소 및 최대 운영 횟수 계산
            unit_counts = filtered_df.groupby(['차대 코드'])['시작 날짜'].count()
            min_operating_counts = unit_counts.min()
            max_operating_counts = unit_counts.max()
            min_operating_unit = unit_counts.idxmin()
            max_operating_unit = unit_counts.idxmax()
            avg_operating_counts = round(unit_counts.mean())

            # 전체 운영 횟수 계산
            total_operating_counts = unit_counts.sum()
            
            # 비율 계산
            min_operating_counts_ratio = (min_operating_counts / total_operating_counts) * 100
            max_operating_counts_ratio = (max_operating_counts / total_operating_counts) * 100
            avg_operating_counts_ratio = (avg_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0

            # 운영 시간 계산
            filtered_df['운영 시간(초)'] = filtered_df['운영 시간(초)'].astype(int)
            operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
            min_operating_time = operating_times.min()
            max_operating_time = operating_times.max()
            min_time_unit = operating_times.idxmin()
            max_time_unit = operating_times.idxmax()
            avg_operating_time = round(operating_times.mean())
            
            # 전체 운영 시간 계산
            total_operating_time = operating_times.sum()

            # 비율 계산
            min_operating_time_ratio = (min_operating_time / total_operating_time) * 100
            max_operating_time_ratio = (max_operating_time / total_operating_time) * 100
            avg_operating_time_ratio = (avg_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
            
            def format_time(seconds):
                hours, seconds = divmod(seconds, 3600)
                minutes, seconds = divmod(seconds, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"

            min_operating_time_formatted = format_time(min_operating_time)
            max_operating_time_formatted = format_time(max_operating_time)
            avg_operating_time_formatted = format_time(avg_operating_time)
            total_operating_time_formatted = format_time(total_operating_time)
            
            summary = {
                'total_counts': total_operating_counts,
                'min_counts': min_operating_counts,
                'min_counts_unit': min_operating_unit,
                'min_counts_ratio': min_operating_counts_ratio,
                'max_counts': max_operating_counts,
                'max_counts_unit': max_operating_unit,
                'max_counts_ratio': max_operating_counts_ratio,
                'avg_counts': avg_operating_counts,
                'avg_counts_ratio': avg_operating_counts_ratio,
                'total_time': total_operating_time_formatted,
                'min_time': min_operating_time_formatted,
                'min_time_unit': min_time_unit,
                'min_time_ratio': min_operating_time_ratio,
                'max_time': max_operating_time_formatted,
                'max_time_unit': max_time_unit,
                'max_time_ratio': max_operating_time_ratio,
                'avg_time': avg_operating_time_formatted,
                'avg_time_ratio': avg_operating_time_ratio
            }
        
        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, index_name, summary

    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace)

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
        title={
            'text': title,
            'x': 0.5
        },
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title=index_name, categoryorder='array', categoryarray=sorted(pivot_table.index)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=150, b=50),
        width=900,  # 고정된 너비
        height=graph_height  # 조정 가능한 높이
    )
    
    # 모든 '시작 날짜'를 세로축에 표시 (월일만 표시)
    if analysis_type == '운영 대수':
        fig.update_yaxes(type='category', tickmode='array', tickvals=sorted(pivot_table.index))

    # 요약 정보를 가로로 배치하여 표시
    if analysis_type == '운영 대수':
        summary_text = (
            f"<b>운영 대수</b><br>"
            f"전체: {int(summary.get('total_units', 0))}대<br>"
            f"최소: {summary.get('min_units_day', 'N/A')} {int(summary.get('min_units', 0))}대 ({float(summary.get('min_units_ratio', 0)):0.2f}%)<br>"
            f"최대: {summary.get('max_units_day', 'N/A')} {int(summary.get('max_units', 0))}대 ({float(summary.get('max_units_ratio', 0)):0.2f}%)<br>"
            f"평균: {float(summary.get('avg_units', 0)):0.2f}대 ({float(summary.get('avg_units_ratio', 0)):0.2f}%)<br>"
            f"<b>운영 횟수</b><br>"
        )
    else:
        summary_text = (
           f"<b>운영 횟수</b><br>"
            f"전체: {int(summary.get('total_counts', 0))}번<br>"
            f"최소: {summary.get('min_counts_unit', 'N/A')} {int(summary.get('min_counts', 0))}번 ({float(summary.get('min_counts_ratio', 0)):0.2f}%)<br>"
            f"최대: {summary.get('max_counts_unit', 'N/A')} {int(summary.get('max_counts', 0))}번 ({float(summary.get('max_counts_ratio', 0)):0.2f}%)<br>"
            f"평균: {float(summary.get('avg_counts', 0)):0.2f}번 ({float(summary.get('avg_counts_ratio', 0)):0.2f}%)<br>"
            f"<b>운영 시간</b><br>"
            f"전체: {summary.get('total_time', 'N/A')}<br>"
            f"최소: {summary.get('min_time_unit', 'N/A')} {summary.get('min_time', 'N/A')} ({float(summary.get('min_time_ratio', 0)):0.2f}%)<br>"
            f"최대: {summary.get('max_time_unit', 'N/A')} {summary.get('max_time', 'N/A')} ({float(summary.get('max_time_ratio', 0)):0.2f}%)<br>"
            f"평균: {summary.get('avg_time', 'N/A')} ({float(summary.get('avg_time_ratio', 0)):0.2f}%)<br>"
        )
    
    # 요약 정보 위치 조정 (그래프 높이에 따라)
    annotation_y = 1.015 + (150 / graph_height)

    fig.add_annotation(
        text=summary_text,
        align='left',
        showarrow=False,
        xref='paper',
        yref='paper',
        x=0,
        y=annotation_y,
        bordercolor='black',
        borderwidth=1,
        bgcolor='white',
        opacity=0.8,
        font=dict(color='black', size=20)  # 텍스트 색상을 검은색으로 지정, 폰트 크기 조정
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
