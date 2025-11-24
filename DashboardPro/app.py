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
    page_title="📊 AI-Powered Dashboard Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 AI-Powered Dashboard Maker")
st.caption("Prototype v2.0 - Rule-based & AI Commentary + Chat Mode")

#######################################
# LOAD API (Optional Groq)
#######################################
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

#######################################
# AI Commentary Function
#######################################
def generate_ai_commentary(region_sales: pd.DataFrame) -> str:
    """Generate commentary with Groq LLM"""
    if not client:
        return "⚠️ AI Commentary tidak aktif (API Key belum diatur)."

    text_summary = region_sales.to_string(index=False)
    prompt = f"""
    Berikut adalah data penjualan per region:
    {text_summary}

    Buat analisis singkat dalam bahasa Indonesia:
    - Region mana yang dominan
    - Region mana yang perlu perhatian
    - Insight strategis singkat
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
uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📜 Data Preview")
    st.dataframe(df.head())

    #######################################
    # DASHBOARD
    #######################################
    st.subheader("📈 Dashboard Overview")

    if "Region" in df.columns and "Sales" in df.columns:
        query = """
        SELECT Region, SUM(Sales) as Total_Sales
        FROM df
        GROUP BY Region
        ORDER BY Total_Sales DESC
        """
        region_sales = duckdb.sql(query).df()

        # Bar chart
        fig = px.bar(region_sales, x="Region", y="Total_Sales",
                     title="Sales by Region", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        #######################################
        # RULE-BASED COMMENTARY
        #######################################
        st.subheader("📝 Auto Commentary (Rule-based)")

        top_region = region_sales.iloc[0]["Region"]
        top_value = region_sales.iloc[0]["Total_Sales"]

        bottom_region = region_sales.iloc[-1]["Region"]
        bottom_value = region_sales.iloc[-1]["Total_Sales"]

        commentary = f"""
        🔍 **Insights**:
        - Region dengan penjualan tertinggi adalah **{top_region}** sebesar **{top_value:,.0f}**.
        - Region dengan penjualan terendah adalah **{bottom_region}** sebesar **{bottom_value:,.0f}**.
        - Gap antara region tertinggi dan terendah adalah **{(top_value - bottom_value):,.0f}**.
        """
        st.markdown(commentary)

        #######################################
        # AI COMMENTARY (Initial)
        #######################################
        st.subheader("🤖 AI Commentary")
        ai_text = generate_ai_commentary(region_sales)
        st.write(ai_text)

        #######################################
        # AI CHAT MODE
        #######################################
        st.subheader("💬 Chat dengan AI Analis")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "system", "content": "Anda adalah analis bisnis yang membantu memahami data penjualan."},
                {"role": "assistant", "content": ai_text}  # mulai dengan hasil commentary
            ]

        # tampilkan riwayat chat
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            elif msg["role"] == "assistant":
                st.chat_message("assistant").write(msg["content"])

        # input pertanyaan baru
        if question := st.chat_input("Tanyakan sesuatu..."):
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.chat_message("user").write(question)

            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.chat_history,
                    temperature=0.7
                )
                answer = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.chat_message("assistant").write(answer)
            except Exception as e:
                st.error(f"❌ Error chat: {e}")

    else:
        st.warning("⚠️ Data harus memiliki kolom `Region` dan `Sales` untuk analisis.")
else:
    st.info("⬆️ Upload file Excel/CSV untuk memulai.")
