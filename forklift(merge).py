import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit 페이지 설정
st.set_page_config(page_title='지게차 운영 분석', layout='wide', initial_sidebar_state='expanded')

# 데이터 검증 및 전처리 함수
def validate_and_preprocess_data(df):
    required_columns = ['시간대', '시작 날짜', '부서', '공정', '차대 분류', '작업 장소', '차대 코드', '운영 시간(초)']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"다음 열이 누락되었습니다: {', '.join(missing_columns)}")
        return None
    
    # '차대 분류' 열 데이터 확인 및 전처리
    df['차대 분류'] = df['차대 분류'].str.strip().str.upper()
    
    # 'C/B'와 'R/T'로 매핑
    classification_mapping = {
        'CB': 'C/B', 'C/B': 'C/B', 'C B': 'C/B',
        'RT': 'R/T', 'R/T': 'R/T', 'R T': 'R/T'
    }
    df['차대 분류'] = df['차대 분류'].map(classification_mapping).fillna('기타')
    
    # '차대 분류'가 'C/B' 또는 'R/T'가 아닌 경우 '기타'로 처리
    df.loc[~df['차대 분류'].isin(['C/B', 'R/T']), '차대 분류'] = '기타'
    
    return df

# Streamlit 사이드바 설정
with st.sidebar:
    uploaded_file = st.file_uploader("파일을 업로드하세요.", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df = validate_and_preprocess_data(df)
            if df is None:
                st.stop()
            
            # 데이터 형식 변환 및 전처리
            df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
            df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
            df['월'] = df['시작 날짜'].dt.month
            df = df[df['월'] != 12]  # 12월 데이터 제외

            # 드롭다운 메뉴 설정
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
            selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().tolist()))
            selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
            selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))
            selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체', 'C/B', 'R/T'])
            selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
            graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)
        except Exception as e:
            st.error(f"파일 로딩 중 오류 발생: {str(e)}")
            st.stop()

# 나머지 코드는 이전과 동일

# ... (중간 코드 생략)

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
            font=dict(color='black', size=12)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("데이터를 표시할 수 없습니다. 선택한 조건을 확인해 주세요.")
