import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os
from dotenv import load_dotenv

#######################################
# PAGE SETUP
#######################################
st.set_page_config(
    page_title="AccuCheck",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AccuCheck")
st.caption("Prototype v2.0 - Rule-based & AI Commentary + Chat Mode")

#######################################
# LOAD API KEY (Optional: GROQ)
#######################################
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

#######################################
# AI COMMENTARY FUNCTION
#######################################
def generate_ai_commentary(region_sales: pd.DataFrame) -> str:
    """
    Generate AI-based commentary using Groq LLM.
    Jika API Key tidak tersedia, fungsi akan menampilkan pesan peringatan.
    """
    if not client:
        return "⚠️ AI Commentary tidak aktif (API Key belum diatur)."

    # Ubah data menjadi teks agar bisa dianalisis oleh LLM
    text_summary = region_sales.to_string(index=False)

    prompt = f"""
    Berikut adalah data penjualan per region:
    {text_summary}

    Sebagai analis bisnis, buat analisis singkat dalam bahasa Indonesia:
    1. Region mana yang paling dominan
    2. Region mana yang perlu perhatian
    3. Insight strategis singkat untuk manajemen
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error AI Commentary: {e}"

#######################################
# DATA UPLOAD
#######################################
uploaded_file = st.file_uploader(
    "📂 Upload file Excel / CSV",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file:
    # Baca file sesuai format
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    #######################################
    # DATA PREVIEW
    #######################################
    st.subheader("📜 Data Preview")
    st.dataframe(df.head())

    #######################################
    # VALIDASI KOLOM
    #######################################
    if not {"Region", "Sales"}.issubset(df.columns):
        st.warning("⚠️ Data harus memiliki kolom `Region` dan `Sales`.")
        st.stop()

    #######################################
    # DASHBOARD AGGREGATION (DuckDB)
    #######################################
    st.subheader("📈 Dashboard Overview")

    query = """
        SELECT 
            Region,
            SUM(Sales) AS Total_Sales
        FROM df
        GROUP BY Region
        ORDER BY Total_Sales DESC
    """
    region_sales = duckdb.sql(query).df()

    #######################################
    # VISUALIZATION (Plotly)
    #######################################
    fig = px.bar(
        region_sales,
        x="Region",
        y="Total_Sales",
        title="Sales by Region",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

    #######################################
    # RULE-BASED COMMENTARY
    #######################################
    st.subheader("📝 Auto Commentary (Rule-based)")

    top_region = region_sales.iloc[0]["Region"]
    top_value = region_sales.iloc[0]["Total_Sales"]

    bottom_region = region_sales.iloc[-1]["Region"]
    bottom_value = region_sales.iloc[-1]["Total_Sales"]

    gap_value = top_value - bottom_value

    rule_commentary = f"""
    🔍 **Insight Utama**:
    - Region dengan penjualan tertinggi adalah **{top_region}** sebesar **{top_value:,.0f}**.
    - Region dengan penjualan terendah adalah **{bottom_region}** sebesar **{bottom_value:,.0f}**.
    - Selisih (gap) antara region tertinggi dan terendah adalah **{gap_value:,.0f}**.
    """

    st.markdown(rule_commentary)

    #######################################
    # AI COMMENTARY
    #######################################
    st.subheader("🤖 AI Commentary")
    ai_text = generate_ai_commentary(region_sales)
    st.write(ai_text)

    #######################################
    # AI CHAT MODE
    #######################################
    st.subheader("💬 Chat dengan AI Analis")

    # Inisialisasi chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": "Anda adalah analis bisnis yang membantu memahami data penjualan."
            },
            {
                "role": "assistant",
                "content": ai_text
            }
        ]

    # Tampilkan riwayat chat
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # Input chat baru
    if question := st.chat_input("Tanyakan sesuatu tentang data penjualan..."):
        st.session_state.chat_history.append(
            {"role": "user", "content": question}
        )
        st.chat_message("user").write(question)

        if client:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.chat_history,
                    temperature=0.7
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"❌ Error chat AI: {e}"
        else:
            answer = "⚠️ AI Chat tidak aktif (API Key belum diatur)."

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )
        st.chat_message("assistant").write(answer)

else:
    st.info("⬆️ Upload file Excel/CSV untuk memulai analisis.")
