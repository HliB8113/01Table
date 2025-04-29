import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np # numpy 추가

# Streamlit 페이지 설정
st.set_page_config(page_title='지게차 운영 분석 대시보드', layout='wide', initial_sidebar_state='expanded')

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 데이터 업로드 및 필터")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"])
    df = None # df 초기화

    if uploaded_file is not None:
        try:
            df_initial = pd.read_csv(uploaded_file)
            st.success("✔️ 파일 로딩 성공!")

            # --- 필수 컬럼 확인 ---
            required_columns = ['시간대', '시작 날짜', '차대 코드', '운영 시간(초)']
            optional_columns = ['부서', '공정', '차대 분류', '작업 장소']
            missing_required = [col for col in required_columns if col not in df_initial.columns]
            missing_optional = [col for col in optional_columns if col not in df_initial.columns]

            if missing_required:
                st.error(f"❌ 오류: 필수 컬럼 누락 - {', '.join(missing_required)}. 분석 불가.")
                st.stop()
            else:
                df = df_initial.copy()

            if missing_optional:
                st.warning(f"⚠️ 경고: 필터링 컬럼 누락 - {', '.join(missing_optional)}. 해당 필터는 작동하지 않거나 제한됩니다.")
                for col in missing_optional:
                    df[col] = '정보 없음'

            # --- 데이터 타입 변환 및 정제 ---
            try:
                df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
                df.dropna(subset=['시간대'], inplace=True)
                if df.empty:
                    st.warning("⚠️ 시간대 변환 후 유효한 데이터가 없습니다.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ '시간대' 컬럼 변환 오류: {e}. 형식을 확인하세요 (예: HH:MM).")
                st.stop()

            try:
                df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
                df.dropna(subset=['시작 날짜'], inplace=True)
                if df.empty:
                    st.warning("⚠️ 시작 날짜 변환 후 유효한 데이터가 없습니다.")
                    st.stop()
                df['월'] = df['시작 날짜'].dt.month
            except Exception as e:
                st.error(f"❌ '시작 날짜' 컬럼 변환 오류: {e}. 날짜 형식을 확인하세요.")
                st.stop()

            df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)

            # --- 데이터 필터링 (12월 제외) ---
            excluded_month = 12
            df = df[df['월'] != excluded_month]
            if df.empty:
                st.warning(f"⚠️ {excluded_month}월 제외 후 분석할 데이터가 없습니다.")
                st.stop()

            # --- 사이드바 필터 옵션 설정 ---
            st.header("📊 분석 옵션")
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'), key='analysis_type')

            month_options = ['전체'] + sorted(df['월'].dropna().unique().astype(int).tolist())
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

        except pd.errors.EmptyDataError:
            st.error("❌ 오류: 업로드된 파일이 비어 있습니다.")
            df = None
        except FileNotFoundError:
            st.error("❌ 오류: 파일을 찾을 수 없습니다.")
            df = None
        except Exception as e:
            st.error(f"❌ 파일 처리 중 예상치 못한 오류 발생: {e}")
            df = None

