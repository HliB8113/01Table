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

        # '공정' 열이 있는지 확인하고 있다면 삭제 (추가된 방어 코드)
        if '공정' in df.columns:
            df = df.drop(columns=['공정'])
        if '운전자' in df.columns: # 혹시 모를 '운전자' 열도 확인 및 삭제
             df = df.drop(columns=['운전자'])

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
        # '공정' 선택 드롭다운은 완전히 제거되었습니다.
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"

# 메인 페이지 설정
if uploaded_file is not None and 'df' in locals():
    # generate_pivot 함수는 이미 'process' 관련 부분이 제거되었습니다.
    def generate_pivot(month, department, forklift_class, workplace):
        filtered_df = df.copy()
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        # '공정' 필터링 로직은 제거되었습니다.
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
            min_operating_units = daily_counts.min() if not daily_counts.empty else 0 # 데이터 없을 경우 0 처리 추가
            max_operating_units = daily_counts.max() if not daily_counts.empty else 0 # 데이터 없을 경우 0 처리 추가
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
            value_name = '시작 날짜'
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'

            # 월 최소 및 최대 운영 횟수 계산
            unit_counts = filtered_df.groupby(['차대 코드'])[value_name].count()
            min_operating_counts = unit_counts.min() if not unit_counts.empty else 0 # 데이터 없을 경우 0 처리 추가
            max_operating_counts = unit_counts.max() if not unit_counts.empty else 0 # 데이터 없을 경우 0 처리 추가
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
            min_operating_time = operating_times.min() if not operating_times.empty else 0 # 데이터 없을 경우 0 처리 추가
            max_operating_time = operating_times.max() if not operating_times.empty else 0 # 데이터 없을 경우 0 처리 추가
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
                # seconds가 숫자가 아닐 경우 0으로 처리
                if not isinstance(seconds, (int, float)):
                    seconds = 0
                seconds = int(seconds) # 정수형으로 변환
                hours, seconds = divmod(seconds, 3600)
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

        # 피벗 테이블 생성 시 데이터가 없을 경우 빈 테이블 생성 방지
        if filtered_df.empty:
             st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
             # 빈 피벗 테이블 대신 None 또는 빈 데이터프레임 반환 고려
             pivot_table = pd.DataFrame() # 빈 데이터프레임 생성
             # 또는 None 반환 후 후속 처리에서 확인
             # return None, title, index_name, summary
        else:
            pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)

        return pivot_table, title, index_name, summary

    # generate_pivot 함수 호출 부분은 이미 수정되었습니다.
    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_forklift_class, selected_workplace)

    # 피벗 테이블이 비어있는지 확인 후 그래프 생성
    if not pivot_table.empty:
        # Heatmap 생성
        fig = make_subplots(rows=1, cols=1)
        # 피벗 테이블 값 타입 확인 및 변환 (오류 방지)
        z_values = pivot_table.values
        try:
            z_values = z_values.astype(float) # 시각화를 위해 float으로 변환 시도
        except ValueError:
            st.error("데이터 타입 오류: 히트맵 값으로 변환할 수 없습니다.")
            z_values = None # 오류 발생 시 z_values를 None으로 설정

        if z_values is not None: # z_values가 유효할 때만 진행
            tooltip_texts = [[f'운영 횟수: {int(val)}회' if analysis_type == '운영 횟수' else f'운영 대수: {int(val)}대' for val in row] for row in z_values]
            heatmap = go.Heatmap(
                z=z_values,
                x=pivot_table.columns,
                y=pivot_table.index,
                colorscale=[[0, 'white'], [1, 'purple']],
                hoverinfo='text',
                text=tooltip_texts,
                zmin=0,
                # zmax 계산 전에 z_values가 비어있는지 확인
                zmax=z_values.max() if z_values.size > 0 else 0
            )
            fig.add_trace(heatmap)

            # 최댓값 하이라이트 추가
            if z_values.size > 0: # 데이터가 있을 때만 최댓값 계산
                max_value = z_values.max()
                # max_value가 0보다 크고 유한한 경우에만 하이라이트 추가
                if max_value > 0 and pd.notna(max_value):
                     max_indices = list(zip(*[(i, j) for i, row in enumerate(z_values) for j, val in enumerate(row) if val == max_value]))
                     if max_indices:
                         max_y_indices, max_x_indices = max_indices
                         for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                             fig.add_trace(go.Scatter(
                                 x=[pivot_table.columns[x_idx]],
                                 y=[pivot_table.index[y_idx]],
                                 mode='markers+text',
                                 marker=dict(size=12, color='yellow', symbol='circle'),
                                 text=[f'{"동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"} {int(max_value)} {"대" if analysis_type == "운영 대수" else "회"}'],
                                 textposition='top center',
                                 textfont=dict(color='black', size=14)
                             ))

            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.4,
                    'font': {'size': 25}  # 제목 크기 설정
                },
                xaxis=dict(title='시간대', fixedrange=True),
                yaxis=dict(title=index_name, categoryorder='array', categoryarray=sorted(pivot_table.index)),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=50, t=150, b=50),
                width=1500,  # 고정된 너비 (확장됨)
                height=graph_height,  # 조정 가능한 높이
                coloraxis_colorbar=dict(title='계급 크기')
            )

            # 모든 '시작 날짜'를 세로축에 표시 (월일만 표시)
            if analysis_type == '운영 대수':
                fig.update_yaxes(type='category', tickmode='array', tickvals=sorted(pivot_table.index))

            # Streamlit을 통해 플롯 보여주기
            st.plotly_chart(fig)

            # 요약 정보 표시 (HTML 구조는 유지)
            if analysis_type == '운영 대수':
                summary_text = (
                    f"<b>운영 대수(Day)</b><br>"
                    f"전체: {summary.get('total_units', 'N/A')}대<br>"
                    # summary 값이 숫자인지 확인 후 포맷팅
                    f"최소: {summary.get('min_units_day', 'N/A')} {summary.get('min_units', 'N/A')}대 "
                    f"({float(summary.get('min_units_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('min_units_ratio'), (int, float)) else ""

                    f"최대: {summary.get('max_units_day', 'N/A')} {summary.get('max_units', 'N/A')}대 "
                    f"({float(summary.get('max_units_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('max_units_ratio'), (int, float)) else ""

                    f"평균: {summary.get('avg_units', 'N/A')}대 "
                    f"({float(summary.get('avg_units_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('avg_units_ratio'), (int, float)) else ""
                )
            else: # analysis_type == '운영 횟수'
                 summary_text = (
                    f"<div style='display: flex; flex-direction: row; align-items: flex-start;'>"
                    f"<div style='margin-right: 50px;'>"
                    f"<b>운영 횟수(Day)</b><br>"
                    f"전체: {summary.get('total_counts', 'N/A')}번<br>"

                    f"최소: {summary.get('min_counts_unit', 'N/A')} {summary.get('min_counts', 'N/A')}번 "
                    f"({float(summary.get('min_counts_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('min_counts_ratio'), (int, float)) else ""

                    f"최대: {summary.get('max_counts_unit', 'N/A')} {summary.get('max_counts', 'N/A')}번 "
                    f"({float(summary.get('max_counts_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('max_counts_ratio'), (int, float)) else ""

                    f"평균: {summary.get('avg_counts', 'N/A')}번 "
                    f"({float(summary.get('avg_counts_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('avg_counts_ratio'), (int, float)) else ""
                    f"</div>"

                    f"<div>"
                    f"<b>운영 시간(Day)</b><br>"
                    f"전체: {summary.get('total_time', 'N/A')}<br>"

                    f"최소: {summary.get('min_time_unit', 'N/A')} {summary.get('min_time', 'N/A')} "
                    f"({float(summary.get('min_time_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('min_time_ratio'), (int, float)) else ""

                    f"최대: {summary.get('max_time_unit', 'N/A')} {summary.get('max_time', 'N/A')} "
                    f"({float(summary.get('max_time_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('max_time_ratio'), (int, float)) else ""

                    f"평균: {summary.get('avg_time', 'N/A')} "
                    f"({float(summary.get('avg_time_ratio', 0)):.2f}%)<br>" if isinstance(summary.get('avg_time_ratio'), (int, float)) else ""
                    f"</div>"
                    f"</div>"
                )

            # 요약 정보를 히트맵 아래로 표시
            st.markdown(summary_text, unsafe_allow_html=True)
        # else: # z_values가 None인 경우 (데이터 타입 오류 발생 시)
            # st.error("히트맵을 생성할 수 없습니다. 데이터 타입을 확인해주세요.") # 이미 위에서 에러 메시지 표시

    # 피벗 테이블이 비어있을 경우 사용자에게 메시지 표시
    # 이 부분은 generate_pivot 함수 내에서 st.warning으로 처리됨
    # else:
    #     st.warning("선택한 조건에 해당하는 데이터가 없어 그래프를 표시할 수 없습니다.")
