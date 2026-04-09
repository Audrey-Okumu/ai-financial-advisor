import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
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
Built as preparation for the **Vunoh Global AI Internship**
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

# Configure Gemini
genai.configure(api_key=api_key)

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
    # Editable table with delete support
    edited_df = st.data_editor(
        st.session_state.expenses,
        num_rows="dynamic",          # Allows adding rows from the table too
        use_container_width=True,
        key="expenses_editor",       # Critical for session state persistence
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

    # Update session state when user edits or deletes rows
    if not edited_df.equals(st.session_state.expenses):
        st.session_state.expenses = edited_df.reset_index(drop=True)

    total_spent = st.session_state.expenses['Amount'].sum()
    remaining = income - total_spent

    # Metrics
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

    # Pie Chart
    fig = px.pie(
        st.session_state.expenses, 
        names="Category", 
        values="Amount", 
        title="Spending Breakdown by Category"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Rule-based Warnings
    if remaining < 0:
        st.error("🚨 **Overspending Alert!** You have gone over your income.")
    elif remaining < savings_goal * 0.3:
        st.warning("⚠️ **Critical Low Balance Warning** — You are at risk of missing your savings goal.")
    elif remaining < savings_goal:
        st.info("💡 You are close to your savings goal. Consider reducing discretionary spending.")

    # ====================== AI ADVICE SECTION ======================
    if st.button("🤖 Get Personalized AI Advice from PesaSmart", type="primary"):
        with st.spinner("Generating intelligent financial advice using Gemini..."):
            expenses_summary = st.session_state.expenses.groupby('Category')['Amount'].sum().to_dict()

            prompt = f"""
            You are PesaSmart, a friendly and practical Kenyan financial advisor.
            
            User Information:
            - Monthly Income: KES {income:,.0f}
            - Total Spent: KES {total_spent:,.0f}
            - Money Remaining: KES {remaining:,.0f}
            - Savings Goal: KES {savings_goal:,.0f}
            - Current Month: {current_month}
            - Expense Breakdown: {expenses_summary}

            Provide **short, actionable, and encouraging advice** in 5-7 bullet points.
            Focus on:
            - Immediate steps to improve the situation
            - Specific suggestions for high-spending categories
            - How to protect or achieve the savings goal
            - Realistic tips relevant to Kenyan students or diaspora (mention HELB, M-Pesa, etc.)
            Keep the tone positive, realistic, and motivating.
            """

            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(prompt)
                st.success("### 💡 PesaSmart AI Advice")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Failed to generate advice: {str(e)}")
                st.info("Tip: Check your Gemini API key and internet connection.")

else:
    st.info("Add at least one expense above to see analysis, charts, and AI advice.")

# ====================== FOOTER ======================
st.markdown("---")
st.markdown("""  
This AI-powered financial advisor demonstrates building intelligent agents for **financial reporting automation**, budgeting, and advisory services.
""")

