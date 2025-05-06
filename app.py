import streamlit as st
import tempfile
import os
import matplotlib.pyplot as plt
import pandas as pd
from utils.processor import analyze_audits
from fpdf import FPDF

st.set_page_config(page_title="Audit Insights Pro", layout="wide")

st.title("📋 Audit Insights Pro")
st.markdown("Upload 2 to 4 audit reports in PDF format. The app will summarize each and compare findings.")
st.info("👆 Please upload 2 to 4 PDF audit reports to begin.")

uploaded_files = st.file_uploader("Upload PDF audit reports", type="pdf", accept_multiple_files=True)

if uploaded_files and 2 <= len(uploaded_files) <= 4:
    with st.spinner("Analyzing audits with AI..."):
        temp_paths, filenames = [], []
        for file in uploaded_files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(file.read())
            temp_file.close()
            temp_paths.append(temp_file.name)
            filenames.append(file.name)

        try:
            result = analyze_audits(temp_paths, filenames)
        except Exception as e:
            st.error(f"❌ Error during analysis: {e}")
            st.stop()

        summaries = result["summaries"]
        logos = result["logos"]
        themes = result["themes"]
        comparison = result["comparison"]
        learnings = result["learnings"]

        st.subheader("📝 Audit Summaries")
        for i, summary in enumerate(summaries):
            lines = summary.split("\n")
            audit_topic = next((l for l in lines if "Audit Topic" in l), "Audit Topic: Unknown")
            findings = next((l for l in lines if "Findings" in l), "Findings: N/A")
            recommendations = next((l for l in lines if "Measures" in l or "Recommendations" in l), "Recommendations: N/A")
            st.markdown(f"""
            <div style='background-color:#f0f2f6;padding:8px;border-left:5px solid #0066cc;margin-bottom:10px;font-family:monospace;'>
            <ul>
                <li><strong>{filenames[i]}</strong></li>
                <li>{findings}</li>
                <li>{recommendations}</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📄 Full Summary: {filenames[i]}"):
                if logos[i] and os.path.exists(logos[i]):
                    st.image(logos[i], width=120)
                st.text_area("Full Summary", summary, height=250)
                text_file = os.path.join(tempfile.gettempdir(), f"{filenames[i]}.txt")
                with open(text_file, "w") as f:
                    f.write(summary)
                st.download_button("⬇ Download This Summary (.txt)", open(text_file, "rb"), file_name=f"{filenames[i]}.txt")

        st.subheader("📊 Common Audit Themes")
        theme_flat = [item for sublist in themes for item in sublist]
        theme_counts = pd.Series(theme_flat).value_counts()
        fig, ax = plt.subplots()
        theme_counts.plot(kind='barh', ax=ax, color="#1f77b4")
        plt.xlabel("Frequency")
        plt.ylabel("Audit Themes")
        st.pyplot(fig)

        st.subheader("🔍 Comparison of Audits")
        st.text(comparison)

        st.subheader("💡 Key Learnings for Future Audits")
        st.text(learnings)

        def create_final_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Audit Insights Summary", ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            for i, summary in enumerate(summaries):
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f"Audit: {filenames[i]}", ln=True)
                if logos[i] and os.path.exists(logos[i]):
                    try:
                        pdf.image(logos[i], w=50)
                    except:
                        pass
                pdf.set_font("Arial", '', 11)
                for line in summary.split("\n"):
                    pdf.multi_cell(0, 8, line)
            pdf.set_font("Arial", 'B', 12)
            pdf.ln(5)
            pdf.cell(0, 10, "Comparison:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 8, comparison)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Learnings:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 8, learnings)
            pdf_path = os.path.join(tempfile.gettempdir(), "audit_summary_all.pdf")
            pdf.output(pdf_path)
            return pdf_path

        final_pdf = create_final_pdf()
        st.download_button("📥 Download Full Summary as PDF", open(final_pdf, "rb"), file_name="audit_summary_all.pdf")

else:
    st.warning("Please upload 2 to 4 PDF audit reports.")
