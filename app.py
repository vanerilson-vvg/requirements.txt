import streamlit as st
import pandas as pd
import requests
import time
import mplfinance as mpf

st.set_page_config(page_title="Radar Fast", layout="wide")

def obter_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=3)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['Date'] = pd.to_datetime(r['timestamp'], unit='s')
        return df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close'}).set_index('Date').dropna()
    except: return None

st.title("⚡ Radar Forex Real-Time")
aviso = st.empty()
col_graf, col_tec = st.columns([1.2, 1])

while True:
    df = obter_dados("1m")
    df5 = obter_dados("5m")
    if df is not None:
        preco = df['Close'].iloc[-1]
        aviso.metric("EUR/USD", f"{preco:.5f}")
        
        with col_graf:
            st.subheader("Tendência M5")
            fig, _ = mpf.plot(df5.tail(30), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig)

        with col_tec:
            st.subheader("Análise Técnica")
            ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
            sinal = "🟢 COMPRA" if preco > ema9 else "🔴 VENDA"
            st.table(pd.DataFrame({"Indicador": ["Preço vs Média", "Tendência"], "Sinal": [sinal, "ALTA" if preco > ema9 else "QUEDA"]}))

    time.sleep(2)
    st.rerun()
