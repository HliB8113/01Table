import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

# Streamlit 페이지 설정
st.set_page_config(page_title='지게차 운영 분석 대시보드', layout='wide', initial_sidebar_state='expanded')

# --- 전역 Helper 함수: 시간 포맷 ---
def format_time(seconds):
    """초 단위 시간을 HH:MM:SS 형식의 문자열로 변환합니다."""
    if pd.isna(seconds) or np.isinf(seconds) or seconds < 0:
        return "00:00:00"
    seconds = int(round(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 데이터 업로드 및 필터")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"])
    df = None

    if uploaded_file is not None:
        try:
            df_initial = pd.read_csv(uploaded_file)
            required_columns = ['시간대', '시작 날짜', '차대 코드', '운영 시간(초)']
            optional_columns = ['부서', '공정', '차대 분류', '작업 장소']
            missing_required = [col for col in required_columns if col not in df_initial.columns]
            missing_optional = [col for col in optional_columns if col not in df_initial.columns]
            if missing_required:
                st.error(f"필수 컬럼이 누락되었습니다: {', '.join(missing_required)}")
                st.stop()
            else:
                df = df_initial.copy()
            if missing_optional:
                for col in missing_optional:
                    df[col] = '정보 없음'
            try:
                df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
                df.dropna(subset=['시간대'], inplace=True)
                if df.empty:
                    st.warning("시간대 데이터를 처리한 후 데이터가 없습니다.")
                    st.stop()
            except Exception as e:
                st.error(f"시간대 컬럼 처리 중 오류 발생: {e}")
                st.stop()
            try:
                df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
                df.dropna(subset=['시작 날짜'], inplace=True)
                if df.empty:
                    st.warning("시작 날짜 데이터를 처리한 후 데이터가 없습니다.")
                    st.stop()
                df['월'] = df['시작 날짜'].dt.month
            except Exception as e:
                st.error(f"시작 날짜 컬럼 처리 중 오류 발생: {e}")
                st.stop()
            try:
                df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)
            except Exception as e:
                st.warning(f"운영 시간(초) 컬럼 처리 중 경미한 오류 발생 (기본값 0으로 대체): {e}")
                pass

            excluded_month = 12
            if '월' in df.columns:
                df = df[df['월'] != excluded_month]
                if df.empty:
                    st.warning(f"{excluded_month}월 데이터를 제외한 후 분석할 데이터가 없습니다.")
                    st.stop()

            st.header("📊 분석 옵션")
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'), key='analysis_type')

            if df is not None and not df.empty and '월' in df.columns:
                month_options = ['전체'] + sorted(df['월'].dropna().unique().astype(int).tolist())
            else:
                month_options = ['전체']

            department_options = ['전체'] + sorted(df['부서'].dropna().unique().tolist()) if '부서' in df.columns else ['전체']
            process_options = ['전체'] + sorted(df['공정'].dropna().unique().tolist()) if '공정' in df.columns else ['전체']
            forklift_class_options = ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()) if '차대 분류' in df.columns else ['전체']
            workplace_options = ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()) if '작업 장소' in df.columns else ['전체']

            selected_month = st.selectbox('🗓️ 월 선택:', month_options, key='month_select')
            selected_department = st.selectbox('🏢 부서 선택:', department_options, key='dept_select')
            selected_process = st.selectbox('🛠️ 공정 선택:', process_options, key='proc_select')
            selected_forklift_class = st.selectbox('🚚 차대 분류 선택:', forklift_class_options, key='class_select')
            selected_workplace = st.selectbox('📍 작업 장소 선택:', workplace_options, key='wp_select')

            st.header("📐 그래프 설정")
            graph_height = st.slider('그래프 높이 조절', min_value=300, max_value=1500, value=900, step=50, key='height_slider')
            graph_width = st.slider('그래프 너비 조절', min_value=300, max_value=2500, value=1800, step=50, key='width_slider')

        except pd.errors.EmptyDataError:
            st.error("업로드된 CSV 파일이 비어있습니다.")
            df = None
        except FileNotFoundError:
            st.error("파일을 찾을 수 없습니다.")
            df = None
        except Exception as e:
            st.error(f"데이터 로드 및 전처리 중 오류 발생: {e}")
            df = None

