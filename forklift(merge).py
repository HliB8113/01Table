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
        
        # 날짜 필터링 및 포맷 설정
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df = df[df['시작 날짜'].dt.month == 5]  # 5월 데이터만 선택
        df['시작 날짜'] = df['시작 날짜'].dt.strftime('%d')  # 일자만 표시
        df = df.sort_values(by=['시작 날짜', '시간대'])
        df.dropna(subset=['부서', '차대 분류'], inplace=True)

        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_department = st.selectbox('부서 선택:', ['전체'] + df['부서'].dropna().unique().tolist())
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + df['차대 분류'].dropna().unique().tolist())
        graph_height = st.slider('Select graph height', 300, 1500, 900)

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
            title = '시작 날짜별 차대 코드 운영 대수'
            unit = '대'
        else:
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '시작 날짜별 운영 횟수'
            unit = '번'

        pivot_table = filtered_df.pivot_table(index='시간대', columns='시작 날짜', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, unit

    pivot_table, title, unit = generate_pivot(selected_department, selected_forklift_class)

    # Heatmap 생성 (애니메이션 추가)
    fig = go.Figure(
        data=[
            go.Heatmap(
                z=[pivot_table[col].values for col in pivot_table.columns],
                x=pivot_table.index,
                y=pivot_table.columns,
                colorscale=[[0, 'white'], [1, 'purple']],
                showscale=False, # 스케일 바 숨기기
            )
        ],
        layout=go.Layout(
            title=title,
            xaxis=dict(title='시간대', tickmode='array'),
            yaxis=dict(title='일자', tickmode='array'),
            height=graph_height,
            margin=dict(l=50, r=50, t=100, b=50)
        )
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
