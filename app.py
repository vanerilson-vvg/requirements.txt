import streamlit as st
import pandas as pd
import requests
import time
import pandas_ta as ta
import mplfinance as mpf

st.set_page_config(page_title="Radar Monitor Elite", layout="wide")

def obter_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['Date'] = pd.to_datetime(r['timestamp'], unit='s')
        return df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close'}).set_index('Date').dropna()
    except:
        return None

def analisar(df):
    if df is None or len(df) < 20:
        return None
    c = df['Close']
    ema9 = ta.ema(c, length=9)
    rsi = ta.rsi(c, length=14)
    def s(cond_c, cond_v):
        if cond_c: return "🟢 COMPRA"
        if cond_v: return "🔴 VENDA"
        return "⚪ NEUTRO"
    return [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("RSI (14)", s(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70))
    ]

# --- Interface na Ordem Solicitada ---
st.title("🛡️ MONITOR EUR/USD")
espaco_dados = st.empty()
st.markdown("---")
espaco_grafico = st.empty()

while True:
    df1 = obter_dados("1m")
    df5 = obter_dados("5m")
    if df1 is not None and df5 is not None:
        with espaco_dados.container():
            st.metric("PREÇO ATUAL", f"{df1['Close'].iloc[-1]:.5f}")
            s1, s5 = analisar(df1), analisar(df5)
            if s1 and s5:
                st.table(pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                }))
        with espaco_grafico.container():
            st.subheader("📊 Tendência Visual M5")
            fig, _ = mpf.plot(df5.tail(35), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig)
    time.sleep(2)
    st.rerun()
