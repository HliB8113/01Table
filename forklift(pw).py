import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import msoffcrypto
import io
import requests

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# 파일 URL 설정
file_url = "https://github.com/HliB8113/01Table/raw/main/%EC%A7%80%EA%B2%8C%EC%B0%A8%20%EC%97%91%EC%85%80.xlsx"

# 사용자에게 파일 비밀번호 입력 받기
input_password = st.sidebar.text_input("파일 암호 입력:", type="password")

# 파일 다운로드 및 로드
if input_password:
    try:
        # 파일을 요청하고 BytesIO로 바로 읽기
        response = requests.get(file_url)
        encrypted_file = io.BytesIO(response.content)
        
        # msoffcrypto를 사용하여 파일 열기
        file = msoffcrypto.OfficeFile(encrypted_file)
        file.load_key(password=input_password)  # 비밀번호 제공
        
        # 해독된 내용을 새로운 BytesIO 객체로 추출
        decrypted_file = io.BytesIO()
        file.decrypt(decrypted_file)

        # pandas로 데이터 로드
        decrypted_file.seek(0)  # 포인터를 파일 시작 부분으로 이동
        df = pd.read_excel(decrypted_file)

        # 데이터 전처리
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M').dt.strftime('%H:%M')
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
        df = df[df['시작 날짜'].dt.month == 5]  # 5월 데이터만 선택
        df['시작 날짜'] = df['시작 날짜'].dt.strftime('%d')  # 일자 형식으로 변경
        df = df.sort_values(by=['시작 날짜', '시간대'])
        df.dropna(subset=['부서', '차대 분류'], inplace=True)

        # 분석 유형 선택
        analysis_type = st.sidebar.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_department = st.sidebar.selectbox('부서 선택:', ['전체'] + df['부서'].dropna().unique().tolist())
        selected_forklift_class = st.sidebar.selectbox('차대 분류 선택:', ['전체'] + df['차대 분류'].dropna().unique().tolist())
        graph_height = st.sidebar.slider('그래프 높이 선택', 300, 1500, 900)

        # 피벗 테이블 생성 및 시각화
        def generate_pivot(department, forklift_class):
            filtered_df = df.copy()
            if department != '전체':
                filtered_df = filtered_df[filtered_df['부서'] == department]
            if forklift_class != '전체':
                filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]

            if analysis_type == '운영 대수':
                index_name = '시작 날짜'
                value_name = '차대 코드'
                agg_func = 'nunique'
                title = '지게차 일자별 운영 대수'
            else:
                index_name = '차대 코드'
                value_name = '시작 날짜'
                agg_func = 'count'
                title = '지게차 시간대별 운영 횟수'

            pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
            return pivot_table, title

        pivot_table, title = generate_pivot(selected_department, selected_forklift_class)

        # Heatmap 생성
        fig = make_subplots(rows=1, cols=1)
        heatmap = go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale=[[0, 'white'], [1, 'purple']],
            hoverinfo='text',
            text=[[f'{analysis_type} {int(val)}번' for val in row] for row in pivot_table.values]
        )
        fig.add_trace(heatmap)
        fig.update_layout(
            title=title,
            xaxis=dict(title='시간대', fixedrange=True),
            yaxis=dict(title=index_name, fixedrange=True),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=100, b=50),
            width=900,
            height=graph_height
        )

        st.plotly_chart(fig, use_container_width=True)
        st.write(df.head())
        
    except Exception as e:
        st.error(f"파일 로드 중 에러 발생: {e}")
else:
    st.warning("엑셀 파일을 로드하려면 비밀번호를 입력해야 합니다.")
