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
        # 기본 pd.read_csv 사용 (사용자 요청에 따라)
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")
            st.stop() # 오류 발생 시 중단

        # 데이터가 비어 있는지 확인
        if df.empty:
            st.warning("업로드된 파일이 비어있습니다.")
            st.stop()

        # 데이터 타입 변환 (오류 발생 시 더 명확한 메시지 추가)
        try:
            # 시간대를 시간 형식으로 변환
            df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

            # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
            df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
            df['월'] = df['시작 날짜'].dt.month

        except KeyError as e:
            st.error(f"오류: CSV 파일에 필수 열 '{e}'이(가) 없습니다. 파일을 확인해주세요.")
            st.stop()
        except Exception as e:
            st.error(f"데이터 타입 변환 중 오류 발생: {e}")
            st.stop()

        # NaN 값 확인 (경고용)
        if df['시간대'].isnull().any():
            st.warning("'시간대' 열에 유효하지 않은 값이 포함되어 있습니다.")
        if df['시작 날짜'].isnull().any():
            st.warning("'시작 날짜' 열에 유효하지 않은 값이 포함되어 있습니다.")
        if df['월'].isnull().any():
             st.warning("'시작 날짜' 열의 일부 값에서 '월' 정보를 추출하지 못했습니다.")


        # 12월 데이터 제외 (NaN 값 발생 가능성 고려)
        # df = df[df['월'] != 12] # 이렇게 하면 월이 NaN인 행도 제외될 수 있음
        if '월' in df.columns and not df['월'].isnull().all(): # 월 컬럼이 있고 NaN만 있는게 아니라면
            excluded_month = 12
            df = df[df['월'].notna() & (df['월'] != excluded_month)]
            if df.empty:
                st.warning("12월 데이터를 제외하니 남는 데이터가 없습니다.")
                st.stop()
        else:
            st.warning("월 정보를 사용할 수 없어 12월 데이터를 제외하지 못했습니다.")


        # 드롭다운 메뉴 설정 ('부서', '공정' 제거)
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))

        # 월 선택 (NaN 처리 강화)
        valid_months = df['월'].dropna().unique()
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted([int(m) for m in valid_months]))

        # 부서 선택 메뉴 제거
        # selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
        # 공정 선택 메뉴 제거
        # selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist()))

        # 필수 열 존재 확인 후 Selectbox 생성
        try:
            selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
            selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
        except KeyError as e:
             st.error(f"오류: 필터링에 필요한 열 '{e}'이(가) CSV 파일에 없습니다.")
             st.stop()

        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"
pivot_table = pd.DataFrame() # 빈 데이터프레임으로 초기화
summary = {}

