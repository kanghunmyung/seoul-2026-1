"""
분반 프로그램 — Streamlit 시작 앱

학생 분반 데이터를 업로드하면 학년/반별로 정리해서 보여주는 프로그램입니다.
"""

import io

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="분반 프로그램",
    page_icon="📊",
    layout="wide",
)

st.title("📊 분반 프로그램")
st.caption("학년/반별 학생 데이터를 업로드하면 반별로 정리해서 보여줍니다.")


# ──────────────────────────────────────────────────────────────
# 공용 유틸 (수정 불필요) — 엑셀 CP949 / 메모장 UTF-8 자동 처리
# ──────────────────────────────────────────────────────────────
def read_csv_any(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.read()
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(raw), encoding="utf-8", errors="replace")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


required_columns = ["학년", "반", "번호", "이름", "성별", "수학성적", "국어성적"]


# ──────────────────────────────────────────────────────────────
# 사이드바: 파일 업로더
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 데이터 업로드")
    uploaded = st.file_uploader("CSV 파일", type=["csv"])
    st.markdown(
        """
        **필수 컬럼**
        - `학년`
        - `반`
        - `번호`
        - `이름`
        - `성별`
        - `수학성적`
        - `국어성적`

        샘플 파일이 필요하면 `sample_data.csv`를 사용하세요.
        """
    )

if uploaded is None:
    st.info("👈 왼쪽 사이드바에서 CSV 파일을 업로드하세요.")
    st.stop()

df = normalize_columns(read_csv_any(uploaded))
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(
        "CSV에 필요한 컬럼이 없습니다: " + ", ".join(missing_columns)
    )
    st.stop()

for col in ["학년", "반", "번호", "수학성적", "국어성적"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.sort_values(["학년", "반", "번호"]).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# 기능 1. 전체 데이터 확인 + 요약
# ──────────────────────────────────────────────────────────────
st.subheader("① 전체 데이터 확인")

col1, col2, col3 = st.columns(3)
col1.metric("전체 학생 수", f"{len(df)}명")
col2.metric("학년 수", int(df["학년"].nunique()))
col3.metric("반 수", int(df[["학년", "반"]].drop_duplicates().shape[0]))

st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# 기능 2. 학년/반 선택해서 보기
# ──────────────────────────────────────────────────────────────
st.subheader("② 학년/반별 학생 보기")

grade_options = sorted(df["학년"].dropna().unique())
selected_grade = st.selectbox("학년 선택", grade_options)

class_options = sorted(df.loc[df["학년"] == selected_grade, "반"].dropna().unique())
selected_class = st.selectbox("반 선택", class_options)

class_df = df[(df["학년"] == selected_grade) & (df["반"] == selected_class)].copy()
class_df = class_df.sort_values("번호")

st.write(f"**{int(selected_grade)}학년 {int(selected_class)}반 학생 목록**")
st.dataframe(class_df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# 기능 3. 반별 성적 요약
# ──────────────────────────────────────────────────────────────
st.subheader("③ 반별 성적 요약")

summary_df = (
    df.groupby(["학년", "반"], as_index=False)
    .agg(
        학생수=("이름", "count"),
        남학생수=("성별", lambda x: (x.astype(str).str.strip() == "남").sum()),
        여학생수=("성별", lambda x: (x.astype(str).str.strip() == "여").sum()),
        수학평균=("수학성적", "mean"),
        국어평균=("국어성적", "mean"),
    )
)

summary_df["수학평균"] = summary_df["수학평균"].round(1)
summary_df["국어평균"] = summary_df["국어평균"].round(1)

st.dataframe(summary_df, use_container_width=True, hide_index=True)
