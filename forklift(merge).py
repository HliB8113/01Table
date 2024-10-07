# 기존 코드 유지, 최댓값을 강조하는 기능 추가
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit 그래프에서 최댓값을 강조하는 기능 추가
if uploaded_file is not None and 'df' in locals():
    def generate_pivot(month, department, process, forklift_class, workplace):
        # ... 기존 코드 생략 ...
        
        pivot_table = filtered_df.pivot_table(index=index_name, columns='시간대', values=value_name, aggfunc=agg_func).fillna(0)
        
        # 최댓값 위치 계산
        max_value = pivot_table.values.max()
        max_value_indices = list(zip(*((pivot_table.values == max_value).nonzero())))
        return pivot_table, title, index_name, summary, max_value_indices

    pivot_table, title, index_name, summary, max_value_indices = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace)

    # Heatmap 생성
    fig = make_subplots(rows=1, cols=1)
    tooltip_texts = [[f'{analysis_type} {int(val)}{"대" if analysis_type == "운영 대수" else "번"}' for val in row] for row in pivot_table.values]
    heatmap = go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale=[[0, 'white'], [1, 'purple']],
        hoverinfo='text',
        text=tooltip_texts,
        zmin=0,
        zmax=pivot_table.values.max()
    )
    fig.add_trace(heatmap)

    # 최댓값 강조 표시 추가
    for (row, col) in max_value_indices:
        fig.add_trace(go.Scatter(
            x=[pivot_table.columns[col]],
            y=[pivot_table.index[row]],
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='star'),
            text=['최댓값'],
            textposition='top center',
            showlegend=False
        ))

    fig.update_layout(
        title={
            'text': title,
            'x': 0.5
        },
        xaxis=dict(title='시간대', fixedrange=True),
        yaxis=dict(title=index_name, categoryorder='array', categoryarray=sorted(pivot_table.index)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=150, b=50),
        width=900,  # 고정된 널비
        height=graph_height  # 조정 가능한 널이
    )

    # 모든 '시작 날짜'를 세로축에 표시 (월일만 표시)
    if analysis_type == '운영 대수':
        fig.update_yaxes(type='category', tickmode='array', tickvals=sorted(pivot_table.index))

    # ... 기존 요약 정보 코드 생략 ...

    # Streamlit을 통해 플롯 보여주기
    st.plotly_chart(fig, use_container_width=True)
