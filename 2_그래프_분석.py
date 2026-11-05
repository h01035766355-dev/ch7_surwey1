import streamlit as st
import pandas as pd

st.set_page_config(page_title="그래프 분석", page_icon="", layout="wide")


def load_data():
    if "clean_df" in st.session_state and st.session_state["clean_df"] is not None:
        return st.session_state["clean_df"], "세션에서 정제된 데이터를 불러왔습니다."

    uploaded_file = st.file_uploader("정제된 CSV 파일을 업로드하세요", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state["clean_df"] = df
        return df, "업로드된 파일을 불러왔습니다."

    return None, "데이터가 없습니다. 1_데이터_정제 페이지를 먼저 실행하거나 파일을 업로드하세요."


def get_ai_ethics_avg(df):
    target_cols = [c for c in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6R"] if c in df.columns]
    if not target_cols:
        return 0.0
    return df[target_cols].mean(numeric_only=True).mean()


def render_summary_metrics(df):
    valid_count = len(df)

    if "AI사용시간" in df.columns:
        avg_time = df["AI사용시간"].mean(numeric_only=True)
    else:
        avg_time = 0.0

    ethics_avg = get_ai_ethics_avg(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("유효 응답 수", f"{valid_count} 명")
    col2.metric("평균 AI 사용 시간", f"{avg_time:.1f} 분")
    col3.metric("AI 윤리의식 평균", f"{ethics_avg:.2f} 점")


def render_comparison_charts(raw_df, clean_df):
    st.subheader("단과대학별 응답자 수 비교 (정제 전후)")

    if "소속단과대학" not in raw_df.columns or "소속단과대학" not in clean_df.columns:
        st.warning("소속단과대학 열이 존재하지 않습니다.")
        return

    raw_counts = raw_df["소속단과대학"].value_counts().reset_index()
    raw_counts.columns = ["소속단과대학", "정제전"]

    clean_counts = clean_df["소속단과대학"].value_counts().reset_index()
    clean_counts.columns = ["소속단과대학", "정제후"]

    merged_counts = pd.merge(raw_counts, clean_counts, on="소속단과대학", how="outer").fillna(0)
    merged_counts = merged_counts.set_index("소속단과대학")

    st.bar_chart(merged_counts, horizontal=True)


def render_tab_respondent_composition(df):
    st.subheader("응답자 구성 분석")

    col1, col2 = st.columns(2)

    with col1:
        if "성별" in df.columns:
            st.write("성별 분포")
            gender_counts = df["성별"].value_counts()
            st.bar_chart(gender_counts, horizontal=True)

    with col2:
        if "학년" in df.columns:
            st.write("학년 분포")
            grade_counts = df["학년"].value_counts().sort_index()
            st.bar_chart(grade_counts, horizontal=True)

    if "소속단과대학" in df.columns:
        st.write("소속단과대학 분포")
        college_counts = df["소속단과대학"].value_counts()
        st.bar_chart(college_counts, horizontal=True)


def render_tab_item_averages(df):
    st.subheader("문항별 평균 점수")

    target_cols = [c for c in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6R"] if c in df.columns]
    if not target_cols:
        st.warning("분석할 문항 데이터가 없습니다.")
        return

    means = df[target_cols].mean(numeric_only=True)
    mean_df = pd.DataFrame({"문항": means.index, "평균점수": means.values})
    mean_df = mean_df.set_index("문항")

    st.bar_chart(mean_df, horizontal=True)


def render_tab_group_comparison(df):
    st.subheader("집단별 비교 분석")

    target_cols = [c for c in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6R"] if c in df.columns]

    if "학년" in df.columns and target_cols:
        st.write("학년별 평균 및 인원 수")
        grade_grouped = df.groupby("학년").agg(
            인원수=("학년", "count"),
            평균점수=(target_cols[0], "mean")
        )
        for col in target_cols[1:]:
            grade_grouped[f"{col}_평균"] = df.groupby("학년")[col].mean()

        grade_grouped = grade_grouped.round(2)
        st.dataframe(grade_grouped, use_container_width=True)

    if "소속단과대학" in df.columns and target_cols:
        st.write("소속단과대학별 평균 및 인원 수")
        college_grouped = df.groupby("소속단과대학").agg(
            인원수=("소속단과대학", "count"),
            평균점수=(target_cols[0], "mean")
        )
        for col in target_cols[1:]:
            college_grouped[f"{col}_평균"] = df.groupby("소속단과대학")[col].mean()

        college_grouped = college_grouped.round(2)
        st.dataframe(college_grouped, use_container_width=True)


def render_tab_time_and_score(df):
    st.subheader("사용 시간과 점수 관계")

    if "AI사용시간" not in df.columns:
        st.warning("AI사용시간 데이터가 없습니다.")
        return

    target_cols = [c for c in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6R"] if c in df.columns]
    if not target_cols:
        st.warning("분석할 문항 데이터가 없습니다.")
        return

    df["전체문항평균"] = df[target_cols].mean(numeric_only=True)
    scatter_df = df[["AI사용시간", "전체문항평균"]].dropna()

    st.scatter_chart(scatter_df, x="AI사용시간", y="전체문항평균")


def main():
    st.title("그래프 분석")

    df, message = load_data()

    if df is None:
        st.info(message)
        return

    raw_df = st.session_state.get("raw_df", df)

    render_summary_metrics(df)
    st.markdown("---")

    render_comparison_charts(raw_df, df)
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "응답자 구성",
        "문항별 평균",
        "집단 비교",
        "사용 시간과 점수"
    ])

    with tab1:
        render_tab_respondent_composition(df)

    with tab2:
        render_tab_item_averages(df)

    with tab3:
        render_tab_group_comparison(df)

    with tab4:
        render_tab_time_and_score(df)


if __name__ == "__main__":
    main()