import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

# Streamlit 페이지 설정
st.set_page_config(page_title='My Streamlit App', layout='wide', initial_sidebar_state='expanded')

# Streamlit 사이드바 설정
with st.sidebar:
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"])
    df = None # df 초기화

    if uploaded_file is not None:
        try:
            # <<< 헤더 없이 파일 읽기 및 컬럼명 직접 지정 >>>
            try:
                # 헤더가 없다고 명시 (header=None)
                df_initial = pd.read_csv(uploaded_file, header=None, encoding='cp949')
            except UnicodeDecodeError:
                df_initial = pd.read_csv(uploaded_file, header=None, encoding='utf-8')

            # 예상되는 컬럼 개수 확인
            expected_columns = 7
            if df_initial.shape[1] != expected_columns:
                 st.error(f"오류: 파일의 컬럼 개수({df_initial.shape[1]})가 예상({expected_columns})과 다릅니다. 파일 형식을 확인하세요.")
                 st.stop()

            # 컬럼명 직접 할당 (추정된 순서 기반)
            df_initial.columns = ['부서', '차대 코드', '작업 장소', '시작 날짜', '운영 시간(초)', '시작 시간', '시간대']
            st.success("파일 로딩 및 컬럼명 할당 성공!")
            st.write("Debug: Assigned column names:", df_initial.columns.tolist()) # 할당된 컬럼명 확인


            # --- 필수 컬럼 확인 (이제 할당된 이름으로 확인) ---
            # 이제 이 컬럼명들이 존재해야 함
            required_columns = ['시간대', '시작 날짜', '차대 코드', '운영 시간(초)']
            optional_columns = ['부서', '공정', '차대 분류', '작업 장소'] # '공정', '차대 분류'는 여전히 없을 수 있음

            # 할당된 컬럼 리스트
            assigned_columns = df_initial.columns.tolist()

            missing_required = [col for col in required_columns if col not in assigned_columns]
            # 실제 파일에 없는 컬럼 (수동 할당 시에도 없을 수 있음, 예: '공정')
            missing_optional = [col for col in optional_columns if col not in assigned_columns]


            if missing_required:
                # 이 오류는 이제 발생하면 안 됨 (컬럼명을 직접 할당했으므로)
                st.error(f"코드 오류: 필수 컬럼 할당 실패 - {', '.join(missing_required)}")
                st.stop()
            else:
                df = df_initial.copy()

            if missing_optional:
                st.warning(f"경고: 다음 필터링 컬럼이 파일에 없어 '정보 없음'으로 처리됩니다 - {', '.join(missing_optional)}")
                # 누락된 선택적 컬럼 추가
                for col in missing_optional:
                    if col not in df.columns:
                       df[col] = '정보 없음'


            # --- 데이터 타입 변환 (컬럼명 기준으로 진행) ---
            # (이후 코드는 컬럼명이 올바르게 할당되었으므로 이전과 거의 동일하게 작동)
            try:
                if '시간대' in df.columns:
                    df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
                    df.dropna(subset=['시간대'], inplace=True)
                    if df.empty:
                        st.warning("시간대 변환 후 유효한 데이터가 없습니다.")
                        st.stop()
                else: # 컬럼 할당 실패 시
                    st.error("'시간대' 컬럼 처리 중 문제 발생.")
                    st.stop()
            except Exception as e:
                st.error(f"'시간대' 컬럼 변환 중 오류 발생: {e}. 데이터 형식을 확인하세요 (예: HH:MM).")
                st.stop()

            try:
                if '시작 날짜' in df.columns:
                    df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
                    df.dropna(subset=['시작 날짜'], inplace=True)
                    if df.empty:
                        st.warning("시작 날짜 변환 후 유효한 데이터가 없습니다.")
                        st.stop()
                    df['월'] = df['시작 날짜'].dt.month
                else:
                    st.error("'시작 날짜' 컬럼 처리 중 문제 발생.")
                    st.stop()
            except Exception as e:
                st.error(f"'시작 날짜' 컬럼 변환 중 오류 발생: {e}. 날짜 형식을 확인하세요.")
                st.stop()

            if '운영 시간(초)' in df.columns:
                 # .0 이 붙어 있을 수 있으므로 numeric 변환 중요
                df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)
            else:
                st.error("'운영 시간(초)' 컬럼 처리 중 문제 발생.")
                df['운영 시간(초)'] = 0 # 오류 방지용 기본값

            if '월' in df.columns:
                excluded_month = 12
                df = df[df['월'] != excluded_month]


            if df.empty:
                st.warning("데이터 처리 후 분석할 데이터가 없습니다.")
                st.stop()

            # --- 드롭다운 메뉴 설정 ---
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))

            month_options = ['전체'] + sorted(df['월'].dropna().unique().astype(int).tolist()) if '월' in df.columns else ['전체']
            department_options = ['전체'] + sorted(df['부서'].dropna().unique().tolist()) if '부서' in df.columns else ['전체']
            # '공정'은 파일에 없으므로 항상 비활성화됨
            process_options = ['전체'] + sorted(df['공정'].dropna().unique().tolist()) if '공정' in df.columns else ['전체']
            # '차대 분류' 컬럼도 할당하지 않았으므로 확인 필요 (현재 '부서'로 할당한 첫번째 컬럼이 실제로는 '차대 분류'일 수도 있음)
            forklift_class_options = ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()) if '차대 분류' in df.columns else ['전체']
            workplace_options = ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()) if '작업 장소' in df.columns else ['전체']

            selected_month = st.selectbox('월 선택:', month_options)
            selected_department = st.selectbox('부서 선택:', department_options)
            selected_process = st.selectbox('공정 선택:', process_options, disabled=('공정' not in df.columns))
            selected_forklift_class = st.selectbox('차대 분류 선택:', forklift_class_options, disabled=('차대 분류' not in df.columns))
            selected_workplace = st.selectbox('작업 장소 선택:', workplace_options)
            graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

        except pd.errors.EmptyDataError:
            st.error("오류: 업로드된 파일이 비어 있습니다.")
            df = None
        except Exception as e:
            st.error(f"파일 처리 중 예상치 못한 오류 발생: {e}")
            df = None


