import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# 예제 데이터 생성
data = {
    '시작 날짜': ['2021-01-01', '2021-01-02', '2021-01-01', '2021-01-02'],
    '시간대': ['08:00', '09:00', '08:00', '09:00'],
    '차대 코드': ['A1', 'A2', 'A1', 'A2'],
    '부서': ['부서1', '부서1', '부서2', '부서2']
}

df = pd.DataFrame(data)
df['시작 날짜'] = pd.to_datetime(df['시작 날짜'])
df['월'] = df['시작 날짜'].dt.month

# 고유 차대 코드가 부서 데이터와 1대2 관계인 경우를 처리
df['차대 코드'] = df['차대 코드'].astype(str) + '_' + df['부서'].astype(str)
df['차대 코드'] = df['차대 코드'].apply(lambda x: x.split('_')[0] if df[df['차대 코드'] == x]['부서'].nunique() == 1 else x)

# Pivot Table 생성
pivot_table = df.pivot_table(index='시작 날짜', columns='시간대', values='차대 코드', aggfunc='nunique').fillna(0)

# 그래프 생성
fig = make_subplots(rows=1, cols=1)
heatmap = go.Heatmap(
    z=pivot_table.values,
    x=pivot_table.columns,
    y=pivot_table.index,
    colorscale='Viridis'
)
fig.add_trace(heatmap)
fig.update_layout(title='지게차 일자별 운영 대수', xaxis={'title': '시간대'}, yaxis={'title': '시작 날짜'})

# 결과 출력 확인 (테스트 환경에서 실행)
print(pivot_table)
fig.show()