# --- 함수 정의: 피벗 테이블 및 요약 정보 생성 ---
def generate_pivot(original_df, month, department, process, forklift_class, workplace, analysis_type, current_selected_month_in_sidebar):
    filtered_df = original_df.copy()
    if month != '전체': filtered_df = filtered_df[filtered_df['월'] == month]
    if department != '전체' and '부서' in filtered_df.columns and department != '정보 없음': filtered_df = filtered_df[filtered_df['부서'] == department]
    if process != '전체' and '공정' in filtered_df.columns and process != '정보 없음': filtered_df = filtered_df[filtered_df['공정'] == process]
    if forklift_class != '전체' and '차대 분류' in filtered_df.columns and forklift_class != '정보 없음': filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
    if workplace != '전체' and '작업 장소' in filtered_df.columns and workplace != '정보 없음': filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

    if filtered_df.empty: return {}, "데이터 없음 (필터링 후)", "분석 기준", {}

    local_summary = {}
    pivot_data = {}
    title_prefix = "분석 결과"

    month_str = str(current_selected_month_in_sidebar) + "월" if isinstance(current_selected_month_in_sidebar, int) else current_selected_month_in_sidebar

    if analysis_type == '운영 대수':
        filtered_df['시작 날짜_표시용'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
        index_name = '시작 날짜_표시용'
        value_name = '차대 코드'
        agg_func = 'nunique'
        title_prefix = f'지게차 일자별 운영 대수 ({month_str})' if current_selected_month_in_sidebar != '전체' else '지게차 일자별 운영 대수 (전체 월)'

        try:
            pivot_table_result = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
            if not pivot_table_result.empty:
                sorted_time_columns = sorted(pivot_table_result.columns)
                pivot_table_result = pivot_table_result[sorted_time_columns]
                pivot_table_result = pivot_table_result.sort_index(axis=0)
            pivot_data['units'] = pivot_table_result
        except Exception:
            return {}, title_prefix, index_name, {}

        if not pivot_table_result.empty:
            try:
                total_operating_units = filtered_df[value_name].nunique()
                # ... (이하 요약 정보 계산 동일)
                daily_counts = filtered_df.groupby('시작 날짜_표시용')[value_name].nunique()
                min_operating_units = daily_counts.min() if not daily_counts.empty else 0
                max_operating_units = daily_counts.max() if not daily_counts.empty else 0
                min_operating_day = daily_counts.idxmin() if not daily_counts.empty and min_operating_units > 0 else '데이터 없음'
                max_operating_day = daily_counts.idxmax() if not daily_counts.empty and max_operating_units > 0 else '데이터 없음'
                avg_operating_units = round(daily_counts.mean()) if not daily_counts.empty else 0
                min_units_ratio = (min_operating_units / total_operating_units * 100) if total_operating_units > 0 else 0
                max_units_ratio = (max_operating_units / total_operating_units * 100) if total_operating_units > 0 else 0
                avg_units_ratio = (avg_operating_units / total_operating_units * 100) if total_operating_units > 0 else 0
                local_summary = {'total_units': total_operating_units, 'min_units': min_operating_units, 'min_units_day': min_operating_day, 'min_units_ratio': min_units_ratio, 'max_units': max_operating_units, 'max_units_day': max_operating_day, 'max_units_ratio': max_units_ratio, 'avg_units': avg_operating_units, 'avg_units_ratio': avg_units_ratio}

            except Exception:
                local_summary = {}

    elif analysis_type == '운영 횟수':
        index_name = '차대 코드'
        title_prefix = f'지게차 시간대별 운영 횟수 ({month_str})' if current_selected_month_in_sidebar != '전체' else '지게차 시간대별 운영 횟수 (전체 월)'
        pivot_table_counts = pd.DataFrame()
        pivot_table_times_data = pd.DataFrame()
        forklift_summary_df = pd.DataFrame()

        try:
            pivot_table_counts = filtered_df.pivot_table(index=index_name, columns='시간대', values='시작 날짜', aggfunc='count').fillna(0)
            pivot_table_times_data = filtered_df.pivot_table(index=index_name, columns='시간대', values='운영 시간(초)', aggfunc='sum').fillna(0)

            if not pivot_table_counts.empty:
                sorted_time_columns = sorted(pivot_table_counts.columns)
                pivot_table_counts = pivot_table_counts[sorted_time_columns]
                pivot_table_counts = pivot_table_counts.sort_index(axis=0)
                pivot_table_times_data = pivot_table_times_data.reindex(index=pivot_table_counts.index, columns=pivot_table_counts.columns).fillna(0)

                forklift_total_counts = pivot_table_counts.sum(axis=1)
                forklift_total_times_sec = pivot_table_times_data.sum(axis=1)
                forklift_avg_times_sec = forklift_total_times_sec.divide(forklift_total_counts).replace([np.inf, -np.inf], 0).fillna(0)

                forklift_summary_df = pd.DataFrame({
                    '총 운영 횟수': forklift_total_counts,
                    '총 운영 시간(초)': forklift_total_times_sec,
                    '평균 운영 시간(초)': forklift_avg_times_sec
                }).sort_index()

            pivot_data['counts'] = pivot_table_counts
            pivot_data['times'] = pivot_table_times_data
            pivot_data['forklift_summary'] = forklift_summary_df
        except Exception as e:
            st.error(f"운영 횟수 피벗 테이블 생성 중 오류: {e}")
            return {}, title_prefix, index_name, {}

        if not forklift_summary_df.empty:
            try:
                # ... (이하 요약 정보 계산 동일, forklift_summary_df 또는 filtered_df.groupby 사용)
                # 전체 요약 정보 계산 (기존 로직 유지, 대상 DataFrame 변경)
                total_operating_counts_overall = forklift_summary_df['총 운영 횟수'].sum()
                avg_operating_counts_overall = round(forklift_summary_df['총 운영 횟수'].mean()) if not forklift_summary_df.empty else 0
                min_operating_counts_vehicle = forklift_summary_df['총 운영 횟수'].min() if not forklift_summary_df.empty else 0
                max_operating_counts_vehicle = forklift_summary_df['총 운영 횟수'].max() if not forklift_summary_df.empty else 0
                min_operating_unit_counts = forklift_summary_df['총 운영 횟수'].idxmin() if not forklift_summary_df.empty and min_operating_counts_vehicle > 0 else '데이터 없음'
                max_operating_unit_counts = forklift_summary_df['총 운영 횟수'].idxmax() if not forklift_summary_df.empty and max_operating_counts_vehicle > 0 else '데이터 없음'


                total_operating_time_overall = forklift_summary_df['총 운영 시간(초)'].sum()
                # 차량별 평균 운영 시간의 평균을 사용하는 것보다, 전체 시간 / 전체 횟수로 구하는 것이 더 직관적일 수 있으나, 일단 차량별 평균시간의 평균으로 유지.
                avg_operating_time_vehicle_avg_sec = forklift_summary_df['평균 운영 시간(초)'].mean() if not forklift_summary_df.empty else 0
                min_operating_time_vehicle_total = forklift_summary_df['총 운영 시간(초)'].min() if not forklift_summary_df.empty else 0
                max_operating_time_vehicle_total = forklift_summary_df['총 운영 시간(초)'].max() if not forklift_summary_df.empty else 0
                min_time_unit_total = forklift_summary_df['총 운영 시간(초)'].idxmin() if not forklift_summary_df.empty and min_operating_time_vehicle_total > 0 else '데이터 없음'
                max_time_unit_total = forklift_summary_df['총 운영 시간(초)'].idxmax() if not forklift_summary_df.empty and max_operating_time_vehicle_total > 0 else '데이터 없음'


                local_summary = {
                    'total_counts': total_operating_counts_overall, 'min_counts': min_operating_counts_vehicle, 'min_counts_unit': min_operating_unit_counts,
                    'max_counts': max_operating_counts_vehicle, 'max_counts_unit': max_operating_unit_counts, 'avg_counts': avg_operating_counts_overall, # 차량 당 평균 횟수
                    'total_time': format_time(total_operating_time_overall), 'min_time': format_time(min_operating_time_vehicle_total), 'min_time_unit': min_time_unit_total,
                    'max_time': format_time(max_operating_time_vehicle_total), 'max_time_unit': max_time_unit_total, 'avg_time': format_time(avg_operating_time_vehicle_avg_sec)
                }
            except Exception as e:
                st.warning(f"요약 정보 생성 중 오류: {e}")
                local_summary = {}
    return pivot_data, title_prefix, index_name, local_summary

# --- 메인 페이지 ---
st.title("🚚 지게차 운영 현황 대시보드")

if df is not None:
    pivot_data_dict, current_title, current_index_name, summary_info = generate_pivot(
        df, selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace, analysis_type, selected_month
    )

    if pivot_data_dict and isinstance(pivot_data_dict, dict):
        main_pivot_table = None
        heatmap_cell_times = None
        forklift_summary_for_display = None

        if analysis_type == '운영 대수':
            main_pivot_table = pivot_data_dict.get('units')
        elif analysis_type == '운영 횟수':
            main_pivot_table = pivot_data_dict.get('counts')
            heatmap_cell_times = pivot_data_dict.get('times')
            forklift_summary_for_display = pivot_data_dict.get('forklift_summary')

        if main_pivot_table is not None and not main_pivot_table.empty:
            y_axis_title_text = '시작 날짜' if current_index_name == '시작 날짜_표시용' else '차대 코드'

            if analysis_type == '운영 횟수' and forklift_summary_for_display is not None and not forklift_summary_for_display.empty:
                # --- '운영 횟수' 분석: 왼쪽 (막대 그래프 + 커스텀 Y축) + 오른쪽 (히트맵) ---
                fig = make_subplots(
                    rows=1, cols=2,
                    column_widths=[0.4, 0.6], # 왼쪽 막대그래프, 오른쪽 히트맵 비율
                    shared_yaxes=True, # Y축 공유
                    horizontal_spacing=0.03 # subplot 간 간격
                    # specs 인자는 여기서는 불필요, 각 subplot에 trace 추가 시 X축 지정
                )

                # 1. 커스텀 Y축 레이블 준비 (공유 Y축에 적용됨)
                y_tickvals_ordered = main_pivot_table.index.tolist()
                custom_y_tick_texts = []
                for forklift_id_val in y_tickvals_ordered:
                    if forklift_id_val in forklift_summary_for_display.index:
                        count_val = forklift_summary_for_display.loc[forklift_id_val, '총 운영 횟수']
                        avg_time_sec_val = forklift_summary_for_display.loc[forklift_id_val, '평균 운영 시간(초)']
                        formatted_avg_time = format_time(avg_time_sec_val)
                        custom_y_tick_texts.append(f"{int(count_val): >4}회, {formatted_avg_time} | {forklift_id_val}")
                    else:
                        custom_y_tick_texts.append(f"정보없음 | {forklift_id_val}")

                # 2. 왼쪽 열 (col=1): 차대별 요약 막대 그래프
                fig.add_trace(go.Bar(
                    y=y_tickvals_ordered,
                    x=forklift_summary_for_display['총 운영 횟수'],
                    name='총 운영 횟수',
                    orientation='h',
                    marker_color='rgba(95, 0, 128, 0.7)',
                    text=forklift_summary_for_display['총 운영 횟수'].apply(lambda x: f'{int(x)}회'),
                    textposition='outside', hoverinfo='text',
                    hovertext=[f"{custom_y_tick_texts[i].split(' | ')[1]}<br>총 운영 횟수: {int(forklift_summary_for_display['총 운영 횟수'].iloc[i])}회" for i in range(len(custom_y_tick_texts))],
                    xaxis='x1' # subplot1의 첫번째 x축 명시 (기본값)
                ), row=1, col=1)

                fig.add_trace(go.Bar(
                    y=y_tickvals_ordered,
                    x=forklift_summary_for_display['평균 운영 시간(초)'],
                    name='평균 사용 시간',
                    orientation='h',
                    marker_color='rgba(255, 165, 0, 0.7)',
                    text=forklift_summary_for_display['평균 운영 시간(초)'].apply(lambda x: format_time(x)),
                    textposition='outside', hoverinfo='text',
                    hovertext=[f"{custom_y_tick_texts[i].split(' | ')[1]}<br>평균 사용 시간: {format_time(forklift_summary_for_display['평균 운영 시간(초)'].iloc[i])}" for i in range(len(custom_y_tick_texts))],
                    xaxis='x2' # subplot1의 두번째 x축 명시 (레이아웃에서 정의 필요)
                ), row=1, col=1)

                # 3. 오른쪽 열 (col=2): 히트맵
                tooltip_texts_heatmap = []
                # ... (히트맵 툴팁 생성 로직은 이전과 동일)
                for r_idx, r_label_val in enumerate(main_pivot_table.index):
                    row_tooltips = []
                    for c_idx, c_label_val in enumerate(main_pivot_table.columns):
                        value = main_pivot_table.iloc[r_idx, c_idx]
                        cell_tooltip = f"{r_label_val}, {c_label_val}<br>운영 횟수: {int(value)}회"
                        if heatmap_cell_times is not None and not heatmap_cell_times.empty:
                            try:
                                time_value = heatmap_cell_times.loc[r_label_val, c_label_val]
                                formatted_cell_time = format_time(time_value)
                                cell_tooltip += f"<br>사용 시간: {formatted_cell_time}"
                            except (KeyError, IndexError):
                                cell_tooltip += "<br>사용 시간: -"
                        row_tooltips.append(cell_tooltip)
                    tooltip_texts_heatmap.append(row_tooltips)

                fig.add_trace(go.Heatmap(
                    z=main_pivot_table.values,
                    x=main_pivot_table.columns,
                    y=y_tickvals_ordered,
                    colorscale=[[0, 'rgb(255,255,255)'], [0.01, 'rgb(240, 230, 247)'], [1, '#5f0080']],
                    hoverinfo='text', text=tooltip_texts_heatmap, zmin=0,
                    colorbar=dict(title='횟수', x=1.0, len=0.9, y=0.5, yanchor='middle'),
                    xaxis='x3' # subplot2의 x축 명시
                ), row=1, col=2)

                # 히트맵 최대값 하이라이트 (row=1, col=2에 추가)
                # ... (최대값 하이라이트 로직은 이전과 동일, row/col 인자 확인)
                if main_pivot_table.values.size > 0:
                    try:
                        numeric_values_h = pd.to_numeric(main_pivot_table.values.flatten(), errors='coerce')
                        valid_values_h = numeric_values_h[~np.isnan(numeric_values_h)]
                        if valid_values_h.size > 0:
                            max_value_cell_h = valid_values_h.max()
                            if max_value_cell_h > 0:
                                max_indices_h = np.where(main_pivot_table.values == max_value_cell_h)
                                if len(max_indices_h[0]) > 0:
                                    for y_idx, x_idx in zip(max_indices_h[0], max_indices_h[1]):
                                        fig.add_trace(go.Scatter(
                                            x=[main_pivot_table.columns[x_idx]], y=[main_pivot_table.index[y_idx]],
                                            mode='markers+text',
                                            marker=dict(size=12, color='yellow', symbol='circle-open', line=dict(width=2, color='black')),
                                            text=[f'<b>동시간대 운영(최대): {int(max_value_cell_h)}회</b>'],
                                            textposition='top right', textfont=dict(color='black', size=12), hoverinfo='none',
                                            xaxis='x3' # 히트맵의 X축 사용
                                        ), row=1, col=2)
                    except Exception: pass


                # 전체 레이아웃 업데이트
                fig.update_layout(
                    title={'text': current_title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    yaxis=dict( # 공유 Y축 설정
                        title="",
                        tickmode='array', tickvals=y_tickvals_ordered, ticktext=custom_y_tick_texts,
                        autorange="reversed", automargin=True,
                        showspikes=False # Y축 스파이크는 너무 번잡할 수 있음
                    ),
                    # 왼쪽 subplot (막대 그래프)의 X축들
                    xaxis=dict( # 총 운영 횟수 축 (subplot1의 기본 x축: x1)
                        domain=[0, 0.18], # 왼쪽 영역 할당
                        title='총횟수', automargin=True, titlefont=dict(size=10),
                        showgrid=False
                    ),
                    xaxis2=dict( # 평균 사용 시간 축 (subplot1의 두번째 x축: x2)
                        domain=[0.19, 0.38], # 총 운영 횟수 축 옆 영역 할당
                        title='평균시간', automargin=True, titlefont=dict(size=10),
                        overlaying='y', # Y축을 기준으로 overlay
                        side='top', # 위쪽에 표시 (또는 bottom)
                        showgrid=False,
                        tickfont=dict(size=9)
                    ),
                    # 오른쪽 subplot (히트맵)의 X축
                    xaxis3=dict( # 히트맵 축 (subplot2의 기본 x축: x3)
                        domain=[0.42, 1.0], # 오른쪽 영역 할당
                        title='시간대', tickangle=45, automargin=True,
                        showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'
                    ),
                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=280, r=10, t=100, b=100), # 왼쪽 여백 늘림
                    height=graph_height, width=graph_width,
                    hovermode='closest',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    bargap=0.2,
                    barmode='overlay' # 막대가 겹치도록 (필요시 'group'으로 변경)
                )

            elif analysis_type == '운영 대수':
                # --- '운영 대수' 분석: 기본 단일 히트맵 ---
                fig = make_subplots(rows=1, cols=1)
                # ... (이하 '운영 대수' 로직은 이전과 거의 동일)
                tooltip_texts_list = []
                for r_idx, r_label_val in enumerate(main_pivot_table.index):
                    row_tooltips = []
                    for c_idx, c_label_val in enumerate(main_pivot_table.columns):
                        value = main_pivot_table.iloc[r_idx, c_idx]
                        cell_tooltip = f"{r_label_val}, {c_label_val}<br>운영 대수: {int(value)}대"
                        row_tooltips.append(cell_tooltip)
                    tooltip_texts_list.append(row_tooltips)

                fig.add_trace(go.Heatmap(
                    z=main_pivot_table.values, x=main_pivot_table.columns, y=main_pivot_table.index,
                    colorscale=[[0, 'rgb(255,255,255)'], [0.01, 'rgb(240, 230, 247)'], [1, '#5f0080']],
                    hoverinfo='text', text=tooltip_texts_list, zmin=0,
                    colorbar=dict(title='운영 대수')
                ))

                if main_pivot_table.values.size > 0:
                    try:
                        numeric_values = pd.to_numeric(main_pivot_table.values.flatten(), errors='coerce')
                        valid_values = numeric_values[~np.isnan(numeric_values)]
                        if valid_values.size > 0:
                            max_value_cell = valid_values.max()
                            if max_value_cell > 0:
                                max_indices = np.where(main_pivot_table.values == max_value_cell)
                                if len(max_indices[0]) > 0:
                                    for y_idx, x_idx in zip(max_indices[0], max_indices[1]):
                                        fig.add_trace(go.Scatter(
                                            x=[main_pivot_table.columns[x_idx]], y=[main_pivot_table.index[y_idx]],
                                            mode='markers+text',
                                            marker=dict(size=12, color='yellow', symbol='circle-open', line=dict(width=2, color='black')),
                                            text=[f'<b>동시 투입 대수(최대): {int(max_value_cell)}대</b>'],
                                            textposition='top right', textfont=dict(color='black', size=12), hoverinfo='none'
                                        ))
                    except Exception: pass

                fig.update_layout(
                    title={'text': current_title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    xaxis=dict(title='시간대', fixedrange=False, tickangle=45, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'),
                    yaxis=dict(title=y_axis_title_text, fixedrange=False, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey', type='category', categoryorder='array', categoryarray=sorted(main_pivot_table.index.astype(str))),
                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=100, r=50, t=100, b=80),
                    height=graph_height, width=graph_width,
                    hovermode='closest'
                )
            else:
                 st.warning("선택된 분석 유형에 대한 그래프를 표시할 수 없거나 필요한 데이터가 부족합니다.")


            if 'fig' in locals() and fig is not None :
                 st.plotly_chart(fig, use_container_width=False)

            st.markdown("---")
            st.subheader("📊 요약 정보")
            # ... (요약 정보 표시는 이전과 동일)
            if summary_info:
                if analysis_type == '운영 대수':
                    summary_cols = st.columns(4)
                    with summary_cols[0]: st.metric(label="총 운영된 차량 수", value=f"{summary_info.get('total_units', 'N/A')} 대")
                    with summary_cols[1]: st.metric(label="일 평균 운영 대수", value=f"{summary_info.get('avg_units', 'N/A')} 대", delta=f"{summary_info.get('avg_units_ratio', 0):.1f}%", delta_color="off")
                    with summary_cols[2]: st.metric(label=f"최소 운영 ({summary_info.get('min_units_day', 'N/A')})", value=f"{summary_info.get('min_units', 'N/A')} 대", delta=f"{summary_info.get('min_units_ratio', 0):.1f}%", delta_color="inverse")
                    with summary_cols[3]: st.metric(label=f"최대 운영 ({summary_info.get('max_units_day', 'N/A')})", value=f"{summary_info.get('max_units', 'N/A')} 대", delta=f"{summary_info.get('max_units_ratio', 0):.1f}%", delta_color="normal")
                elif analysis_type == '운영 횟수':
                    st.markdown("##### 🔢 운영 횟수 요약 (차량별)") # 요약 정보 타이틀 수정
                    count_cols = st.columns(4)
                    with count_cols[0]: st.metric(label="전체 운영 횟수", value=f"{summary_info.get('total_counts', 'N/A')} 회")
                    with count_cols[1]: st.metric(label="차량당 평균 운영 횟수", value=f"{summary_info.get('avg_counts', 'N/A')} 회") # 차량'별' 평균 횟수
                    with count_cols[2]: st.metric(label=f"최소 운영 차량 ({summary_info.get('min_counts_unit', 'N/A')})", value=f"{summary_info.get('min_counts', 'N/A')} 회")
                    with count_cols[3]: st.metric(label=f"최대 운영 차량 ({summary_info.get('max_counts_unit', 'N/A')})", value=f"{summary_info.get('max_counts', 'N/A')} 회")
                    st.markdown("---")
                    st.markdown("##### ⏱️ 운영 시간 요약 (차량별)") # 요약 정보 타이틀 수정
                    time_cols = st.columns(4)
                    with time_cols[0]: st.metric(label="전체 운영 시간", value=f"{summary_info.get('total_time', 'N/A')}")
                    with time_cols[1]: st.metric(label="차량당 평균 운영 시간", value=f"{summary_info.get('avg_time', 'N/A')}") # 차량'별' 평균 시간
                    with time_cols[2]: st.metric(label=f"최소 운영 차량 ({summary_info.get('min_time_unit', 'N/A')})", value=f"{summary_info.get('min_time', 'N/A')}")
                    with time_cols[3]: st.metric(label=f"최대 운영 차량 ({summary_info.get('max_time_unit', 'N/A')})", value=f"{summary_info.get('max_time', 'N/A')}")
            else:
                st.info("요약 정보를 표시할 데이터가 충분하지 않거나, 요약 정보 계산 중 오류가 발생했습니다.")

        elif current_title == "데이터 없음 (필터링 후)":
                st.warning("선택하신 필터 조건에 해당하는 데이터가 없습니다. 다른 필터 옵션을 선택해 보세요.")
        else:
            st.warning("피벗 테이블을 생성할 데이터가 없습니다. 원본 데이터를 확인하거나 필터 옵션을 조정해 주세요.")
    elif uploaded_file is not None and df is None:
        st.error("데이터 처리 중 문제가 발생했습니다. 업로드된 파일의 형식을 확인하거나 필수 컬럼이 올바르게 포함되어 있는지 확인해 주세요.")

elif uploaded_file is None:
    st.info("👈 사이드바에서 CSV 파일을 업로드하고 옵션을 선택하면 분석 결과를 볼 수 있습니다.")
