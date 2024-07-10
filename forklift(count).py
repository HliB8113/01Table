import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='collapsed')

# Streamlit 파일 업로더를 사용하여 파일 업로드
uploaded_file = st.file_uploader("파일을 업로드하세요.", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 데이터 전처리
    df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M').dt.strftime('%H:%M')
    df['시작 날짜'] = pd.to_datetime(df['시작 날짜']).dt.strftime('%d')
    df = df.sort_values(by=['시작 날짜', '시간대'])
    df.dropna(subset=['부서', '차대 분류'], inplace=True)

    # 필터링: '부서' 열에서 상온IB, 냉동IB만
    df = df[df['부서'].isin(['상온IB', '냉동IB'])]

    # 선택 상자를 통한 부서와 차대 분류 선택
    selected_department = st.selectbox(
        '부서 선택:',
        ['전체'] + df['부서'].dropna().unique().tolist()
    )
    selected_forklift_class = st.selectbox(
        '차대 분류 선택:',
        ['전체'] + df['차대 분류'].dropna().unique().tolist()
    )

    # 피벗 테이블 생성 함수
    def generate_pivot(department, forklift_class):
        filtered_df = df.copy()
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]

        pivot_table = filtered_df.pivot_table(index='시작 날짜', columns='시간대', values='차대 코드', aggfunc='nunique').fillna(0)
        return pivot_table

    pivot_table = generate_pivot(selected_department, selected_forklift_class)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        text=[['{}'.format(int(val)) for val in row] for row in pivot_table.values],
        texttemplate="%{text}",
        hoverinfo='text+z'
    )
    fig.add_trace(heatmap)
    fig.update_layout(
        title='시작 날짜 및 시간대별 차대 코드 운영 횟수 Heatmap',
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title='시작 날짜'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=100, b=50)
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
