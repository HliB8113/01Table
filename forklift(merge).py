# --- 메인 페이지 ---
st.title("🚚 지게차 운영 현황 대시보드")

if df is not None:
    pivot_data, title, index_name, summary = generate_pivot(
        df, selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace, analysis_type
    )

    if pivot_data and isinstance(pivot_data, dict):
        pivot_table = None
        pivot_table_times = None
        forklift_summary_for_graph = None # 차대별 요약 데이터 (그래프용)

        if analysis_type == '운영 대수':
            pivot_table = pivot_data.get('units')
        elif analysis_type == '운영 횟수':
            pivot_table = pivot_data.get('counts')
            pivot_table_times = pivot_data.get('times')
            forklift_summary_for_graph = pivot_data.get('forklift_summary') # 차대별 요약 데이터 가져오기

        if pivot_table is not None and not pivot_table.empty:
            y_axis_title = '시작 날짜' if index_name == '시작 날짜_표시용' else index_name

            # --- 그래프 생성 ---
            if analysis_type == '운영 횟수' and forklift_summary_for_graph is not None and not forklift_summary_for_graph.empty:
                # 운영 횟수 분석 시: 히트맵 + 막대 그래프 (차대별 요약)
                fig = make_subplots(
                    rows=1, cols=2,
                    column_widths=[0.7, 0.3], # 히트맵과 막대그래프 너비 비율
                    specs=[[{"type": "heatmap"}, {"type": "bar"}]], # 각 서브플롯 타입 지정
                    shared_yaxes=True # Y축 공유
                )

                # 1. 히트맵 추가 (첫 번째 열)
                tooltip_texts_heatmap = []
                for r_idx, r_label in enumerate(pivot_table.index):
                    row_tooltips = []
                    for c_idx, c_label in enumerate(pivot_table.columns):
                        value = pivot_table.iloc[r_idx, c_idx]
                        cell_tooltip = f"{r_label}, {c_label}<br>운영 횟수: {int(value)}회"
                        if pivot_table_times is not None:
                            try:
                                time_value = pivot_table_times.iloc[r_idx, c_idx]
                                formatted_time = format_time(time_value)
                                cell_tooltip += f"<br>사용 시간: {formatted_time}"
                            except (IndexError, Exception):
                                cell_tooltip += "<br>사용 시간: -"
                        row_tooltips.append(cell_tooltip)
                    tooltip_texts_heatmap.append(row_tooltips)

                fig.add_trace(go.Heatmap(
                    z=pivot_table.values,
                    x=pivot_table.columns,
                    y=pivot_table.index,
                    colorscale=[[0, 'rgb(255,255,255)'], [0.01, 'rgb(240, 230, 247)'], [1, '#5f0080']],
                    hoverinfo='text', text=tooltip_texts_heatmap, zmin=0,
                    colorbar=dict(title='횟수', x=0.68) # 컬러바 위치 조정
                ), row=1, col=1)

                # 최대값 하이라이트 (히트맵에만 적용)
                if pivot_table.values.size > 0:
                    try:
                        numeric_values = pd.to_numeric(pivot_table.values.flatten(), errors='coerce')
                        valid_values = numeric_values[~np.isnan(numeric_values)]
                        if valid_values.size > 0:
                            max_value = valid_values.max()
                            if max_value > 0:
                                max_indices = np.where(pivot_table.values == max_value)
                                if len(max_indices[0]) > 0:
                                    max_y_indices, max_x_indices = max_indices[0], max_indices[1]
                                    for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                                        fig.add_trace(go.Scatter(
                                            x=[pivot_table.columns[x_idx]], y=[pivot_table.index[y_idx]],
                                            mode='markers+text',
                                            marker=dict(size=12, color='yellow', symbol='circle-open', line=dict(width=2, color='black')),
                                            text=[f'<b>동시간대 운영(최대): {int(max_value)}회</b>'],
                                            textposition='top right', textfont=dict(color='black', size=12),
                                            hoverinfo='none'
                                        ), row=1, col=1)
                    except Exception:
                        pass


                # 2. 차대별 요약 막대 그래프 추가 (두 번째 열)
                # Y축은 히트맵과 공유 (차대 코드), X축은 이중 축 사용
                fig.add_trace(go.Bar(
                    y=forklift_summary_for_graph.index,
                    x=forklift_summary_for_graph['총 운영 횟수'],
                    name='총 운영 횟수',
                    orientation='h', # 수평 막대 그래프
                    marker_color='rgba(95, 0, 128, 0.7)', # #5f0080 에 alpha 추가
                    text=forklift_summary_for_graph['총 운영 횟수'].apply(lambda x: f'{x}회'),
                    textposition='outside',
                    hoverinfo='y+x',
                    xaxis='x2' # 두 번째 X축 사용
                ), row=1, col=2)

                fig.add_trace(go.Bar(
                    y=forklift_summary_for_graph.index,
                    x=forklift_summary_for_graph['평균 운영 시간(초)'],
                    name='평균 사용 시간(초)',
                    orientation='h',
                    marker_color='rgba(255, 165, 0, 0.7)', # 주황색 계열
                    text=forklift_summary_for_graph['평균 운영 시간(초)'].apply(lambda x: format_time(x)), # 시간 포맷 적용
                    textposition='outside',
                    hoverinfo='y+x',
                    xaxis='x3' # 세 번째 X축 사용 (이중 축을 위해 별도 축으로)
                ), row=1, col=2)

                fig.update_layout(
                    title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    xaxis=dict(title='시간대', tickangle=45, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'), # 히트맵 X축
                    yaxis=dict(title=y_axis_title, automargin=True, showspikes=False, type='category'), # 공유 Y축 (히트맵 기준)
                    xaxis2=dict(title='총 운영 횟수', overlaying='x', side='bottom', anchor='y', domain=[0.75, 1.0], showgrid=False), # 막대그래프 X축 1 (도메인 조정)
                    xaxis3=dict(title='평균 사용 시간(초)', overlaying='x', side='top', anchor='free', position=1, domain=[0.75, 1.0], showgrid=False), # 막대그래프 X축 2 (도메인 조정)
                    yaxis2=dict(showticklabels=False, showgrid=False, zeroline=False), # 막대그래프 쪽 Y축은 레이블 숨김 (공유되므로)

                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=100, r=50, t=100, b=80),
                    height=graph_height, width=graph_width,
                    hovermode='closest',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                # Y축 순서 정렬 (히트맵과 막대그래프 동일하게)
                sorted_y_labels = sorted(pivot_table.index.astype(str))
                fig.update_yaxes(categoryorder='array', categoryarray=sorted_y_labels, row=1, col=1)
                fig.update_yaxes(categoryorder='array', categoryarray=sorted_y_labels, row=1, col=2)


            else: # 운영 대수 분석 또는 운영 횟수 분석 시 필요한 데이터가 없는 경우 (기존 히트맵만 표시)
                fig = make_subplots(rows=1, cols=1)
                tooltip_texts = []
                value_prefix = "운영 횟수" if analysis_type == '운영 횟수' else "운영 대수"
                value_suffix = "회" if analysis_type == '운영 횟수' else "대"

                for r_idx, r_label in enumerate(pivot_table.index):
                    row_tooltips = []
                    for c_idx, c_label in enumerate(pivot_table.columns):
                        value = pivot_table.iloc[r_idx, c_idx]
                        cell_tooltip = f"{r_label}, {c_label}<br>{value_prefix}: {int(value)}{value_suffix}"
                        if analysis_type == '운영 횟수' and pivot_table_times is not None:
                            try:
                                time_value = pivot_table_times.iloc[r_idx, c_idx]
                                formatted_time = format_time(time_value)
                                cell_tooltip += f"<br>사용 시간: {formatted_time}"
                            except (IndexError, Exception):
                                cell_tooltip += "<br>사용 시간: -"
                        row_tooltips.append(cell_tooltip)
                    tooltip_texts.append(row_tooltips)

                heatmap_trace = go.Heatmap(
                    z=pivot_table.values, x=pivot_table.columns, y=pivot_table.index,
                    colorscale=[[0, 'rgb(255,255,255)'], [0.01, 'rgb(240, 230, 247)'], [1, '#5f0080']],
                    hoverinfo='text', text=tooltip_texts, zmin=0,
                    colorbar=dict(title='값' if analysis_type == '운영 대수' else '횟수')
                )
                fig.add_trace(heatmap_trace)

                if pivot_table.values.size > 0:
                    try:
                        numeric_values = pd.to_numeric(pivot_table.values.flatten(), errors='coerce')
                        valid_values = numeric_values[~np.isnan(numeric_values)]
                        if valid_values.size > 0:
                            max_value = valid_values.max()
                            if max_value > 0:
                                max_indices = np.where(pivot_table.values == max_value)
                                if len(max_indices[0]) > 0:
                                    max_y_indices, max_x_indices = max_indices[0], max_indices[1]
                                    highlight_text_prefix = "동시 투입 대수(최대):" if analysis_type == "운영 대수" else "동시간대 운영(최대):"
                                    highlight_text_suffix = "대" if analysis_type == "운영 대수" else "회"
                                    for y_idx, x_idx in zip(max_y_indices, max_x_indices):
                                        fig.add_trace(go.Scatter(
                                            x=[pivot_table.columns[x_idx]], y=[pivot_table.index[y_idx]],
                                            mode='markers+text',
                                            marker=dict(size=12, color='yellow', symbol='circle-open', line=dict(width=2, color='black')),
                                            text=[f'<b>{highlight_text_prefix} {int(max_value)}{highlight_text_suffix}</b>'],
                                            textposition='top right',
                                            textfont=dict(color='black', size=12, family="Arial, sans-serif"),
                                            hoverinfo='none'
                                        ))
                    except Exception:
                        pass

                fig.update_layout(
                    title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'family': "Arial Black, sans-serif", 'color': 'black'}},
                    xaxis=dict(title='시간대', fixedrange=False, tickangle=45, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'),
                    yaxis=dict(title=y_axis_title, fixedrange=False, automargin=True, showspikes=True, spikemode='across', spikesnap='data', spikethickness=1, spikecolor='grey'),
                    plot_bgcolor='rgba(245, 245, 245, 1)', paper_bgcolor='white',
                    margin=dict(l=100, r=50, t=100, b=80),
                    height=graph_height, width=graph_width,
                    hovermode='closest',
                    coloraxis_colorbar=dict(title='운영 대수' if analysis_type == '운영 대수' else '운영 횟수')
                )
                # Y축 순서 정렬
                if analysis_type == '운영 대수':
                    fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted(pivot_table.index.astype(str)))
                else:
                    fig.update_yaxes(type='category', categoryorder='array', categoryarray=sorted(pivot_table.index.astype(str)))

            st.plotly_chart(fig, use_container_width=False)

            # --- 이하 요약 정보 표시는 동일 ---
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
                st.info("요약 정보를 표시할 데이터가 충분하지 않거나, 요약 정보 계산 중 오류가 발생했습니다.")
        elif title == "데이터 없음 (필터링 후)":
            st.warning("선택하신 필터 조건에 해당하는 데이터가 없습니다. 다른 필터 옵션을 선택해 보세요.")
        else:
            st.warning("피벗 테이블을 생성할 데이터가 없습니다. 원본 데이터를 확인하거나 필터 옵션을 조정해 주세요.")
    elif uploaded_file is not None and df is None:
        st.error("데이터 처리 중 문제가 발생했습니다. 업로드된 파일의 형식을 확인하거나 필수 컬럼이 올바르게 포함되어 있는지 확인해 주세요.")

elif uploaded_file is None:
    st.info("👈 사이드바에서 CSV 파일을 업로드하고 옵션을 선택하면 분석 결과를 볼 수 있습니다.")
