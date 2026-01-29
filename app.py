import streamlit as st
import pandas as pd
import requests
import time
import pandas_ta as ta
from datetime import datetime

st.set_page_config(page_title="Monitor Elite", layout="wide")

def pegar_dados(tempo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={tempo}&range=1d"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5).json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['Date'] = pd.to_datetime(r['timestamp'], unit='s')
        return df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close'}).set_index('Date').dropna()
    except: return None

def calcular_sinal(df):
    if df is None or len(df) < 40: return None
    c, h, l = df['Close'], df['High'], df['Low']
    # Cálculos Técnicos
    rsi = ta.rsi(c, 14).iloc[-1]
    macd = ta.macd(c).iloc[-1]
    stoch = ta.stoch(h, l, c).iloc[-1]
    ema9, ema21 = ta.ema(c, 9).iloc[-1], ta.ema(c, 21).iloc[-1]
    bb = ta.bbands(c, 20).iloc[-1]
    # Lógica de Sinais
    def s(compra, venda):
        if compra: return "🟢 COMPRA"
        if venda: return "🔴 VENDA"
        return "⚪ NEUTRO"
    # Lista de 10 Indicadores
    return [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9, c.iloc[-1] < ema9)),
        ("Média (EMA 21)", s(c.iloc[-1] > ema21, c.iloc[-1] < ema21)),
        ("RSI (14)", s(rsi < 30, rsi > 70)),
        ("MACD", s(macd.iloc[0] > macd.iloc[2], macd.iloc[0] < macd.iloc[2])),
        ("Estocástico", s(stoch.iloc[0] < 20, stoch.iloc[0] > 80)),
        ("Bollinger", s(c.iloc[-1] < bb.iloc[0], c.iloc[-1] > bb.iloc[2])),
        ("Ichimoku", s(c.iloc[-1] > c.rolling(26).mean().iloc[-1], c.iloc[-1] < c.rolling(26).mean().iloc[-1])),
        ("Tendência", s(c.iloc[-1] > c.iloc[-10], c.iloc[-1] < c.iloc[-10])),
        ("Volume OBV", "🟢 ALTA" if c.iloc[-1] > c.iloc[-2] else "🔴 BAIXA"),
        ("Força ADX", "🟢 FORTE" if ta.adx(h, l, c).iloc[-1, 0] > 25 else "⚪ NEUTRO")
    ]

# Interface
st.title("📊 MONITOR 10 INDICADORES")
placeholder = st.empty()

while True:
    d1, d5 = pegar_dados("1m"), pegar_dados("5m")
    if d1 is not None and d5 is not None:
        s1, s5 = calcular_sinal(d1), calcular_sinal(d5)
        if s1 and s5:
            with placeholder.container():
                st.metric("PREÇO EUR/USD", f"{d1['Close'].iloc[-1]:.5f}")
                # Tabela Comparativa
                df_term = pd.DataFrame({"INDICADOR": [x[0] for x in s1], "SINAL M1": [x[1] for x in s1], "SINAL M5": [x[1] for x in s5]})
                st.table(df_term)
                # Super Sinal
                v_c = sum(1 for x in s1+s5 if "COMPRA" in x[1] or "ALTA" in x[1])
                v_v = sum(1 for x in s1+s5 if "VENDA" in x[1] or "BAIXA" in x[1])
                f = (max(v_c, v_v) / 20) * 100
                if f >= 75:
                    st.success(f"🔥 SUPER SINAL: {'COMPRA' if v_c > v_v else 'VENDA'} ({f:.0f}%)")
                else: st.warning(f"⚖️ AGUARDANDO CONFLUÊNCIA ({f:.0f}%)")
    time.sleep(2)
    st.rerun()
