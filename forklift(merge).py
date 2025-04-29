import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np # numpy 추가

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# Streamlit 사이드바 설정
with st.sidebar:
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"])
    df = None # df 초기화

    if uploaded_file is not None:
        try:
            df_initial = pd.read_csv(uploaded_file)
            st.success("파일 로딩 성공!")

            # --- 필수 컬럼 확인 ---
            required_columns = ['시간대', '시작 날짜', '차대 코드', '운영 시간(초)']
            # 선택적 필터링 컬럼 (없어도 앱은 동작하지만 필터링 기능 제한)
            optional_columns = ['부서', '공정', '차대 분류', '작업 장소']
            missing_required = [col for col in required_columns if col not in df_initial.columns]
            missing_optional = [col for col in optional_columns if col not in df_initial.columns]

            if missing_required:
                st.error(f"오류: 필수 컬럼이 누락되었습니다 - {', '.join(missing_required)}. 분석을 진행할 수 없습니다.")
                st.stop() # 앱 실행 중지
            else:
                df = df_initial.copy() # 필수 컬럼 확인 후 df에 할당

            if missing_optional:
                st.warning(f"경고: 다음 필터링 컬럼이 누락되었습니다 - {', '.join(missing_optional)}. 해당 필터는 작동하지 않습니다.")
                # 누락된 선택적 컬럼을 빈 값으로 추가 (필터링 UI 유지를 위해)
                for col in missing_optional:
                    df[col] = '정보 없음'


            # --- 데이터 타입 변환 ---
            try:
                # 시간대 변환 (오류 발생 시 NaT로 처리)
                df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
                # NaT 값 처리 (예: 해당 행 제거 또는 특정 시간으로 대체 - 여기서는 제거)
                df.dropna(subset=['시간대'], inplace=True)
                if df.empty:
                    st.warning("시간대 변환 후 유효한 데이터가 없습니다.")
                    st.stop()

            except Exception as e:
                st.error(f"'시간대' 컬럼 변환 중 오류 발생: {e}. 컬럼 형식을 확인하세요 (예: HH:MM).")
                st.stop()

            try:
                # 시작 날짜 변환 (오류 발생 시 NaT로 처리)
                df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
                # NaT 값 처리 (예: 해당 행 제거)
                df.dropna(subset=['시작 날짜'], inplace=True)
                if df.empty:
                    st.warning("시작 날짜 변환 후 유효한 데이터가 없습니다.")
                    st.stop()

                df['월'] = df['시작 날짜'].dt.month
            except Exception as e:
                st.error(f"'시작 날짜' 컬럼 변환 중 오류 발생: {e}. 날짜 형식을 확인하세요.")
                st.stop()

            # 운영 시간(초) 숫자 변환 (오류 발생 시 NaN 처리 후 0으로 채움)
            df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)

            # 12월 데이터 제외
            excluded_month = 12
            df = df[df['월'] != excluded_month]

            if df.empty:
                st.warning("12월 제외 후 분석할 데이터가 없습니다.")
                st.stop()

            # --- 드롭다운 메뉴 설정 ---
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))

            # 각 필터링 컬럼에 대해 고유값 추출 (NaN 값 제외 및 정렬)
            month_options = ['전체'] + sorted(df['월'].dropna().unique().astype(int).tolist())
            department_options = ['전체'] + sorted(df['부서'].dropna().unique().tolist()) if '부서' in df.columns else ['전체']
            process_options = ['전체'] + sorted(df['공정'].dropna().unique().tolist()) if '공정' in df.columns else ['전체']
            forklift_class_options = ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()) if '차대 분류' in df.columns else ['전체']
            workplace_options = ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()) if '작업 장소' in df.columns else ['전체']

            selected_month = st.selectbox('월 선택:', month_options)
            selected_department = st.selectbox('부서 선택:', department_options)
            selected_process = st.selectbox('공정 선택:', process_options)
            selected_forklift_class = st.selectbox('차대 분류 선택:', forklift_class_options)
            selected_workplace = st.selectbox('작업 장소 선택:', workplace_options)
            graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

        except pd.errors.EmptyDataError:
            st.error("오류: 업로드된 파일이 비어 있습니다.")
            df = None
        except Exception as e:
            st.error(f"파일 처리 중 오류 발생: {e}")
            df = None

