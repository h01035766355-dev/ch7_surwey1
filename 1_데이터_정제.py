import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="데이터 정제", page_icon="🧹", layout="wide")

# -----------------------------------------------------------------------------
# 1. 사이드바 구성
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ 데이터 정제 옵션")

# 이상치 허용 범위 (분 단위)
max_time_limit = st.sidebar.slider(
    "AI 사용 시간 이상치 허용 범위 (분)",
    min_value=60,
    max_value=1440,
    value=480,
    step=30,
    help="설정한 분을 초과하는 응답은 이상치로 판단하여 정제 과정에서 제거합니다."
)

# 결측치 처리 선택
na_action = st.sidebar.radio(
    "결측치(빈칸) 처리 방식",
    options=["그대로 두기", "행 삭제"],
    index=0
)

# -----------------------------------------------------------------------------
# 2. 메인 화면 구성
# -----------------------------------------------------------------------------
st.title("🧹 데이터 정제 (Data Cleaning)")

uploaded_file = st.file_uploader("구글 설문지 CSV 파일(survey_raw.csv)을 업로드하세요.", type=["csv"])

if uploaded_file is not None:
    # 원본 데이터 로드
    raw_df = pd.read_csv(uploaded_file)

    # -------------------------------------------------------------------------
    # 상단 정보 표시 (응답자 수 & 원본 데이터)
    # -------------------------------------------------------------------------
    st.subheader("📌 원본 데이터 확인")
    col_top1, col_top2 = st.columns([1, 3])
    with col_top1:
        st.metric("총 응답자 수", f"{len(raw_df)} 명")

    with st.expander("원본 데이터 전체 보기", expanded=False):
        st.dataframe(raw_df, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 데이터 정제 프로세스 (원본 보존, 복사본 생성)
    # -------------------------------------------------------------------------
    df = raw_df.copy()
    logs = []

    # 1. 열 제목 축소
    short_cols = ["타임스탬프", "성별", "학년", "소속단과대학", "AI사용시간", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "서술형"]
    if len(df.columns) == len(short_cols):
        df.columns = short_cols
        logs.append("1. 열 제목을 표준 명칭(타임스탬프, 성별, 학년, 소속단과대학, AI사용시간, Q1~Q6, 서술형)으로 축소 변경했습니다.")
    else:
        logs.append(f"1. 열 개수({len(df.columns)}개)가 기본 서식({len(short_cols)}개)과 달라 원본 열 제목을 유지합니다.")

    # 2. 중복 제거 (타임스탬프 제외 모든 열 기준)
    check_cols = [c for c in df.columns if c != "타임스탬프"]
    initial_cnt = len(df)
    df = df.drop_duplicates(subset=check_cols, keep="first")
    dup_removed = initial_cnt - len(df)
    logs.append(f"2. 중복 응답 {dup_removed}건 제거 (타임스탬프 제외 동일 응답 첫 행만 유지)")


    # 3. 학년 표기 통일 (숫자만 추출)
    def clean_grade(val):
        if pd.isna(val):
            return val
        nums = re.findall(r"\d+", str(val))
        if nums:
            return int(nums[0])
        kor_num_map = {"일": 1, "이": 2, "삼": 3, "사": 4}
        for k, v in kor_num_map.items():
            if k in str(val):
                return v
        return val


    if "학년" in df.columns:
        df["학년"] = df["학년"].apply(clean_grade)
        logs.append("3. 학년 표기를 숫자 형태(1, 2, ...)로 통일했습니다.")


    # 4. 단과대학 분류
    def clean_college(val):
        if pd.isna(val):
            return "기타"
        text = str(val)
        if "인문" in text:
            return "인문대학"
        elif "사과" in text or "사회" in text:
            return "사회과학대학"
        elif "경통" in text or "경제" in text:
            return "경제통상대학"
        elif "경영" in text:
            return "경영대학"
        elif "사범" in text:
            return "사범대학"
        else:
            return "기타"


    if "소속단과대학" in df.columns:
        df["소속단과대학"] = df["소속단과대학"].apply(clean_college)
        logs.append("4. 단과대학을 5개 핵심 대학(인문/사회과학/경제통상/경영/사범) 및 기타로 분류 완료했습니다.")


    # 5. AI 사용시간 분 단위 변환 및 이상치 처리
    def parse_time_to_minutes(val):
        if pd.isna(val):
            return None
        text = str(val).strip()
        hours, minutes = 0, 0
        h_match = re.search(r"(\d+)\s*시간", text)
        m_match = re.search(r"(\d+)\s*분", text)

        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))

        if not h_match and not m_match:
            digits = re.findall(r"\d+", text)
            if digits:
                minutes = int(digits[0])
            else:
                return None
        return hours * 60 + minutes


    if "AI사용시간" in df.columns:
        df["AI사용시간"] = df["AI사용시간"].apply(parse_time_to_minutes)
        before_outlier = len(df)
        df = df[df["AI사용시간"].isna() | (df["AI사용시간"] <= max_time_limit)]
        outlier_cnt = before_outlier - len(df)
        logs.append(f"5. AI사용시간 분 단위 변환 및 이상치({max_time_limit}분 초과) {outlier_cnt}건 제거 완료했습니다.")

    # 6. 결측치 처리
    null_counts = df.isnull().sum()
    null_info = ", ".join([f"{col}: {cnt}개" for col, cnt in null_counts.items() if cnt > 0])
    if not null_info:
        null_info = "없음"

    if na_action == "행 삭제":
        before_na = len(df)
        df = df.dropna()
        na_removed = before_na - len(df)
        logs.append(f"6. 결측치 처리: '행 삭제' 적용 (총 {na_removed}개 행 삭제됨, 열별 결측치: {null_info})")
    else:
        logs.append(f"6. 결측치 처리: '그대로 두기' 적용 (열별 결측치 수량 -> {null_info})")

    # 7. 역문항 계산 (Q6R = 6 - Q6)
    if "Q6" in df.columns:
        df["Q6"] = pd.to_numeric(df["Q6"], errors="coerce")
        df["Q6R"] = 6 - df["Q6"]
        logs.append("7. 학업 정직성 역문항 점수 재계산 완료 (Q6R = 6 - Q6)")

    # -------------------------------------------------------------------------
    # 결과 출력
    # -------------------------------------------------------------------------
    st.subheader("📊 정제 결과 요약")

    col1, col2, col3 = st.columns(3)
    col1.metric("원본 데이터 수", f"{len(raw_df)} 건")
    col2.metric("최종 정제 데이터 수", f"{len(df)} 건")
    col3.metric("제거된 응답 수", f"{len(raw_df) - len(df)} 건")

    st.subheader("📋 정제 기록")
    for log in logs:
        st.write(f"- {log}")

    st.subheader("✨ 최종 정제된 데이터")
    st.dataframe(df, use_container_width=True)

    # -------------------------------------------------------------------------
    # Session State 저장 및 CSV 다운로드
    # -------------------------------------------------------------------------
    st.session_state["clean_df"] = df

    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 정제된 데이터 CSV 다운로드",
        data=csv_data,
        file_name="clean_survey_data.csv",
        mime="text/csv"
    )

else:
    st.info("👈 사이드바 조건 설정 후, 메인 화면에 CSV 파일을 업로드해 주세요.")