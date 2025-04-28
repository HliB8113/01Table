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
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"파일을 읽는 중 오류 발생: {e}")
            st.stop() # 오류 발생 시 앱 실행 중지

        # --- '운전자', '공정' 열 관련 코드 제거 ---
        # 혹시 모를 경우를 대비해 해당 열이 존재하면 삭제 (방어 코드)
        if '공정' in df.columns:
            df = df.drop(columns=['공정'])
            st.info("'공정' 열이 파일에 존재하여 제거했습니다.") # 사용자에게 알림
        if '운전자' in df.columns:
            df = df.drop(columns=['운전자'])
            st.info("'운전자' 열이 파일에 존재하여 제거했습니다.") # 사용자에게 알림
        # -----------------------------------------

        # 필수 열 존재 여부 확인
        required_columns = ['시간대', '시작 날짜', '부서', '차대 분류', '작업 장소', '차대 코드', '운영 시간(초)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"필수 열이 누락되었습니다: {', '.join(missing_columns)}")
            st.stop() # 필수 열 없으면 앱 실행 중지

        try:
            # 시간대를 시간 형식으로 변환
            df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

            # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
            df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
            df['월'] = df['시작 날짜'].dt.month

            # 날짜 변환 실패 확인
            if df['시간대'].isnull().any() or df['시작 날짜'].isnull().any():
                 st.warning("시간 또는 날짜 형식 변환에 실패한 데이터가 있습니다. 해당 데이터는 분석에서 제외될 수 있습니다.")
                 # NaT 값 처리 (예: 해당 행 제거)
                 df.dropna(subset=['시간대', '시작 날짜'], inplace=True)


            # 12월 데이터 제외
            excluded_month = 12
            df = df[df['월'] != excluded_month]

            # 데이터가 비어 있는지 확인
            if df.empty:
                st.warning("처리할 데이터가 없습니다. (12월 제외 후)")
                st.stop()


            # 드롭다운 메뉴 설정
            analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
            selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().astype(int).tolist())) # 월을 정수로 변환 후 정렬
            selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
            # selected_process = st.selectbox('공정 선택:', ['전체'] + sorted(df['공정'].dropna().unique().tolist())) # <-- '공정' 드롭다운 완전 삭제
            selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
            selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
            graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

        except KeyError as e:
            st.error(f"데이터 처리 중 오류 발생: '{e}' 열을 찾을 수 없습니다. CSV 파일의 열 이름을 확인해주세요.")
            st.stop()
        except Exception as e:
            st.error(f"데이터 처리 중 예기치 않은 오류 발생: {e}")
            st.stop()


# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"

