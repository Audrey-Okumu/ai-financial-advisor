import streamlit as st
import pandas as pd
import plotly.express as px
import google.genai as genai  
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="PesaSmart AI Advisor",
    page_icon="💰",
    layout="wide"
)

st.title("💰 PesaSmart: AI Personal Financial Advisor")
st.markdown("""
**Helping Kenyan students and diaspora manage money smarter**  
""")

# ====================== GEMINI API KEY SETUP ======================
api_key = (
    os.getenv("GEMINI_API_KEY") 
    or st.secrets.get("GEMINI_API_KEY")
)

if not api_key:
    api_key = st.text_input(
        "Enter your Gemini API Key (from Google AI Studio)", 
        type="password"
    )

if not api_key:
    st.warning("❌ Gemini API key is required. Add `GEMINI_API_KEY` to your `.env` file or in Streamlit Secrets.")
    st.stop()

# Configure the new GenAI client
client = genai.Client(api_key=api_key)

# ====================== SESSION STATE ======================
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Category", "Amount"])

# ====================== MAIN INPUTS ======================
col1, col2, col3 = st.columns(3)

with col1:
    income = st.number_input("Monthly Income (KES)", 
                             min_value=0.0, 
                             value=45000.0, 
                             step=500.0)

with col2:
    savings_goal = st.number_input("Monthly Savings Goal (KES)", 
                                   min_value=0.0, 
                                   value=8000.0, 
                                   step=500.0)

with col3:
    current_month = datetime.now().strftime("%B %Y")

# ====================== ADD EXPENSE ======================
st.subheader("➕ Add New Expense")

category = st.selectbox(
    "Expense Category",
    ["Food & Groceries", "Transport", "Rent/Housing", "Education/HELB", 
     "Airtime & Data", "Entertainment", "Health", "Shopping", "Other"]
)

amount = st.number_input("Amount (KES)", min_value=0.0, step=100.0)

if st.button("Add Expense", type="primary"):
    if amount > 0:
        new_row = pd.DataFrame({"Category": [category], "Amount": [amount]})
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
        st.success(f"✅ Added **{category}**: KES {amount:,.0f}")
    else:
        st.error("Amount must be greater than zero.")

# ====================== EXPENSES DISPLAY & MANAGEMENT ======================
st.subheader(f"📊 Your Expenses - {current_month}")

if not st.session_state.expenses.empty:
    edited_df = st.data_editor(
        st.session_state.expenses,
        num_rows="dynamic",
        width="stretch",                    # Fixed deprecation
        key="expenses_editor",
        hide_index=True,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=["Food & Groceries", "Transport", "Rent/Housing", "Education/HELB", 
                        "Airtime & Data", "Entertainment", "Health", "Shopping", "Other"],
                required=True
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount (KES)",
                min_value=0,
                format="%.0f"
            )
        }
    )

    if not edited_df.equals(st.session_state.expenses):
        st.session_state.expenses = edited_df.reset_index(drop=True)

    total_spent = st.session_state.expenses['Amount'].sum()
    remaining = income - total_spent

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Total Spent", f"KES {total_spent:,.0f}")
    with col_b:
        st.metric("Remaining Money", f"KES {remaining:,.0f}",
                  delta=f"KES {abs(remaining):,.0f}" if remaining < 0 else None)
    with col_c:
        progress = min(max((remaining / savings_goal) * 100, 0), 100) if savings_goal > 0 else 0
        st.metric("Savings Goal Progress", f"{progress:.0f}%", 
                  delta=f"Short by KES {(savings_goal - remaining):,.0f}" if remaining < savings_goal else "On Track ✅")

    fig = px.pie(
        st.session_state.expenses, 
        names="Category", 
        values="Amount", 
        title="Spending Breakdown by Category"
    )
    st.plotly_chart(fig, width="stretch")   # Fixed deprecation

    # Warnings
    if remaining < 0:
        st.error("🚨 **Overspending Alert!** You have gone over your income.")
    elif remaining < savings_goal * 0.3:
        st.warning("⚠️ **Critical Low Balance Warning** — You are at risk of missing your savings goal.")
    elif remaining < savings_goal:
        st.info("💡 You are close to your savings goal. Consider reducing discretionary spending.")

    # ====================== AI ADVICE ======================
    if st.button("🤖 Get Personalized AI Advice from PesaSmart", type="primary", key="ai_btn"):
        with st.spinner("Generating advice using Gemini..."):
            expenses_summary = st.session_state.expenses.groupby('Category')['Amount'].sum().to_dict()

            prompt = f"""
            You are PesaSmart, a friendly and practical Kenyan financial advisor.

            User Information:
            - Monthly Income: KES {income:,.0f}
            - Total Spent: KES {total_spent:,.0f}
            - Remaining: KES {remaining:,.0f}
            - Savings Goal: KES {savings_goal:,.0f}
            - Month: {current_month}
            - Expenses: {expenses_summary}

            Give short, actionable, encouraging advice in 5-7 bullet points.
            Focus on high-spending categories, protecting savings, and realistic Kenyan tips (HELB, M-Pesa, etc.).
            Keep tone positive and motivating.
            """

            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                st.success("### 💡 PesaSmart AI Advice")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error generating advice: {str(e)}")

else:
    st.info("Add at least one expense to see analysis and AI advice.")

# ====================== FOOTER ======================
st.markdown("---")
st.markdown("""

This AI-powered financial advisor demonstrates building intelligent agents for financial reporting automation, budgeting, and advisory services.
""")