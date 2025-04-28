import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import traceback # 상세 오류 출력을 위해 추가

# Streamlit 페이지 설정
st.set_page_config(page_title='지게차 데이터 분석 대시보드', layout='wide', initial_sidebar_state='expanded')

st.title('지게차 운영 데이터 분석')

# --- Streamlit 사이드바 설정 ---
with st.sidebar:
    st.header("데이터 업로드 및 설정")
    # 파일 업로드 위젯: key 추가하여 상태 유지 개선
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"], key="file_uploader")

    # df 변수 초기화 (파일 업로드 안 됐을 때 오류 방지)
    df = None
    analysis_options_enabled = False # 파일 로드 성공 시 True로 변경

    if uploaded_file is not None:
        st.write("---")
        st.subheader("데이터 로딩 및 확인")
        try:
            # 파일 포인터 초기화 (재업로드/재실행 시 중요)
            uploaded_file.seek(0)
            # 인코딩 지정하여 파일 읽기 (cp949 시도)
            df = pd.read_csv(uploaded_file, encoding='cp949')
            st.success("파일 로딩 성공 (cp949)")
        except UnicodeDecodeError:
            st.warning("cp949 인코딩 실패. UTF-8으로 다시 시도합니다.")
            try:
                # utf-8로 다시 시도
                uploaded_file.seek(0) # 파일 포인터 다시 초기화
                df = pd.read_csv(uploaded_file, encoding='utf-8')
                st.success("파일 로딩 성공 (UTF-8)")
            except Exception as e:
                st.error(f"UTF-8 파일 읽기 오류: {e}")
                st.exception(e) # 전체 Traceback 출력
                df = None # 오류 시 df 초기화
                st.stop()
        except Exception as e:
            st.error(f"파일 처리 중 예상치 못한 오류 발생: {e}")
            st.exception(e) # 전체 Traceback 출력
            df = None # 오류 시 df 초기화
            st.stop()

        # df가 성공적으로 로드되었는지 확인
        if df is not None and not df.empty:
            st.write("**파일에서 읽어온 열 이름:**") # 열 이름 확인용 출력
            st.write(df.columns.tolist()) # 리스트 형태로 보기 좋게 출력

            # 열 이름 앞뒤 공백 제거
            try:
                original_columns = df.columns.tolist()
                df.columns = df.columns.str.strip()
                new_columns = df.columns.tolist()
                if original_columns != new_columns:
                    st.write("**공백 제거 후 열 이름:**") # 공백 제거 후 열 이름 확인
                    st.write(new_columns)
                else:
                    st.write("(열 이름에 앞뒤 공백 없음)")

            except Exception as e:
                st.warning(f"열 이름 공백 제거 중 오류: {e}")

            # 필수 컬럼 존재 여부 확인 ('공정' 제외)
            required_columns = ['시간대', '시작 날짜', '부서', '차대 분류', '작업 장소', '차대 코드', '운영 시간(초)']
            missing_cols = [col for col in required_columns if col not in df.columns]

            if missing_cols:
                st.error(f"**오류:** 필수 열이 누락되었습니다: **{', '.join(missing_cols)}**")
                st.warning("계속 진행하기 전에 CSV 파일의 열 이름을 확인하고 필요한 열이 모두 있는지 확인해주세요.")
                df = None # 오류 시 df 초기화
                st.stop()
            else:
                st.success("필수 열 확인 완료.")

            # 데이터 타입 변환 (오류 발생 가능성 있는 부분 try-except로 감싸기)
            st.write("---")
            st.subheader("데이터 타입 변환")
            try:
                # 시간대를 시간 형식으로 변환
                df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
                if df['시간대'].isnull().any():
                    st.warning("'시간대' 열에 유효하지 않은 시간 형식이 있습니다. 해당 행은 분석에서 제외될 수 있습니다.")
                    # df.dropna(subset=['시간대'], inplace=True) # 필요시 NaT 제거

                # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
                df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
                if df['시작 날짜'].isnull().any():
                    st.warning("'시작 날짜' 열에 유효하지 않은 날짜 형식이 있습니다. 해당 행은 분석에서 제외될 수 있습니다.")
                    # df.dropna(subset=['시작 날짜'], inplace=True) # 필요시 NaT 제거
                # NaT가 아닌 값에 대해서만 월 추출
                df['월'] = df['시작 날짜'].dropna().dt.month

                # 12월 데이터 제외 (월 컬럼 생성 후 수행)
                # excluded_month = 12
                # df = df[df['월'] != excluded_month]

                # '운영 시간(초)'를 숫자로 변환
                df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0)
                st.success("데이터 타입 변환 완료.")
                analysis_options_enabled = True # 모든 확인 및 변환 성공 시 분석 옵션 활성화

            except KeyError as e:
                st.error(f"데이터 타입 변환 중 오류: '{e}' 열을 찾을 수 없습니다. CSV파일을 확인해주세요.")
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
             df = None # df 초기화
             st.stop()
        # else: df가 None인 경우는 이미 위에서 처리됨


    # --- 분석 옵션 설정 (파일 로딩 성공 시에만 표시) ---
    if analysis_options_enabled and df is not None:
        st.write("---")
        st.subheader("분석 옵션")
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'), key='analysis_type_radio')

        # 월 선택 (NaT 제거 후 unique 값 사용, int로 변환)
        valid_months = df['월'].dropna().unique()
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted([int(m) for m in valid_months]), key='month_select')

        # 부서 선택 (NaT 제거 후 unique 값 사용)
        valid_departments = df['부서'].dropna().unique()
        selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(valid_departments.tolist()), key='dept_select')

        # '공정' 선택 메뉴 제거됨
        # selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))

        # 차대 분류 선택 (NaT 제거 후 unique 값 사용)
        valid_classes = df['차대 분류'].dropna().unique()
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(valid_classes.tolist()), key='class_select')

        # 작업 장소 선택 (NaT 제거 후 unique 값 사용)
        valid_workplaces = df['작업 장소'].dropna().unique()
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(valid_workplaces.tolist()), key='workplace_select')

        graph_height = st.slider('그래프 높이 선택', min_value=400, max_value=1500, value=900, step=50, key='height_slider')
    else:
        # 파일 로드 안됐거나 실패 시 안내 메시지
        if uploaded_file is None:
            st.info("데이터를 분석하려면 먼저 CSV 파일을 업로드하세요.")
        # else: 오류는 위에서 이미 처리됨


