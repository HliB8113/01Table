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
        df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

        # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
        df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
        df['월'] = df['시작 날짜'].dt.month

        # 12월 데이터 제외
        excluded_month = 12
        df = df[df['월'] != excluded_month]

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
        def calculate_max_avg_by_time(filtered_df, value_name):
            avg_by_time = filtered_df.groupby('시간대')[value_name].mean()
            max_avg_value = avg_by_time.max()
            max_avg_time = avg_by_time.idxmax()
            return max_avg_value, max_avg_time
        def calculate_max_avg_by_time(filtered_df, value_name):
            avg_by_time = filtered_df.groupby('시간대')[value_name].nunique().mean() if value_name == '차대 코드' else filtered_df.groupby('시간대')[value_name].count().mean()
            max_by_time_series = filtered_df.groupby('시간대')[value_name].nunique()
            
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
            min_operating_day = daily_counts.idxmin() if not daily_counts.empty else '데이터 없음'
            max_operating_day = daily_counts.idxmax() if not daily_counts.empty else '데이터 없음'
            avg_operating_units = round(daily_counts.mean()) if not daily_counts.empty else 0

            # 비율 계산
            min_operating_units_ratio = (min_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
            max_operating_units_ratio = (max_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
            avg_operating_units_ratio = (avg_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0

            # 시간대별 최대 평균 운영 대수 계산
            avg_by_time_series = filtered_df.groupby('시간대')[value_name].nunique().mean()
            max_avg_units_time = filtered_df.groupby('시간대')[value_name].nunique().idxmax()
            max_avg_units = filtered_df.groupby('시간대')[value_name].nunique().max()

            
            # 시간대별 최대 평균 운영 대수 계산
            max_avg_units, max_avg_units_time = calculate_max_avg_by_time(filtered_df, value_name)
            summary = {
                'total_units': total_operating_units,
                'min_units': min_operating_units,
                'min_units_day': min_operating_day,
                'min_units_ratio': min_operating_units_ratio,
                'max_units': max_operating_units,
                'max_units_day': max_operating_day,
                'max_units_ratio': max_operating_units_ratio,
                'avg_units': avg_operating_units,
                'avg_units_ratio': avg_operating_units_ratio,
                '시간대 최대 평균 운영 대수': f'시간대({max_avg_units_time}) 최대 평균 운영 대수: {max_avg_units}대',
                '시간대 최대 평균 운영 대수': f'{max_avg_units_time} 최대 평균 운영 대수: {max_avg_units}대'
            }
        else:
                        index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'
            
            # 월 최소 및 최대 운영 횟수 계산
            unit_counts = filtered_df.groupby(['차대 코드'])[value_name].count()
            min_operating_counts = unit_counts.min()
            max_operating_counts = unit_counts.max()
            min_operating_unit = unit_counts.idxmin() if not unit_counts.empty else '데이터 없음'
            max_operating_unit = unit_counts.idxmax() if not unit_counts.empty else '데이터 없음'
            avg_operating_counts = round(unit_counts.mean()) if not unit_counts.empty else 0

            # 전체 운영 횟수 계산
            total_operating_counts = unit_counts.sum()
            
            # 비율 계산
            min_operating_counts_ratio = (min_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0
            max_operating_counts_ratio = (max_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0
            avg_operating_counts_ratio = (avg_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0

            # 운영 시간 계산
            filtered_df['운영 시간(초)'] = pd.to_numeric(filtered_df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)
            operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
            min_operating_time = operating_times.min()
            max_operating_time = operating_times.max()
            min_time_unit = operating_times.idxmin() if not operating_times.empty else '데이터 없음'
            max_time_unit = operating_times.idxmax() if not operating_times.empty else '데이터 없음'
            avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0
            
            # 전체 운영 시간 계산
            total_operating_time = operating_times.sum()

            # 비율 계산
            min_operating_time_ratio = (min_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
            max_operating_time_ratio = (max_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
            avg_operating_time_ratio = (avg_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0

            # 시간대별 최대 평균 운영 횟수 및 시간 계산
            avg_counts_by_time_series = filtered_df.groupby('시간대')[value_name].count().mean()
            max_avg_counts_time = filtered_df.groupby('시간대')[value_name].count().idxmax()
            max_avg_counts = filtered_df.groupby('시간대')[value_name].count().max()

            avg_time_by_time_series = filtered_df.groupby('시간대')['운영 시간(초)'].mean().mean()
            max_avg_time_time = filtered_df.groupby('시간대')['운영 시간(초)'].mean().idxmax()
            max_avg_time = filtered_df.groupby('시간대')['운영 시간(초)'].mean().max()

            def format_time(seconds):
                hours, seconds = divmod(seconds, 3600)
                minutes, seconds = divmod(seconds, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"

            min_operating_time_formatted = format_time(min_operating_time)
            max_operating_time_formatted = format_time(max_operating_time)
            avg_operating_time_formatted = format_time(avg_operating_time)
            total_operating_time_formatted = format_time(total_operating_time)
            
            
            # 시간대별 최대 평균 운영 횟수 및 운영 시간 계산
            max_avg_counts, max_avg_counts_time = calculate_max_avg_by_time(filtered_df, value_name)
            max_avg_time, max_avg_time_time = calculate_max_avg_by_time(filtered_df, '운영 시간(초)')
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
                'avg_time_ratio': avg_operating_time_ratio,
                '시간대 최대 평균 운영 횟수': f'시간대({max_avg_counts_time}) 최대 평균 운영 횟수: {max_avg_counts}회',
                '시간대 최대 평균 운영 시간': f'시간대({max_avg_time_time}) 최대 평균 운영 시간: {max_avg_time}초',
                '시간대 최대 평균 운영 횟수': f'{max_avg_counts_time} 최대 평균 운영 횟수: {max_avg_counts}회',
                '시간대 최대 평균 운영 시간': f'{max_avg_time_time} 최대 평균 운영 시간: {max_avg_time}초'
            }
        
        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        return pivot_table, title, index_name, summary

    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    tooltip_texts = [[f'월 최대 운영 횟수: {int(val)}회' if analysis_type == '운영 횟수' else f'시간대 최대 운영 대수: {int(val)}대'
