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
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜']).dt.strftime('%Y-%m-%d')  # 날짜 형식을 년-월-일로 조정
        df = df.sort_values(by=['시간대'])
        df.dropna(subset=['부서', '차대 분류'], inplace=True)

        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_department = st.selectbox('부서 선택:', ['전체'] + df['부서'].dropna().unique().tolist())
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + df['차대 분류'].dropna().unique().tolist())
        graph_height = st.slider('Select graph height', 300, 1500, 900)

        # 날짜 선택 슬라이더 구성
        if '시작 날짜' in df:
            date_options = sorted(df['시작 날짜'].unique())
            if date_options:
                selected_date = st.select_slider('Select date', options=date_options, value=date_options[0])

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals() and 'selected_date' in locals():
    def generate_pivot(department, forklift_class):
        filtered_df = df[df['시작 날짜'] == selected_date]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]

        if analysis_type == '운영 대수':
            index_name = '시작 날짜'
            value_name = '차대 코드'
            agg_func = 'nunique'
            title = '시작 날짜 및 시간대별 차대 코드 운영 대수 Heatmap'
            text_template = '운영 대수: %{text}대'
        else:
            index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '차대 코드별 시간대 운영 횟수 Heatmap'
            text_template = '운영 횟수: %{text}번'

        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, index_name, text_template

    pivot_table, title, index_name, text_template = generate_pivot(selected_department, selected_forklift_class)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=[[f'{int(val)}' for val in row] for row in pivot_table.values],
        texttemplate=text_template
    )
    fig.add_trace(heatmap)
    fig.update_layout(
        title=title,
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title=index_name),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=100, b=50),
        width=900,
        height=graph_height
    )

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
