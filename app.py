import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="Ultimate Global DCA Simulator", page_icon="🌍", layout="wide")

# ---------------------------------------------------------
# 2. Huge Asset Dictionary (100+ Assets)
# ---------------------------------------------------------
assets_db = {
    "🇺🇸 US Market ETFs": {
        "S&P 500 ETF (VOO)": "VOO", "SPDR S&P 500 (SPY)": "SPY", "NASDAQ 100 (QQQ)": "QQQ",
        "Total Stock Market (VTI)": "VTI", "Dividend Equity (SCHD)": "SCHD", "Dow Jones (DIA)": "DIA",
        "Russell 2000 (IWM)": "IWM", "Vanguard Growth (VUG)": "VUG", "Vanguard Value (VTV)": "VTV"
    },
    "🌍 Global & Regional ETFs": {
        "Total World Stock (VT)": "VT", "Total Intl Stock (VXUS)": "VXUS", 
        "Emerging Markets (VWO)": "VWO", "Developed Markets (VEA)": "VEA",
        "Japan ETF (EWJ)": "EWJ", "China ETF (MCHI)": "MCHI", "India ETF (INDA)": "INDA",
        "Europe ETF (VGK)": "VGK", "UK ETF (EWU)": "EWU", "Germany ETF (EWG)": "EWG"
    },
    "🇯🇵 Japan Top Stocks": {
        "Nikkei 225 Index": "^N225", "Toyota Motor": "7203.T", "Sony Group": "6758.T",
        "Mitsubishi UFJ": "8306.T", "Keyence": "6861.T", "Tokyo Electron": "8035.T",
        "SoftBank Group": "9984.T", "Nintendo": "7974.T", "Honda Motor": "7267.T",
        "Hitachi": "6501.T", "Shin-Etsu Chemical": "4063.T", "Takeda Pharma": "4502.T",
        "Itochu": "8001.T", "Mitsui & Co": "8031.T", "Fast Retailing (Uniqlo)": "9983.T"
    },
    "🇺🇸 US Tech & Mag 7": {
        "Apple (AAPL)": "AAPL", "Microsoft (MSFT)": "MSFT", "Alphabet (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN", "NVIDIA (NVDA)": "NVDA", "Meta (META)": "META",
        "Tesla (TSLA)": "TSLA", "Netflix (NFLX)": "NFLX", "AMD (AMD)": "AMD",
        "Intel (INTC)": "INTC", "Broadcom (AVGO)": "AVGO", "Qualcomm (QCOM)": "QCOM",
        "Salesforce (CRM)": "CRM", "Adobe (ADBE)": "ADBE", "Cisco (CSCO)": "CSCO"
    },
    "🇺🇸 US Finance & Health": {
        "JPMorgan Chase (JPM)": "JPM", "Visa (V)": "V", "Mastercard (MA)": "MA",
        "Bank of America (BAC)": "BAC", "Berkshire Hathaway (BRK-B)": "BRK-B",
        "UnitedHealth (UNH)": "UNH", "Johnson & Johnson (JNJ)": "JNJ",
        "Eli Lilly (LLY)": "LLY", "Pfizer (PFE)": "PFE", "AbbVie (ABBV)": "ABBV"
    },
    "🇹🇭 Thai Stocks (SET50)": {
        "SET Index": "^SET.BK", "PTT (PTT.BK)": "PTT.BK", "AOT (AOT.BK)": "AOT.BK",
        "CPALL (CPALL.BK)": "CPALL.BK", "ADVANC (ADVANC.BK)": "ADVANC.BK",
        "SCC (SCC.BK)": "SCC.BK", "BDMS (BDMS.BK)": "BDMS.BK", "GULF (GULF.BK)": "GULF.BK",
        "PTTEP (PTTEP.BK)": "PTTEP.BK", "KBANK (KBANK.BK)": "KBANK.BK",
        "SCB (SCB.BK)": "SCB.BK", "BBL (BBL.BK)": "BBL.BK", "EA (EA.BK)": "EA.BK",
        "MINT (MINT.BK)": "MINT.BK", "CRC (CRC.BK)": "CRC.BK"
    },
    "🟡 Commodities & Crypto": {
        "Gold Trust (GLD)": "GLD", "Silver Trust (SLV)": "SLV", "US Oil Fund (USO)": "USO",
        "Bitcoin (BTC-USD)": "BTC-USD", "Ethereum (ETH-USD)": "ETH-USD",
        "Solana (SOL-USD)": "SOL-USD", "Binance Coin (BNB-USD)": "BNB-USD",
        "Ripple (XRP-USD)": "XRP-USD", "Cardano (ADA-USD)": "ADA-USD",
        "Dogecoin (DOGE-USD)": "DOGE-USD", "Chainlink (LINK-USD)": "LINK-USD"
    }
}

# สร้าง List ของสินทรัพย์ทั้งหมด
all_assets_flat = {}
for category, assets in assets_db.items():
    for name, ticker in assets.items():
        all_assets_flat[f"{category.split(' ')[0]} {name}"] = ticker

