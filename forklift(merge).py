import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import traceback # 상세 오류 출력을 위해 추가
import io # df.info() 출력을 위해 추가

# Streamlit 페이지 설정
st.set_page_config(page_title='지게차 데이터 분석 대시보드', layout='wide', initial_sidebar_state='expanded')

st.title('지게차 운영 데이터 분석')

# --- Streamlit 사이드바 설정 ---
with st.sidebar:
    st.header("데이터 업로드 및 설정")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"], key="file_uploader")

    df = None
    analysis_options_enabled = False

    if uploaded_file is not None:
        st.write("---")
        st.subheader("데이터 로딩 시도")
        read_success = False
        error_message = None
        loaded_encoding = None # 성공한 인코딩 저장

        # 시도 1: cp949 인코딩
        if not read_success:
            try:
                st.write("1. cp949 인코딩으로 읽기 시도...")
                uploaded_file.seek(0)
                # 헤더만 먼저 읽어서 확인 (디버깅용)
                # header_test_cp949 = pd.read_csv(uploaded_file, encoding='cp949', nrows=0).columns.tolist()
                # st.write(f"   - cp949 헤더 인식 시도...") # 헤더 읽기 자체에서 오류날 수 있어 주석 처리
                uploaded_file.seek(0)
                # 전체 파일 읽기 (구분자 명시, 오류 라인 경고 추가)
                df = pd.read_csv(uploaded_file, encoding='cp949', sep=',', on_bad_lines='warn')
                st.success("   - cp949 인코딩으로 파일 로딩 성공!")
                read_success = True
                loaded_encoding = 'cp949'
            except UnicodeDecodeError:
                st.warning("   - cp949 인코딩 실패. 다음 인코딩으로 시도합니다.")
                error_message = "cp949 인코딩 실패"
            except KeyError as e:
                st.error(f"   - cp949 읽기 중 KeyError 발생: Pandas가 열 `'{e}'`을(를) 찾는 데 실패했습니다.")
                st.error("   - CSV 파일의 헤더(첫 줄)나 구조를 확인해보세요.")
                error_message = f"cp949 읽기 중 KeyError: {e}" # 오류 메시지 저장
                # 여기서 st.exception(e) 제거 (아래에서 통합 처리)
            except Exception as e:
                st.error(f"   - cp949 읽기 중 예상치 못한 오류 발생:")
                error_message = f"cp949 읽기 중 오류: {e}" # 오류 메시지 저장
                # 여기서 st.exception(e) 제거 (아래에서 통합 처리)

        # 시도 2: utf-8 인코딩 (cp949 실패 시)
        if not read_success:
            try:
                st.write("2. utf-8 인코딩으로 읽기 시도...")
                uploaded_file.seek(0)
                 # 헤더만 먼저 읽어서 확인 (디버깅용)
                # header_test_utf8 = pd.read_csv(uploaded_file, encoding='utf-8', nrows=0).columns.tolist()
                # st.write(f"   - utf-8 헤더 인식 시도...") # 헤더 읽기 자체에서 오류날 수 있어 주석 처리
                uploaded_file.seek(0)
                # 전체 파일 읽기 (구분자 명시, 오류 라인 경고 추가)
                df = pd.read_csv(uploaded_file, encoding='utf-8', sep=',', on_bad_lines='warn')
                st.success("   - utf-8 인코딩으로 파일 로딩 성공!")
                read_success = True
                loaded_encoding = 'utf-8'
            except KeyError as e:
                 st.error(f"   - utf-8 읽기 중 KeyError 발생: Pandas가 열 `'{e}'`을(를) 찾는 데 실패했습니다.")
                 st.error("   - CSV 파일의 헤더(첫 줄)나 구조를 확인해보세요.")
                 error_message = f"utf-8 읽기 중 KeyError: {e}" # 오류 메시지 저장
                 # 여기서 st.exception(e) 제거 (아래에서 통합 처리)
            except Exception as e:
                st.error(f"   - utf-8 읽기 중 예상치 못한 오류 발생:")
                error_message = f"utf-8 읽기 중 오류: {e}" # 오류 메시지 저장
                # 여기서 st.exception(e) 제거 (아래에서 통합 처리)

        # 최종 결과 처리
        if not read_success:
            st.error("모든 인코딩으로 파일 읽기에 실패했습니다.")
            if error_message:
                 st.error(f"마지막 오류: {error_message}")
            # 실패 시에도 상세 오류 로그 출력 시도 (가능하다면)
            if 'e' in locals() and isinstance(e, Exception):
                 st.exception(e)
            df = None # 실패 시 df 초기화
            st.stop()

        # --- 데이터프레임 로드 성공 후 상세 디버깅 ---
        if df is not None and not df.empty:
            st.write("---")
            st.subheader("로드된 데이터 상세 확인 (Debug)")

            # 1. Print df.info() output
            st.info("DataFrame Info (df.info()):")
            buffer = io.StringIO()
            try:
                df.info(buf=buffer)
                s = buffer.getvalue()
                st.text(s)
            except Exception as info_e:
                 st.warning(f"df.info() 실행 중 오류: {info_e}")


            # 2. Print df.head()
            st.info("DataFrame Head (df.head()):")
            try:
                st.dataframe(df.head())
            except Exception as head_e:
                st.warning(f"df.head() 표시 중 오류: {head_e}")


            # 3. Explicitly check for the column *before* trying to use it
            st.info("열 이름 존재 확인:")
            column_to_check = '시작 날짜'
            try:
                df_columns_list = df.columns.tolist() # 현재 열 목록 가져오기
                column_exists = column_to_check in df_columns_list
                st.write(f"`{column_to_check}` 열이 df.columns에 있습니까? : **{column_exists}**")
                # 열 목록 상세 출력 (따옴표 등 확인 용이하게)
                st.write("df.columns 리스트:")
                st.code(f"{df_columns_list}", language=None)
            except Exception as col_check_e:
                st.error(f"열 목록 확인 중 오류: {col_check_e}")
                column_exists = False # 오류 시 없다고 간주


            # If the column doesn't exist, stop before the error occurs
            if not column_exists:
                st.error(f"오류 감지: 코드에서 사용하려는 열 이름 `'{column_to_check}'`이(가) 로드된 데이터프레임의 열 목록에 없습니다!")
                st.error("CSV 파일의 헤더(첫 줄) 철자, 띄어쓰기, 숨겨진 문자 등을 다시 한번 면밀히 확인해주세요.")
                st.stop()

            # --- 데이터 후처리 시작 ---
            st.write("---")
            st.subheader("데이터 후처리 및 확인")
            # 열 이름 앞뒤 공백 제거
            try:
                original_columns = df.columns.tolist()
                df.columns = df.columns.str.strip()
                new_columns = df.columns.tolist()
                if original_columns != new_columns:
                    st.write("**공백 제거 후 열 이름:**")
                    st.code(f"{new_columns}", language=None)
                else:
                    st.write("(열 이름에 앞뒤 공백 없음)")
            except Exception as e:
                st.warning(f"열 이름 공백 제거 중 오류: {e}")

            # 필수 컬럼 존재 여부 확인 ('부서', '공정' 제외, '시작 날짜'는 위에서 이미 확인됨)
            required_columns = ['시간대', '차대 분류', '작업 장소', '차대 코드', '운영 시간(초)'] # '시작 날짜', '부서', '공정' 제외
            missing_cols = [col for col in required_columns if col not in df.columns]

            if missing_cols:
                st.error(f"**오류:** 필수 열이 누락되었습니다: **`{', '.join(missing_cols)}`**")
                st.warning("계속 진행하기 전에 CSV 파일의 열 이름을 확인하고 필요한 열이 모두 있는지 확인해주세요.")
                df = None # 오류 시 df 초기화
                st.stop()
            else:
                st.success("필수 열 확인 완료.")

            # 데이터 타입 변환
            st.write("---")
            st.subheader("데이터 타입 변환")
            try:
                # 이 블록은 위에서 '시작 날짜' 존재 확인 후 실행됨
                df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
                if df['시간대'].isnull().any():
                    st.warning("'시간대' 열에 유효하지 않은 시간 형식이 있습니다.")

                # 시작 날짜 변환 (이미 열 존재 확인됨)
                df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
                if df['시작 날짜'].isnull().any():
                    st.warning("'시작 날짜' 열에 유효하지 않은 날짜 형식이 있습니다.")
                df['월'] = df['시작 날짜'].dropna().dt.month # NaN 제외하고 월 추출

                # '운영 시간(초)' 변환
                df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0)
                st.success("데이터 타입 변환 완료.")
                analysis_options_enabled = True # 모든 확인 및 변환 성공 시

            except KeyError as e:
                # 이 KeyError는 '시간대' 또는 '운영 시간(초)'에서 발생할 수 있음
                st.error(f"데이터 타입 변환 중 오류: 필요한 열 `'{e}'`을(를) 찾을 수 없습니다. CSV 파일을 다시 확인해주세요.")
                df = None
                st.stop()
            except Exception as e:
                st.error(f"데이터 타입 변환 중 오류 발생: {e}")
                st.warning("CSV 파일의 '시간대', '시작 날짜', '운영 시간(초)' 열의 데이터 형식을 확인해주세요.")
                st.exception(e)
                df = None
                st.stop()
        elif df is not None and df.empty:
             st.error("CSV 파일이 비어있습니다.")
             df = None
             st.stop()
        # else: df가 None인 경우는 파일 읽기 단계에서 이미 처리됨

    # --- 분석 옵션 설정 ---
    # (이전 코드와 동일)
    if analysis_options_enabled and df is not None:
        st.write("---")
        st.subheader("분석 옵션")
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'), key='analysis_type_radio')
        if '월' in df.columns:
            valid_months = df['월'].dropna().unique()
            selected_month = st.selectbox('월 선택:', ['전체'] + sorted([int(m) for m in valid_months]), key='month_select')
        else:
            st.warning("'월' 데이터를 생성할 수 없어 월 선택이 비활성화됩니다."); selected_month = '전체'
        valid_classes = df['차대 분류'].dropna().unique()
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(valid_classes.tolist()), key='class_select')
        valid_workplaces = df['작업 장소'].dropna().unique()
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(valid_workplaces.tolist()), key='workplace_select')
        graph_height = st.slider('그래프 높이 선택', min_value=400, max_value=1500, value=900, step=50, key='height_slider')
    else:
        if uploaded_file is None: st.info("데이터를 분석하려면 먼저 CSV 파일을 업로드하세요.")


