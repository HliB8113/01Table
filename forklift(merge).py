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

# 메인 함수
def main():
    # Streamlit 사이드바 설정
    with st.sidebar:
        uploaded_file = st.file_uploader("파일을 업로드하세요.", type=["csv"])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                df = validate_and_preprocess_data(df)
                if df is None:
                    return
                
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

                # 데이터 분석 및 그래프 생성
                create_analysis(df, analysis_type, selected_month, selected_department, selected_process, 
                                selected_forklift_class, selected_workplace, graph_height)

            except Exception as e:
                st.error(f"파일 로딩 중 오류 발생: {str(e)}")

def create_analysis(df, analysis_type, selected_month, selected_department, selected_process, 
                    selected_forklift_class, selected_workplace, graph_height):
    # generate_pivot 함수 정의 (이전 코드와 동일)
    def generate_pivot(month, department, process, forklift_class, workplace):
        # ... (이전 코드와 동일)

    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, 
                                                             selected_process, selected_forklift_class, 
                                                             selected_workplace)

    if pivot_table is not None and not pivot_table.empty:
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
            title={'text': title, 'x': 0.5},
            xaxis=dict(title='시간대', fixedrange=True),
            yaxis=dict(title=index_name, categoryorder='array', categoryarray=sorted(pivot_table.index)),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=150, b=50),
            width=900,
            height=graph_height
        )
        
        if analysis_type == '운영 대수':
            fig.update_yaxes(type='category', tickmode='array', tickvals=sorted(pivot_table.index))

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
            font=dict(color='black', size=12)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("데이터를 표시할 수 없습니다. 선택한 조건을 확인해 주세요.")

if __name__ == "__main__":
    main()
