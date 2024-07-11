import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='collapsed')

# 사이드바 옵션
with st.sidebar:
    uploaded_file = st.file_uploader("파일을 업로드하세요.", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M').dt.strftime('%H:%M')
        df = df.sort_values(by=['시간대'])
        df.dropna(subset=['부서', '차대 분류'], inplace=True)

        # 분석 유형 선택
        analysis_type = st.radio(
            "분석 유형 선택:",
            ('운영 대수', '운영 횟수')
        )

        # 선택 상자를 통한 부서와 차대 분류 선택
        menu_width = st.slider('조정 메뉴 너비', 100, 300, 150)
        st.markdown(f'<style>.stSelectbox{{width: {menu_width}px;}}</style>', unsafe_allow_html=True)
        selected_department = st.selectbox(
            '부서 선택:',
            ['전체'] + df['부서'].dropna().unique().tolist()
        )
        selected_forklift_class = st.selectbox(
            '차대 분류 선택:',
            ['전체'] + df['차대 분류'].dropna().unique().tolist()
        )

        # 그래프 높이 슬라이더
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900, step=50, orientation='vertical')

if uploaded_file is not None:
    # 데이터 전처리 및 피벗 테이블 생성
    if analysis_type == '운영 대수':
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜']).dt.strftime('%d')
        df = df.sort_values(by=['시작 날짜', '시간대'])
        index_name = '시작 날짜'
        value_name = '차대 코드'
        agg_func = 'nunique'
        title = '시작 날짜 및 시간대별 차대 코드 운영 대수 Heatmap'
    else:
        index_name = '차대 코드'
        value_name = '시작 날짜'
        agg_func = 'count'
        title = '차대 코드별 시간대 운영 횟수 Heatmap'

    pivot_table = generate_pivot(selected_department, selected_forklift_class)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=[[f'{int(val)}번' for val in row] for row in pivot_table.values]
    )
    fig.add_trace(heatmap)
    fig.update_layout(
        title=title,
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title=index_name),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=100, b=50)
    )
    fig.update_layout(width=900, height=graph_height)

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
