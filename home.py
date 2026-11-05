import streamlit as st

st.set_page_config(
    page_title="생성형 AI 활용 인식 조사 데이터 분석",
    page_icon="📊",
    layout="wide"
)

st.title("📊 생성형 AI 활용 인식 조사 분석 시스템")
st.subheader("부산대학교 인문사회계열 학생 대상 설문 데이터 분석")

st.markdown("""
---
### 📌 앱 안내
이 애플리케이션은 생성형 AI 활용 인식 조사 데이터(`survey_raw.csv`)를 정제하고 분석하기 위해 제작되었습니다.

**왼쪽 사이드바 메뉴**를 통해 데이터 정제 및 분석 단계로 이동할 수 있습니다.

1. **1_데이터_정제**: CSV 파일 업로드, 열 이름 변경, 중복/이상치/결측치 처리 및 역문항 재계산을 수행하고 결과를 저장/다운로드합니다.
2. **이후 분석 페이지**: 정제된 데이터를 기반으로 시각화 및 통계 분석을 진행할 수 있습니다.
""")

# 세션 상태 초기화 확인
if "clean_df" in st.session_state:
    st.success("✅ 현재 정제된 데이터가 메모리(st.session_state)에 저장되어 있습니다.")
else:
    st.info("💡 사이드바의 **'1_데이터_정제'** 페이지에서 데이터 파일을 업로드하고 정제를 진행해 주세요.")