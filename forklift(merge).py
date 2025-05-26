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
            graph_width = st.slider('그래프 너비 조절', min_value=300, max_value=2500, value=1800, step=50, key='width_slider') # 너비 기본값 조정

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
        pivot_table_times_data = pd.DataFrame() # 변수명 변경
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

        if not pivot_table_counts.empty:
            try:
                # 전체 요약 정보 계산 (기존 로직 유지)
                unit_counts_summary = filtered_df.groupby('차대 코드')['시작 날짜'].count()
                total_operating_counts = unit_counts_summary.sum()
                min_operating_counts = unit_counts_summary.min() if not unit_counts_summary.empty else 0
                max_operating_counts = unit_counts_summary.max() if not unit_counts_summary.empty else 0
                min_operating_unit = unit_counts_summary.idxmin() if not unit_counts_summary.empty and min_operating_counts > 0 else '데이터 없음'
                max_operating_unit = unit_counts_summary.idxmax() if not unit_counts_summary.empty and max_operating_counts > 0 else '데이터 없음'
                avg_operating_counts = round(unit_counts_summary.mean()) if not unit_counts_summary.empty else 0
                min_counts_ratio = (min_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
                max_counts_ratio = (max_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
                avg_counts_ratio = (avg_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0

                operating_times_summary = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
                total_operating_time = operating_times_summary.sum()
                min_operating_time = operating_times_summary.min() if not operating_times_summary.empty else 0
                max_operating_time = operating_times_summary.max() if not operating_times_summary.empty else 0
                min_time_unit = operating_times_summary.idxmin() if not operating_times_summary.empty and min_operating_time > 0 else '데이터 없음'
                max_time_unit = operating_times_summary.idxmax() if not operating_times_summary.empty and max_operating_time > 0 else '데이터 없음'
                avg_operating_time = operating_times_summary.mean() if not operating_times_summary.empty else 0
                min_time_ratio = (min_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
                max_time_ratio = (max_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
                avg_time_ratio = (avg_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0

                local_summary = {
                    'total_counts': total_operating_counts, 'min_counts': min_operating_counts, 'min_counts_unit': min_operating_unit, 'min_counts_ratio': min_counts_ratio,
                    'max_counts': max_operating_counts, 'max_counts_unit': max_operating_unit, 'max_counts_ratio': max_counts_ratio, 'avg_counts': avg_operating_counts, 'avg_counts_ratio': avg_counts_ratio,
                    'total_time': format_time(total_operating_time), 'min_time': format_time(min_operating_time), 'min_time_unit': min_time_unit, 'min_time_ratio': min_time_ratio,
                    'max_time': format_time(max_operating_time), 'max_time_unit': max_time_unit, 'max_time_ratio': max_time_ratio, 'avg_time': format_time(avg_operating_time), 'avg_time_ratio': avg_time_ratio
                }
            except Exception:
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
                # --- '운영 횟수' 분석: 히트맵 (커스텀 Y축 레이블) + 오른쪽 막대 그래프 ---
                fig = make_subplots(
                    rows=1, cols=2,
                    column_widths=[0.65, 0.35], # 히트맵과 막대그래프 너비 비율 조정
                    specs=[[{}, {"secondary_y": True}]], # 오른쪽 막대그래프를 위한 spec
                    shared_yaxes=True,
                    horizontal_spacing=0.02
                )

                # 1. 히트맵 (왼쪽, col=1) - 커스텀 Y축 레이블 적용
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

                tooltip_texts_heatmap = []
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
                    colorbar=dict(title='횟수', x=0.62, len=0.8, y=0.5, yanchor='middle') # 컬러바 위치 조정
                ), row=1, col=1)

                # 히트맵 최대값 하이라이트
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
                                            textposition='top right', textfont=dict(color='black', size=12), hoverinfo='none'
                                        ), row=1, col=1)
                    except Exception: pass

                # 2. 차대별 요약 막대 그래프 (오른쪽, col=2)
                fig.add_trace(go.Bar(
                    y=forklift_summary_for_display.index,
                    x=forklift_summary_for_display['총 운영 횟수'],
                    name='총 운영 횟수',
                    orientation='h',
                    marker_color='rgba(95, 0, 128, 0.7)',
                    text=forklift_summary_for_display['총 운영 횟수'].apply(lambda x: f'{int(x)}회'),
                    textposition='outside', hoverinfo='y+x'
                ), row=1, col=2, secondary_y=False)

                fig.add_trace(go.Bar(
                    y=forklift_summary_for_display.index,
                    x=forklift_summary_for_display['평균 운영 시간(초)'],
                    name='평균 사용 시간',
                    orientation='h',
                    marker_color='rgba(255, 165, 0, 0.7)',
                    text=forklift_summary_for_display['평균 운영 시간(초)'].apply(lambda x: format_time(x)),
                    textposition='outside', hoverinfo='y+x'
                ), row=1, col=2, secondary_y=True)

                # 전체 레이아웃 업데이트
                fig.update_layout(
                    title={'text': current_title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    # 히트맵 축 (xaxis, yaxis)
                    xaxis=dict(domain=[0, 0.63], title='시간대', tickangle=45, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'), # 히트맵 X축 도메인 조정
                    yaxis=dict(
                        title="", # Y축 제목 없음
                        tickmode='array', tickvals=y_tickvals_ordered, ticktext=custom_y_tick_texts,
                        autorange="reversed", automargin=True,
                        showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'
                    ),
                    # 막대 그래프 축 (xaxis2, yaxis2, yaxis3)
                    xaxis2=dict(domain=[0.67, 1.0], title='총 운영 횟수', side='bottom', showgrid=False, automargin=True), # 막대그래프 주 X축 (총 횟수)
                    yaxis2=dict(showticklabels=False, showgrid=False, zeroline=False), # 막대그래프 Y축 레이블 숨김 (공유되므로)
                    yaxis3=dict(title='평균 사용 시간(초)', overlaying='y', side='right', showgrid=False, zeroline=False, automargin=True, showticklabels=True, ticks="outside", tickfont=dict(size=10)), # 막대그래프 보조 Y축 (평균 시간 값 표시용)

                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=260, r=50, t=100, b=100), # 왼쪽 여백 유지, 하단 여백 증가
                    height=graph_height, width=graph_width,
                    hovermode='closest',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    bargap=0.2
                )
                # Y축 순서 동기화 (autorange="reversed"가 이미 yaxis에 적용됨)
                # 막대 그래프의 X축 값 순서 관련해서는 특별한 반전이 필요 없을 수 있음 (기본 값 표시)

            elif analysis_type == '운영 대수':
                # --- '운영 대수' 분석: 기본 단일 히트맵 ---
                fig = make_subplots(rows=1, cols=1) # 명시적으로 1x1 서브플롯 생성
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

                # 최대값 하이라이트
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
            else: # 예기치 않은 경우 또는 데이터 부족으로 그래프 생성 불가
                 st.warning("선택된 분석 유형에 대한 그래프를 표시할 수 없거나 필요한 데이터가 부족합니다.")


            if 'fig' in locals() and fig is not None : # fig 객체가 유효한 경우에만 표시
                 st.plotly_chart(fig, use_container_width=False)

            # --- 요약 정보 표시 (이전과 동일) ---
            st.markdown("---")
            st.subheader("📊 요약 정보")
            # ... (요약 정보 표시 로직은 변경 없음) ...
            if summary_info:
                if analysis_type == '운영 대수':
                    summary_cols = st.columns(4)
                    with summary_cols[0]: st.metric(label="총 운영된 차량 수", value=f"{summary_info.get('total_units', 'N/A')} 대")
                    with summary_cols[1]: st.metric(label="일 평균 운영 대수", value=f"{summary_info.get('avg_units', 'N/A')} 대", delta=f"{summary_info.get('avg_units_ratio', 0):.1f}%", delta_color="off")
                    with summary_cols[2]: st.metric(label=f"최소 운영 ({summary_info.get('min_units_day', 'N/A')})", value=f"{summary_info.get('min_units', 'N/A')} 대", delta=f"{summary_info.get('min_units_ratio', 0):.1f}%", delta_color="inverse")
                    with summary_cols[3]: st.metric(label=f"최대 운영 ({summary_info.get('max_units_day', 'N/A')})", value=f"{summary_info.get('max_units', 'N/A')} 대", delta=f"{summary_info.get('max_units_ratio', 0):.1f}%", delta_color="normal")
                elif analysis_type == '운영 횟수':
                    st.markdown("##### 🔢 운영 횟수 요약 (차량별)")
                    count_cols = st.columns(4)
                    with count_cols[0]: st.metric(label="전체 운영 횟수", value=f"{summary_info.get('total_counts', 'N/A')} 회")
                    with count_cols[1]: st.metric(label="차량 평균 운영 횟수", value=f"{summary_info.get('avg_counts', 'N/A')} 회", delta=f"{summary_info.get('avg_counts_ratio', 0):.1f}%", delta_color="off")
                    with count_cols[2]: st.metric(label=f"최소 운영 ({summary_info.get('min_counts_unit', 'N/A')})", value=f"{summary_info.get('min_counts', 'N/A')} 회", delta=f"{summary_info.get('min_counts_ratio', 0):.1f}%", delta_color="inverse")
                    with count_cols[3]: st.metric(label=f"최대 운영 ({summary_info.get('max_counts_unit', 'N/A')})", value=f"{summary_info.get('max_counts', 'N/A')} 회", delta=f"{summary_info.get('max_counts_ratio', 0):.1f}%", delta_color="normal")
                    st.markdown("---")
                    st.markdown("##### ⏱️ 운영 시간 요약 (차량별)")
                    time_cols = st.columns(4)
                    with time_cols[0]: st.metric(label="전체 운영 시간", value=f"{summary_info.get('total_time', 'N/A')}")
                    with time_cols[1]: st.metric(label="차량 평균 운영 시간", value=f"{summary_info.get('avg_time', 'N/A')}", delta=f"{summary_info.get('avg_time_ratio', 0):.1f}%", delta_color="off")
                    with time_cols[2]: st.metric(label=f"최소 운영 ({summary_info.get('min_time_unit', 'N/A')})", value=f"{summary_info.get('min_time', 'N/A')}", delta=f"{summary_info.get('min_time_ratio', 0):.1f}%", delta_color="inverse")
                    with time_cols[3]: st.metric(label=f"최대 운영 ({summary_info.get('max_time_unit', 'N/A')})", value=f"{summary_info.get('max_time', 'N/A')}", delta=f"{summary_info.get('max_time_ratio', 0):.1f}%", delta_color="normal")
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
