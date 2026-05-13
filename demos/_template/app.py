"""
분반 프로그램 — Streamlit 시작 앱

3학년 각 반 CSV 파일을 여러 개 업로드하면 하나로 모아 반별로 정리해서 보여주는 프로그램입니다.
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
st.caption("3학년 각 반 CSV 파일을 여러 개 업로드하면 전체 데이터를 모아서 반별로 보여줍니다.")


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



def rotating_class_label(base_class: int, selected_offset: int, row_index: int) -> str:
    target_class = ((base_class + selected_offset + row_index - 1) % 10) + 1
    return f"{target_class}반"



def highlight_duplicate_names(group_df: pd.DataFrame):
    duplicate_mask = group_df["이름"].duplicated(keep=False)
    styles = pd.DataFrame("", index=group_df.index, columns=group_df.columns)
    styles.loc[duplicate_mask, :] = "background-color: yellow"
    return styles


required_columns = ["학년", "반", "번호", "이름", "성별", "수학성적", "국어성적"]
assign_options = list(range(1, 11))
all_class_options = list(range(1, 11))


# ──────────────────────────────────────────────────────────────
# 사이드바: 여러 파일 업로더
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 데이터 업로드")
    uploaded_files = st.file_uploader("3학년 각 반 CSV 파일", type=["csv"], accept_multiple_files=True)
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

        **사용 방법**
        - `3학년 1반 데이터`, `3학년 2반 데이터`처럼 반별 CSV를 따로 업로드하세요.
        - 여러 파일을 한 번에 선택하면 자동으로 하나로 합쳐집니다.
        - 샘플 파일은 `sample_data_1반.csv` ~ `sample_data_10반.csv`를 사용하세요.
        """
    )

if not uploaded_files:
    st.info("👈 왼쪽 사이드바에서 3학년 각 반 CSV 파일을 업로드하세요.")
    st.stop()

frames = []
file_summaries = []

for uploaded_file in uploaded_files:
    temp_df = normalize_columns(read_csv_any(uploaded_file))
    missing_columns = [col for col in required_columns if col not in temp_df.columns]

    if missing_columns:
        st.error(
            f"{uploaded_file.name} 파일에 필요한 컬럼이 없습니다: " + ", ".join(missing_columns)
        )
        st.stop()

    for col in ["학년", "반", "번호", "수학성적", "국어성적"]:
        temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")

    temp_df["성별"] = temp_df["성별"].astype(str).str.strip()
    temp_df = temp_df[temp_df["학년"] == 3].copy()
    temp_df["총합"] = temp_df["수학성적"] + temp_df["국어성적"]
    temp_df["3학년 학급"] = temp_df["반"].astype("Int64").astype(str) + "반"

    frames.append(temp_df)
    file_summaries.append({"파일명": uploaded_file.name, "학생수": len(temp_df)})

if not frames:
    st.warning("업로드된 파일에서 3학년 데이터를 찾지 못했습니다.")
    st.stop()

df = pd.concat(frames, ignore_index=True)
df = df.sort_values(["반", "번호"]).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# 기능 1. 업로드 파일 확인 + 전체 데이터 확인
# ──────────────────────────────────────────────────────────────
st.subheader("① 업로드 파일 및 전체 데이터 확인")

file_summary_df = pd.DataFrame(file_summaries)
st.dataframe(file_summary_df, use_container_width=True, hide_index=True)

col1, col2, col3 = st.columns(3)
col1.metric("전체 학생 수", f"{len(df)}명")
col2.metric("업로드한 반 수", int(df["반"].nunique()))
col3.metric("업로드 파일 수", len(uploaded_files))

st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# 기능 2. 반 선택해서 보기
# ──────────────────────────────────────────────────────────────
st.subheader("② 반별 학생 보기")

class_options = sorted(df["반"].dropna().unique())
selected_class = st.selectbox("반 선택", class_options)

class_df = df[df["반"] == selected_class].copy().sort_values("번호")