# 변수 초기화
title = "분석 대기 중..."
pivot_table = pd.DataFrame() # 빈 데이터프레임으로 초기화
summary = {}
index_name = "데이터 선택"

# 메인 페이지 설정
if df is not None and not df.empty:
    def generate_pivot(original_df, month, department, process, forklift_class, workplace, analysis_type):
        filtered_df = original_df.copy()

        # --- 필터링 ---
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체' and '부서' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if process != '전체' and '공정' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['공정'] == process]
        if forklift_class != '전체' and '차대 분류' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체' and '작업 장소' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        # --- 필터링 후 데이터 유무 확인 ---
        if filtered_df.empty:
            st.warning("선택된 조건에 해당하는 데이터가 없습니다.")
            # 빈 피벗 테이블과 기본 요약 정보 반환
            empty_pivot = pd.DataFrame()
            empty_summary = {}
            default_title = "데이터 없음"
            default_index_name = "데이터 없음"
            return empty_pivot, default_title, default_index_name, empty_summary

        # --- 분석 유형별 처리 ---
        local_summary = {} # 함수 내 지역 변수로 summary 사용

        if analysis_type == '운영 대수':
            # 날짜 형식 변경은 피벗 테이블 생성 직전에 적용
            filtered_df['시작 날짜_표시용'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
            index_name = '시작 날짜_표시용' # 피벗 인덱스용 컬럼
            value_name = '차대 코드'
            agg_func = 'nunique'
            title = '지게차 일자별 운영 대수'

            # 피벗 테이블 생성
            pivot_table_result = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)

            # 요약 정보 계산
            total_operating_units = filtered_df[value_name].nunique()
            daily_counts = filtered_df.groupby('시작 날짜_표시용')[value_name].nunique()

            min_operating_units = daily_counts.min() if not daily_counts.empty else 0
            max_operating_units = daily_counts.max() if not daily_counts.empty else 0
            min_operating_day = daily_counts.idxmin() if not daily_counts.empty else '데이터 없음'
            max_operating_day = daily_counts.idxmax() if not daily_counts.empty else '데이터 없음'
            avg_operating_units = round(daily_counts.mean()) if not daily_counts.empty else 0

            min_operating_units_ratio = (min_operating_units / total_operating_units * 100) if total_operating_units > 0 else 0
            max_operating_units_ratio = (max_operating_units / total_operating_units * 100) if total_operating_units > 0 else 0
            avg_operating_units_ratio = (avg_operating_units / total_operating_units * 100) if total_operating_units > 0 else 0

            local_summary = {
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
            value_name = '시작 날짜' # 운영 횟수 계산을 위해 임의의 컬럼 사용 (count)
            agg_func = 'count'
            title = '지게차 시간대별 운영 횟수'

            # 피벗 테이블 생성
            pivot_table_result = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)

            # 운영 횟수 요약 정보 계산
            unit_counts = filtered_df.groupby('차대 코드')[value_name].count() # value_name은 count를 위해 사용

            min_operating_counts = unit_counts.min() if not unit_counts.empty else 0
            max_operating_counts = unit_counts.max() if not unit_counts.empty else 0
            min_operating_unit = unit_counts.idxmin() if not unit_counts.empty else '데이터 없음'
            max_operating_unit = unit_counts.idxmax() if not unit_counts.empty else '데이터 없음'
            avg_operating_counts = round(unit_counts.mean()) if not unit_counts.empty else 0
            total_operating_counts = unit_counts.sum()

            min_operating_counts_ratio = (min_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
            max_operating_counts_ratio = (max_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
            avg_operating_counts_ratio = (avg_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0

            # 운영 시간 요약 정보 계산
            # '운영 시간(초)' 컬럼이 숫자로 변환되었는지 확인 (위에서 처리됨)
            operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()

            min_operating_time = operating_times.min() if not operating_times.empty else 0
            max_operating_time = operating_times.max() if not operating_times.empty else 0
            min_time_unit = operating_times.idxmin() if not operating_times.empty else '데이터 없음'
            max_time_unit = operating_times.idxmax() if not operating_times.empty else '데이터 없음'
            avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0
            total_operating_time = operating_times.sum()

            min_operating_time_ratio = (min_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
            max_operating_time_ratio = (max_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
            avg_operating_time_ratio = (avg_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0

            def format_time(seconds):
                # seconds가 NaN 또는 Inf인지 확인하고 처리
                if pd.isna(seconds) or np.isinf(seconds):
                    return "00:00:00" # 또는 다른 적절한 기본값
                seconds = int(seconds) # 정수로 변환
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"

            min_operating_time_formatted = format_time(min_operating_time)
            max_operating_time_formatted = format_time(max_operating_time)
            avg_operating_time_formatted = format_time(avg_operating_time)
            total_operating_time_formatted = format_time(total_operating_time)

            local_summary = {
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

        # 최종 반환값
        return pivot_table_result, title, index_name, local_summary

    # 피벗 테이블 및 요약 정보 생성
    pivot_table, title, index_name, summary = generate_pivot(
        df, selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace, analysis_type
    )

    # --- 시각화 ---
    if not pivot_table.empty: # 피벗 테이블이 비어있지 않을 때만 그래프 생성
        fig = make_subplots(rows=1, cols=1)

        # 툴팁 텍스트 생성
        if analysis_type == '운영 횟수':
            tooltip_texts = [[f'운영 횟수: {int(val)}회' for val in row] for row in pivot_table.values]
        else: # 운영 대수
            tooltip_texts = [[f'운영 대수: {int(val)}대' for val in row] for row in pivot_table.values]

        # 히트맵 생성
        heatmap = go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale=[[0, 'white'], [0.01, 'lightblue'], [1, 'darkblue']], # 색상 스케일 조정 (0값 명확히)
            hoverinfo='text',
            text=tooltip_texts,
            zmin=0,
            # zmax=pivot_table.values.max() if pivot_table.values.size > 0 else 1 # 빈 테이블 방지
        )
        fig.add_trace(heatmap)

        # 최댓값 하이라이트 추가
        if pivot_table.values.size > 0: # 데이터가 있을 때만 최대값 계산
            max_value = np.nanmax(pivot_table.values) # NaN 무시하고 최대값 계산
            if max_value > 0: # 최대값이 0보다 클 때만 하이라이트
                # np.where를 사용하여 NaN을 안전하게 처리하며 인덱스 찾기
                max_indices = np.where(pivot_table.values == max_value)
                max_y_indices, max_x_indices = max_indices[0], max_indices[1]

                highlight_text_prefix = "동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"
                highlight_text_suffix = "대" if analysis_type == "운영 대수" else "회"

                for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                    fig.add_trace(go.Scatter(
                        x=[pivot_table.columns[x_idx]],
                        y=[pivot_table.index[y_idx]],
                        mode='markers+text',
                        marker=dict(size=10, color='red', symbol='circle-open', line=dict(width=2)), # 마커 스타일 변경
                        text=[f'{highlight_text_prefix} {int(max_value)}{highlight_text_suffix}'],
                        textposition='top center',
                        textfont=dict(color='red', size=12, family="Arial, sans-serif"), # 폰트 지정
                        hoverinfo='none' # 하이라이트 마커는 툴팁 표시 안 함
                    ))

        # 레이아웃 업데이트
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5, # 제목 중앙 정렬
                'xanchor': 'center',
                'font': {'size': 24, 'family': "Arial Black, sans-serif"} # 제목 폰트/크기
            },
            xaxis=dict(
                title='시간대',
                fixedrange=True,
                tickangle=0 # x축 레이블 각도
            ),
            yaxis=dict(
                title=index_name if index_name != '시작 날짜_표시용' else '시작 날짜', # 실제 의미있는 이름 표시
                fixedrange=True,
                # categoryorder='array', # 기본 정렬 사용 또는 필요시 재정의
                # categoryarray=sorted(pivot_table.index.astype(str)) # 문자열로 변환하여 정렬
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=100, r=50, t=100, b=80), # 여백 조정
            width=None, # 너비 자동 조정 (Streamlit layout='wide' 활용)
            height=graph_height,
            xaxis_tickformat = '%H:%M', # x축 시간 포맷 (필요시)
            coloraxis_colorbar=dict(
                title='값의 크기' if analysis_type == '운영 대수' else '운영 횟수/대수',
                len=0.8, # 컬러바 길이 조정
                yanchor='middle',
                y=0.5
            )
        )

        # '운영 대수' 분석 시 y축 정렬 (문자열로 변환 후 정렬)
        if analysis_type == '운영 대수':
             fig.update_yaxes(categoryorder='array', categoryarray=sorted(pivot_table.index.astype(str)))


        # Streamlit을 통해 플롯 보여주기
        st.plotly_chart(fig, use_container_width=True) # 컨테이너 너비 사용

        # --- 요약 정보 표시 ---
        if summary: # summary 딕셔너리가 비어있지 않을 때만 표시
            if analysis_type == '운영 대수':
                summary_text = (
                    f"<b>📊 운영 대수 요약 (일별)</b><br><hr>"
                    f"📅 <b>전체 운영일 총합계:</b> {summary.get('total_units', 'N/A')} 대<br>"
                    f"📉 <b>최소 운영일:</b> {summary.get('min_units_day', 'N/A')} ({summary.get('min_units', 'N/A')} 대, 전체의 {summary.get('min_units_ratio', 0):.2f}%)<br>"
                    f"📈 <b>최대 운영일:</b> {summary.get('max_units_day', 'N/A')} ({summary.get('max_units', 'N/A')} 대, 전체의 {summary.get('max_units_ratio', 0):.2f}%)<br>"
                    f"📊 <b>일 평균 운영 대수:</b> {summary.get('avg_units', 'N/A')} 대 (전체의 {summary.get('avg_units_ratio', 0):.2f}%)"
                )
                st.markdown(summary_text, unsafe_allow_html=True)
            else: # 운영 횟수
                 # st.columns를 사용하여 가로 배치
                col1, col2 = st.columns(2)
                with col1:
                    summary_text_counts = (
                        f"<b>🔢 운영 횟수 요약 (차량별)</b><br><hr>"
                        f"🚚 <b>전체 운영 횟수:</b> {summary.get('total_counts', 'N/A')} 번<br>"
                        f"📉 <b>최소 운영 차량:</b> {summary.get('min_counts_unit', 'N/A')} ({summary.get('min_counts', 'N/A')} 번, 전체의 {summary.get('min_counts_ratio', 0):.2f}%)<br>"
                        f"📈 <b>최대 운영 차량:</b> {summary.get('max_counts_unit', 'N/A')} ({summary.get('max_counts', 'N/A')} 번, 전체의 {summary.get('max_counts_ratio', 0):.2f}%)<br>"
                        f"📊 <b>차량 평균 운영 횟수:</b> {summary.get('avg_counts', 'N/A')} 번 (전체의 {summary.get('avg_counts_ratio', 0):.2f}%)"
                    )
                    st.markdown(summary_text_counts, unsafe_allow_html=True)
                with col2:
                    summary_text_time = (
                        f"<b>⏱️ 운영 시간 요약 (차량별)</b><br><hr>"
                        f"⏳ <b>전체 운영 시간:</b> {summary.get('total_time', 'N/A')}<br>"
                        f"📉 <b>최소 운영 차량:</b> {summary.get('min_time_unit', 'N/A')} ({summary.get('min_time', 'N/A')}, 전체의 {summary.get('min_time_ratio', 0):.2f}%)<br>"
                        f"📈 <b>최대 운영 차량:</b> {summary.get('max_time_unit', 'N/A')} ({summary.get('max_time', 'N/A')}, 전체의 {summary.get('max_time_ratio', 0):.2f}%)<br>"
                        f"📊 <b>차량 평균 운영 시간:</b> {summary.get('avg_time', 'N/A')} (전체의 {summary.get('avg_time_ratio', 0):.2f}%)"
                    )
                    st.markdown(summary_text_time, unsafe_allow_html=True)
        else:
             st.info("요약 정보를 표시할 데이터가 없습니다.")

    # 만약 generate_pivot 함수에서 빈 테이블을 반환했다면 (데이터 없음 경고 후)
    elif uploaded_file is not None and df is not None and df.empty:
         # df가 비어있지만 파일은 업로드 된 경우 (전처리 후 데이터 없음)
         st.warning("파일 로딩 및 전처리 후 분석 가능한 데이터가 없습니다. 필터 조건을 확인하거나 원본 데이터를 확인해주세요.")
    # 그 외의 경우 (예: 파일 업로드 안됨)
    # else:
    #     st.info("분석할 파일을 업로드해주세요.")

# 파일 업로드되지 않았을 때 초기 메시지
if uploaded_file is None:
    st.info("사이드바에서 CSV 파일을 업로드하면 분석 결과를 볼 수 있습니다.")