# ---------------------------------------------------------
# 3. UI & Sidebar
# ---------------------------------------------------------
st.title("🌍 Ultimate Global Assets: Advanced DCA Simulator")
st.markdown("โปรแกรมจำลองผลตอบแทนการลงทุนระยะยาวแบบถัวเฉลี่ย (DCA) คลังข้อมูลหุ้น 100+ ตัวทั่วโลก (คำนวณกำไร/ขาดทุนแบบแม่นยำสูงด้วยข้อมูลรายวันแบบ Resample)")

st.sidebar.header("⚙️ การตั้งค่าพอร์ตลงทุน")
monthly_invest = st.sidebar.number_input("เงินลงทุนรายเดือน (บาท)", min_value=1, value=5000, step=1000)
years = st.sidebar.slider("ระยะเวลาลงทุนย้อนหลัง (ปี)", min_value=1, max_value=20, value=5)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 เลือกสินทรัพย์")

selected_assets = st.sidebar.multiselect(
    "พิมพ์ค้นหาหรือเลือกหุ้น/ETF/Crypto (เลือกได้หลายตัว)",
    options=list(all_assets_flat.keys()),
    default=["🇺🇸 S&P 500 ETF (VOO)", "🇯🇵 Nikkei 225 Index"]
)

# ---------------------------------------------------------
# 4. Core Logic & Data Fetching (FIXED & HIGH PRECISION)
# ---------------------------------------------------------
end_date = datetime.today()
start_date = end_date - timedelta(days=years * 365)

@st.cache_data(ttl=3600)
def fetch_and_process_data(ticker, start, end):
    try:
        # ดึงข้อมูล "รายวัน" เพื่อความแม่นยำสูงสุด แล้วค่อยจับกลุ่มหา "วันทำการสุดท้ายของเดือน"
        data = yf.download(ticker, start=start, end=end, interval="1d", progress=False)
        
        if data.empty:
            return None
            
        # จัดการโครงสร้างคอลัมน์ของ yfinance เวอร์ชั่นใหม่
        if isinstance(data.columns, pd.MultiIndex):
            close_prices = data['Close'].iloc[:, 0]
        else:
            close_prices = data['Close']
            
        # จับกลุ่มข้อมูลเป็นรายเดือน (ME = Month End) และเลือกราคาปิดวันสุดท้ายของเดือนนั้นๆ
        monthly_data = close_prices.resample('ME').last().dropna().to_frame(name='Price')
        return monthly_data
    except Exception as e:
        return None