# --- 메인 페이지 로직 ---

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"
pivot_table = pd.DataFrame() # 빈 데이터프레임으로 초기화
summary = {}

# df가 성공적으로 로드되고 분석 옵션이 활성화되었을 때만 분석 실행
if df is not None and not df.empty and analysis_options_enabled:

    # --- 피벗 테이블 및 요약 정보 생성 함수 ---
    # 'process' 매개변수 제거
    def generate_pivot(month, department, forklift_class, workplace, analysis_type_local):
        # 원본 데이터프레임 변경 방지 위해 복사본 사용
        filtered_df = df.copy()

        # 데이터 필터링 ('공정' 필터링 제거)
        if month != '전체':
            # '월' 컬럼이 NaN인 경우를 제외하고 필터링
            filtered_df = filtered_df[filtered_df['월'].notna() & (filtered_df['월'] == month)]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        # if process != '전체': # '공정' 필터링 제거
        #     filtered_df = filtered_df[filtered_df['공정'] == process]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체':
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        # 유효한 시간대 데이터만 필터링 (NaT 제거)
        filtered_df.dropna(subset=['시간대'], inplace=True)

        # 필터링 후 데이터가 없는 경우
        if filtered_df.empty:
            st.warning("선택된 조건에 해당하는 데이터가 없습니다.")
            return pd.DataFrame(), "데이터 없음", "데이터 없음", {}

        # --- 분석 로직 시작 ---
        local_pivot_table = pd.DataFrame() # 함수 내 지역 변수 초기화
        local_summary = {}
        local_title = "분석 오류"
        local_index_name = "오류"

        if analysis_type_local == '운영 대수':
            try:
                # 날짜 형식 변환 전에 NaT 확인 및 제거
                filtered_df.dropna(subset=['시작 날짜'], inplace=True)
                if filtered_df.empty:
                     st.warning("유효한 '시작 날짜'가 있는 데이터가 없습니다.")
                     return pd.DataFrame(), "데이터 없음", "날짜 없음", {}

                filtered_df['시작 날짜_str'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
                local_index_name = '시작 날짜'
                value_name = '차대 코드'
                agg_func = 'nunique'
                # 제목 생성 로직 단순화
                title_parts = [f"{m}월" if m != '전체' else None,
                               f"{d}" if d != '전체' else None,
                               f"{fc}" if fc != '전체' else None,
                               f"{wp}" if wp != '전체' else None]
                title_prefix = ' '.join(filter(None, title_parts))
                local_title = f"{title_prefix} 지게차 일자별 운영 대수" if title_prefix else "전체 지게차 일자별 운영 대수"


                # 월 전체 운영 대수 계산
                total_operating_units = filtered_df[value_name].nunique()

                # 일별 운영 대수 계산
                daily_counts = filtered_df.groupby('시작 날짜_str')[value_name].nunique()
                if daily_counts.empty: # 혹시 모를 빈 그룹 결과 처리
                    min_operating_units, max_operating_units, avg_operating_units = 0, 0, 0
                    min_operating_day, max_operating_day = 'N/A', 'N/A'
                else:
                    min_operating_units = daily_counts.min()
                    max_operating_units = daily_counts.max()
                    min_operating_day = daily_counts.idxmin()
                    max_operating_day = daily_counts.idxmax()
                    avg_operating_units = round(daily_counts.mean())

                # 비율 계산
                min_units_ratio = (min_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
                max_units_ratio = (max_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
                avg_units_ratio = (avg_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0

                local_summary = {
                    'total_units': total_operating_units,
                    'min_units': min_operating_units, 'min_units_day': min_operating_day, 'min_units_ratio': min_units_ratio,
                    'max_units': max_operating_units, 'max_units_day': max_operating_day, 'max_units_ratio': max_units_ratio,
                    'avg_units': avg_operating_units, 'avg_units_ratio': avg_units_ratio,
                }
                # 피벗 테이블 생성
                local_pivot_table = filtered_df.pivot_table(index='시작 날짜_str', columns='시간대', values=value_name, aggfunc=agg_func).fillna(0).astype(int)

            except KeyError as e:
                st.error(f"'운영 대수' 분석 중 오류: 필요한 열 '{e}'를 찾을 수 없습니다.")
                return pd.DataFrame(), "오류", "오류", {}
            except Exception as e:
                st.error(f"'운영 대수' 분석 중 예상치 못한 오류: {e}")
                st.exception(e)
                return pd.DataFrame(), "오류", "오류", {}

        elif analysis_type_local == '운영 횟수':
            try:
                local_index_name = '차대 코드'
                value_name_for_count = '시작 날짜' # 횟수 계산 위한 임의의 열 (null이 없어야 함)
                agg_func = 'count'
                 # 제목 생성 로직 단순화 (위와 동일)
                title_parts = [f"{m}월" if m != '전체' else None,
                               f"{d}" if d != '전체' else None,
                               f"{fc}" if fc != '전체' else None,
                               f"{wp}" if wp != '전체' else None]
                title_prefix = ' '.join(filter(None, title_parts))
                local_title = f"{title_prefix} 지게차 차대별 시간대별 운영 횟수" if title_prefix else "전체 지게차 차대별 시간대별 운영 횟수"

                 # null 값 없는지 확인 (만약 있다면 다른 컬럼 사용 고려)
                filtered_df.dropna(subset=[value_name_for_count], inplace=True) # 계산 전 null 행 제거
                if filtered_df.empty:
                     st.warning(f"'{value_name_for_count}' 열에 유효한 데이터가 없습니다.")
                     return pd.DataFrame(), "데이터 없음", "데이터 없음", {}


                # 차대별 운영 횟수 계산
                unit_counts = filtered_df.groupby(local_index_name)[value_name_for_count].count()
                if unit_counts.empty:
                    min_counts, max_counts, avg_counts, total_counts = 0, 0, 0, 0
                    min_unit, max_unit = 'N/A', 'N/A'
                else:
                    min_counts = unit_counts.min()
                    max_counts = unit_counts.max()
                    min_unit = unit_counts.idxmin()
                    max_unit = unit_counts.idxmax()
                    avg_counts = round(unit_counts.mean())
                    total_counts = unit_counts.sum()

                # 횟수 비율 계산
                min_counts_ratio = (min_counts / total_counts) * 100 if total_counts > 0 else 0
                max_counts_ratio = (max_counts / total_counts) * 100 if total_counts > 0 else 0
                avg_counts_ratio = (avg_counts / total_counts) * 100 if total_counts > 0 else 0

                # 운영 시간 계산
                operating_times = filtered_df.groupby(local_index_name)['운영 시간(초)'].sum()
                if operating_times.empty:
                    min_time, max_time, avg_time, total_time = 0, 0, 0, 0
                    min_time_unit, max_time_unit = 'N/A', 'N/A'
                else:
                    min_time = operating_times.min()
                    max_time = operating_times.max()
                    min_time_unit = operating_times.idxmin()
                    max_time_unit = operating_times.idxmax()
                    avg_time = round(operating_times.mean())
                    total_time = operating_times.sum()

                # 시간 비율 계산
                min_time_ratio = (min_time / total_time) * 100 if total_time > 0 else 0
                max_time_ratio = (max_time / total_time) * 100 if total_time > 0 else 0
                avg_time_ratio = (avg_time / total_time) * 100 if total_time > 0 else 0

                def format_time(seconds):
                    seconds = int(seconds) # 정수 변환 보장
                    hours, remainder = divmod(seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    return f"{hours:02}:{minutes:02}:{seconds:02}"

                min_time_fmt = format_time(min_time)
                max_time_fmt = format_time(max_time)
                avg_time_fmt = format_time(avg_time)
                total_time_fmt = format_time(total_time)

                local_summary = {
                    'total_counts': total_counts,
                    'min_counts': min_counts, 'min_counts_unit': min_unit, 'min_counts_ratio': min_counts_ratio,
                    'max_counts': max_counts, 'max_counts_unit': max_unit, 'max_counts_ratio': max_counts_ratio,
                    'avg_counts': avg_counts, 'avg_counts_ratio': avg_counts_ratio,
                    'total_time': total_time_fmt,
                    'min_time': min_time_fmt, 'min_time_unit': min_time_unit, 'min_time_ratio': min_time_ratio,
                    'max_time': max_time_fmt, 'max_time_unit': max_time_unit, 'max_time_ratio': max_time_ratio,
                    'avg_time': avg_time_fmt, 'avg_time_ratio': avg_time_ratio,
                }
                # 피벗 테이블 생성
                local_pivot_table = filtered_df.pivot_table(index=local_index_name, columns='시간대', values=value_name_for_count, aggfunc=agg_func).fillna(0).astype(int)

            except KeyError as e:
                st.error(f"'운영 횟수' 분석 중 오류: 필요한 열 '{e}'를 찾을 수 없습니다.")
                return pd.DataFrame(), "오류", "오류", {}
            except Exception as e:
                st.error(f"'운영 횟수' 분석 중 예상치 못한 오류: {e}")
                st.exception(e)
                return pd.DataFrame(), "오류", "오류", {}
        else:
            st.error(f"알 수 없는 분석 유형: {analysis_type_local}")
            return pd.DataFrame(), "오류", "오류", {}

        # 결과 반환
        return local_pivot_table, local_title, local_index_name, local_summary

    # --- 함수 호출 및 결과 받기 ---
    try:
        # 함수 호출 시 'selected_process' 인자 제거
        pivot_table, title, index_name, summary = generate_pivot(
            selected_month, selected_department, selected_forklift_class, selected_workplace, analysis_type
        )
    except Exception as e:
        st.error("데이터 분석 함수 실행 중 오류 발생")
        st.exception(e)
        # 오류 발생 시 빈 결과로 설정
        pivot_table, title, index_name, summary = pd.DataFrame(), "분석 오류", "오류", {}


    # --- 결과 시각화 (피벗 테이블이 비어 있지 않은 경우) ---
    if not pivot_table.empty:
        st.subheader(f"분석 결과: {title}")
        try:
            fig = make_subplots(rows=1, cols=1)

            # 툴팁 텍스트 생성 (HTML 태그 사용 개선)
            tooltip_texts = []
            for r_idx, row_name in enumerate(pivot_table.index):
                row_texts = []
                for c_idx, col_name in enumerate(pivot_table.columns):
                    val = pivot_table.iloc[r_idx, c_idx]
                    y_label = f"{index_name}: {row_name}"
                    x_label = f"시간대: {col_name}"
                    val_label = f"{'운영 대수' if analysis_type == '운영 대수' else '운영 횟수'}: <b>{int(val)}{'대' if analysis_type == '운영 대수' else '회'}</b>"
                    # <extra></extra>는 Plotly에서 추가 정보 표시 없애는 역할
                    row_texts.append(f"{y_label}<br>{x_label}<br>{val_label}<extra></extra>")
                tooltip_texts.append(row_texts)

            # 히트맵 트레이스 추가
            heatmap = go.Heatmap(
                z=pivot_table.values,
                x=pivot_table.columns,
                y=pivot_table.index,
                colorscale=[[0, '#ffffff'], [0.0001, '#fff7f3'], [0.1, '#fde0dd'], [0.3, '#fcc5c0'], [0.5, '#fa9fb5'], [0.7, '#f768a1'],[0.9,'#c51b8a'], [1, '#7a0177']], # 좀 더 부드러운 컬러 스케일
                hoverinfo='text',
                text=tooltip_texts, # 수정된 툴팁 적용
                zmin=0,
                # zmax=pivot_table.values.max() if pivot_table.values.size > 0 else 1, # 자동 스케일 사용 시 제거 가능
                colorbar=dict(title='운영 강도', tickformat=',d') # 컬러바 제목 및 정수 포맷
            )
            fig.add_trace(heatmap)

            # 최댓값 하이라이트 추가
            if pivot_table.values.size > 0:
                max_value = pivot_table.values.max()
                if max_value > 0:
                    max_indices = [
                        (pivot_table.index[i], pivot_table.columns[j])
                        for i in range(pivot_table.shape[0])
                        for j in range(pivot_table.shape[1])
                        if pivot_table.iloc[i, j] == max_value
                    ]

                    annotations = []
                    for y_val, x_val in max_indices:
                        annotations.append(
                            go.Scatter(
                                x=[x_val], y=[y_val], mode='markers+text',
                                marker=dict(size=12, color='yellow', symbol='circle', line=dict(color='black', width=1)),
                                text=[f"{'최대 동시 투입' if analysis_type == '운영 대수' else '최대 동시간 운영'}: {int(max_value)}{'대' if analysis_type == '운영 대수' else '회'}"],
                                textposition='top center', textfont=dict(color='black', size=12, family="Arial, sans-serif"), # 폰트 크기 조정
                                hoverinfo='none' # 하이라이트 마커는 툴팁 불필요
                            )
                        )
                    for trace in annotations:
                        fig.add_trace(trace)

            # 레이아웃 설정
            fig.update_layout(
                # title 제거 (st.subheader 사용)
                xaxis=dict(title='시간대', fixedrange=True, tickangle=0, type='category'), # 시간대 순서 보장 위해 category 타입 사용
                yaxis=dict(title=index_name, fixedrange=True, autorange=True), # autorange=True로 설정하여 모든 y축 값 보이도록
                plot_bgcolor='white', paper_bgcolor='white',
                margin=dict(l=100, r=50, t=50, b=80), # 상단 여백 줄임
                height=graph_height,
                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial, sans-serif") # 툴팁 스타일
            )

            # y축 정렬 및 타입 설정
            if analysis_type == '운영 대수':
                 # 날짜 문자열('mm-dd') 정렬
                try:
                    # 월-일 순서로 정렬되도록 키 함수 사용
                    sorted_dates = sorted(pivot_table.index, key=lambda d: tuple(map(int, d.split('-'))))
                    fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_dates)
                except Exception as e:
                    st.warning(f"Y축 날짜 정렬 중 오류 발생: {e}. 기본 순서로 표시합니다.")
                    fig.update_yaxes(type='category') # 오류 시 기본 카테고리 순서
            else: # 운영 횟수
                # 운영 횟수 합계 기준 내림차순 정렬
                try:
                    sorted_units = pivot_table.sum(axis=1).sort_values(ascending=False).index.tolist()
                    fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_units)
                except Exception as e:
                    st.warning(f"Y축 차대 코드 정렬 중 오류: {e}. 기본 순서로 표시합니다.")
                    fig.update_yaxes(type='category') # 오류 시 기본 카테고리 순서

            # --- Streamlit으로 결과 표시 ---
            st.plotly_chart(fig, use_container_width=True)

            # --- 요약 정보 표시 ---
            st.subheader("요약 정보")
            if summary: # summary 딕셔너리가 비어있지 않으면
                # 선택된 필터 정보 추가
                filter_info = []
                if selected_month != '전체': filter_info.append(f"{selected_month}월")
                if selected_department != '전체': filter_info.append(selected_department)
                if selected_forklift_class != '전체': filter_info.append(selected_forklift_class)
                if selected_workplace != '전체': filter_info.append(selected_workplace)
                filter_subtitle = f" ({' '.join(filter_info)})" if filter_info else ""

                if analysis_type == '운영 대수':
                    summary_html = f"""
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
                        <h4 style="margin-top:0; color: #333;">일별 운영 대수 요약{filter_subtitle}</h4>
                        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;">
                            <div style="text-align: center;"><b>총 운영 대수 (월):</b><br>{summary.get('total_units', 'N/A')}대</div>
                            <div style="text-align: center;"><b>최소 운영일 ({summary.get('min_units_day', 'N/A')}):</b><br>{summary.get('min_units', 'N/A')}대 ({summary.get('min_units_ratio', 0):.1f}%)</div>
                            <div style="text-align: center;"><b>최대 운영일 ({summary.get('max_units_day', 'N/A')}):</b><br>{summary.get('max_units', 'N/A')}대 ({summary.get('max_units_ratio', 0):.1f}%)</div>
                            <div style="text-align: center;"><b>일 평균 운영 대수:</b><br>{summary.get('avg_units', 'N/A')}대 ({summary.get('avg_units_ratio', 0):.1f}%)</div>
                        </div>
                    </div>
                    """
                elif analysis_type == '운영 횟수':
                    summary_html = f"""
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
                        <h4 style="margin-top:0; color: #333;">차대별 운영 요약{filter_subtitle}</h4>
                        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;">
                            <div style="border-right: 1px solid #eee; padding-right: 15px; margin-right: 15px; margin-bottom: 10px;">
                                <h5 style="margin-bottom: 5px;">운영 횟수</h5>
                                총: {summary.get('total_counts', 'N/A')}회<br>
                                최소: {summary.get('min_counts_unit', 'N/A')} ({summary.get('min_counts', 'N/A')}회, {summary.get('min_counts_ratio', 0):.1f}%)<br>
                                최대: {summary.get('max_counts_unit', 'N/A')} ({summary.get('max_counts', 'N/A')}회, {summary.get('max_counts_ratio', 0):.1f}%)<br>
                                평균: {summary.get('avg_counts', 'N/A')}회 ({summary.get('avg_counts_ratio', 0):.1f}%)
                            </div>
                            <div>
                                <h5 style="margin-bottom: 5px;">운영 시간</h5>
                                총: {summary.get('total_time', 'N/A')}<br>
                                최소: {summary.get('min_time_unit', 'N/A')} ({summary.get('min_time', 'N/A')}, {summary.get('min_time_ratio', 0):.1f}%)<br>
                                최대: {summary.get('max_time_unit', 'N/A')} ({summary.get('max_time', 'N/A')}, {summary.get('max_time_ratio', 0):.1f}%)<br>
                                평균: {summary.get('avg_time', 'N/A')} ({summary.get('avg_time_ratio', 0):.1f}%)
                            </div>
                        </div>
                    </div>
                    """
                else:
                    summary_html = "<p>요약 정보를 표시할 수 없습니다.</p>"

                st.markdown(summary_html, unsafe_allow_html=True)
            else:
                # 피벗 테이블은 있지만 요약 정보가 없는 경우 (generate_pivot 내부 오류 등)
                 if title != "분석 오류" and title != "데이터 없음":
                     st.info("요약 정보를 생성할 수 없습니다.")

        except Exception as e:
            st.error("결과 시각화 중 오류가 발생했습니다.")
            st.exception(e)

    # 피벗 테이블이 비어있는 경우 (generate_pivot 함수에서 경고 후 빈 df 반환 시)
    elif df is not None and not df.empty and analysis_options_enabled: # df는 로드됐지만 결과가 없는 경우
         if title != "분석 오류" and title != "분석 대기 중...": # generate_pivot 함수가 정상 실행됐으나 데이터가 없는 경우
             # 경고 메시지는 generate_pivot 함수에서 이미 표시되었으므로 여기서는 추가 메시지 없음
             pass
         # else: 오류 메시지는 generate_pivot 함수 내에서 이미 표시됨

# 초기 상태 또는 파일 미업로드 시 안내
elif not analysis_options_enabled and uploaded_file is None:
    st.info("시작하려면 사이드바에서 CSV 파일을 업로드하세요.")
