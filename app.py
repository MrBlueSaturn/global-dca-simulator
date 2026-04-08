import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. Page Config & Custom CSS (UI Upgrade)
# ==========================================
st.set_page_config(page_title="Pro Portfolio & DCA Simulator", page_icon="🏦", layout="wide")

# ใส่ CSS ตกแต่งให้ดูเป็นแอปการเงินระดับพรีเมียม
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00B4D8;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    .metric-title { color: #A0AEC0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;}
    .metric-value { color: #FFFFFF; font-size: 28px; font-weight: bold; margin-top: 5px;}
    .green-text { color: #00FF7F !important; }
    .red-text { color: #FF4500 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Asset Database & Localization
# ==========================================
lang = st.sidebar.radio("🌐 Language", ["ไทย", "English"])

# Dictionary หุ้นยอดฮิต (ลดความยาวโค้ดลงมาให้แสดงผลได้เร็วขึ้น แต่ครอบคลุม)
assets_db = {
    "🇺🇸 S&P 500 (VOO)": "VOO", "🇺🇸 NASDAQ 100 (QQQ)": "QQQ", "🌍 All-World (VT)": "VT",
    "🇯🇵 Nikkei 225 (^N225)": "^N225", "🇯🇵 Toyota (7203.T)": "7203.T", "🇯🇵 Sony (6758.T)": "6758.T",
    "🍎 Apple (AAPL)": "AAPL", "🤖 NVIDIA (NVDA)": "NVDA", "🇹🇭 SET50 (^SET50.BK)": "^SET50.BK",
    "🟡 Gold (GLD)": "GLD", "🪙 Bitcoin (BTC-USD)": "BTC-USD"
}

# ==========================================
# 3. Sidebar UI
# ==========================================
st.sidebar.markdown("---")
monthly_invest = st.sidebar.number_input("💵 เงินลงทุนรายเดือน (บาท)" if lang=="ไทย" else "Monthly Investment", min_value=1000, value=5000, step=1000)
years = st.sidebar.slider("📅 ดูข้อมูลย้อนหลัง (ปี)" if lang=="ไทย" else "Historical Years", 1, 20, 5)

st.sidebar.markdown("---")
selected_assets = st.sidebar.multiselect(
    "🔍 เลือกสินทรัพย์เปรียบเทียบ" if lang=="ไทย" else "Select Assets",
    options=list(assets_db.keys()),
    default=["🇺🇸 S&P 500 (VOO)", "🪙 Bitcoin (BTC-USD)"]
)

# ==========================================
# 4. Main App Header
# ==========================================
st.title("🏦 Pro Portfolio Strategy & DCA Simulator")
st.markdown("แพลตฟอร์มวิเคราะห์การลงทุนระดับ Enterprise พร้อมระบบคาดการณ์อนาคตด้วย Monte Carlo Simulation" if lang=="ไทย" else "Enterprise-grade investment analysis platform with Monte Carlo future projections.")

# ==========================================
# 5. Core Logic (Data Fetching & Finance Math)
# ==========================================
end_date = datetime.today()
start_date = end_date - timedelta(days=years * 365)

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            return data['Close'].iloc[:, 0].resample('ME').last()
        return data['Close'].resample('ME').last()
    except:
        return None

if selected_assets:
    # สร้าง Tabs โมเดิร์นๆ
    tab_hist, tab_metrics, tab_future, tab_data = st.tabs([
        "📈 การเติบโตในอดีต (Historical)", 
        "🧠 วิเคราะห์เชิงลึก (Advanced Metrics)", 
        "🔮 พยากรณ์อนาคต (Monte Carlo)", 
        "💾 ดาวน์โหลดข้อมูล (Data)"
    ])
    
    with st.spinner("Analyzing market data..." if lang=="English" else "กำลังประมวลผลข้อมูลตลาดระดับลึก..."):
        fig_hist = go.Figure()
        results = []
        raw_dict = {}
        baseline_x, baseline_y = None, None
        
        # Risk-free rate สมมติที่ 3% ต่อปี สำหรับคำนวณ Sharpe Ratio
        risk_free_rate = 0.03 

        for asset in selected_assets:
            prices = fetch_data(assets_db[asset])
            
            if prices is not None:
                df = prices.dropna().to_frame(name='Price')
                
                # --- Basic DCA Math ---
                df['Shares'] = monthly_invest / df['Price']
                df['Total_Shares'] = df['Shares'].cumsum()
                df['Invested'] = [monthly_invest * i for i in range(1, len(df) + 1)]
                df['Value'] = df['Total_Shares'] * df['Price']
                
                raw_dict[asset] = df['Value']
                
                # เก็บเส้นเงินต้น
                if baseline_x is None or len(df) > len(baseline_x):
                    baseline_x, baseline_y = df.index, df['Invested']
                
                fig_hist.add_trace(go.Scatter(x=df.index, y=df['Value'], mode='lines', name=asset, hovertemplate="<b>%{x|%b %Y}</b><br>Value: ฿%{y:,.0f}<extra></extra>"))
                
                # --- Advanced Finance Math ---
                final_val = df['Value'].iloc[-1]
                total_inv = df['Invested'].iloc[-1]
                profit = final_val - total_inv
                roi = (profit / total_inv) * 100
                
                # 1. CAGR (Compound Annual Growth Rate)
                years_actual = len(df) / 12
                cagr = ((final_val / total_inv) ** (1 / years_actual) - 1) * 100 if years_actual > 0 else 0
                
                # 2. Monthly Returns & Annualized Volatility
                df['Return'] = df['Value'].pct_change()
                volatility = df['Return'].std() * np.sqrt(12) * 100 # Annualized
                
                # 3. Sharpe Ratio (ผลตอบแทนเทียบกับความเสี่ยง)
                annual_return = df['Return'].mean() * 12
                sharpe = (annual_return - risk_free_rate) / (df['Return'].std() * np.sqrt(12)) if df['Return'].std() > 0 else 0
                
                # 4. Max Drawdown
                df['Peak'] = df['Value'].cummax()
                mdd = ((df['Value'] - df['Peak']) / df['Peak']).min() * 100
                
                results.append({
                    "Asset": asset, "Invested": total_inv, "Value": final_val, 
                    "ROI (%)": roi, "CAGR (%)": cagr, "Volatility (%)": volatility, 
                    "Sharpe Ratio": sharpe, "Max Drawdown (%)": mdd
                })
        
        # ==========================================
        # TAB 1: Historical Performance
        # ==========================================
        with tab_hist:
            if baseline_x is not None:
                fig_hist.add_trace(go.Scatter(x=baseline_x, y=baseline_y, mode='lines', name='เงินต้น (Cash)', line=dict(color='white', dash='dot')))
            
            fig_hist.update_layout(title="Historical Portfolio Value", template="plotly_dark", hovermode="x unified", height=500)
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # โชว์ Metric Cards สุดเท่สำหรับตัวที่ผลตอบแทนสูงสุด
            if results:
                best_asset = max(results, key=lambda x: x['ROI (%)'])
                col1, col2, col3 = st.columns(3)
                col1.markdown(f'<div class="metric-card"><div class="metric-title">🏆 Top Performer</div><div class="metric-value">{best_asset["Asset"].split()[1]}</div></div>', unsafe_allow_html=True)
                col2.markdown(f'<div class="metric-card"><div class="metric-title">💰 Max Value</div><div class="metric-value green-text">฿ {best_asset["Value"]:,.0f}</div></div>', unsafe_allow_html=True)
                col3.markdown(f'<div class="metric-card"><div class="metric-title">📈 Total ROI</div><div class="metric-value green-text">+{best_asset["ROI (%)"]:,.1f}%</div></div>', unsafe_allow_html=True)
                st.write("")

        # ==========================================
        # TAB 2: Advanced Metrics (Institutional Grade)
        # ==========================================
        with tab_metrics:
            st.subheader("Deep Financial Analysis")
            df_res = pd.DataFrame(results)
            
            # Formatting
            df_format = df_res.copy()
            df_format['Invested'] = df_format['Invested'].apply(lambda x: f"฿{x:,.0f}")
            df_format['Value'] = df_format['Value'].apply(lambda x: f"฿{x:,.0f}")
            df_format['ROI (%)'] = df_format['ROI (%)'].apply(lambda x: f"{x:+.2f}%")
            df_format['CAGR (%)'] = df_format['CAGR (%)'].apply(lambda x: f"{x:.2f}%")
            df_format['Volatility (%)'] = df_format['Volatility (%)'].apply(lambda x: f"{x:.2f}%")
            df_format['Sharpe Ratio'] = df_format['Sharpe Ratio'].apply(lambda x: f"{x:.2f}")
            df_format['Max Drawdown (%)'] = df_format['Max Drawdown (%)'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(df_format, use_container_width=True, hide_index=True)
            
            with st.expander("📚 อธิบายความหมายของตัวชี้วัด (Metrics Explanation)"):
                st.markdown("""
                * **CAGR:** อัตราการเติบโตเฉลี่ยทบต้นต่อปี (บอกว่าพอร์ตโตเฉลี่ยปีละกี่เปอร์เซ็นต์)
                * **Volatility:** ความผันผวนของราคา (ยิ่งสูง ยิ่งสวิงแรง)
                * **Sharpe Ratio:** ประสิทธิภาพในการบริหารความเสี่ยง (ยิ่งสูงยิ่งดี ควร > 1.0)
                * **Max Drawdown:** ช่วงที่ขาดทุนหนักที่สุดจากจุดสูงสุด (วัดว่าทนความเจ็บปวดได้แค่ไหน)
                """)

        # ==========================================
        # TAB 3: Monte Carlo Future Simulation
        # ==========================================
        with tab_future:
            st.subheader("🔮 10-Year Future Projection (Monte Carlo)")
            st.write("จำลองอนาคต 10 ปีข้างหน้า ด้วยการสุ่มทิศทางตลาด 50 รูปแบบ (อ้างอิงจากความผันผวนในอดีตของแต่ละสินทรัพย์)")
            
            if len(selected_assets) > 0:
                target = st.selectbox("เลือกสินทรัพย์เพื่อจำลองอนาคต:", selected_assets)
                target_data = next(item for item in results if item["Asset"] == target)
                
                # ดึง Volatility และ CAGR รายเดือนมาจำลอง
                mu = (target_data['CAGR (%)'] / 100) / 12
                vol = (target_data['Volatility (%)'] / 100) / np.sqrt(12)
                
                months_future = 12 * 10 # 10 years
                simulations = 50
                last_value = target_data['Value']
                
                sim_results = np.zeros((months_future, simulations))
                sim_results[0] = last_value
                
                for t in range(1, months_future):
                    random_shocks = np.random.normal(mu, vol, simulations)
                    # จำลองการเติบโต + เงินลงทุน DCA เพิ่มเข้าไปทุกเดือน
                    sim_results[t] = sim_results[t-1] * (1 + random_shocks) + monthly_invest
                
                fig_mc = go.Figure()
                for i in range(simulations):
                    fig_mc.add_trace(go.Scatter(y=sim_results[:, i], mode='lines', line=dict(color='rgba(0,180,216,0.1)'), showlegend=False))
                
                # เพิ่มเส้นค่าเฉลี่ย
                fig_mc.add_trace(go.Scatter(y=np.mean(sim_results, axis=1), mode='lines', name='Expected Average', line=dict(color='yellow', width=3)))
                
                fig_mc.update_layout(title=f"จำลองอนาคต 10 ปีของ {target}", xaxis_title="เดือนที่ (Months)", yaxis_title="มูลค่าพอร์ต (THB)", template="plotly_dark")
                st.plotly_chart(fig_mc, use_container_width=True)

        # ==========================================
        # TAB 4: Raw Data & Export
        # ==========================================
        with tab_data:
            if raw_dict:
                export_df = pd.DataFrame(raw_dict)
                export_df.index = export_df.index.strftime('%Y-%m')
                st.dataframe(export_df)
                st.download_button("💾 Download CSV", export_df.to_csv().encode('utf-8'), "pro_dca_data.csv", "text/csv")
else:
    st.info("👈 Please select assets from the sidebar to begin analysis.")