# 메인 페이지 설정
# 파일이 성공적으로 업로드되고 df가 생성되었는지 확인
if uploaded_file is not None and 'df' in locals() and not df.empty:
    # --- generate_pivot 함수에서 'process' 관련 부분 제거 ---
    # def generate_pivot(month, department, process, forklift_class, workplace): <-- process 매개변수 제거
    def generate_pivot(month, department, forklift_class, workplace):
        filtered_df = df.copy()
        if month != '전체':
            filtered_df = filtered_df[filtered_df['월'] == month]
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        # if process != '전체': <-- process 필터링 로직 제거
        #     filtered_df = filtered_df[filtered_df['공정'] == process]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체':
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        # 필터링 후 데이터가 비었는지 확인
        if filtered_df.empty:
             # st.warning("선택한 조건에 해당하는 데이터가 없습니다.") # 여기서 경고보다는 아래에서 처리
             # 빈 데이터프레임과 기본 요약 정보 반환
             empty_summary = {}
             if analysis_type == '운영 대수':
                 empty_summary = {'total_units': 0, 'min_units': 0, 'min_units_day': 'N/A', 'min_units_ratio': 0,
                                 'max_units': 0, 'max_units_day': 'N/A', 'max_units_ratio': 0, 'avg_units': 0, 'avg_units_ratio': 0}
                 index_name = '시작 날짜'
                 title = '지게차 일자별 운영 대수'
             else: # '운영 횟수'
                 empty_summary = {'total_counts': 0, 'min_counts': 0, 'min_counts_unit': 'N/A', 'min_counts_ratio': 0,
                                 'max_counts': 0, 'max_counts_unit': 'N/A', 'max_counts_ratio': 0, 'avg_counts': 0, 'avg_counts_ratio': 0,
                                 'total_time': '00:00:00', 'min_time': '00:00:00', 'min_time_unit': 'N/A', 'min_time_ratio': 0,
                                 'max_time': '00:00:00', 'max_time_unit': 'N/A', 'max_time_ratio': 0, 'avg_time': '00:00:00', 'avg_time_ratio': 0}
                 index_name = '차대 코드'
                 title = '지게차 시간대별 운영 횟수'
             return pd.DataFrame(), title, index_name, empty_summary


        summary = {} # summary 초기화
        if analysis_type == '운영 대수':
            try:
                filtered_df['시작 날짜'] = filtered_df['시작 날짜'].dt.strftime('%m-%d')
                index_name = '시작 날짜'
                value_name = '차대 코드'
                agg_func = 'nunique'
                title = '지게차 일자별 운영 대수'

                # 월 전체 운영 대수 계산
                total_operating_units = filtered_df[value_name].nunique()

                # 월 최소 및 최대 운영 대수 계산
                daily_counts = filtered_df.groupby('시작 날짜')[value_name].nunique()
                min_operating_units = daily_counts.min() if not daily_counts.empty else 0
                max_operating_units = daily_counts.max() if not daily_counts.empty else 0
                min_operating_day = daily_counts.idxmin() if not daily_counts.empty else 'N/A'
                max_operating_day = daily_counts.idxmax() if not daily_counts.empty else 'N/A'
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
            except Exception as e:
                 st.error(f"'운영 대수' 분석 중 오류 발생: {e}")
                 # 오류 발생 시 빈 결과 반환
                 return pd.DataFrame(), '오류 발생', '시작 날짜', {'total_units': 0, 'min_units': 0, 'min_units_day': 'N/A', 'min_units_ratio': 0,
                                                        'max_units': 0, 'max_units_day': 'N/A', 'max_units_ratio': 0, 'avg_units': 0, 'avg_units_ratio': 0}

        else: # analysis_type == '운영 횟수'
            try:
                index_name = '차대 코드'
                value_name = '시작 날짜' # 운영 횟수는 시작 날짜를 count
                agg_func = 'count'
                title = '지게차 시간대별 운영 횟수'

                # 월 최소 및 최대 운영 횟수 계산
                unit_counts = filtered_df.groupby('차대 코드')[value_name].count()
                min_operating_counts = unit_counts.min() if not unit_counts.empty else 0
                max_operating_counts = unit_counts.max() if not unit_counts.empty else 0
                min_operating_unit = unit_counts.idxmin() if not unit_counts.empty else 'N/A'
                max_operating_unit = unit_counts.idxmax() if not unit_counts.empty else 'N/A'
                avg_operating_counts = round(unit_counts.mean()) if not unit_counts.empty else 0

                # 전체 운영 횟수 계산
                total_operating_counts = unit_counts.sum()

                # 비율 계산
                min_operating_counts_ratio = (min_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0
                max_operating_counts_ratio = (max_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0
                avg_operating_counts_ratio = (avg_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0

                # 운영 시간 계산
                # '운영 시간(초)' 열이 숫자가 아닐 수 있으므로 errors='coerce' 사용
                filtered_df['운영 시간(초)'] = pd.to_numeric(filtered_df['운영 시간(초)'], errors='coerce').fillna(0).astype(int)
                operating_times = filtered_df.groupby('차대 코드')['운영 시간(초)'].sum()
                min_operating_time = operating_times.min() if not operating_times.empty else 0
                max_operating_time = operating_times.max() if not operating_times.empty else 0
                min_time_unit = operating_times.idxmin() if not operating_times.empty else 'N/A'
                max_time_unit = operating_times.idxmax() if not operating_times.empty else 'N/A'
                avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0

                # 전체 운영 시간 계산
                total_operating_time = operating_times.sum()

                # 비율 계산
                min_operating_time_ratio = (min_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
                max_operating_time_ratio = (max_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
                avg_operating_time_ratio = (avg_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0


                def format_time(seconds):
                    if not isinstance(seconds, (int, float)):
                        seconds = 0
                    seconds = int(seconds)
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
            except Exception as e:
                st.error(f"'운영 횟수' 분석 중 오류 발생: {e}")
                # 오류 발생 시 빈 결과 반환
                return pd.DataFrame(), '오류 발생', '차대 코드', {'total_counts': 0, 'min_counts': 0, 'min_counts_unit': 'N/A', 'min_counts_ratio': 0,
                                                      'max_counts': 0, 'max_counts_unit': 'N/A', 'max_counts_ratio': 0, 'avg_counts': 0, 'avg_counts_ratio': 0,
                                                      'total_time': '00:00:00', 'min_time': '00:00:00', 'min_time_unit': 'N/A', 'min_time_ratio': 0,
                                                      'max_time': '00:00:00', 'max_time_unit': 'N/A', 'max_time_ratio': 0, 'avg_time': '00:00:00', 'avg_time_ratio': 0}

        # 피벗 테이블 생성 (try-except 추가)
        try:
             pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
             # 피벗 테이블 인덱스 정렬 (문자열로 변환 후 정렬)
             if analysis_type == '운영 대수' and not pivot_table.empty:
                 pivot_table.index = pd.Categorical(pivot_table.index, categories=sorted(pivot_table.index), ordered=True)
                 pivot_table.sort_index(inplace=True)
             elif analysis_type == '운영 횟수' and not pivot_table.empty:
                 # 차대 코드는 문자열로 간주하고 정렬
                 pivot_table.index = pd.Categorical(pivot_table.index.astype(str), categories=sorted(pivot_table.index.astype(str)), ordered=True)
                 pivot_table.sort_index(inplace=True)

        except KeyError as e:
            st.error(f"피벗 테이블 생성 오류: '{e}' 열을 찾을 수 없습니다. ({value_name=}, {index_name=})")
            return pd.DataFrame(), title, index_name, summary # 빈 테이블 반환
        except Exception as e:
            st.error(f"피벗 테이블 생성 중 예기치 않은 오류 발생: {e}")
            return pd.DataFrame(), title, index_name, summary # 빈 테이블 반환


        return pivot_table, title, index_name, summary

    # --- generate_pivot 함수 호출 시 selected_process 인자 제거 ---
    # pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace)
    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_forklift_class, selected_workplace)


    # 피벗 테이블이 비어있는지 확인 후 그래프 생성 및 요약 정보 표시
    if not pivot_table.empty:
        try: # 그래프 생성 및 요약 표시 전체를 try-except로 감싸기
            # Heatmap 생성
            fig = make_subplots(rows=1, cols=1)
            z_values = pivot_table.values.astype(float) # 시각화를 위해 float으로 변환

            tooltip_texts = [[f'운영 횟수: {int(val)}회' if analysis_type == '운영 횟수' else f'운영 대수: {int(val)}대' for val in row] for row in z_values]
            heatmap = go.Heatmap(
                z=z_values,
                x=pivot_table.columns,
                y=pivot_table.index.astype(str), # y축 값을 문자열로 변환하여 오류 방지
                colorscale=[[0, 'white'], [1, 'purple']],
                hoverinfo='text',
                text=tooltip_texts,
                zmin=0,
                zmax=z_values.max() if z_values.size > 0 else 0
            )
            fig.add_trace(heatmap)

            # 최댓값 하이라이트 추가
            if z_values.size > 0: # 데이터가 있을 때만 최댓값 계산
                max_value = z_values.max()
                if max_value > 0 and pd.notna(max_value):
                    max_indices = list(zip(*[(i, j) for i, row in enumerate(z_values) for j, val in enumerate(row) if val == max_value]))
                    if max_indices:
                        max_y_indices, max_x_indices = max_indices
                        for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                            fig.add_trace(go.Scatter(
                                x=[pivot_table.columns[x_idx]],
                                y=[str(pivot_table.index[y_idx])], # y값도 문자열로 변환
                                mode='markers+text',
                                marker=dict(size=12, color='yellow', symbol='circle'),
                                text=[f'{"동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"} {int(max_value)} {"대" if analysis_type == "운영 대수" else "회"}'],
                                textposition='top center',
                                textfont=dict(color='black', size=14)
                            ))

            # Y축 레이블 정렬을 위해 categoryorder 사용 (피벗 테이블 생성 시 정렬했으므로 여기서는 제거해도 무방)
            fig.update_layout(
                title={
                    'text': title,
                    'x': 0.4,
                    'font': {'size': 25}
                },
                xaxis=dict(title='시간대', fixedrange=True),
                # yaxis=dict(title=index_name, categoryorder='array', categoryarray=sorted(pivot_table.index.astype(str))), # 정렬된 상태이므로 categoryarray 제거 가능
                yaxis=dict(title=index_name, type='category'), # type='category' 유지
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=50, t=150, b=50),
                width=1500,
                height=graph_height,
                coloraxis_colorbar=dict(title='계급 크기')
            )

            # 모든 '시작 날짜'를 세로축에 표시 (월일만 표시) - 운영 대수 분석 시
            # 피벗테이블 생성 시 인덱스 정렬했으므로 아래 코드는 불필요할 수 있음
            # if analysis_type == '운영 대수':
            #     fig.update_yaxes(type='category', tickmode='array', tickvals=sorted(pivot_table.index))


            # Streamlit을 통해 플롯 보여주기
            st.plotly_chart(fig)

            # 요약 정보 표시 (HTML 구조는 유지, 값 존재 확인 강화)
            if analysis_type == '운영 대수':
                summary_text = (
                    f"<b>운영 대수(Day)</b><br>"
                    f"전체: {summary.get('total_units', 'N/A')}대<br>"
                    f"최소: {summary.get('min_units_day', 'N/A')} {summary.get('min_units', 'N/A')}대 "
                    f"({float(summary.get('min_units_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('min_units_ratio')) else ""
                    f"최대: {summary.get('max_units_day', 'N/A')} {summary.get('max_units', 'N/A')}대 "
                    f"({float(summary.get('max_units_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('max_units_ratio')) else ""
                    f"평균: {summary.get('avg_units', 'N/A')}대 "
                    f"({float(summary.get('avg_units_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('avg_units_ratio')) else ""
                )
            else: # analysis_type == '운영 횟수'
                 summary_text = (
                    f"<div style='display: flex; flex-direction: row; align-items: flex-start;'>"
                    f"<div style='margin-right: 50px;'>"
                    f"<b>운영 횟수(Day)</b><br>"
                    f"전체: {summary.get('total_counts', 'N/A')}번<br>"
                    f"최소: {summary.get('min_counts_unit', 'N/A')} {summary.get('min_counts', 'N/A')}번 "
                    f"({float(summary.get('min_counts_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('min_counts_ratio')) else ""
                    f"최대: {summary.get('max_counts_unit', 'N/A')} {summary.get('max_counts', 'N/A')}번 "
                    f"({float(summary.get('max_counts_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('max_counts_ratio')) else ""
                    f"평균: {summary.get('avg_counts', 'N/A')}번 "
                    f"({float(summary.get('avg_counts_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('avg_counts_ratio')) else ""
                    f"</div>"
                    f"<div>"
                    f"<b>운영 시간(Day)</b><br>"
                    f"전체: {summary.get('total_time', 'N/A')}<br>"
                    f"최소: {summary.get('min_time_unit', 'N/A')} {summary.get('min_time', 'N/A')} "
                    f"({float(summary.get('min_time_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('min_time_ratio')) else ""
                    f"최대: {summary.get('max_time_unit', 'N/A')} {summary.get('max_time', 'N/A')} "
                    f"({float(summary.get('max_time_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('max_time_ratio')) else ""
                    f"평균: {summary.get('avg_time', 'N/A')} "
                    f"({float(summary.get('avg_time_ratio', 0)):.2f}%)<br>" if pd.notna(summary.get('avg_time_ratio')) else ""
                    f"</div>"
                    f"</div>"
                )

            # 요약 정보를 히트맵 아래로 표시
            st.markdown(summary_text, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"그래프 또는 요약 정보 표시 중 오류 발생: {e}")

    # 피벗 테이블이 비어있을 경우 사용자에게 메시지 표시
    elif uploaded_file is not None and 'df' in locals(): # df가 존재하지만 필터링 결과가 빈 경우
        st.warning("선택하신 조건에 해당하는 데이터가 없습니다. 다른 조건을 선택해보세요.")

# 파일 업로드가 안 된 초기 상태 메시지 (선택 사항)
elif uploaded_file is None:
    st.info("분석할 CSV 파일을 사이드바에서 업로드해주세요.")
