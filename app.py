import streamlit as st
import pandas as pd
import requests
import time
import pandas_ta as ta
import mplfinance as mpf

st.set_page_config(page_title="Radar Elite v2", layout="wide")

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

def analisar(df):
    if df is None or len(df) < 30: return None
    c = df['Close']
    # Cálculos Técnicos
    ema9 = ta.ema(c, length=9)
    ema21 = ta.ema(c, length=21)
    rsi = ta.rsi(c, length=14)
    macd = ta.macd(c)
    stoch = ta.stoch(df['High'], df['Low'], c)
    bbands = ta.bbands(c, length=20)
    
    # Lógica de Sinais
    def sinal(cond_c, cond_v):
        if cond_c: return "🟢 COMPRA"
        if cond_v: return "🔴 VENDA"
        return "⚪ NEUTRO"

    dados = [
        ("Média (EMA 9)", sinal(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", sinal(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("RSI (14)", sinal(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD", sinal(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", sinal(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", sinal(c.iloc[-1] < bbands.iloc[-1, 0], c.iloc[-1] > bbands.iloc[-1, 2]))
    ]
    return dados

# Interface
st.title("📈 MONITOR PROFISSIONAL EUR/USD")
preco_spot = st.empty()
graf_spot = st.empty()
tabela_spot = st.empty()

while True:
    df1 = obter_dados("1m")
    df5 = obter_dados("5m")
    
    if df1 is not None and df5 is not None:
        # 1. Preço em destaque
        preco_spot.metric("EUR/USD AO VIVO", f"{df1['Close'].iloc[-1]:.5f}")
        
        # 2. Gráfico M5
        with graf_spot.container():
            st.subheader("Tendência M5 (Visão Geral)")
            fig, _ = mpf.plot(df5.tail(30), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig)
            
        # 3. Tabela de 10 Indicadores (Modelo solicitado)
        with tabela_spot.container():
            st.markdown("### 🔍 MONITOR DE INDICADORES | EUR/USD")
            sinais1 = analisar(df1)
            sinais5 = analisar(df5)
            
            if sinais1 and sinais5:
                df_final = pd.DataFrame({
                    "INDICADOR": [s[0] for s in sinais1],
                    "SINAL M1": [s[1] for s in sinais1],
                    "SINAL M5": [s[1] for s in sinais5]
                })
                st.table(df_final)
                
                # Confluência Estratégica
                compra = sum(1 for s in sinais1 + sinais5 if "COMPRA" in s[1])
                venda = sum(1 for s in sinais1 + sinais5 if "VENDA" in s[1])
                total = len(sinais1 + sinais5)
                
                st.markdown(f"**FORÇA TOTAL:** 🟢 {compra*100/total:.0f}% COMPRA | 🔴 {venda*100/total:.0f}% VENDA")
                if (compra/total) > 0.7: st.success("🔥 CONFLUÊNCIA DE COMPRA FORTE!")
                elif (venda/total) > 0.7: st.error("🔥 CONFLUÊNCIA DE VENDA FORTE!")

    time.sleep(2)
    st.rerun()
