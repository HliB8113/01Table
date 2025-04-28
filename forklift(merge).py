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

        # 12월 데이터 제외 (필요시 주석 해제 또는 수정)
        # excluded_month = 12
        # df = df[df['월'] != excluded_month]

        # 드롭다운 메뉴 설정
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().tolist()))
        selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
        # '공정' 선택 메뉴 제거
        # selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals():
    # generate_pivot 함수에서 'process' 매개변수 제거
    def generate_pivot(month, department, forklift_class, workplace):
        filtered_df = df.copy()
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        # '공정' 필터링 로직 제거
        # if process != '전체':
        #     filtered_df = filtered_df[filtered_df['공정'] == process]
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
            min_operating_units = daily_counts.min() if not daily_counts.empty else 0
            max_operating_units = daily_counts.max() if not daily_counts.empty else 0
            min_operating_day = daily_counts.idxmin() if not daily_counts.empty else '데이터 없음'
            max_operating_day = daily_counts.idxmax() if not daily_counts.empty else '데이터 없음'
            avg_operating_units = round(daily_counts.mean()) if not daily_counts.empty else 0

            # 비율 계산
            min_operating_units_ratio = (min_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
            max_operating_units_ratio = (max_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
            avg_operating_units_ratio = (avg_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0


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

            }
        else: # analysis_type == '운영 횟수'
            index_name = '차대 코드'
            value_name = '시작 날짜' # 집계 기준이 되는 값이므로, 횟수를 세기 위해 임의의 열(여기서는 시작 날짜) 사용
            agg_func = 'count'
            title = '지게차 차대별 시간대별 운영 횟수'

            # 차대별 운영 횟수 계산
            unit_counts = filtered_df.groupby(index_name)[value_name].count() # value_name은 count를 위해 사용
            min_operating_counts = unit_counts.min() if not unit_counts.empty else 0
            max_operating_counts = unit_counts.max() if not unit_counts.empty else 0
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
            min_operating_time = operating_times.min() if not operating_times.empty else 0
            max_operating_time = operating_times.max() if not operating_times.empty else 0
            min_time_unit = operating_times.idxmin() if not operating_times.empty else '데이터 없음'
            max_time_unit = operating_times.idxmax() if not operating_times.empty else '데이터 없음'
            avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0

            # 전체 운영 시간 계산
            total_operating_time = operating_times.sum()

            # 비율 계산
            min_operating_time_ratio = (min_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
            max_operating_time_ratio = (max_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
            avg_operating_time_ratio = (avg_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0


            def format_time(seconds):
                hours, seconds = divmod(int(seconds), 3600) # int() 추가하여 정수 변환 보장
                minutes, seconds = divmod(seconds, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"

            min_operating_time_formatted = format_time(min_operating_time)
            max_operating_time_formatted = format_time(max_operating_time)
            avg_operating_time_formatted = format_time(avg_operating_time)
            total_operating_time_formatted = format_time(total_operating_time)

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

            }

        # 피벗 테이블 생성 시 value_name 수정 ('운영 횟수' 시)
        pivot_value_name = '차대 코드' if analysis_type == '운영 대수' else '시작 날짜' # 운영 횟수 시 count를 위한 임의의 열
        pivot_agg_func = agg_func

        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=pivot_value_name, aggfunc=pivot_agg_func).fillna(0)

        # 운영 대수 분석 시 값이 nunique 결과이므로 정수로 변환
        if analysis_type == '운영 대수':
             pivot_table = pivot_table.astype(int)

        return pivot_table, title, index_name, summary

    # generate_pivot 함수 호출 시 'selected_process' 인자 제거
    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_forklift_class, selected_workplace)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    tooltip_texts = [[f'운영 횟수: {int(val)}회' if analysis_type == '운영 횟수' else f'운영 대수: {int(val)}대' for val in row] for row in pivot_table.values]
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [0.0001, '#fde0dd'], [0.1, '#fa9fb5'], [0.3, '#c51b8a'], [1, '#7a0177']], # 보라색 계열 조정
        hoverinfo='text',
        text=tooltip_texts,
        zmin=0,
        zmax=pivot_table.values.max() if pivot_table.values.size > 0 else 1 # 빈 데이터프레임 오류 방지
    )
    fig.add_trace(heatmap)

    # 최댓값 하이라이트 추가
    if pivot_table.values.size > 0: # 데이터가 있을 때만 실행
        max_value = pivot_table.values.max()
        if max_value > 0: # 최댓값이 0보다 클 때만 하이라이트
            max_indices = list(zip(*[(i, j) for i, row in enumerate(pivot_table.values) for j, val in enumerate(row) if val == max_value]))
            if max_indices:
                max_y_indices, max_x_indices = max_indices
                annotations = []
                for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                    # 운영 대수 분석 시 y축 인덱스(날짜) 가져오기
                    y_label = pivot_table.index[y_idx]
                    # 운영 횟수 분석 시 y축 인덱스(차대 코드) 가져오기
                    # y_label = pivot_table.index[y_idx]

                    annotations.append(
                         go.Scatter(
                                x=[pivot_table.columns[x_idx]],
                                y=[y_label], # 실제 y축 값 사용
                                mode='markers+text',
                                marker=dict(size=12, color='yellow', symbol='circle', line=dict(color='black', width=1)), # 마커 테두리 추가
                                text=[f'{"동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"} {int(max_value)} {"대" if analysis_type == "운영 대수" else "회"}'],
                                textposition='top center',
                                textfont=dict(color='black', size=14),
                                hoverinfo='none' # 하이라이트 마커 툴팁 제거
                         )
                    )
                # 하이라이트를 별도 트레이스로 추가 (기존 히트맵 위에 표시되도록)
                for annotation_trace in annotations:
                     fig.add_trace(annotation_trace)


    fig.update_layout(
        title={
            'text': title,
            'x': 0.5, # 제목 중앙 정렬
            'xanchor': 'center',
            'font': {'size': 25}  # 제목 크기 설정
        },
        xaxis=dict(title='시간대', fixedrange=True, tickangle=0), # x축 레이블 각도 0으로 설정
        yaxis=dict(title=index_name, fixedrange=True), # y축 확대/축소 방지
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=100, r=50, t=100, b=50), # 여백 조정
        # width=1500, 제거 -> Streamlit의 layout='wide' 활용
        height=graph_height,
        coloraxis_colorbar=dict(title='운영 강도') # 컬러바 제목 변경
    )

    # y축 카테고리 순서 및 표시 설정
    if analysis_type == '운영 대수':
        # 날짜 순서대로 정렬
        all_dates = sorted(pivot_table.index, key=lambda d: pd.to_datetime(d, format='%m-%d'))
        fig.update_yaxes(type='category', categoryorder='array', categoryarray=all_dates, tickmode='array', tickvals=all_dates)
    else: # 운영 횟수
        # 운영 횟수가 많은 순서대로 정렬 (내림차순)
        sorted_units = pivot_table.sum(axis=1).sort_values(ascending=False).index.tolist()
        fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_units)


    # 요약 정보를 가로로 배치하여 표시
    if analysis_type == '운영 대수':
        summary_html = f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
            <h4 style="margin-top:0; color: #333;">일별 운영 대수 요약</h4>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                <div style="text-align: center; margin: 5px;"><b>전체 운영 대수 (월):</b><br>{summary.get('total_units', 'N/A')}대</div>
                <div style="text-align: center; margin: 5px;"><b>최소 운영일 ({summary.get('min_units_day', 'N/A')}):</b><br>{summary.get('min_units', 'N/A')}대 ({float(summary.get('min_units_ratio', 0)):.2f}%)</div>
                <div style="text-align: center; margin: 5px;"><b>최대 운영일 ({summary.get('max_units_day', 'N/A')}):</b><br>{summary.get('max_units', 'N/A')}대 ({float(summary.get('max_units_ratio', 0)):.2f}%)</div>
                <div style="text-align: center; margin: 5px;"><b>일 평균 운영 대수:</b><br>{summary.get('avg_units', 'N/A')}대 ({float(summary.get('avg_units_ratio', 0)):.2f}%)</div>
            </div>
        </div>
        """
    else: # 운영 횟수
        summary_html = f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
            <h4 style="margin-top:0; color: #333;">차대별 운영 요약</h4>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                <div style="border-right: 1px solid #eee; padding-right: 20px; margin-right: 20px;">
                    <b>운영 횟수</b><br>
                    전체: {summary.get('total_counts', 'N/A')}번<br>
                    최소: {summary.get('min_counts_unit', 'N/A')} ({summary.get('min_counts', 'N/A')}번, {float(summary.get('min_counts_ratio', 0)):.2f}%)<br>
                    최대: {summary.get('max_counts_unit', 'N/A')} ({summary.get('max_counts', 'N/A')}번, {float(summary.get('max_counts_ratio', 0)):.2f}%)<br>
                    평균: {summary.get('avg_counts', 'N/A')}번 ({float(summary.get('avg_counts_ratio', 0)):.2f}%)
                </div>
                <div>
                    <b>운영 시간</b><br>
                    전체: {summary.get('total_time', 'N/A')}<br>
                    최소: {summary.get('min_time_unit', 'N/A')} ({summary.get('min_time', 'N/A')}, {float(summary.get('min_time_ratio', 0)):.2f}%)<br>
                    최대: {summary.get('max_time_unit', 'N/A')} ({summary.get('max_time', 'N/A')}, {float(summary.get('max_time_ratio', 0)):.2f}%)<br>
                    평균: {summary.get('avg_time', 'N/A')} ({float(summary.get('avg_time_ratio', 0)):.2f}%)
                </div>
            </div>
        </div>
        """

    # Streamlit을 통해 플롯과 요약 정보 보여주기
    st.plotly_chart(fig, use_container_width=True) # 컨테이너 너비 사용
    st.markdown(summary_html, unsafe_allow_html=True) # 스타일링된 요약 정보 표시

# 파일이 업로드되지 않았거나 df가 정의되지 않은 경우 메시지 표시
elif uploaded_file is None:
    st.info("데이터를 분석하려면 CSV 파일을 업로드하세요.")
else: # df는 정의되었으나 다른 이유로 메인 페이지 로직이 실행되지 않은 경우 (이론상 발생하기 어려움)
    st.warning("데이터 처리 중 오류가 발생했습니다. 파일을 다시 확인해주세요.")