# 메인 페이지 설정
# df가 성공적으로 로드되었는지 확인
if uploaded_file is not None and 'df' in locals() and not df.empty:
    # generate_pivot 함수 정의에서 'department', 'process' 매개변수 제거
    def generate_pivot(month, forklift_class, workplace):
        filtered_df = df.copy()
        # 필터링 ('부서', '공정' 제거)
        if month != '전체':
            # NaN 값 제외하고 비교
            filtered_df = filtered_df[filtered_df['월'].notna() & (filtered_df['월'] == month)]
        # if department != '전체': # 부서 필터링 제거
        #     filtered_df = filtered_df[filtered_df['부서'] == department]
        # if process != '전체': # 공정 필터링 제거
        #     filtered_df = filtered_df[filtered_df['공정'] == process]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체':
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        # 필터링 후 데이터가 비었는지 확인
        if filtered_df.empty:
            st.warning("선택된 조건에 해당하는 데이터가 없습니다.")
            # 빈 데이터프레임과 기본값 반환
            return pd.DataFrame(), "데이터 없음", "데이터 없음", {}

        # 전역 변수 수정 방지 위해 로컬 변수 사용
        local_title = title
        local_index_name = index_name
        local_summary = {}

        if analysis_type == '운영 대수':
            try:
                # '시작 날짜' NaT 제거 후 형식 변환
                filtered_df.dropna(subset=['시작 날짜'], inplace=True)
                if filtered_df.empty: return pd.DataFrame(), "데이터 없음", "날짜 없음", {}
                filtered_df['시작 날짜_str'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')

                local_index_name = '시작 날짜'
                value_name = '차대 코드'
                agg_func = 'nunique'
                local_title = '지게차 일자별 운영 대수'

                # 월 전체 운영 대수 계산
                total_operating_units = filtered_df[value_name].nunique()

                # 월 최소 및 최대 운영 대수 계산
                daily_counts = filtered_df.groupby('시작 날짜_str')[value_name].nunique()
                min_operating_units = daily_counts.min() if not daily_counts.empty else 0
                max_operating_units = daily_counts.max() if not daily_counts.empty else 0
                min_operating_day = daily_counts.idxmin() if not daily_counts.empty else '데이터 없음'
                max_operating_day = daily_counts.idxmax() if not daily_counts.empty else '데이터 없음'
                avg_operating_units = round(daily_counts.mean()) if not daily_counts.empty else 0

                # 비율 계산
                min_operating_units_ratio = (min_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
                max_operating_units_ratio = (max_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0
                avg_operating_units_ratio = (avg_operating_units / total_operating_units) * 100 if total_operating_units > 0 else 0


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
                # 피벗 테이블 생성 ('시작 날짜_str' 사용)
                local_pivot_table = filtered_df.pivot_table(index='시작 날짜_str', columns='시간대', values=value_name, aggfunc=agg_func).fillna(0).astype(int)

            except KeyError as e:
                st.error(f"'운영 대수' 분석 오류: 열 '{e}' 없음.")
                return pd.DataFrame(), "오류", "오류", {}
            except Exception as e:
                st.error(f"'운영 대수' 분석 중 오류 발생: {e}")
                return pd.DataFrame(), "오류", "오류", {}

        else: # analysis_type == '운영 횟수'
            try:
                local_index_name = '차대 코드'
                value_name = '시작 날짜' # Count용
                agg_func = 'count'
                local_title = '지게차 차대별 시간대별 운영 횟수' # 제목 수정

                # '시작 날짜' NaT 제거
                filtered_df.dropna(subset=['시작 날짜'], inplace=True)
                if filtered_df.empty: return pd.DataFrame(), "데이터 없음", "날짜 없음", {}


                # 월 최소 및 최대 운영 횟수 계산
                unit_counts = filtered_df.groupby(local_index_name)[value_name].count() # index_name 대신 local_index_name 사용
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
                # '운영 시간(초)' 열 존재 확인
                if '운영 시간(초)' not in filtered_df.columns:
                    st.error("오류: '운영 시간(초)' 열이 없어 운영 시간 분석을 할 수 없습니다.")
                    # 운영 시간 관련 계산 건너뛰고 횟수 데이터만 반환하거나 빈 결과 반환
                    operating_times = pd.Series(dtype='float64') # 빈 시리즈
                    min_operating_time, max_operating_time, avg_operating_time, total_operating_time = 0, 0, 0, 0
                    min_time_unit, max_time_unit = 'N/A', 'N/A'
                    min_operating_time_ratio, max_operating_time_ratio, avg_operating_time_ratio = 0, 0, 0
                    min_operating_time_formatted, max_operating_time_formatted, avg_operating_time_formatted, total_operating_time_formatted = "N/A", "N/A", "N/A", "N/A"
                else:
                    filtered_df['운영 시간(초)'] = pd.to_numeric(filtered_df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)
                    operating_times = filtered_df.groupby(local_index_name)['운영 시간(초)'].sum()
                    min_operating_time = operating_times.min() if not operating_times.empty else 0
                    max_operating_time = operating_times.max() if not operating_times.empty else 0
                    min_time_unit = operating_times.idxmin() if not operating_times.empty else '데이터 없음'
                    max_time_unit = operating_times.idxmax() if not operating_times.empty else '데이터 없음'
                    avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0
                    total_operating_time = operating_times.sum()

                    # 비율 계산
                    min_operating_time_ratio = (min_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
                    max_operating_time_ratio = (max_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
                    avg_operating_time_ratio = (avg_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0

                    def format_time(seconds):
                        seconds = int(seconds) # 정수 변환
                        hours, remainder = divmod(seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        return f"{hours:02}:{minutes:02}:{seconds:02}"

                    min_operating_time_formatted = format_time(min_operating_time)
                    max_operating_time_formatted = format_time(max_operating_time)
                    avg_operating_time_formatted = format_time(avg_operating_time)
                    total_operating_time_formatted = format_time(total_operating_time)

                local_summary = {
                    'total_counts': total_operating_counts,
                    'min_counts': min_operating_counts, 'min_counts_unit': min_operating_unit, 'min_counts_ratio': min_operating_counts_ratio,
                    'max_counts': max_operating_counts, 'max_counts_unit': max_operating_unit, 'max_counts_ratio': max_operating_counts_ratio,
                    'avg_counts': avg_operating_counts, 'avg_counts_ratio': avg_operating_counts_ratio,
                    # 운영 시간 정보 추가 (오류 발생 시 N/A 또는 0)
                    'total_time': total_operating_time_formatted,
                    'min_time': min_operating_time_formatted, 'min_time_unit': min_time_unit, 'min_time_ratio': min_operating_time_ratio,
                    'max_time': max_operating_time_formatted, 'max_time_unit': max_time_unit, 'max_time_ratio': max_operating_time_ratio,
                    'avg_time': avg_operating_time_formatted, 'avg_time_ratio': avg_operating_time_ratio,
                }
                # 피벗 테이블 생성
                local_pivot_table = filtered_df.pivot_table(index=local_index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0).astype(int)

            except KeyError as e:
                st.error(f"'운영 횟수' 분석 오류: 열 '{e}' 없음.")
                return pd.DataFrame(), "오류", "오류", {}
            except Exception as e:
                st.error(f"'운영 횟수' 분석 중 오류 발생: {e}")
                return pd.DataFrame(), "오류", "오류", {}

        # 피벗 테이블이 비었는지 확인 후 반환
        if local_pivot_table.empty:
             st.info("피벗 테이블 생성 결과 데이터가 없습니다.")
             return pd.DataFrame(), "데이터 없음", "데이터 없음", {}

        return local_pivot_table, local_title, local_index_name, local_summary

    # 함수 호출 시 'selected_department', 'selected_process' 인자 제거
    try:
        pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_forklift_class, selected_workplace)
    except Exception as e:
        st.error(f"분석 함수 호출 중 오류: {e}")
        pivot_table, title, index_name, summary = pd.DataFrame(), "분석 오류", "오류", {}


    # 결과 시각화 (피벗 테이블이 비어있지 않을 때)
    if not pivot_table.empty:
        st.subheader(f"분석 결과: {title}") # 동적으로 제목 표시
        try:
            # Heatmap 생성
            fig = make_subplots(rows=1, cols=1)

            # 툴팁 텍스트 개선
            tooltip_texts = []
            for r_idx, row_name in enumerate(pivot_table.index):
                row_texts = []
                for c_idx, col_name in enumerate(pivot_table.columns):
                    val = pivot_table.iloc[r_idx, c_idx]
                    y_label = f"{index_name}: {row_name}"
                    x_label = f"시간대: {col_name}"
                    val_label = f"{'운영 대수' if analysis_type == '운영 대수' else '운영 횟수'}: <b>{int(val)}{'대' if analysis_type == '운영 대수' else '회'}</b>"
                    row_texts.append(f"{y_label}<br>{x_label}<br>{val_label}<extra></extra>")
                tooltip_texts.append(row_texts)

            heatmap = go.Heatmap(
                z=pivot_table.values,
                x=pivot_table.columns,
                y=pivot_table.index,
                colorscale=[[0, 'white'], [0.1, '#fde0dd'], [0.5, '#fa9fb5'],[0.8, '#c51b8a'], [1, '#7a0177']], # 보라색 계열 조정
                hoverinfo='text',
                text=tooltip_texts,
                zmin=0,
                # zmax=pivot_table.values.max() # 자동 스케일링 사용
                colorbar=dict(title='운영 강도')
            )
            fig.add_trace(heatmap)

            # 최댓값 하이라이트 추가
            if pivot_table.values.size > 0: # 배열이 비어있지 않은지 확인
                max_value = pivot_table.values.max()
                if max_value > 0: # 0보다 클 때만 하이라이트
                    # 최댓값 인덱스 찾기 (동일 값 모두 포함)
                    max_indices = [
                        (pivot_table.index[i], pivot_table.columns[j])
                        for i in range(pivot_table.shape[0])
                        for j in range(pivot_table.shape[1])
                        if pivot_table.iloc[i, j] == max_value
                    ]

                    # 하이라이트 추가
                    for y_val, x_val in max_indices:
                        fig.add_trace(go.Scatter(
                            x=[x_val],
                            y=[y_val],
                            mode='markers+text',
                            marker=dict(size=12, color='yellow', symbol='circle', line=dict(color='black',width=1)),
                            text=[f'{"동시 투입(최대):" if analysis_type == "운영 대수" else "동시간 운영(최대):"} {int(max_value)}{"대" if analysis_type == "운영 대수" else "회"}'],
                            textposition='top center',
                            textfont=dict(color='black', size=12), # 폰트 크기 조정
                            hoverinfo='none' # 하이라이트 툴팁 비활성화
                        ))

            # 레이아웃 업데이트
            fig.update_layout(
                # title 제거 (st.subheader 사용)
                xaxis=dict(title='시간대', fixedrange=True, type='category'), # type='category'로 시간 순서 유지
                yaxis=dict(title=index_name, fixedrange=True, autorange=True), # 모든 라벨 보이도록
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=100, r=50, t=50, b=80), # 여백 조정
                # width=1500, # 레이아웃 wide 사용 시 불필요
                height=graph_height,
                hoverlabel=dict(bgcolor="white", font_size=12) # 툴팁 스타일
            )

            # 모든 y축 레이블 보이도록 설정 및 정렬
            if analysis_type == '운영 대수':
                 # 월-일 순서로 정렬
                 try:
                     sorted_dates = sorted(pivot_table.index, key=lambda d: tuple(map(int, d.split('-'))))
                     fig.update_yaxes(type='category', tickmode='array', tickvals=sorted_dates, categoryorder='array', categoryarray=sorted_dates)
                 except: # 정렬 실패 시 기본값
                      fig.update_yaxes(type='category', tickmode='auto')
            else: # 운영 횟수 (차대 코드) - 합계 기준 정렬
                 try:
                     y_order = pivot_table.sum(axis=1).sort_values(ascending=False).index.tolist()
                     fig.update_yaxes(type='category', categoryorder='array', categoryarray=y_order)
                 except: # 정렬 실패 시 기본값
                     fig.update_yaxes(type='category', tickmode='auto')


            # Streamlit을 통해 플롯 보여주기
            st.plotly_chart(fig, use_container_width=True) # 너비 자동 조정

            # 요약 정보 표시 (HTML 포맷 개선)
            st.subheader("요약 정보")
            if summary: # summary 딕셔너리가 비어있지 않을 때
                filter_info = [f"{v}{k}" if k=='월' else f"{v}" for k, v in [('월',selected_month), ('차대',selected_forklift_class), ('장소',selected_workplace)] if v != '전체']
                filter_subtitle = f" ({', '.join(filter_info)})" if filter_info else " (전체)"

                if analysis_type == '운영 대수':
                    summary_text = (
                        f'<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">'
                        f'<h4 style="margin-top:0;">일별 운영 대수 요약{filter_subtitle}</h4>'
                        f'<div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;">'
                        f'<div><b>총(월):</b><br>{summary.get("total_units", "N/A")}대</div>'
                        f'<div><b>최소({summary.get("min_units_day", "N/A")}):</b><br>{summary.get("min_units", "N/A")}대 ({summary.get("min_units_ratio", 0):.1f}%)</div>'
                        f'<div><b>최대({summary.get("max_units_day", "N/A")}):</b><br>{summary.get("max_units", "N/A")}대 ({summary.get("max_units_ratio", 0):.1f}%)</div>'
                        f'<div><b>평균(일):</b><br>{summary.get("avg_units", "N/A")}대 ({summary.get("avg_units_ratio", 0):.1f}%)</div>'
                        f'</div></div>'
                    )
                else: # 운영 횟수
                    summary_text = (
                        f'<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">'
                        f'<h4 style="margin-top:0;">차대별 운영 요약{filter_subtitle}</h4>'
                        f'<div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;">'
                        f'<div style="border-right: 1px solid #eee; padding-right: 15px; margin-right: 15px;">'
                        f'<h5 style="margin-bottom: 5px;">운영 횟수</h5>'
                        f'총: {summary.get("total_counts", "N/A")}회<br>'
                        f'최소: {summary.get("min_counts_unit", "N/A")} ({summary.get("min_counts", "N/A")}회, {summary.get("min_counts_ratio", 0):.1f}%)<br>'
                        f'최대: {summary.get("max_counts_unit", "N/A")} ({summary.get("max_counts", "N/A")}회, {summary.get("max_counts_ratio", 0):.1f}%)<br>'
                        f'평균: {summary.get("avg_counts", "N/A")}회 ({summary.get("avg_counts_ratio", 0):.1f}%)'
                        f'</div><div>'
                        f'<h5 style="margin-bottom: 5px;">운영 시간</h5>'
                        f'총: {summary.get("total_time", "N/A")}<br>'
                        f'최소: {summary.get("min_time_unit", "N/A")} ({summary.get("min_time", "N/A")}, {summary.get("min_time_ratio", 0):.1f}%)<br>'
                        f'최대: {summary.get("max_time_unit", "N/A")} ({summary.get("max_time", "N/A")}, {summary.get("max_time_ratio", 0):.1f}%)<br>'
                        f'평균: {summary.get("avg_time", "N/A")} ({summary.get("avg_time_ratio", 0):.1f}%)'
                        f'</div></div></div>'
                    )

                st.markdown(summary_text, unsafe_allow_html=True)
            else:
                # 요약 정보 생성 실패 시
                if title != "분석 오류" and title != "데이터 없음":
                    st.info("요약 정보를 표시할 수 없습니다.")

        except Exception as e:
             st.error(f"결과 표시 중 오류 발생: {e}")

    # 피벗 테이블 생성 실패 또는 데이터 없는 경우
    elif uploaded_file is not None and 'df' in locals(): # 파일은 업로드 되었으나 결과가 없는 상태
        # 오류 메시지는 generate_pivot 함수에서 이미 표시됨
        if title == "데이터 없음" or title == "날짜 없음":
            st.info("선택된 조건에 맞는 데이터가 없어 그래프를 표시할 수 없습니다.")
        elif title == "분석 오류" or title == "오류":
             st.error("분석 중 오류가 발생하여 결과를 표시할 수 없습니다. 사이드바의 오류 메시지를 확인하세요.")
        # else: # 초기 상태 ("분석 대기 중...") - 아무것도 표시 안 함

# 파일 업로드 안 된 초기 상태
elif uploaded_file is None:
    st.info("데이터를 분석하려면 사이드바에서 CSV 파일을 업로드하세요.")
