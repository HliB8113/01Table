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

def format_to_hh_mm(seconds):
    """초 단위 시간을 HH:MM 형식의 문자열로 변환합니다."""
    if pd.isna(seconds) or np.isinf(seconds) or seconds < 0:
        return "00:00"
    seconds = int(round(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}"

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
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수', '운영 시간'), key='analysis_type')


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
            
            y_axis_font_size = 10 
            bar_label_font_size = 14 

            if analysis_type == '운영 횟수':
                y_axis_font_size = st.slider('Y축 레이블 폰트 크기 (운영 횟수 시)', min_value=8, max_value=20, value=y_axis_font_size, step=1, key='y_font_slider')
            elif analysis_type == '운영 시간':
                bar_label_font_size = st.slider('막대 라벨 폰트 크기 (운영 시간 시)', min_value=8, max_value=24, value=bar_label_font_size, step=1, key='bar_font_slider')


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
# generate_pivot 함수는 이전과 동일
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
    index_name = "분석 기준"
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
                forklift_avg_time_per_op_sec = forklift_total_times_sec.divide(forklift_total_counts).replace([np.inf, -np.inf], 0).fillna(0)

                active_days_per_forklift = filtered_df.groupby('차대 코드')['시작 날짜'].nunique()
                active_days_per_forklift = active_days_per_forklift.reindex(pivot_table_counts.index).fillna(1)
                active_days_per_forklift[active_days_per_forklift == 0] = 1

                avg_ops_per_active_day = forklift_total_counts.divide(active_days_per_forklift).replace([np.inf, -np.inf], 0).fillna(0)

                forklift_summary_df = pd.DataFrame({
                    '총 운영 횟수': forklift_total_counts,
                    '일 평균 운영 횟수': avg_ops_per_active_day,
                    '총 운영 시간(초)': forklift_total_times_sec,
                    '평균 운영 시간(초)': forklift_avg_time_per_op_sec
                }).sort_index()

            pivot_data['counts'] = pivot_table_counts
            pivot_data['times'] = pivot_table_times_data
            pivot_data['forklift_summary'] = forklift_summary_df
        except Exception as e:
            st.error(f"운영 횟수 피벗 테이블/요약 생성 중 오류: {e}")
            return {}, title_prefix, index_name, {}

        if not forklift_summary_df.empty:
            try:
                total_counts_all_forklifts = forklift_summary_df['총 운영 횟수'].sum()
                avg_total_counts_per_forklift = round(forklift_summary_df['총 운영 횟수'].mean()) if not forklift_summary_df.empty else 0
                min_total_counts_for_a_forklift = forklift_summary_df['총 운영 횟수'].min() if not forklift_summary_df.empty else 0
                max_total_counts_for_a_forklift = forklift_summary_df['총 운영 횟수'].max() if not forklift_summary_df.empty else 0
                min_total_counts_forklift_id = forklift_summary_df['총 운영 횟수'].idxmin() if not forklift_summary_df.empty and min_total_counts_for_a_forklift > 0 else '데이터 없음'
                max_total_counts_forklift_id = forklift_summary_df['총 운영 횟수'].idxmax() if not forklift_summary_df.empty and max_total_counts_for_a_forklift > 0 else '데이터 없음'

                total_time_all_forklifts = forklift_summary_df['총 운영 시간(초)'].sum()
                avg_op_time_per_op_across_forklifts = forklift_summary_df['평균 운영 시간(초)'].mean() if not forklift_summary_df.empty else 0
                min_total_time_for_a_forklift = forklift_summary_df['총 운영 시간(초)'].min() if not forklift_summary_df.empty else 0
                max_total_time_for_a_forklift = forklift_summary_df['총 운영 시간(초)'].max() if not forklift_summary_df.empty else 0
                min_total_time_forklift_id = forklift_summary_df['총 운영 시간(초)'].idxmin() if not forklift_summary_df.empty and min_total_time_for_a_forklift > 0 else '데이터 없음'
                max_total_time_forklift_id = forklift_summary_df['총 운영 시간(초)'].idxmax() if not forklift_summary_df.empty and max_total_time_for_a_forklift > 0 else '데이터 없음'

                local_summary = {
                    'total_counts': total_counts_all_forklifts, 'avg_counts': avg_total_counts_per_forklift,
                    'min_counts': min_total_counts_for_a_forklift, 'min_counts_unit': min_total_counts_forklift_id,
                    'max_counts': max_total_counts_for_a_forklift, 'max_counts_unit': max_total_counts_forklift_id,
                    'total_time': format_time(total_time_all_forklifts), 'avg_time': format_time(avg_op_time_per_op_across_forklifts),
                    'min_time': format_time(min_total_time_for_a_forklift), 'min_time_unit': min_total_time_forklift_id,
                    'max_time': format_time(max_total_time_for_a_forklift), 'max_time_unit': max_total_time_forklift_id,
                }
            except Exception as e:
                st.warning(f"요약 정보 생성 중 오류: {e}")
                local_summary = {}

    elif analysis_type == '운영 시간':
        index_name = '차대 코드'
        title_prefix = f'차대 코드별 총 운영 시간 ({month_str})' if current_selected_month_in_sidebar != '전체' else '차대 코드별 총 운영 시간 (전체 월)'
        if filtered_df.empty or '차대 코드' not in filtered_df.columns or '운영 시간(초)' not in filtered_df.columns:
            pivot_data['total_operation_time'] = pd.Series(dtype='float64')
        else:
            total_time_per_forklift = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum().sort_values(ascending=False)
            pivot_data['total_operation_time'] = total_time_per_forklift

        if 'total_operation_time' in pivot_data and not pivot_data['total_operation_time'].empty:
            summary_series = pivot_data['total_operation_time']
            overall_total_time_all_forklifts = summary_series.sum()
            avg_total_time_per_forklift = summary_series.mean()
            min_total_time_val = summary_series.min()
            max_total_time_val = summary_series.max()
            min_total_time_id = summary_series.idxmin() if not pd.isna(min_total_time_val) and min_total_time_val > 0 else '데이터 없음'
            max_total_time_id = summary_series.idxmax() if not pd.isna(max_total_time_val) and max_total_time_val > 0 else '데이터 없음'
            local_summary = {
                'overall_total_time': format_time(overall_total_time_all_forklifts),
                'avg_total_time_per_forklift': format_time(avg_total_time_per_forklift),
                'min_total_time_for_a_forklift': format_time(min_total_time_val),
                'min_total_time_forklift_id': min_total_time_id,
                'max_total_time_for_a_forklift': format_time(max_total_time_val),
                'max_total_time_forklift_id': max_total_time_id,
                'number_of_forklifts': len(summary_series)
            }
        else:
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
        total_operation_time_data = None

        # 슬라이더 값을 여기서 한 번만 읽어옴
        current_y_axis_font_size = y_axis_font_size
        current_bar_label_font_size = bar_label_font_size


        if analysis_type == '운영 대수':
            main_pivot_table = pivot_data_dict.get('units')
        elif analysis_type == '운영 횟수':
            main_pivot_table = pivot_data_dict.get('counts')
            heatmap_cell_times = pivot_data_dict.get('times')
            forklift_summary_for_display = pivot_data_dict.get('forklift_summary')
        elif analysis_type == '운영 시간':
            total_operation_time_data = pivot_data_dict.get('total_operation_time')

        if (main_pivot_table is not None and not main_pivot_table.empty) or \
           (total_operation_time_data is not None and not total_operation_time_data.empty and analysis_type == '운영 시간'):

            y_axis_title_text = '시작 날짜' if current_index_name == '시작 날짜_표시용' else '차대 코드'
            fig = None

            if analysis_type == '운영 횟수' and forklift_summary_for_display is not None and not forklift_summary_for_display.empty:
                if current_y_axis_font_size >= 16: # current_y_axis_font_size 사용
                    margin_left = 320 + (current_y_axis_font_size - 16) * 10
                    col_width_left_dynamic = 0.30
                elif current_y_axis_font_size >= 12:
                    margin_left = 280 + (current_y_axis_font_size - 12) * 10
                    col_width_left_dynamic = 0.28
                else:
                    margin_left = 260 + current_y_axis_font_size * 2
                    col_width_left_dynamic = 0.25
                col_width_left_dynamic = min(col_width_left_dynamic, 0.4)
                col_width_right_dynamic = 1.0 - col_width_left_dynamic
                spacing = 0.03

                fig = make_subplots(
                    rows=1, cols=2,
                    column_widths=[col_width_left_dynamic, col_width_right_dynamic],
                    shared_yaxes=True,
                    horizontal_spacing=spacing
                )
                y_tickvals_ordered = main_pivot_table.index.tolist()
                custom_y_tick_texts = []
                for forklift_id_val in y_tickvals_ordered:
                    if forklift_id_val in forklift_summary_for_display.index:
                        avg_ops_daily_val = forklift_summary_for_display.loc[forklift_id_val, '일 평균 운영 횟수']
                        avg_time_per_op_sec_val = forklift_summary_for_display.loc[forklift_id_val, '평균 운영 시간(초)']
                        formatted_avg_time_per_op = format_time(avg_time_per_op_sec_val)
                        custom_y_tick_texts.append(f"{avg_ops_daily_val:.1f}회/일, {formatted_avg_time_per_op} | {forklift_id_val}")
                    else:
                        custom_y_tick_texts.append(f"정보없음 | {forklift_id_val}")

                fig.add_trace(go.Bar(
                    y=y_tickvals_ordered,
                    x=forklift_summary_for_display['평균 운영 시간(초)'],
                    name='1회당 평균 사용시간',
                    orientation='h',
                    marker_color='rgba(255, 165, 0, 0.7)',
                    hoverinfo='text',
                    hovertext=[f"{custom_y_tick_texts[i].split(' | ')[1]}<br>1회당 평균 사용시간: {format_time(forklift_summary_for_display['평균 운영 시간(초)'].iloc[i])}" for i in range(len(custom_y_tick_texts))],
                    xaxis='x1'
                ), row=1, col=1)

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
                    colorbar=dict(title='시간대별<br>운영횟수', x=1.01, len=0.9, y=0.5, yanchor='middle', xanchor='left'),
                    xaxis='x2'
                ), row=1, col=2)

                if main_pivot_table.values.size > 0:
                    try:
                        numeric_values_h = pd.to_numeric(main_pivot_table.values.flatten(), errors='coerce')
                        valid_values_h = numeric_values_h[~np.isnan(numeric_values_h)]
                        if valid_values_h.size > 0:
                            max_value_cell_h = valid_values_h.max()
                            if max_value_cell_h > 0:
                                max_indices_h = np.where(main_pivot_table.values == max_value_cell_h)
                                if len(max_indices_h[0]) > 0:
                                    for y_idx, x_idx_val in zip(max_indices_h[0], max_indices_h[1]):
                                        fig.add_trace(go.Scatter(
                                            x=[main_pivot_table.columns[x_idx_val]], y=[main_pivot_table.index[y_idx]],
                                            mode='markers',
                                            marker=dict(size=12, color='yellow', symbol='circle-open', line=dict(width=2, color='black')),
                                            hoverinfo='none',
                                            xaxis='x2'
                                        ), row=1, col=2)
                    except Exception: pass

                fig.update_layout(
                    title={'text': current_title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    yaxis=dict(
                        title="",
                        tickmode='array', tickvals=y_tickvals_ordered, ticktext=custom_y_tick_texts,
                        autorange="reversed", automargin=True,
                        tickfont=dict(size=current_y_axis_font_size), # current_y_axis_font_size 사용
                        showspikes=False
                    ),
                    xaxis1=dict(
                        domain=[0, col_width_left_dynamic - (spacing / 2) if col_width_left_dynamic > spacing else 0],
                        title='1회당 평균시간', automargin=True, titlefont=dict(size=10),
                        showgrid=False, fixedrange=False
                    ),
                    xaxis2=dict(
                        domain=[col_width_left_dynamic + (spacing / 2) if col_width_left_dynamic < 1.0 - spacing else col_width_left_dynamic, 1.0],
                        title='시간대', tickangle=45, automargin=True,
                        showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey',
                        fixedrange=False
                    ),
                    hoverlabel=dict(font_size=14), # 툴팁 폰트 크기 일괄 적용
                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=margin_left, r=30, t=100, b=100),
                    height=graph_height, width=graph_width,
                    hovermode='closest',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal"),
                    bargap=0.2
                )
                fig.update_xaxes(automargin=True)
                fig.update_yaxes(automargin=True)


            elif analysis_type == '운영 대수':
                fig = make_subplots(rows=1, cols=1)
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
                                    for y_idx, x_idx_val in zip(max_indices[0], max_indices[1]):
                                        fig.add_trace(go.Scatter(
                                            x=[main_pivot_table.columns[x_idx_val]], y=[main_pivot_table.index[y_idx]],
                                            mode='markers',
                                            marker=dict(size=12, color='yellow', symbol='circle-open', line=dict(width=2, color='black')),
                                            hoverinfo='none'
                                        ))
                    except Exception: pass

                fig.update_layout(
                    title={'text': current_title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    xaxis=dict(title='시간대', fixedrange=False, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey', tickangle=45),
                    yaxis=dict(title=y_axis_title_text, fixedrange=False, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey', type='category', categoryorder='array', categoryarray=sorted(main_pivot_table.index.astype(str))),
                    hoverlabel=dict(font_size=14), # 툴팁 폰트 크기 일괄 적용
                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=100, r=50, t=100, b=80),
                    height=graph_height, width=graph_width,
                    hovermode='closest'
                )

            elif analysis_type == '운영 시간' and total_operation_time_data is not None and not total_operation_time_data.empty:
                fig = make_subplots(rows=1, cols=1)
                y_labels_op_time = total_operation_time_data.index.tolist()
                x_values_op_time_sec = total_operation_time_data.values
                bar_texts_op_time = [format_time(s) for s in x_values_op_time_sec]

                fig.add_trace(go.Bar(
                    y=y_labels_op_time,
                    x=x_values_op_time_sec,
                    orientation='h',
                    text=bar_texts_op_time,
                    textposition='outside', # 항상 바깥쪽에 표시
                    marker_color='gold', 
                    name='총 운영 시간',
                    hoverinfo='y+text',
                    customdata=x_values_op_time_sec,
                    hovertemplate='<b>%{y}</b><br>총 운영 시간: %{text} (%{customdata}초)<extra></extra>',
                    textfont=dict(size=current_bar_label_font_size, color='black') # current_bar_label_font_size 사용
                ))
                
                if len(x_values_op_time_sec) > 0 and max(x_values_op_time_sec) > 0:
                    max_x_sec = max(x_values_op_time_sec)
                    tickvals = np.linspace(0, max_x_sec, num=5).tolist()
                    ticktext_hh_mm = [format_to_hh_mm(s) for s in tickvals]
                else:
                    tickvals = [0]
                    ticktext_hh_mm = ["00:00"]

                fig.update_layout(
                    title={'text': current_title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    xaxis=dict(
                        title='총 운영 시간 (HH:MM)', 
                        automargin=True,
                        tickmode='array',
                        tickvals=tickvals,
                        ticktext=ticktext_hh_mm,
                        fixedrange=False # 확대/축소 허용
                    ),
                    yaxis=dict(title='차대 코드', automargin=True, autorange="reversed",
                               categoryorder='array', categoryarray=y_labels_op_time,
                               fixedrange=False # 확대/축소 허용
                              ),
                    hoverlabel=dict(font_size=14), # 툴팁 폰트 크기 일괄 적용
                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=150, r=50, t=100, b=80), # 오른쪽 여백 확보 (textposition='outside' 시 필요할 수 있음)
                    height=graph_height, width=graph_width,
                    hovermode='y'
                )
                fig.update_xaxes(automargin=True)
                fig.update_yaxes(automargin=True)

            else:
                 if analysis_type not in ['운영 대수', '운영 횟수', '운영 시간']:
                    st.error(f"알 수 없는 분석 유형입니다: {analysis_type}")
                 elif current_title != "데이터 없음 (필터링 후)":
                    st.warning("선택된 분석 유형에 대한 데이터를 표시할 수 없습니다.")

            if fig is not None:
                 st.plotly_chart(fig, use_container_width=False)
            elif current_title == "데이터 없음 (필터링 후)":
                st.warning("선택하신 필터 조건에 해당하는 데이터가 없습니다. 다른 필터 옵션을 선택해 보세요.")
            elif not ((main_pivot_table is not None and not main_pivot_table.empty) or \
                      (total_operation_time_data is not None and not total_operation_time_data.empty and analysis_type == '운영 시간')):
                st.warning("피벗 테이블 또는 운영 시간 데이터를 생성할 수 없습니다. 원본 데이터를 확인하거나 필터 옵션을 조정해 주세요.")

            st.markdown("---")
            st.subheader("📊 요약 정보")
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
                    with count_cols[1]: st.metric(label="차량당 총 운영횟수 평균", value=f"{summary_info.get('avg_counts', 'N/A')} 회")
                    with count_cols[2]: st.metric(label=f"최소 운영 차량(총횟수)", value=f"{summary_info.get('min_counts_unit', 'N/A')}: {summary_info.get('min_counts', 'N/A')} 회")
                    with count_cols[3]: st.metric(label=f"최대 운영 차량(총횟수)", value=f"{summary_info.get('max_counts_unit', 'N/A')}: {summary_info.get('max_counts', 'N/A')} 회")
                    st.markdown("---")
                    st.markdown("##### ⏱️ 운영 시간 요약 (차량별)")
                    time_cols = st.columns(4)
                    with time_cols[0]: st.metric(label="전체 운영 시간", value=f"{summary_info.get('total_time', 'N/A')}")
                    with time_cols[1]: st.metric(label="차량당 1회 평균 운영시간 평균", value=f"{summary_info.get('avg_time', 'N/A')}")
                    with time_cols[2]: st.metric(label=f"최소 운영 차량(총시간)", value=f"{summary_info.get('min_time_unit', 'N/A')}: {summary_info.get('min_time', 'N/A')}")
                    with time_cols[3]: st.metric(label=f"최대 운영 차량(총시간)", value=f"{summary_info.get('max_time_unit', 'N/A')}: {summary_info.get('max_time', 'N/A')}")
                
                elif analysis_type == '운영 시간':
                    st.markdown("##### ⏱️ 차대 코드별 총 운영 시간 요약")
                    num_forklifts = summary_info.get('number_of_forklifts', 'N/A')
                    st.metric(label="분석 대상 차량 수", value=f"{num_forklifts} 대")

                    overall_total_time = summary_info.get('overall_total_time', 'N/A')
                    avg_total_time = summary_info.get('avg_total_time_per_forklift', 'N/A')
                    
                    col1, col2 = st.columns(2)
                    col1.metric(label="전체 차량 총 운영 시간", value=overall_total_time)
                    col2.metric(label="차량당 평균 총 운영 시간", value=avg_total_time)
                    
                    min_id = summary_info.get('min_total_time_forklift_id', 'N/A')
                    min_val = summary_info.get('min_total_time_for_a_forklift', 'N/A')
                    max_id = summary_info.get('max_total_time_forklift_id', 'N/A')
                    max_val = summary_info.get('max_total_time_for_a_forklift', 'N/A')

                    st.markdown(f"**최소 총 운영 시간 차량:** `{min_id}` ({min_val})")
                    st.markdown(f"**최대 총 운영 시간 차량:** `{max_id}` ({max_val})")
            else:
                st.info("요약 정보를 표시할 데이터가 충분하지 않거나, 요약 정보 계산 중 오류가 발생했습니다.")
        elif current_title == "데이터 없음 (필터링 후)":
            st.warning("선택하신 필터 조건에 해당하는 데이터가 없습니다. 다른 필터 옵션을 선택해 보세요.")
        elif not ((main_pivot_table is not None and not main_pivot_table.empty) or \
                  (total_operation_time_data is not None and not total_operation_time_data.empty and analysis_type == '운영 시간')):
            st.warning("피벗 테이블 또는 운영 시간 데이터를 생성할 수 없습니다. 원본 데이터를 확인하거나 필터 옵션을 조정해 주세요.")
    elif uploaded_file is not None and df is None:
        st.error("데이터 처리 중 문제가 발생했습니다. 업로드된 파일의 형식을 확인하거나 필수 컬럼이 올바르게 포함되어 있는지 확인해 주세요.")
elif uploaded_file is None:
    st.info("👈 사이드바에서 CSV 파일을 업로드하고 옵션을 선택하면 분석 결과를 볼 수 있습니다.")
