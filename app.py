import streamlit as st
import pandas as pd
import requests
import time
import pandas_ta as ta
from datetime import datetime

st.set_page_config(page_title="Monitor 10 Indicadores", layout="wide")

# Estilo para parecer um terminal profissional
st.markdown("""<style>
    .reportview-container { background: #000000; }
    .stMetric { color: #ffffff !important; }
    table { background-color: #000000; color: #ffffff !important; }
</style>""", unsafe_allow_html=True)

def obter_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['Date'] = pd.to_datetime(r['timestamp'], unit='s')
        return df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close'}).set_index('Date').dropna()
    except: return None

def analisar(df):
    if df is None or len(df) < 40: return None
    c, h, l = df['Close'], df['High'], df['Low']
    
    # 10 Indicadores Técnicos
    ema9 = ta.ema(c, length=9)
    ema21 = ta.ema(c, length=21)
    rsi = ta.rsi(c, length=14)
    macd = ta.macd(c)
    stoch = ta.stoch(h, l, c)
    bb = ta.bbands(c, length=20)
    cci = ta.cci(h, l, c, length=20)
    adx = ta.adx(h, l, c)
    atr = ta.atr(h, l, c, length=14)
    
    def s(compra, venda):
        if compra: return "🟢 COMPRA"
        if venda: return "🔴 VENDA"
        return "⚪ NEUTRO"

    return [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", s(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("Ichimoku", s(c.iloc[-1] > c.rolling(26).mean().iloc[-1], c.iloc[-1] < c.rolling(26).mean().iloc[-1])),
        ("RSI (14)", s(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD", s(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", s(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", s(c.iloc[-1] < bb.iloc[-1, 0], c.iloc[-1] > bb.iloc[-1, 2])),
        ("ATR (Volat.)", "🔴 VENDA" if atr.iloc[-1] > atr.mean() else "🟢 COMPRA"),
        ("CCI (Canal)", s(cci.iloc[-1] < -100, cci.iloc[-1] > 100)),
        ("Volume (OBV)", "🟢 COMPRA" if c.iloc[-1] > c.iloc[-2] else "🔴 VENDA")
    ]

# --- Interface Principal ---
placeholder = st.empty()

while True:
    d1, d5 = obter_dados("1m"), obter_dados("5m")
    if d1 is not None and d5 is not None:
        s1, s5 = analisar(d1), analisar(d5)
        if s1 and s5:
            with placeholder.container():
                st.code(f"📊 MONITOR 10 INDICADORES | EUR/USD: {d1['Close'].iloc[-1]:.5f}\nHORA: {datetime.now().strftime('%H:%M:%S')}")
                
                # Tabela Principal
                df_tab = pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                })
                st.table(df_tab)
                
                # Cálculo de Força e Confluência
                v_c = sum(1 for x in s1+s5 if "COMPRA" in x[1])
                v_v = sum(1 for x in s1+s5 if "VENDA" in x[1])
                forca = (max(v_c, v_v) / 20) * 100
                
                st.markdown("---")
                st.subheader("🔍 CONFLUÊNCIA ESTRATÉGICA (HARMONIA DE GRUPOS)")
                
                col1, col2 = st.columns(2)
                col1.metric("FORÇA TOTAL M1", f"{(sum(1 for x in s1 if 'COMPRA' in x[1])/10)*100:.0f}% 🟢")
                col2.metric("FORÇA TOTAL M5", f"{(sum(1 for x in s5 if 'VENDA' in x[1])/10)*100:.0f}% 🔴")

                if forca >= 75:
                    msg = "🔥 FORTE CONFLUÊNCIA DE COMPRA" if v_c > v_v else "🔥 FORTE CONFLUÊNCIA DE VENDA"
                    st.success(f"{msg} ({forca:.0f}%)")
                else:
                    st.warning(f"⚖️ AGUARDANDO HARMONIA ({forca:.0f}%)")
                    
    time.sleep(2)
    st.rerun()
        return "⚪ NEUTRO"
    # Lista dos 10 Indicadores
    return [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", s(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("RSI (14)", s(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD (Trend)", s(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", s(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", s(c.iloc[-1] < bb.iloc[-1, 0], c.iloc[-1] > bb.iloc[-1, 2])),
        ("CCI (Canal)", s(cci.iloc[-1] < -100, cci.iloc[-1] > 100)),
        ("Ichimoku", s(c.iloc[-1] > c.rolling(26).mean().iloc[-1], c.iloc[-1] < c.rolling(26).mean().iloc[-1])),
        ("Força ADX", "🟢 FORTE" if adx.iloc[-1, 0] > 25 else "⚪ NEUTRO"),
        ("Volume OBV", "🟢 ALTA" if c.iloc[-1] > c.iloc[-2] else "🔴 BAIXA")
    ]

# --- Interface Principal ---
st.title("🛡️ MONITOR DE CONFLUÊNCIA")
container = st.empty()

while True:
    d1, d5 = obter_dados("1m"), obter_dados("5m")
    if d1 is not None and d5 is not None:
        s1, s5 = analisar_tecnica(d1), analisar_tecnica(d5)
        if s1 and s5:
            with container.container():
                st.metric("PREÇO ATUAL EUR/USD", f"{d1['Close'].iloc[-1]:.5f}")
                # Tabela de Comparação
                st.table(pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                }))
                # Lógica do Super Sinal
                v_c = sum(1 for x in s1+s5 if "COMPRA" in x[1] or "ALTA" in x[1] or "FORTE" in x[1])
                v_v = sum(1 for x in s1+s5 if "VENDA" in x[1] or "BAIXA" in x[1])
                forca = (max(v_c, v_v) / 20) * 100
                if v_c > v_v and forca >= 70:
                    st.success(f"🔥 SUPER SINAL DE COMPRA: {forca:.0f}%")
                elif v_v > v_c and forca >= 70:
                    st.error(f"🔥 SUPER SINAL DE VENDA: {forca:.0f}%")
                else:
                    st.warning(f"⚖️ AGUARDANDO CONFLUÊNCIA ({forca:.0f}%)")
    time.sleep(2)
    st.rerun()
        if cond_v: return "🔴 VENDA"
        return "⚪ NEUTRO"

    # Esta é a lista dos 10 indicadores (Harmonia de Grupos)
    resumo = [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", s(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("RSI (14)", s(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD (Trend)", s(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", s(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", s(c.iloc[-1] < bb.iloc[-1, 0], c.iloc[-1] > bb.iloc[-1, 2])),
        ("CCI (Canal)", s(cci.iloc[-1] < -100, cci.iloc[-1] > 100)),
        ("Ichimoku", s(c.iloc[-1] > c.rolling(26).mean().iloc[-1], c.iloc[-1] < c.rolling(26).mean().iloc[-1])),
        ("Força ADX", "🟢 FORTE" if adx.iloc[-1, 0] > 25 else "⚪ NEUTRO"),
        ("Volume OBV", "🟢 ALTA" if c.iloc[-1] > c.iloc[-2] else "🔴 BAIXA")
    ]
    return resumo

