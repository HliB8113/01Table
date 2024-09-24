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
            agg_func = lambda x: x.nunique()  # 고유한 값의 수를 계산하여 중복 제거
            title = '지게차 일자별 운영 대수'
            
            # 차대 코드가 부서별로 중복될 수 있으므로, 중복 제거
            filtered_df = filtered_df.drop_duplicates(subset=['차대 코드', '부서'])

            # 월 전체 운영 대수 계산
            total_operating_units = filtered_df[value_name].nunique()

            # 월 최소 및 최대 운영 대수 계산
            daily_counts = filtered_df.groupby('시작 날짜')[value_name].nunique()
            min_operating_units = daily_counts.min()
            max_operating_units = daily_counts.max()
            min_operating_day = daily_counts.idxmin()
            max_operating_day = daily_counts.idxmax()

            # 비율 계산
            min_operating_units_ratio = (min_operating_units / total_operating_units) * 100
            max_operating_units_ratio = (max_operating_units / total_operating_units) * 100
            
            summary = {
                'total_units': total_operating_units,
                'min_units': min_operating_units,
                'min_units_day': min_operating_day,
                'min_units_ratio': min_operating_units_ratio,
                'max_units': max_operating_units,
                'max_units_day': max_operating_day,
                'max_units_ratio': max_operating_units_ratio,
            }
        else:
            # 기타 분석 유형의 코드는 변경되지 않았습니다.
            pass

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
            f"전체: {summary.get('total_units', 'N/A')}대<br>"
            f"최소: {summary.get('min_units_day', 'N/A')} {summary.get('min_units', 'N/A')}대 ({summary.get('min_units_ratio', 0):.2f}%)<br>"
            f"최대: {summary.get('max_units_day', 'N/A')} {summary.get('max_units', 'N/A')}대 ({summary.get('max_units_ratio', 0):.2f}%)<br>"
        )
    else:
        summary_text = (
            f"<b>운영 횟수</b><br>"
            f"전체: {summary.get('total_counts', 'N/A')}번<br>"
            f"최소: {summary.get('min_counts_unit', 'N/A')} {summary.get('min_counts', 'N/A')}번 ({summary.get('min_counts_ratio', 0):.2f}%)<br>"
            f"최대: {summary.get('max_counts_unit', 'N/A')} {summary.get('max_counts', 'N/A')}번 ({summary.get('max_counts_ratio', 0):.2f}%)<br>"
            f"<br><b>운영 시간</b><br>"
            f"전체: {summary.get('total_time', 'N/A')}<br>"
            f"최소: {summary.get('min_time_unit', 'N/A')} {summary.get('min_time', 'N/A')} ({summary.get('min_time_ratio', 0):.2f}%)<br>"
            f"최대: {summary.get('max_time_unit', 'N/A')} {summary.get('max_time', 'N/A')} ({summary.get('max_time_ratio', 0):.2f}%)"
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
        font=dict(color='black', size=12)  # 텍스트 색상을 검은색으로 지정, 폰트 크기 조정
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