st.write(f"**3학년 {int(selected_class)}반 학생 목록**")
st.dataframe(class_df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# 기능 3. 분반 준비
# ──────────────────────────────────────────────────────────────
st.subheader("③ 분반 준비")

st.markdown("#### 3학년 반별 시작 번호 설정")
class_start_map = {}
assignment_frames = []

for class_no in all_class_options:
    col_left, col_right = st.columns(2)
    with col_left:
        boys_start = st.selectbox(
            f"3학년 {class_no}반 남학생 시작 번호",
            assign_options,
            key=f"boys_start_class_{class_no}",
        )
    with col_right:
        girls_start = st.selectbox(
            f"3학년 {class_no}반 여학생 시작 번호",
            assign_options,
            key=f"girls_start_class_{class_no}",
        )
    class_start_map[class_no] = {"남": boys_start, "여": girls_start}

for class_num in sorted(df["반"].dropna().unique()):
    st.markdown(f"### 3학년 {int(class_num)}반")

    class_data = df[df["반"] == class_num].copy()
    boys_offset = class_start_map[int(class_num)]["남"]
    girls_offset = class_start_map[int(class_num)]["여"]

    boys_df = (
        class_data[class_data["성별"] == "남"]
        .sort_values(["총합", "수학성적", "국어성적", "번호"], ascending=[False, False, False, True])
        .reset_index(drop=True)
    )
    boys_df = boys_df[["번호", "이름", "성별", "수학성적", "국어성적", "총합", "3학년 학급"]].copy()
    boys_df["4학년 반"] = [
        rotating_class_label(int(class_num), boys_offset, idx)
        for idx in range(len(boys_df))
    ]

    girls_df = (
        class_data[class_data["성별"] == "여"]
        .sort_values(["총합", "수학성적", "국어성적", "번호"], ascending=[False, False, False, True])
        .reset_index(drop=True)
    )
    girls_df = girls_df[["번호", "이름", "성별", "수학성적", "국어성적", "총합", "3학년 학급"]].copy()
    girls_df["4학년 반"] = [
        rotating_class_label(int(class_num), girls_offset, idx)
        for idx in range(len(girls_df))
    ]

    col_left, col_right = st.columns(2)

    with col_left:
        st.write("**남학생 분반 순서**")
        edited_boys_df = st.data_editor(
            boys_df,
            use_container_width=True,
            hide_index=True,
            disabled=["번호", "이름", "성별", "수학성적", "국어성적", "총합", "3학년 학급"],
            column_config={
                "4학년 반": st.column_config.SelectboxColumn(
                    "4학년 반",
                    options=[f"{i}반" for i in range(1, 11)],
                    required=True,
                )
            },
            key=f"boys_editor_{int(class_num)}",
        )
        assignment_frames.append(edited_boys_df)

    with col_right:
        st.write("**여학생 분반 순서**")
        edited_girls_df = st.data_editor(
            girls_df,
            use_container_width=True,
            hide_index=True,
            disabled=["번호", "이름", "성별", "수학성적", "국어성적", "총합", "3학년 학급"],
            column_config={
                "4학년 반": st.column_config.SelectboxColumn(
                    "4학년 반",
                    options=[f"{i}반" for i in range(1, 11)],
                    required=True,
                )
            },
            key=f"girls_editor_{int(class_num)}",
        )
        assignment_frames.append(edited_girls_df)


# ──────────────────────────────────────────────────────────────
# 기능 4. 분반 결과
# ──────────────────────────────────────────────────────────────
st.subheader("④ 분반 결과")

if assignment_frames:
    result_df = pd.concat(assignment_frames, ignore_index=True)
    result_df["4학년 반 번호"] = result_df["4학년 반"].str.extract(r"(\d+)").astype(int)

    for grade4_class in range(1, 11):
        st.markdown(f"### 4학년 {grade4_class}반")
        grade4_df = result_df[result_df["4학년 반 번호"] == grade4_class].copy()
        grade4_df = grade4_df.sort_values("이름").reset_index(drop=True)
        grade4_df = grade4_df[["번호", "이름", "성별", "3학년 학급"]]
        st.dataframe(
            grade4_df.style.apply(highlight_duplicate_names, axis=None),
            use_container_width=True,
            hide_index=True,
        )
