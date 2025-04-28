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
            # 인코딩 지정하여 파일 읽기 (cp949 시도, 안되면 'utf-8', 'euc-kr' 등 시도)
            df = pd.read_csv(uploaded_file, encoding='cp949')
        except UnicodeDecodeError:
            st.warning("cp949 인코딩 실패. utf-8으로 다시 시도합니다.")
            try:
                # utf-8로 다시 시도
                uploaded_file.seek(0) # 파일 포인터 초기화
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")
                st.stop() # 오류 발생 시 중단
        except Exception as e:
            st.error(f"파일 처리 중 예상치 못한 오류 발생: {e}")
            st.stop()

        st.write("파일에서 읽어온 열 이름:") # 열 이름 확인용 출력
        st.write(df.columns.tolist()) # 리스트 형태로 보기 좋게 출력

        # 열 이름 앞뒤 공백 제거
        try:
            df.columns = df.columns.str.strip()
            st.write("공백 제거 후 열 이름:") # 공백 제거 후 열 이름 확인
            st.write(df.columns.tolist())
        except Exception as e:
            st.warning(f"열 이름 공백 제거 중 오류: {e}")
            # 오류가 발생해도 일단 진행하도록 pass 또는 다른 처리 가능

        # 필수 컬럼 존재 여부 확인 및 처리 (예시: 필요한 컬럼 리스트)
        required_columns = ['시간대', '시작 날짜', '부서', '차대 분류', '작업 장소', '차대 코드', '운영 시간(초)']
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"필수 열이 누락되었습니다: {', '.join(missing_cols)}")
            st.warning("진행하기 전에 CSV 파일의 열 이름을 확인하고 코드를 수정해주세요.")
            st.stop() # 필수 열 없으면 중단

        # 데이터 타입 변환 (오류 발생 가능성 있는 부분 try-except로 감싸기)
        try:
            # 시간대를 시간 형식으로 변환
            df['시간대'] = pd.to_datetime(df['시간대'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

            # 시작 날짜를 날짜 형식으로 변환 및 월 열 추가
            df['시작 날짜'] = pd.to_datetime(df['시작 날짜'], errors='coerce')
            df['월'] = df['시작 날짜'].dt.month

            # 12월 데이터 제외 (필요시 주석 해제 또는 수정)
            # excluded_month = 12
            # df = df[df['월'] != excluded_month]

            # '운영 시간(초)'를 숫자로 변환 (문자열이나 다른 타입이 섞여있을 경우 대비)
            df['운영 시간(초)'] = pd.to_numeric(df['운영 시간(초)'], errors='coerce').fillna(0)

        except Exception as e:
            st.error(f"데이터 타입 변환 중 오류 발생: {e}")
            st.warning("CSV 파일의 '시간대', '시작 날짜', '운영 시간(초)' 열의 데이터 형식을 확인해주세요.")
            st.stop()


        # 드롭다운 메뉴 설정 (이제 컬럼 존재가 확인되었으므로 안전)
        analysis_type = st.radio("분석 유형 선택:", ('운영 대수', '운영 횟수'))
        selected_month = st.selectbox('월 선택:', ['전체'] + sorted(df['월'].dropna().unique().tolist()))
        selected_department = st.selectbox('부서 선택:', ['전체'] + sorted(df['부서'].dropna().unique().tolist()))
        # '공정' 선택 메뉴 제거
        selected_forklift_class = st.selectbox('차대 분류 선택:', ['전체'] + sorted(df['차대 분류'].dropna().unique().tolist()))
        selected_workplace = st.selectbox('작업 장소 선택:', ['전체'] + sorted(df['작업 장소'].dropna().unique().tolist()))
        graph_height = st.slider('그래프 높이 선택', 300, 1500, 900)

# 변수 초기화
title = "분석 대기 중..."
index_name = "데이터 선택"

# --- 이하 메인 페이지 로직은 이전과 거의 동일 ---
# (단, generate_pivot 함수 내부에서 사용하는 컬럼들도 df에 있는지 확인 필요)

# 메인 페이지 설정
# 'df'가 정상적으로 정의되었는지 확인 후 진행
if uploaded_file is not None and 'df' in locals() and not df.empty:
    # generate_pivot 함수에서 'process' 매개변수 제거
    def generate_pivot(month, department, forklift_class, workplace):
        filtered_df = df.copy() # 원본 df 유지 위해 복사본 사용

        # 필터링 전 데이터 타입 확인 (디버깅용)
        # print(f"Filtering: Month={month}, Dept={department}, Class={forklift_class}, Place={workplace}")
        # print(filtered_df.dtypes)

        # 필터링 조건 적용
        if month != '전체':
            # '월' 컬럼이 숫자인지 확인
            if pd.api.types.is_numeric_dtype(filtered_df['월']):
                filtered_df = filtered_df[filtered_df['월'] == month]
            else:
                st.warning("'월' 컬럼이 숫자 타입이 아닙니다. 월별 필터링을 건너<0xEB><0x9B><0x84>니다.")
        if department != '전체':
            filtered_df = filtered_df[filtered_df['부서'] == department]
        if forklift_class != '전체':
            filtered_df = filtered_df[filtered_df['차대 분류'] == forklift_class]
        if workplace != '전체':
            filtered_df = filtered_df[filtered_df['작업 장소'] == workplace]

        # 필터링 후 데이터프레임이 비었는지 확인
        if filtered_df.empty:
            st.warning("선택된 조건에 해당하는 데이터가 없습니다.")
            # 빈 피벗 테이블과 기본 요약 정보 반환
            empty_pivot = pd.DataFrame()
            empty_summary = {}
            return empty_pivot, "데이터 없음", "데이터 없음", empty_summary

        # --- 분석 로직 시작 ---
        if analysis_type == '운영 대수':
            try:
                filtered_df['시작 날짜'] = pd.to_datetime(filtered_df['시작 날짜']).dt.strftime('%m-%d') # 날짜 형식 재확인
                index_name = '시작 날짜'
                value_name = '차대 코드'
                agg_func = 'nunique'
                title = '지게차 일자별 운영 대수'

                # 월 전체 운영 대수 계산
                total_operating_units = filtered_df[value_name].nunique()

                # 일별 운영 대수 계산
                daily_counts = filtered_df.groupby(index_name)[value_name].nunique()
                min_operating_units = daily_counts.min() if not daily_counts.empty else 0
                max_operating_units = daily_counts.max() if not daily_counts.empty else 0
                min_operating_day = daily_counts.idxmin() if not daily_counts.empty else '데이터 없음'
                max_operating_day = daily_counts.idxmax() if not daily_counts.empty else '데이터 없음'
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

                # 피벗 테이블 생성
                pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0).astype(int)

            except KeyError as e:
                st.error(f"'운영 대수' 분석 중 오류: 필요한 열 '{e}'를 찾을 수 없습니다.")
                return pd.DataFrame(), "오류", "오류", {}
            except Exception as e:
                st.error(f"'운영 대수' 분석 중 예상치 못한 오류: {e}")
                return pd.DataFrame(), "오류", "오류", {}

        else: # analysis_type == '운영 횟수'
            try:
                index_name = '차대 코드'
                value_name = '시작 날짜' # 집계 기준이 되는 값이므로, 횟수를 세기 위해 임의의 열(여기서는 시작 날짜) 사용
                agg_func = 'count'
                title = '지게차 차대별 시간대별 운영 횟수'

                # 차대별 운영 횟수 계산
                unit_counts = filtered_df.groupby(index_name)[value_name].count() # value_name은 count를 위해 사용
                min_operating_counts = unit_counts.min() if not unit_counts.empty else 0
                max_operating_counts = unit_counts.max() if not unit_counts.empty else 0
                min_operating_unit = unit_counts.idxmin() if not unit_counts.empty else '데이터 없음'
                max_operating_unit = unit_counts.idxmax() if not unit_counts.empty else '데이터 없음'
                avg_operating_counts = round(unit_counts.mean()) if not unit_counts.empty else 0
                total_operating_counts = unit_counts.sum()

                # 비율 계산
                min_operating_counts_ratio = (min_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0
                max_operating_counts_ratio = (max_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0
                avg_operating_counts_ratio = (avg_operating_counts / total_operating_counts) * 100 if total_operating_counts > 0 else 0

                # 운영 시간 계산 (이미 숫자 타입으로 변환됨)
                operating_times = filtered_df.groupby(index_name)['운영 시간(초)'].sum()
                min_operating_time = operating_times.min() if not operating_times.empty else 0
                max_operating_time = operating_times.max() if not operating_times.empty else 0
                min_time_unit = operating_times.idxmin() if not operating_times.empty else '데이터 없음'
                max_time_unit = operating_times.idxmax() if not operating_times.empty else '데이터 없음'
                avg_operating_time = round(operating_times.mean()) if not operating_times.empty else 0
                total_operating_time = operating_times.sum()

                # 운영 시간 비율 계산
                min_operating_time_ratio = (min_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
                max_operating_time_ratio = (max_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0
                avg_operating_time_ratio = (avg_operating_time / total_operating_time) * 100 if total_operating_time > 0 else 0


                def format_time(seconds):
                    hours, remainder = divmod(int(seconds), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    return f"{hours:02}:{minutes:02}:{seconds:02}"

                min_operating_time_formatted = format_time(min_operating_time)
                max_operating_time_formatted = format_time(max_operating_time)
                avg_operating_time_formatted = format_time(avg_operating_time)
                total_operating_time_formatted = format_time(total_operating_time)

                summary = {
                    'total_counts': total_operating_counts,
                    'min_counts': min_operating_counts, 'min_counts_unit': min_operating_unit, 'min_counts_ratio': min_operating_counts_ratio,
                    'max_counts': max_operating_counts, 'max_counts_unit': max_operating_unit, 'max_counts_ratio': max_operating_counts_ratio,
                    'avg_counts': avg_operating_counts, 'avg_counts_ratio': avg_operating_counts_ratio,
                    'total_time': total_operating_time_formatted,
                    'min_time': min_operating_time_formatted, 'min_time_unit': min_time_unit, 'min_time_ratio': min_operating_time_ratio,
                    'max_time': max_operating_time_formatted, 'max_time_unit': max_time_unit, 'max_time_ratio': max_operating_time_ratio,
                    'avg_time': avg_operating_time_formatted, 'avg_time_ratio': avg_operating_time_ratio,
                }

                # 피벗 테이블 생성
                pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0).astype(int)

            except KeyError as e:
                st.error(f"'운영 횟수' 분석 중 오류: 필요한 열 '{e}'를 찾을 수 없습니다.")
                return pd.DataFrame(), "오류", "오류", {}
            except Exception as e:
                st.error(f"'운영 횟수' 분석 중 예상치 못한 오류: {e}")
                return pd.DataFrame(), "오류", "오류", {}


        return pivot_table, title, index_name, summary

    # generate_pivot 함수 호출 및 결과 받기
    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_forklift_class, selected_workplace)

    # 피벗 테이블이 비어 있지 않은 경우에만 그래프 및 요약 표시
    if not pivot_table.empty:
        # Heatmap 생성
        fig = make_subplots(rows=1, cols=1)
        tooltip_texts = [[f'운영 횟수: {int(val)}회' if analysis_type == '운영 횟수' else f'운영 대수: {int(val)}대' for val in row] for row in pivot_table.values]
        heatmap = go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale=[[0, 'white'], [0.0001, '#fde0dd'], [0.1, '#fa9fb5'], [0.3, '#c51b8a'], [1, '#7a0177']],
            hoverinfo='text',
            text=tooltip_texts,
            zmin=0,
            zmax=pivot_table.values.max() if pivot_table.values.size > 0 else 1
        )
        fig.add_trace(heatmap)

        # 최댓값 하이라이트 추가 (데이터 있을 때만)
        if pivot_table.values.size > 0:
            max_value = pivot_table.values.max()
            if max_value > 0:
                # 최댓값 위치 찾기 (동일 최댓값 모두)
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
                            x=[x_val],
                            y=[y_val],
                            mode='markers+text',
                            marker=dict(size=12, color='yellow', symbol='circle', line=dict(color='black', width=1)),
                            text=[f'{"동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"} {int(max_value)} {"대" if analysis_type == "운영 대수" else "회"}'],
                            textposition='top center',
                            textfont=dict(color='black', size=14),
                            hoverinfo='none'
                        )
                    )
                for trace in annotations:
                    fig.add_trace(trace)


        # 레이아웃 설정
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 25}},
            xaxis=dict(title='시간대', fixedrange=True, tickangle=0),
            yaxis=dict(title=index_name, fixedrange=True),
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(l=100, r=50, t=100, b=50),
            height=graph_height,
            coloraxis_colorbar=dict(title='운영 강도')
        )

        # y축 정렬
        if analysis_type == '운영 대수':
            all_dates = sorted(pivot_table.index, key=lambda d: pd.to_datetime(d, format='%m-%d'))
            fig.update_yaxes(type='category', categoryorder='array', categoryarray=all_dates, tickmode='array', tickvals=all_dates)
        else: # 운영 횟수
            sorted_units = pivot_table.sum(axis=1).sort_values(ascending=False).index.tolist()
            fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted_units)


        # 요약 정보 HTML 생성
        if analysis_type == '운영 대수' and summary:
             summary_html = f"""
             <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9; margin-top: 15px;">
                 <h4 style="margin-top:0; color: #333;">일별 운영 대수 요약</h4>
                 <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                     <div style="text-align: center; margin: 5px;"><b>전체 운영 대수 (월):</b><br>{summary.get('total_units', 'N/A')}대</div>
                     <div style="text-align: center; margin: 5px;"><b>최소 운영일 ({summary.get('min_units_day', 'N/A')}):</b><br>{summary.get('min_units', 'N/A')}대 ({float(summary.get('min_units_ratio', 0)):.2f}%)</div>
                     <div style="text-align: center; margin: 5px;"><b>최대 운영일 ({summary.get('max_units_day', 'N/A')}):</b><br>{summary.get('max_units', 'N/A')}대 ({float(summary.get('max_units_ratio', 0)):.2f}%)</div>
                     <div style="text-align: center; margin: 5px;"><b>일 평균 운영 대수:</b><br>{summary.get('avg_units', 'N/A')}대 ({float(summary.get('avg_units_ratio', 0)):.2f}%)</div>
                 </div>
             </div>
             """
        elif analysis_type == '운영 횟수' and summary:
             summary_html = f"""
             <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9; margin-top: 15px;">
                 <h4 style="margin-top:0; color: #333;">차대별 운영 요약</h4>
                 <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                     <div style="border-right: 1px solid #eee; padding-right: 20px; margin-right: 20px; margin-bottom: 10px;">
                         <b>운영 횟수</b><br>
                         전체: {summary.get('total_counts', 'N/A')}번<br>
                         최소: {summary.get('min_counts_unit', 'N/A')} ({summary.get('min_counts', 'N/A')}번, {float(summary.get('min_counts_ratio', 0)):.2f}%)<br>
                         최대: {summary.get('max_counts_unit', 'N/A')} ({summary.get('max_counts', 'N/A')}번, {float(summary.get('max_counts_ratio', 0)):.2f}%)<br>
                         평균: {summary.get('avg_counts', 'N/A')}번 ({float(summary.get('avg_counts_ratio', 0)):.2f}%)
                     </div>
                     <div>
                         <b>운영 시간</b><br>
                         전체: {summary.get('total_time', 'N/A')}<br>
                         최소: {summary.get('min_time_unit', 'N/A')} ({summary.get('min_time', 'N/A')}, {float(summary.get('min_time_ratio', 0)):.2f}%)<br>
                         최대: {summary.get('max_time_unit', 'N/A')} ({summary.get('max_time', 'N/A')}, {float(summary.get('max_time_ratio', 0)):.2f}%)<br>
                         평균: {summary.get('avg_time', 'N/A')} ({float(summary.get('avg_time_ratio', 0)):.2f}%)
                     </div>
                 </div>
             </div>
             """
        else:
            summary_html = "" # 요약 정보 없음


        # Streamlit으로 결과 표시
        st.plotly_chart(fig, use_container_width=True)
        if summary_html:
            st.markdown(summary_html, unsafe_allow_html=True)
    elif uploaded_file is not None: # 피벗 테이블은 비었지만 파일은 업로드 된 경우
        st.info("선택하신 조건에 맞는 데이터가 없어 그래프를 표시할 수 없습니다. 필터 조건을 변경해보세요.")


# 파일이 업로드되지 않았을 경우 메시지
elif uploaded_file is None:
    st.info("데이터를 분석하려면 CSV 파일을 업로드하세요.")

# 그 외의 경우 (예: 파일 읽기 실패 후 df가 정의되지 않은 상태) - 이미 위에서 처리됨