# --- Interface ---
st.title("🛡️ MONITOR DE CONFLUÊNCIA")
placeholder = st.empty()

while True:
    d1, d5 = obter_dados("1m"), obter_dados("5m")
    if d1 is not None and d5 is not None:
        s1, s5 = analisar_tecnica(d1), analisar_tecnica(d5)
        if s1 and s5:
            with placeholder.container():
                st.metric("PREÇO ATUAL", f"{d1['Close'].iloc[-1]:.5f}")
                
                # Tabela de 10 Indicadores
                st.table(pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                }))
                
                # Super Sinal (Lógica 70%+)
                v_c = sum(1 for x in s1+s5 if "COMPRA" in x[1] or "ALTA" in x[1] or "FORTE" in x[1])
                v_v = sum(1 for x in s1+s5 if "VENDA" in x[1] or "BAIXA" in x[1])
                forca = (max(v_c, v_v) / 20) * 100
                
                if v_c > v_v and forca >= 70:
                    st.success(f"🔥 SUPER SINAL DE COMPRA: {forca:.0f}%")
                elif v_v > v_c and forca >= 70:
                    st.error(f"🔥 SUPER SINAL DE VENDA: {forca:.0f}%")
                else:
                    st.info(f"⚖️ AGUARDANDO CONFLUÊNCIA ({forca:.0f}%)")
    time.sleep(2)
    st.rerun()
        return "⚪ NEUTRO"

    return [
        ("Média (EMA 9)", s(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", s(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("RSI (14)", s(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD (Trend)", s(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", s(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", s(c.iloc[-1] < bbands.iloc[-1, 0], c.iloc[-1] > bbands.iloc[-1, 2])),
        ("CCI (Canal)", s(cci.iloc[-1] < -100, cci.iloc[-1] > 100)),
        ("Ichimoku", s(c.iloc[-1] > c.rolling(26).mean().iloc[-1], c.iloc[-1] < c.rolling(26).mean().iloc[-1])),
        ("Força ADX", "🟢 FORTE" if adx.iloc[-1, 0] > 25 else "⚪ NEUTRO"),
        ("Volume OBV", "🟢 ALTA" if c.iloc[-1] > c.iloc[-2] else "🔴 BAIXA")
    ]

st.title("🛡️ MONITOR ESTRATÉGICO EUR/USD")
topo = st.empty()
tabela = st.empty()
sinal_box = st.empty()

while True:
    df1, df5 = obter_dados("1m"), obter_dados("5m")
    if df1 is not None and df5 is not None:
        with topo:
            st.metric("PREÇO EUR/USD", f"{df1['Close'].iloc[-1]:.5f}")
        
        s1, s5 = analisar(df1), analisar(df5)
        if s1 and s5:
            with tabela:
                df_final = pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                })
                st.table(df_final)

            with sinal_box:
                votos_c = sum(1 for x in s1+s5 if "COMPRA" in x[1] or "ALTA" in x[1] or "FORTE" in x[1])
                votos_v = sum(1 for x in s1+s5 if "VENDA" in x[1] or "BAIXA" in x[1])
                forca = (max(votos_c, votos_v) / 20) * 100
                
                st.markdown("### 🎯 CONFLUÊNCIA (HARMONIA DE GRUPOS)")
                if votos_c > votos_v and forca >= 70:
                    st.success(f"🔥 SUPER SINAL DE COMPRA: {forca:.0f}%")
                elif votos_v > votos_c and forca >= 70:
                    st.error(f"🔥 SUPER SINAL DE VENDA: {forca:.0f}%")
                else:
                    st.warning(f"⚖️ AGUARDANDO CONFLUÊNCIA ({forca:.0f}%)")
    time.sleep(2)
    st.rerun()
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