# --- 메인 페이지 로직 ---
# (이전 코드와 동일 - generate_pivot, 시각화, 요약 정보 표시)
# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"
pivot_table = pd.DataFrame()
summary = {}

if df is not None and not df.empty and analysis_options_enabled:
    # --- generate_pivot 함수 정의 ---
    def generate_pivot(month, forklift_class, workplace, analysis_type_local):
        filtered_df = df.copy()
        # 필터링 ('부서', '공정' 없음)
        if month != '전체':
            if '월' in filtered_df.columns: filtered_df = filtered_df[filtered_df['월'].notna() & (filtered_df['월'] == month)]
            else: st.warning("월별 필터링 불가 ('월' 컬럼 부재).")
        if forklift_class != '전체': filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체': filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        filtered_df.dropna(subset=['시간대'], inplace=True)
        if filtered_df.empty: return pd.DataFrame(), "데이터 없음", "데이터 없음", {}

        local_pivot_table = pd.DataFrame()
        local_summary = {}
        local_title = "분석 오류"
        local_index_name = "오류"

        # --- '운영 대수' 분석 ---
        if analysis_type_local == '운영 대수':
            try:
                filtered_df.dropna(subset=['시작 날짜'], inplace=True)
                if filtered_df.empty: return pd.DataFrame(), "데이터 없음", "날짜 없음", {}
                filtered_df['시작 날짜_str'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
                local_index_name = '시작 날짜'
                value_name = '차대 코드'
                agg_func = 'nunique'
                title_parts = [f"{m}월" if m != '전체' else None, f"{fc}" if fc != '전체' else None, f"{wp}" if wp != '전체' else None] # 부서 제거
                title_prefix = ' '.join(filter(None, title_parts))
                local_title = f"{title_prefix} 지게차 일자별 운영 대수" if title_prefix else "전체 지게차 일자별 운영 대수"

                total_operating_units = filtered_df[value_name].nunique()
                daily_counts = filtered_df.groupby('시작 날짜_str')[value_name].nunique()
                if daily_counts.empty: min_op, max_op, avg_op, min_day, max_day = 0, 0, 0, 'N/A', 'N/A'
                else: min_op, max_op, avg_op, min_day, max_day = daily_counts.min(), daily_counts.max(), round(daily_counts.mean()), daily_counts.idxmin(), daily_counts.idxmax()
                min_ratio, max_ratio, avg_ratio = [(v / total_operating_units * 100) if total_operating_units > 0 else 0 for v in [min_op, max_op, avg_op]]

                local_summary = {'total_units': total_operating_units, 'min_units': min_op, 'min_units_day': min_day, 'min_units_ratio': min_ratio,'max_units': max_op, 'max_units_day': max_day, 'max_units_ratio': max_ratio,'avg_units': avg_op, 'avg_units_ratio': avg_ratio}
                local_pivot_table = filtered_df.pivot_table(index='시작 날짜_str', columns='시간대', values=value_name, aggfunc=agg_func).fillna(0).astype(int)
            except KeyError as e: st.error(f"'운영 대수' 분석 오류: 열 `'{e}'` 없음."); return pd.DataFrame(), "오류", "오류", {}
            except Exception as e: st.error(f"'운영 대수' 분석 중 오류."); st.exception(e); return pd.DataFrame(), "오류", "오류", {}

        # --- '운영 횟수' 분석 ---
        elif analysis_type_local == '운영 횟수':
            try:
                local_index_name = '차대 코드'
                value_name_for_count = '시작 날짜'
                agg_func = 'count'
                title_parts = [f"{m}월" if m != '전체' else None, f"{fc}" if fc != '전체' else None, f"{wp}" if wp != '전체' else None] # 부서 제거
                title_prefix = ' '.join(filter(None, title_parts))
                local_title = f"{title_prefix} 지게차 차대별 시간대별 운영 횟수" if title_prefix else "전체 지게차 차대별 시간대별 운영 횟수"

                filtered_df.dropna(subset=[value_name_for_count], inplace=True)
                if filtered_df.empty: return pd.DataFrame(), "데이터 없음", "데이터 없음", {}

                unit_counts = filtered_df.groupby(local_index_name)[value_name_for_count].count()
                if unit_counts.empty: min_c, max_c, avg_c, total_c, min_u, max_u = 0, 0, 0, 0, 'N/A', 'N/A'
                else: min_c, max_c, avg_c, total_c, min_u, max_u = unit_counts.min(), unit_counts.max(), round(unit_counts.mean()), unit_counts.sum(), unit_counts.idxmin(), unit_counts.idxmax()
                min_c_ratio, max_c_ratio, avg_c_ratio = [(v / total_c * 100) if total_c > 0 else 0 for v in [min_c, max_c, avg_c]]

                op_times = filtered_df.groupby(local_index_name)['운영 시간(초)'].sum()
                if op_times.empty: min_t, max_t, avg_t, total_t, min_tu, max_tu = 0, 0, 0, 0, 'N/A', 'N/A'
                else: min_t, max_t, avg_t, total_t, min_tu, max_tu = op_times.min(), op_times.max(), round(op_times.mean()), op_times.sum(), op_times.idxmin(), op_times.idxmax()
                min_t_ratio, max_t_ratio, avg_t_ratio = [(v / total_t * 100) if total_t > 0 else 0 for v in [min_t, max_t, avg_t]]

                def fmt_time(s): h, r = divmod(int(s), 3600); m, s = divmod(r, 60); return f"{h:02}:{m:02}:{s:02}"
                min_t_fmt, max_t_fmt, avg_t_fmt, total_t_fmt = map(fmt_time, [min_t, max_t, avg_t, total_t])

                local_summary = {'total_counts': total_c, 'min_counts': min_c, 'min_counts_unit': min_u, 'min_counts_ratio': min_c_ratio,'max_counts': max_c, 'max_counts_unit': max_u, 'max_counts_ratio': max_c_ratio,'avg_counts': avg_c, 'avg_counts_ratio': avg_c_ratio,'total_time': total_t_fmt, 'min_time': min_t_fmt, 'min_time_unit': min_tu, 'min_time_ratio': min_t_ratio,'max_time': max_t_fmt, 'max_time_unit': max_tu, 'max_time_ratio': max_t_ratio,'avg_time': avg_t_fmt, 'avg_time_ratio': avg_t_ratio}
                local_pivot_table = filtered_df.pivot_table(index=local_index_name, columns='시간대', values=value_name_for_count, aggfunc=agg_func).fillna(0).astype(int)
            except KeyError as e: st.error(f"'운영 횟수' 분석 오류: 열 `'{e}'` 없음."); return pd.DataFrame(), "오류", "오류", {}
            except Exception as e: st.error(f"'운영 횟수' 분석 중 오류."); st.exception(e); return pd.DataFrame(), "오류", "오류", {}
        else:
            st.error(f"알 수 없는 분석 유형: {analysis_type_local}")
            return pd.DataFrame(), "오류", "오류", {}

        if local_pivot_table.empty: return pd.DataFrame(), "데이터 없음", "데이터 없음", {}
        return local_pivot_table, local_title, local_index_name, local_summary

    # --- 함수 호출 ---
    try:
        pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_forklift_class, selected_workplace, analysis_type) # 부서, 공정 인자 제거됨
    except Exception as e:
        st.error("데이터 분석 함수 실행 중 오류 발생"); st.exception(e)
        pivot_table, title, index_name, summary = pd.DataFrame(), "분석 오류", "오류", {}

    # --- 결과 시각화 ---
    if not pivot_table.empty:
        st.subheader(f"분석 결과: {title}")
        try:
            # (시각화 및 요약 정보 표시는 이전 코드와 동일)
            fig = make_subplots(rows=1, cols=1)
            tooltip_texts = []
            for r_idx, r_name in enumerate(pivot_table.index):
                r_texts = []
                for c_idx, c_name in enumerate(pivot_table.columns):
                    val = pivot_table.iloc[r_idx, c_idx]
                    y_lbl, x_lbl = f"{index_name}: {r_name}", f"시간대: {c_name}"
                    val_lbl = f"{'운영 대수' if analysis_type == '운영 대수' else '운영 횟수'}: <b>{int(val)}{'대' if analysis_type == '운영 대수' else '회'}</b>"
                    r_texts.append(f"{y_lbl}<br>{x_lbl}<br>{val_lbl}<extra></extra>")
                tooltip_texts.append(r_texts)
            fig.add_trace(go.Heatmap(z=pivot_table.values, x=pivot_table.columns, y=pivot_table.index, colorscale=[[0, '#ffffff'], [0.0001, '#fff7f3'], [0.1, '#fde0dd'], [0.3, '#fcc5c0'], [0.5, '#fa9fb5'], [0.7, '#f768a1'],[0.9,'#c51b8a'], [1, '#7a0177']], hoverinfo='text', text=tooltip_texts, zmin=0, colorbar=dict(title='운영 강도', tickformat=',d')))
            if pivot_table.values.size > 0:
                 max_val = pivot_table.values.max()
                 if max_val > 0:
                     max_idxs = [(pivot_table.index[i], pivot_table.columns[j]) for i in range(pivot_table.shape[0]) for j in range(pivot_table.shape[1]) if pivot_table.iloc[i, j] == max_val]
                     for y_v, x_v in max_idxs:
                         fig.add_trace(go.Scatter(x=[x_v], y=[y_v], mode='markers+text', marker=dict(size=12, color='yellow', symbol='circle', line=dict(color='black', width=1)), text=[f"{'최대 동시 투입' if analysis_type == '운영 대수' else '최대 동시간 운영'}: {int(max_val)}{'대' if analysis_type == '운영 대수' else '회'}"], textposition='top center', textfont=dict(color='black', size=12), hoverinfo='none'))
            fig.update_layout(xaxis=dict(title='시간대', fixedrange=True, tickangle=0, type='category'), yaxis=dict(title=index_name, fixedrange=True, autorange=True), plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=100, r=50, t=50, b=80), height=graph_height, hoverlabel=dict(bgcolor="white", font_size=12))
            if analysis_type == '운영 대수':
                 try: sorted_dates = sorted(pivot_table.index, key=lambda d: tuple(map(int, d.split('-')))); fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_dates)
                 except Exception as e: st.warning(f"Y축 날짜 정렬 오류: {e}"); fig.update_yaxes(type='category')
            else:
                 try: sorted_units = pivot_table.sum(axis=1).sort_values(ascending=False).index.tolist(); fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_units)
                 except Exception as e: st.warning(f"Y축 차대 코드 정렬 오류: {e}"); fig.update_yaxes(type='category')
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("요약 정보")
            if summary:
                filter_info = [f"{v}{k}" if k=='월' else f"{v}" for k, v in [('월',selected_month), ('차대',selected_forklift_class), ('장소',selected_workplace)] if v != '전체'] # 부서 제거
                filter_subtitle = f" ({', '.join(filter_info)})" if filter_info else " (전체)"
                if analysis_type == '운영 대수':
                    summary_html = f"""<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;"><h4 style="margin-top:0;">일별 운영 대수 요약{filter_subtitle}</h4><div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;"><div style="text-align: center;"><b>총(월):</b><br>{summary.get('total_units', 'N/A')}대</div><div style="text-align: center;"><b>최소({summary.get('min_units_day', 'N/A')}):</b><br>{summary.get('min_units', 'N/A')}대 ({summary.get('min_units_ratio', 0):.1f}%)</div><div style="text-align: center;"><b>최대({summary.get('max_units_day', 'N/A')}):</b><br>{summary.get('max_units', 'N/A')}대 ({summary.get('max_units_ratio', 0):.1f}%)</div><div style="text-align: center;"><b>평균(일):</b><br>{summary.get('avg_units', 'N/A')}대 ({summary.get('avg_units_ratio', 0):.1f}%)</div></div></div>"""
                elif analysis_type == '운영 횟수':
                    summary_html = f"""<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;"><h4 style="margin-top:0;">차대별 운영 요약{filter_subtitle}</h4><div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;"><div style="border-right: 1px solid #eee; padding-right: 15px; margin-right: 15px; margin-bottom: 10px;"><h5 style="margin-bottom: 5px;">운영 횟수</h5>총: {summary.get('total_counts', 'N/A')}회<br>최소: {summary.get('min_counts_unit', 'N/A')} ({summary.get('min_counts', 'N/A')}회, {summary.get('min_counts_ratio', 0):.1f}%)<br>최대: {summary.get('max_counts_unit', 'N/A')} ({summary.get('max_counts', 'N/A')}회, {summary.get('max_counts_ratio', 0):.1f}%)<br>평균: {summary.get('avg_counts', 'N/A')}회 ({summary.get('avg_counts_ratio', 0):.1f}%)</div><div><h5 style="margin-bottom: 5px;">운영 시간</h5>총: {summary.get('total_time', 'N/A')}<br>최소: {summary.get('min_time_unit', 'N/A')} ({summary.get('min_time', 'N/A')}, {summary.get('min_time_ratio', 0):.1f}%)<br>최대: {summary.get('max_time_unit', 'N/A')} ({summary.get('max_time', 'N/A')}, {summary.get('max_time_ratio', 0):.1f}%)<br>평균: {summary.get('avg_time', 'N/A')} ({summary.get('avg_time_ratio', 0):.1f}%)</div></div></div>"""
                else: summary_html = "<p>요약 정보 없음.</p>"
                st.markdown(summary_html, unsafe_allow_html=True)
            else:
                 if title != "분석 오류" and title != "데이터 없음": st.info("요약 정보 생성 불가.")
        except Exception as e: st.error("결과 시각화 중 오류 발생"); st.exception(e)

    elif df is not None and not df.empty and analysis_options_enabled:
         if title == "데이터 없음" or title == "날짜 없음": st.info("선택된 조건에 맞는 데이터가 없어 그래프를 표시할 수 없습니다.")
         elif title == "분석 오류" or title == "오류": st.error("분석 중 오류가 발생하여 결과를 표시할 수 없습니다. 사이드바의 오류 메시지를 확인하세요.")

elif not analysis_options_enabled and uploaded_file is None:
    st.info("시작하려면 사이드바에서 CSV 파일을 업로드하세요.")
