import streamlit as st
import pandas as pd
import requests
import time
import pandas_ta as ta

st.set_page_config(page_title="Super Radar Forex", layout="wide")

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

def analisar_completo(df):
    if df is None or len(df) < 40: return None
    c = df['Close']
    h = df['High']
    l = df['Low']
    
    # Cálculos Técnicos
    rsi = ta.rsi(c, length=14)
    macd = ta.macd(c)
    stoch = ta.stoch(h, l, c)
    ema9 = ta.ema(c, length=9)
    ema21 = ta.ema(c, length=21)
    bbands = ta.bbands(c, length=20)
    cci = ta.cci(h, l, c, length=20)
    adx = ta.adx(h, l, c)
    
    def s(cond_c, cond_v):
        if cond_c: return "🟢 COMPRA"
        if cond_v: return "🔴 VENDA"
        return "⚪ NEUTRO"

    indicadores = [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", s(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("RSI (14)", s(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD", s(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", s(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", s(c.iloc[-1] < bbands.iloc[-1, 0], c.iloc[-1] > bbands.iloc[-1, 2])),
        ("CCI (Canal)", s(cci.iloc[-1] < -100, cci.iloc[-1] > 100)),
        ("ADX (Força)", "🟢 FORTE" if adx.iloc[-1, 0] > 25 else "⚪ FRACA"),
        ("Ichimoku (Base)", s(c.iloc[-1] > c.rolling(26).mean().iloc[-1], c.iloc[-1] < c.rolling(26).mean().iloc[-1])),
        ("Volume (OBV)", "🟢 ALTA" if c.iloc[-1] > c.iloc[-2] else "🔴 BAIXA")
    ]
    return indicadores

# --- Interface ---
st.title("🚀 MONITOR 10 INDICADORES | EUR/USD")
monitor_spot = st.empty()
sinal_spot = st.empty()

while True:
    df1 = obter_dados("1m")
    df5 = obter_dados("5m")
    
    if df1 is not None and df5 is not None:
        s1 = analisar_completo(df1)
        s5 = analisar_completo(df5)
        
        if s1 and s5:
            with monitor_spot.container():
                st.metric("PREÇO ATUAL", f"{df1['Close'].iloc[-1]:.5f}")
                df_final = pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                })
                st.table(df_final)

            with sinal_spot.container():
                # Lógica do Super Sinal (Harmonia de Grupos)
                votos_c = sum(1 for x in s1+s5 if "COMPRA" in x[1] or "ALTA" in x[1])
                votos_v = sum(1 for x in s1+s5 if "VENDA" in x[1] or "BAIXA" in x[1])
                forca = (max(votos_c, votos_v) / 20) * 100
                
                st.markdown("### 🎯 CONFLUÊNCIA ESTRATÉGICA")
                if votos_c > votos_v and forca >= 70:
                    st.success(f"🔥 SUPER SINAL DE COMPRA: {forca:.0f}% DE FORÇA")
                elif votos_v > votos_c and forca >= 70:
                    st.error(f"🔥 SUPER SINAL DE VENDA: {forca:.0f}% DE FORÇA")
                else:
                    st.warning(f"⚖️ AGUARDANDO CONFLUÊNCIA ({forca:.0f}%)")

    time.sleep(2)
    st.rerun()