# ---------------------------------------------------------
# 5. Dashboard Rendering
# ---------------------------------------------------------
if selected_assets:
    tab1, tab2 = st.tabs(["📈 แดชบอร์ดและกราฟวิเคราะห์", "📝 ข้อมูลดิบสำหรับ Excel (CSV)"])
    
    with st.spinner("กำลังเชื่อมต่อเซิร์ฟเวอร์ Yahoo Finance และคำนวณข้อมูลระดับ High-Precision..."):
        fig = go.Figure()
        results_data = []
        raw_data_dict = {}
        
        baseline_x = None
        baseline_y = None
        max_months = 0

        for asset in selected_assets:
            ticker_symbol = all_assets_flat[asset]
            df = fetch_and_process_data(ticker_symbol, start_date, end_date)
            
            if df is not None and not df.empty:
                # --- NEW HIGH-PRECISION PNL MATH ---
                # 1. บันทึกจำนวนเงินที่ลงทุนจริงในแต่ละเดือน
                df['Invested_This_Month'] = monthly_invest
                
                # 2. คำนวณจำนวนหน่วย (Shares) ที่ซื้อได้ในเดือนนั้น
                df['Shares_Bought'] = df['Invested_This_Month'] / df['Price']
                
                # 3. รวมจำนวนหน่วยสะสม
                df['Total_Shares'] = df['Shares_Bought'].cumsum()
                
                # 4. รวมเงินต้นสะสม (คำนวณตามจำนวนเดือนที่มีข้อมูลจริง)
                df['Total_Invested'] = df['Invested_This_Month'].cumsum()
                
                # 5. คำนวณมูลค่าพอร์ต (จำนวนหน่วยสะสม * ราคาปัจจุบันของเดือนนั้น)
                df['Portfolio_Value'] = df['Total_Shares'] * df['Price']
                
                # 6. วิเคราะห์ความเสี่ยง Maximum Drawdown
                df['Peak'] = df['Portfolio_Value'].cummax()
                df['Drawdown'] = (df['Portfolio_Value'] - df['Peak']) / df['Peak']
                max_drawdown = df['Drawdown'].min() * 100
                
                # จัดเก็บข้อมูลสำหรับ Export
                raw_data_dict[f"{asset} Value"] = df['Portfolio_Value']
                
                # วาดเส้นกราฟมูลค่าพอร์ต
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['Portfolio_Value'], 
                    mode='lines', name=asset,
                    hovertemplate="%{x|%b %Y}<br>มูลค่า: ฿%{y:,.0f}<extra></extra>"
                ))
                
                # เก็บเส้นอ้างอิงเงินต้น (เลือกตัวที่มีข้อมูลยาวที่สุด)
                if len(df) > max_months:
                    max_months = len(df)
                    baseline_x = df.index
                    baseline_y = df['Total_Invested']
                
                # จัดเตรียมข้อมูลลงตารางสรุป
                final_value = df['Portfolio_Value'].iloc[-1]
                total_invested = df['Total_Invested'].iloc[-1]
                profit = final_value - total_invested
                profit_pct = (profit / total_invested) * 100 if total_invested > 0 else 0
                
                results_data.append({
                    "สินทรัพย์": asset,
                    "เดือนที่ลงทุนจริง": len(df),
                    "เงินต้นสะสม": total_invested,
                    "มูลค่าพอร์ตปัจจุบัน": final_value,
                    "กำไร/ขาดทุนสุทธิ": profit,
                    "ผลตอบแทน (%)": profit_pct,
                    "Max Drawdown": max_drawdown
                })

        # --- Tab 1: Render Charts and Tables ---
        with tab1:
            if results_data:
                # วาดเส้นเงินต้นสะสม
                if baseline_x is not None:
                    fig.add_trace(go.Scatter(
                        x=baseline_x, y=baseline_y, 
                        mode='lines', name='เงินต้นสะสม (Total Cash)', 
                        line=dict(color='#A0AEC0', width=2, dash='dash'),
                        hovertemplate="%{x|%b %Y}<br>เงินต้น: ฿%{y:,.0f}<extra></extra>"
                    ))
                
                # ปรับแต่งกราฟ
                fig.update_layout(
                    title=f"การเติบโตของพอร์ตลงทุนย้อนหลัง {years} ปี (เปรียบเทียบตามจริง)",
                    xaxis_title="เวลา",
                    yaxis_title="มูลค่า (บาท)",
                    template="plotly_dark",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

                # ตารางสรุปผล
                st.subheader("📊 สรุปผลตอบแทนและความเสี่ยง (Performance Matrix)")
                summary_df = pd.DataFrame(results_data)
                
                # ฟอร์แมตตารางให้สวยงาม
                formatted_df = summary_df.copy()
                formatted_df["เงินต้นสะสม"] = formatted_df["เงินต้นสะสม"].apply(lambda x: f"฿ {x:,.0f}")
                formatted_df["มูลค่าพอร์ตปัจจุบัน"] = formatted_df["มูลค่าพอร์ตปัจจุบัน"].apply(lambda x: f"฿ {x:,.0f}")
                
                # ทำสีให้ตัวเลขกำไร/ขาดทุน
                formatted_df["กำไร/ขาดทุนสุทธิ"] = formatted_df["กำไร/ขาดทุนสุทธิ"].apply(
                    lambda x: f"🟢 ฿ {x:,.0f}" if x > 0 else f"🔴 ฿ {x:,.0f}"
                )
                formatted_df["ผลตอบแทน (%)"] = formatted_df["ผลตอบแทน (%)"].apply(
                    lambda x: f"🟢 +{x:,.2f}%" if x > 0 else f"🔴 {x:,.2f}%"
                )
                formatted_df["Max Drawdown"] = formatted_df["Max Drawdown"].apply(
                    lambda x: f"⚠️ {x:,.2f}%" if x < -20 else f"{x:,.2f}%"
                )
                
                # เรียงลำดับตามเปอร์เซ็นต์ผลตอบแทน
                formatted_df = formatted_df.sort_values(by="ผลตอบแทน (%)", ascending=False)
                
                st.dataframe(formatted_df, use_container_width=True, hide_index=True)
                st.caption("แหล่งข้อมูลอ้างอิง: ข้อมูลราคาปิดรายวันจาก **Yahoo Finance** ถูกนำมาแปลงเป็นความถี่รายเดือนเพื่อความแม่นยำในการคำนวณ DCA | โปรแกรมนี้จำลองผลตอบแทนโดยตัดตัวแปรด้านความผันผวนของอัตราแลกเปลี่ยน (FX Rate) ออก")

        # --- Tab 2: Export Data ---
        with tab2:
            st.subheader("💾 ตารางข้อมูลดิบ (Raw Data) และส่งออกไฟล์")
            st.markdown("ข้อมูลด้านล่างแสดง **มูลค่าพอร์ต (Portfolio Value)** ในแต่ละเดือน สามารถดาวน์โหลดไปวิเคราะห์ต่อใน Excel ได้")
            
            if raw_data_dict:
                export_df = pd.DataFrame(raw_data_dict)
                if baseline_x is not None:
                    export_df['Total Cash Invested'] = baseline_y.values
                
                export_df.index = export_df.index.strftime('%Y-%m')
                export_df = export_df.round(2)
                
                st.dataframe(export_df, use_container_width=True)
                
                csv_data = export_df.to_csv().encode('utf-8')
                st.download_button(
                    label="⬇️ Download CSV Data",
                    data=csv_data,
                    file_name=f'ultimate_dca_export_{years}yrs.csv',
                    mime='text/csv',
                )

else:
    st.info("👈 พิมพ์ค้นหาและเลือกสินทรัพย์ที่ต้องการเปรียบเทียบจากแถบด้านซ้ายมือได้เลยครับ")