# --- 함수 정의: 피벗 테이블 및 요약 정보 생성 ---
def generate_pivot(original_df, month, department, process, forklift_class, workplace, analysis_type):
    filtered_df = original_df.copy()

    # --- 필터링 적용 ---
    if month != '전체':
        filtered_df = filtered_df[filtered_df['월'] == month]
    if department != '전체' and '부서' in filtered_df.columns and department != '정보 없음':
        filtered_df = filtered_df[filtered_df['부서'] == department]
    if process != '전체' and '공정' in filtered_df.columns and process != '정보 없음':
        filtered_df = filtered_df[filtered_df['공정'] == process]
    if forklift_class != '전체' and '차대 분류' in filtered_df.columns and forklift_class != '정보 없음':
        filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
    if workplace != '전체' and '작업 장소' in filtered_df.columns and workplace != '정보 없음':
        filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

    # --- 필터링 후 데이터 유무 확인 ---
    if filtered_df.empty:
        st.warning("⚠️ 선택된 조건에 해당하는 데이터가 없습니다.")
        return pd.DataFrame(), "데이터 없음", "데이터 없음", {} # 빈 데이터프레임과 기본값 반환

    # --- 분석 유형별 처리 ---
    local_summary = {} # 함수 내 지역 변수로 summary 사용
    pivot_table_result = pd.DataFrame() # 결과 초기화
    title = "분석 결과"
    index_name = "분석 기준"

    if analysis_type == '운영 대수':
        filtered_df['시작 날짜_표시용'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
        index_name = '시작 날짜_표시용'
        value_name = '차대 코드'
        agg_func = 'nunique'
        title = f'지게차 일자별 운영 대수 ({selected_month}월)' if selected_month != '전체' else '지게차 일자별 운영 대수 (전체 월)'

        try:
            pivot_table_result = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
            if not pivot_table_result.empty:
                 pivot_table_result = pivot_table_result.sort_index(axis=1)
        except Exception as e:
             st.error(f"❌ '운영 대수' 피벗 테이블 생성 오류: {e}")
             return pd.DataFrame(), title, index_name, {}

        if not pivot_table_result.empty:
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
            local_summary = {
                'total_units': total_operating_units, 'min_units': min_operating_units,
                'min_units_day': min_operating_day, 'min_units_ratio': min_units_ratio,
                'max_units': max_operating_units, 'max_units_day': max_operating_day,
                'max_units_ratio': max_units_ratio, 'avg_units': avg_operating_units,
                'avg_units_ratio': avg_units_ratio,
            }

    elif analysis_type == '운영 횟수':
        index_name = '차대 코드'
        value_name = '시작 날짜'
        agg_func = 'count'
        title = f'지게차 시간대별 운영 횟수 ({selected_month}월)' if selected_month != '전체' else '지게차 시간대별 운영 횟수 (전체 월)'

        try:
            pivot_table_result = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
            if not pivot_table_result.empty:
                 pivot_table_result = pivot_table_result.sort_index(axis=1)
        except Exception as e:
            st.error(f"❌ '운영 횟수' 피벗 테이블 생성 오류: {e}")
            return pd.DataFrame(), title, index_name, {}

        if not pivot_table_result.empty:
            unit_counts = filtered_df.groupby('차대 코드')[value_name].count()
            total_operating_counts = unit_counts.sum()
            min_operating_counts = unit_counts.min() if not unit_counts.empty else 0
            max_operating_counts = unit_counts.max() if not unit_counts.empty else 0
            min_operating_unit = unit_counts.idxmin() if not unit_counts.empty and min_operating_counts > 0 else '데이터 없음'
            max_operating_unit = unit_counts.idxmax() if not unit_counts.empty and max_operating_counts > 0 else '데이터 없음'
            avg_operating_counts = round(unit_counts.mean()) if not unit_counts.empty else 0
            min_counts_ratio = (min_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
            max_counts_ratio = (max_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0
            avg_counts_ratio = (avg_operating_counts / total_operating_counts * 100) if total_operating_counts > 0 else 0

            operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
            total_operating_time = operating_times.sum()
            min_operating_time = operating_times.min() if not operating_times.empty else 0
            max_operating_time = operating_times.max() if not operating_times.empty else 0
            min_time_unit = operating_times.idxmin() if not operating_times.empty and min_operating_time > 0 else '데이터 없음'
            max_time_unit = operating_times.idxmax() if not operating_times.empty and max_operating_time > 0 else '데이터 없음'
            avg_operating_time = operating_times.mean() if not operating_times.empty else 0
            min_time_ratio = (min_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
            max_time_ratio = (max_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0
            avg_time_ratio = (avg_operating_time / total_operating_time * 100) if total_operating_time > 0 else 0

            def format_time(seconds):
                if pd.isna(seconds) or np.isinf(seconds) or seconds < 0: return "00:00:00"
                seconds = int(round(seconds))
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"

            local_summary = {
                'total_counts': total_operating_counts, 'min_counts': min_operating_counts,
                'min_counts_unit': min_operating_unit, 'min_counts_ratio': min_counts_ratio,
                'max_counts': max_operating_counts, 'max_counts_unit': max_operating_unit,
                'max_counts_ratio': max_counts_ratio, 'avg_counts': avg_operating_counts,
                'avg_counts_ratio': avg_counts_ratio, 'total_time': format_time(total_operating_time),
                'min_time': format_time(min_operating_time), 'min_time_unit': min_time_unit,
                'min_time_ratio': min_time_ratio, 'max_time': format_time(max_operating_time),
                'max_time_unit': max_time_unit, 'max_time_ratio': max_time_ratio,
                'avg_time': format_time(avg_operating_time), 'avg_time_ratio': avg_time_ratio,
            }

    return pivot_table_result, title, index_name, local_summary

# --- 메인 페이지 ---
st.title("🚚 지게차 운영 현황 대시보드")

if df is not None and not df.empty:
    pivot_table, title, index_name, summary = generate_pivot(
        df, selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace, analysis_type
    )

    # --- 시각화 (피벗 테이블이 비어있지 않을 때) ---
    if not pivot_table.empty:
        y_axis_title = '시작 날짜' if index_name == '시작 날짜_표시용' else index_name

        # --- 그래프 생성 ---
        fig = make_subplots(rows=1, cols=1)

        # --- 수정된 툴팁 텍스트 생성 (좌표 포함) ---
        tooltip_texts = []
        value_prefix = "운영 횟수" if analysis_type == '운영 횟수' else "운영 대수"
        value_suffix = "회" if analysis_type == '운영 횟수' else "대"

        # 피벗 테이블의 각 셀을 순회하며 툴팁 생성
        for r in range(len(pivot_table.index)):
            y_label = pivot_table.index[r] # 현재 행의 Y축 레이블
            row_tooltips = []
            for c in range(len(pivot_table.columns)):
                x_label = pivot_table.columns[c] # 현재 열의 X축 레이블
                value = pivot_table.iloc[r, c] # 현재 셀의 값
                # Y축, X축 레이블과 값을 포함하는 툴팁 문자열 생성 (<br>은 줄바꿈)
                cell_tooltip = f"{y_label}, {x_label}<br>{value_prefix}: {int(value)}{value_suffix}"
                row_tooltips.append(cell_tooltip)
            tooltip_texts.append(row_tooltips)
        # --- 툴팁 생성 끝 ---

        # 히트맵 생성
        heatmap = go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Purples',
            hoverinfo='text',       # 'text' 모드를 사용하여 아래 'text' 인수에 전달된 내용 표시
            text=tooltip_texts,     # 위에서 생성한 사용자 정의 툴팁 텍스트 리스트 전달
            zmin=0,
            colorbar=dict(title='값' if analysis_type == '운영 대수' else '횟수')
        )
        fig.add_trace(heatmap)

        # 최댓값 하이라이트 추가 (이전과 동일)
        if pivot_table.values.size > 0:
            try:
                numeric_values = pd.to_numeric(pivot_table.values.flatten(), errors='coerce')
                valid_values = numeric_values[~np.isnan(numeric_values)]
                if valid_values.size > 0:
                    max_value = valid_values.max()
                    if max_value > 0:
                        max_indices = np.where(np.isclose(pd.to_numeric(pivot_table.values, errors='coerce'), max_value))
                        if len(max_indices[0]) > 0:
                            max_y_indices, max_x_indices = max_indices[0], max_indices[1]
                            highlight_text_prefix = "동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"
                            highlight_text_suffix = "대" if analysis_type == "운영 대수" else "회"
                            for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                                fig.add_trace(go.Scatter(
                                    x=[pivot_table.columns[x_idx]], y=[pivot_table.index[y_idx]],
                                    mode='markers+text',
                                    marker=dict(size=12, color='red', symbol='circle-open', line=dict(width=3)),
                                    text=[f'<b>{highlight_text_prefix} {int(max_value)}{highlight_text_suffix}</b>'],
                                    textposition='top right',
                                    textfont=dict(color='red', size=12, family="Arial, sans-serif"),
                                    hoverinfo='none'
                                ))
            except Exception as e:
                 st.warning(f"⚠️ 최대값 하이라이트 중 오류 발생: {e}")

        # --- 레이아웃 업데이트 (Spikelines 포함) ---
        fig.update_layout(
            title={
                'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
                'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}
            },
            xaxis=dict(
                title='시간대', fixedrange=True, tickangle=0,
                showspikes=True, spikemode='across', spikesnap='data',
                spikethickness=1, spikecolor='grey'
            ),
            yaxis=dict(
                title=y_axis_title, fixedrange=True,
                showspikes=True, spikemode='across', spikesnap='data',
                spikethickness=1, spikecolor='grey'
            ),
            plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
            margin=dict(l=100, r=50, t=100, b=80), height=graph_height,
            hovermode='closest', # Spikeline과 함께 사용
            coloraxis_colorbar=dict(
                title='운영 대수' if analysis_type == '운영 대수' else '운영 횟수',
            )
        )

        # Y축 정렬 및 타입 설정 (이전과 동일)
        if analysis_type == '운영 대수':
             fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted(pivot_table.index.astype(str)))
        else:
             fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted(pivot_table.index.astype(str)))


        # Streamlit에 그래프 표시
        st.plotly_chart(fig, use_container_width=True)

        # --- 요약 정보 표시 (이전과 동일) ---
        st.markdown("---")
        st.subheader("📊 요약 정보")
        if summary:
            if analysis_type == '운영 대수':
                summary_cols = st.columns(4)
                with summary_cols[0]: st.metric(label="총 운영된 차량 수", value=f"{summary.get('total_units', 'N/A')} 대")
                with summary_cols[1]: st.metric(label="일 평균 운영 대수", value=f"{summary.get('avg_units', 'N/A')} 대", delta=f"{summary.get('avg_units_ratio', 0):.1f}%", delta_color="off")
                with summary_cols[2]: st.metric(label=f"최소 운영 ({summary.get('min_units_day', 'N/A')})", value=f"{summary.get('min_units', 'N/A')} 대", delta=f"{summary.get('min_units_ratio', 0):.1f}%", delta_color="inverse")
                with summary_cols[3]: st.metric(label=f"최대 운영 ({summary.get('max_units_day', 'N/A')})", value=f"{summary.get('max_units', 'N/A')} 대", delta=f"{summary.get('max_units_ratio', 0):.1f}%", delta_color="normal")
            else:
                st.markdown("##### 🔢 운영 횟수 요약 (차량별)")
                count_cols = st.columns(4)
                with count_cols[0]: st.metric(label="전체 운영 횟수", value=f"{summary.get('total_counts', 'N/A')} 회")
                with count_cols[1]: st.metric(label="차량 평균 운영 횟수", value=f"{summary.get('avg_counts', 'N/A')} 회", delta=f"{summary.get('avg_counts_ratio', 0):.1f}%", delta_color="off")
                with count_cols[2]: st.metric(label=f"최소 운영 ({summary.get('min_counts_unit', 'N/A')})", value=f"{summary.get('min_counts', 'N/A')} 회", delta=f"{summary.get('min_counts_ratio', 0):.1f}%", delta_color="inverse")
                with count_cols[3]: st.metric(label=f"최대 운영 ({summary.get('max_counts_unit', 'N/A')})", value=f"{summary.get('max_counts', 'N/A')} 회", delta=f"{summary.get('max_counts_ratio', 0):.1f}%", delta_color="normal")
                st.markdown("---")
                st.markdown("##### ⏱️ 운영 시간 요약 (차량별)")
                time_cols = st.columns(4)
                with time_cols[0]: st.metric(label="전체 운영 시간", value=f"{summary.get('total_time', 'N/A')}")
                with time_cols[1]: st.metric(label="차량 평균 운영 시간", value=f"{summary.get('avg_time', 'N/A')}", delta=f"{summary.get('avg_time_ratio', 0):.1f}%", delta_color="off")
                with time_cols[2]: st.metric(label=f"최소 운영 ({summary.get('min_time_unit', 'N/A')})", value=f"{summary.get('min_time', 'N/A')}", delta=f"{summary.get('min_time_ratio', 0):.1f}%", delta_color="inverse")
                with time_cols[3]: st.metric(label=f"최대 운영 ({summary.get('max_time_unit', 'N/A')})", value=f"{summary.get('max_time', 'N/A')}", delta=f"{summary.get('max_time_ratio', 0):.1f}%", delta_color="normal")
        else:
             st.info("요약 정보를 표시할 데이터가 없습니다.")

    elif uploaded_file is not None:
        pass

elif uploaded_file is None:
    st.info("👈 사이드바에서 CSV 파일을 업로드하고 옵션을 선택하면 분석 결과를 볼 수 있습니다.")

else:
    if 'df' not in locals() or df is None:
         st.warning("파일을 처리하는 중 오류가 발생했습니다. 사이드바에서 오류 메시지를 확인하거나 파일을 다시 업로드해주세요.")
