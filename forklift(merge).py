import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def format_time(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# Streamlit 사이드바 설정
with st.sidebar:
    uploaded_file = st.file_uploader("파일을 업로드하세요.", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df['시간대'] = pd.to_datetime(df['시간대'], errors='coerce').dt.strftime('%H:%M')
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df['월'] = df['시작 날짜'].dt.month
        df = df[df['월'] != 12]

        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().tolist()))
        selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
        selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

# 이후 코드는 위에서 제공한 전체 코드와 동일합니다.


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
            
            # 전체, 최소, 최대, 평균 운영 대수 계산
            daily_counts = filtered_df.groupby('시작 날짜')[value_name].nunique()
            total_operating_units = daily_counts.sum()
            min_operating_units = daily_counts.min()
            max_operating_units = daily_counts.max()
            avg_operating_units = daily_counts.mean()
            min_operating_day = daily_counts.idxmin()
            max_operating_day = daily_counts.idxmax()

            summary = {
                'total_units': total_operating_units,
                'min_units': min_operating_units,
                'min_units_day': min_operating_day,
                'max_units': max_operating_units,
                'max_units_day': max_operating_day,
                'avg_units': avg_operating_units
            }
        else:
            index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'
            
            # 전체, 최소, 최대, 평균 운영 횟수 및 시간 계산
            unit_counts = filtered_df.groupby(['차대 코드'])['시작 날짜'].count()
            total_operating_counts = unit_counts.sum()
            min_operating_counts = unit_counts.min()
            max_operating_counts = unit_counts.max()
            avg_operating_counts = unit_counts.mean()
            min_operating_unit = unit_counts.idxmin()
            max_operating_unit = unit_counts.idxmax()

            # 전체, 최소, 최대, 평균 운영 시간 계산
            operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
            total_operating_time = operating_times.sum()
            min_operating_time = operating_times.min()
            max_operating_time = operating_times.max()
            avg_operating_time = operating_times.mean()
            min_time_unit = operating_times.idxmin()
            max_time_unit = operating_times.idxmax()
            
            summary = {
                'total_counts': total_operating_counts,
                'min_counts': min_operating_counts,
                'min_counts_unit': min_operating_unit,
                'max_counts': max_operating_counts,
                'max_counts_unit': max_operating_unit,
                'avg_counts': avg_operating_counts,
                'total_time': total_operating_time,
                'min_time': min_operating_time,
                'min_time_unit': min_time_unit,
                'max_time': max_operating_time,
                'max_time_unit': max_time_unit,
                'avg_time': avg_operating_time
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
    
    # 요약 정보를 업데이트하여 평균값을 포함하도록 조정
    if analysis_type == '운영 대수':
        summary_text = (
            f"<b>운영 대수</b><br>"
            f"전체: {summary['total_units']}대<br>"
            f"최소: {summary['min_units_day']} {summary['min_units']}대<br>"
            f"최대: {summary['max_units_day']} {summary['max_units']}대<br>"
            f"평균: {summary['avg_units']:.2f}대"
        )
    else:
        summary_text = (
            f"<b>운영 횟수 및 시간</b><br>"
            f"전체 횟수: {summary['total_counts']}번<br>"
            f"최소: {summary['min_counts_unit']} {summary['min_counts']}번<br>"
            f"최대: {summary['max_counts_unit']} {summary['max_counts']}번<br>"
            f"평균 횟수: {summary['avg_counts']:.2f}번<br>"
            f"<br>"
            f"전체 시간: {format_time(summary['total_time'])}<br>"
            f"최소: {summary['min_time_unit']} {format_time(summary['min_time'])}<br>"
            f"최대: {summary['max_time_unit']} {format_time(summary['max_time'])}<br>"
            f"평균 시간: {format_time(summary['avg_time'])}"
        )

    # Streamlit을 통해 업데이트된 요약 정보와 플롯을 표시
    st.plotly_chart(fig, use_container_width=True)
