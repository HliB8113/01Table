import pandas as pd
import streamlit as st

def generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace):
    # 데이터 로딩 (이 부분은 실제 데이터 로드 방식에 맞게 수정해야 합니다)
    df = pd.read_csv('your_data.csv')  # 또는 다른 방식으로 데이터를 로드
    
    # 필터링 로직 (이 부분은 실제 필터링 로직에 맞게 수정해야 합니다)
    filtered_df = df[
        (df['월'] == selected_month) &
        (df['부서'] == selected_department) &
        (df['공정'] == selected_process) &
        (df['지게차 등급'] == selected_forklift_class) &
        (df['작업 장소'] == selected_workplace)
    ]
    
    # 필요한 열이 있는지 확인
    required_columns = ['운영 시간(초)', '작업 장소', '지게차 번호']  # 필요한 열 목록
    missing_columns = [col for col in required_columns if col not in filtered_df.columns]
    
    if missing_columns:
        st.error(f"다음 열이 데이터프레임에 없습니다: {', '.join(missing_columns)}")
        st.write("사용 가능한 열:", filtered_df.columns.tolist())
        return None, None, None, None
    
    # '운영 시간(초)' 열 처리
    try:
        filtered_df['운영 시간(초)'] = pd.to_numeric(filtered_df['운영 시간(초)'], errors='coerce')
        filtered_df['운영 시간(초)'] = filtered_df['운영 시간(초)'].fillna(0).astype(int)
    except Exception as e:
        st.error(f"'운영 시간(초)' 열 처리 중 오류 발생: {str(e)}")
        return None, None, None, None

    # 피벗 테이블 생성
    try:
        pivot_table = pd.pivot_table(filtered_df, values='운영 시간(초)', 
                                     index=['작업 장소'], 
                                     columns=['지게차 번호'], 
                                     aggfunc='sum', 
                                     fill_value=0)
        
        # 나머지 로직 (제목 생성, 요약 등)
        title = f"{selected_month} {selected_department} {selected_process} {selected_forklift_class} 지게차별 운영시간"
        index_name = "작업 장소"
        summary = filtered_df['운영 시간(초)'].sum()
        
        return pivot_table, title, index_name, summary
    except Exception as e:
        st.error(f"피벗 테이블 생성 중 오류 발생: {str(e)}")
        return None, None, None, None

# 메인 코드
try:
    pivot_table, title, index_name, summary = generate_pivot(selected_month, selected_department, selected_process, selected_forklift_class, selected_workplace)
    
    if pivot_table is not None:
        st.write(title)
        st.dataframe(pivot_table)
        st.write(f"총 운영 시간: {summary} 초")
    else:
        st.warning("피벗 테이블을 생성할 수 없습니다. 데이터를 확인해 주세요.")
except Exception as e:
    st.error(f"예상치 못한 오류 발생: {str(e)}")
    st.write("오류 세부 정보:", e)