# --- 이하 generate_pivot, 시각화, 요약 정보 표시는 이전 코드와 동일 ---
# (컬럼명이 코드 내부에서 사용하는 이름과 일치하게 되었으므로 잘 작동할 것으로 예상)

# 변수 초기화
title = "분석 대기 중..."
pivot_table = pd.DataFrame()
summary = {}
index_name = "데이터 선택"

# 메인 페이지 설정
if df is not None and not df.empty:
    # generate_pivot 함수 정의 (이전 코드와 동일)
    def generate_pivot(original_df, month, department, process, forklift_class, workplace, analysis_type):
        filtered_df = original_df.copy()

        # --- 필터링 ---
        if month != '전체' and '월' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체' and '부서' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['부서'] == department]
        # '공정' 컬럼이 있을 때만 필터링 적용 (파일에 없으므로 항상 실행 안됨)
        if process != '전체' and '공정' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['공정'] == process]
        # '차대 분류' 컬럼이 있을 때만 필터링 적용 (현재는 없음)
        if forklift_class != '전체' and '차대 분류' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체' and '작업 장소' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        if filtered_df.empty:
            return pd.DataFrame(), "데이터 없음", "데이터 없음", {}

        local_summary = {}
        pivot_table_result = pd.DataFrame()
        local_index_name = "데이터 없음"
        local_title = "데이터 없음"


        if analysis_type == '운영 대수':
            filtered_df['시작 날짜_표시용'] = filtered_df['시작 날짜'].dt.strftime('%m/%d')
            local_index_name = '시작 날짜_표시용'
            value_name = '차대 코드'
            agg_func = 'nunique'
            local_title = '지게차 일자별 운영 대수'

            pivot_table_result = filtered_df.pivot_table(index=local_index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)

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
                'total_units': total_operating_units, 'min_units': min_operating_units, 'min_units_day': min_operating_day,
                'min_units_ratio': min_operating_units_ratio, 'max_units': max_operating_units, 'max_units_day': max_operating_day,
                'max_units_ratio': max_operating_units_ratio, 'avg_units': avg_operating_units, 'avg_units_ratio': avg_operating_units_ratio,
            }

        else: # analysis_type == '운영 횟수'
            local_index_name = '차대 코드'
            value_name = '시작 날짜'
            agg_func = 'count'
            local_title = '지게차 시간대별 운영 횟수'

            pivot_table_result = filtered_df.pivot_table(index=local_index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)

            unit_counts = filtered_df.groupby('차대 코드')[value_name].count()
            min_operating_counts = unit_counts.min() if not unit_counts.empty else 0
            max_operating_counts = unit_counts.max() if not unit_counts.empty else 0
            min_operating_unit = unit_counts.idxmin() if not unit_counts.empty else '데이터 없음'
            max_operating_unit = unit_counts.idxmax() if not unit_counts.empty else '데이터 없음'
            avg_operating_counts = round(unit_counts.mean()) if not unit_counts.empty else 0
            total_operating_counts = unit_counts.sum()

            min_operating_counts_ratio = (min_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
            max_operating_counts_ratio = (max_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
            avg_operating_counts_ratio = (avg_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0

            if '운영 시간(초)' in filtered_df.columns:
                operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
                min_operating_time = operating_times.min() if not operating_times.empty else 0
                max_operating_time = operating_times.max() if not operating_times.empty else 0
                min_time_unit = operating_times.idxmin() if not operating_times.empty else '데이터 없음'
                max_time_unit = operating_times.idxmax() if not operating_times.empty else '데이터 없음'
                avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0
                total_operating_time = operating_times.sum()
            else:
                min_operating_time, max_operating_time, avg_operating_time, total_operating_time = 0, 0, 0, 0
                min_time_unit, max_time_unit = '데이터 없음', '데이터 없음'


            min_operating_time_ratio = (min_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
            max_operating_time_ratio = (max_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
            avg_operating_time_ratio = (avg_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0

            def format_time(seconds):
                if pd.isna(seconds) or np.isinf(seconds): return "00:00:00"
                seconds = int(seconds)
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"

            min_operating_time_formatted = format_time(min_operating_time)
            max_operating_time_formatted = format_time(max_operating_time)
            avg_operating_time_formatted = format_time(avg_operating_time)
            total_operating_time_formatted = format_time(total_operating_time)

            local_summary = {
                'total_counts': total_operating_counts, 'min_counts': min_operating_counts, 'min_counts_unit': min_operating_unit,
                'min_counts_ratio': min_operating_counts_ratio, 'max_counts': max_operating_counts, 'max_counts_unit': max_operating_unit,
                'max_counts_ratio': max_operating_counts_ratio, 'avg_counts': avg_operating_counts, 'avg_counts_ratio': avg_operating_counts_ratio,
                'total_time': total_operating_time_formatted, 'min_time': min_operating_time_formatted, 'min_time_unit': min_time_unit,
                'min_time_ratio': min_operating_time_ratio, 'max_time': max_operating_time_formatted, 'max_time_unit': max_time_unit,
                'max_time_ratio': max_operating_time_ratio, 'avg_time': avg_operating_time_formatted, 'avg_time_ratio': avg_operating_time_ratio,
            }

        return pivot_table_result, local_title, local_index_name, local_summary

    # 피벗 테이블 및 요약 정보 생성
    pivot_table, title, index_name, summary = generate_pivot(
        df, selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace, analysis_type
    )

    # --- 시각화 ---
    if not pivot_table.empty:
        fig = make_subplots(rows=1, cols=1)

        # 툴팁 텍스트 생성
        if analysis_type == '운영 횟수':
            tooltip_texts = [[f'운영 횟수: {int(val)}회' for val in row] for row in pivot_table.values]
            hover_name = '운영 횟수'
        else: # 운영 대수
            tooltip_texts = [[f'운영 대수: {int(val)}대' for val in row] for row in pivot_table.values]
            hover_name = '운영 대수'

        # 히트맵 생성
        heatmap = go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Purples',
            hoverinfo='text',
            text=tooltip_texts,
            name=hover_name,
            zmin=0
        )
        fig.add_trace(heatmap)

        # 최댓값 하이라이트 추가
        if pivot_table.values.size > 0:
            max_value = np.nanmax(pivot_table.values)
            if max_value > 0:
                max_indices = np.where(pivot_table.values == max_value)
                max_y_indices, max_x_indices = max_indices[0], max_indices[1]
                highlight_text_prefix = "동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"
                highlight_text_suffix = "대" if analysis_type == "운영 대수" else "회"

                for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                    fig.add_trace(go.Scatter(
                        x=[pivot_table.columns[x_idx]],
                        y=[pivot_table.index[y_idx]],
                        mode='markers+text',
                        marker=dict(size=10, color='red', symbol='circle-open', line=dict(width=2)),
                        text=[f'{highlight_text_prefix} {int(max_value)}{highlight_text_suffix}'],
                        textposition='top center',
                        textfont=dict(color='red', size=12, family="Arial, sans-serif"),
                        hoverinfo='none'
                    ))

        # 레이아웃 업데이트
        y_axis_title = '시작 날짜' if index_name == '시작 날짜_표시용' else index_name

        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 24, 'family': "Arial Black, sans-serif"}},
            xaxis=dict(title='시간대', fixedrange=True, tickangle=0),
            yaxis=dict(title=y_axis_title, fixedrange=True),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=100, r=50, t=100, b=80),
            height=graph_height,
            coloraxis_colorbar=dict(title='값의 크기', len=0.8, yanchor='middle', y=0.5)
        )

        # Y축 타입 및 정렬 설정
        if analysis_type == '운영 대수':
             sorted_y_labels = sorted(pivot_table.index.astype(str))
             fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_y_labels)
        else:
             fig.update_yaxes(type='category')

        st.plotly_chart(fig, use_container_width=True)

        # --- 요약 정보 표시 ---
        if summary:
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
                    if '운영 시간(초)' in df.columns:
                        summary_text_time = (
                            f"<b>⏱️ 운영 시간 요약 (차량별)</b><br><hr>"
                            f"⏳ <b>전체 운영 시간:</b> {summary.get('total_time', 'N/A')}<br>"
                            f"📉 <b>최소 운영 차량:</b> {summary.get('min_time_unit', 'N/A')} ({summary.get('min_time', 'N/A')}, 전체의 {summary.get('min_time_ratio', 0):.2f}%)<br>"
                            f"📈 <b>최대 운영 차량:</b> {summary.get('max_time_unit', 'N/A')} ({summary.get('max_time', 'N/A')}, 전체의 {summary.get('max_time_ratio', 0):.2f}%)<br>"
                            f"📊 <b>차량 평균 운영 시간:</b> {summary.get('avg_time', 'N/A')} (전체의 {summary.get('avg_time_ratio', 0):.2f}%)"
                        )
                    else:
                        summary_text_time = "<b>⏱️ 운영 시간 요약 (차량별)</b><br><hr>데이터 없음 ('운영 시간(초)' 컬럼 누락)"
                    st.markdown(summary_text_time, unsafe_allow_html=True)
        else:
             st.info("요약 정보를 표시할 데이터가 없습니다.")

    elif uploaded_file is not None and df is not None and df.empty:
         st.warning("파일 로딩 및 전처리 후 분석 가능한 데이터가 없습니다. 필터 조건을 확인하거나 원본 데이터를 확인해주세요.")

# 파일 업로드되지 않았을 때 초기 메시지
if uploaded_file is None:
    st.info("사이드바에서 CSV 파일을 업로드하면 분석 결과를 볼 수 있습니다.")
