import streamlit as st
import fitz  # pymupdf

from ai_matcher import compare_resume

st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="📄",
    layout="centered",
)

st.title("📄 AI Resume Matcher")
st.write("Compare any resume with any job description.")

resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

job_description = st.text_area(
    "Paste Job Description",
    height=250,
    placeholder="Paste the complete job description here...",
)

use_ai = st.checkbox(
    "Also use AI for extra requirements not in my skill list (slower)",
    value=True,
)

if st.button("Analyze Resume", type="primary"):

    if resume_file is None:
        st.error("Please upload a resume.")

    elif not job_description.strip():
        st.error("Please enter a job description.")

    else:
        try:
            with st.spinner("Analyzing..."):
                pdf = fitz.open(stream=resume_file.getvalue(), filetype="pdf")
                resume_text = "\n".join(page.get_text() for page in pdf)
                pdf.close()
                st.expander("Extracted resume text").text(resume_text[:1500])

                if not resume_text.strip():
                    st.error(
                        "No readable text in this PDF. "
                        "Scanned resumes need OCR."
                    )
                    st.stop()

                result = compare_resume(resume_text, job_description, use_ai)

            st.success("Analysis completed!")
            st.divider()

            st.subheader("📊 Resume Match Percentage")
            score = result["match_percentage"]
            st.metric("Job Description Match", f"{score}%")
            st.progress(min(score / 100, 1.0))

            if result["ai_error"]:
                st.warning(
                    "AI step was skipped (is Ollama running?). "
                    "Results use the rule-based check only."
                )

            st.divider()
            st.subheader("✅ Matched Skills")
            if result["matched_skills"]:
                for skill in result["matched_skills"]:
                    proof = result["evidence"].get(skill, "")
                    ai_tag = " 🤖" if skill in result["ai_checked"] else ""
                    st.success(f"{skill}{ai_tag}  —  found: {proof}")
            else:
                st.info("No matching requirements found.")

            st.divider()
            st.subheader("❌ Missing Skills")
            if result["missing_skills"]:
                for skill in result["missing_skills"]:
                    st.error(skill)
            else:
                st.success("No missing requirements!")

        except Exception as e:
            st.error(f"Analysis failed: {e}")