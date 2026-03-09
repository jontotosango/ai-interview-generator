import streamlit as st

st.title("AI Interview Generator")

job_description = st.text_area("Job description")

cv_file = st.file_uploader("Upload CV", type=["pdf"])

if st.button("Generate Interview"):
    st.write("Job description:")
    st.write(job_description)

    if cv_file:
        st.success("CV uploaded successfully")
    else:
        st.warning("Please upload a CV")