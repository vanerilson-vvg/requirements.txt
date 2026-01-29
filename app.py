import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import mplfinance as mpf

# Configuração da Página para parecer um Dashboard Profissional
st.set_page_config(page_title="Radar Elite EUR/USD", layout="wide")

def obter_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['Date'] = pd.to_datetime(r['timestamp'], unit='s')
        df = df.rename(columns={'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'})
        return df.set_index('Date').dropna()
    except: return None

def calcular_indicadores(df):
    if df is None or len(df) < 20: return None
    c = df['Close']
    s = {}
    # Lógica simplificada para o Dashboard Web
    s['Média (EMA 9)'] = 1 if c.iloc[-1] > c.ewm(span=9).mean().iloc[-1] else -1
    s['Média (EMA 21)'] = 1 if c.iloc[-1] > c.ewm(span=21).mean().iloc[-1] else -1
    votos = list(s.values())
    return {"lista": s, "compra": (votos.count(1)/len(votos))*100, "venda": (votos.count(-1)/len(votos))*100, "preco": c.iloc[-1]}

st.title("💹 Meu Radar Forex Profissional")

# Organização em Colunas para visualização no celular
col1, col2 = st.columns(2)
placeholder_m1 = col1.empty()
placeholder_m5 = col2.empty()

while True:
    df_m1 = obter_dados("1m")
    df_m5 = obter_dados("5m")
    m1 = calcular_indicadores(df_m1)
    
    if df_m1 is not None and m1:
        with placeholder_m1.container():
            st.subheader(f"M1 - Preço: {m1['preco']:.5f}")
            # Gera o gráfico de velas (Candlestick)
            fig1, _ = mpf.plot(df_m1.tail(40), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig1)
            st.write(f"**Sinal M1:** {'🟢 COMPRA' if m1['compra'] >= 70 else ('🔴 VENDA' if m1['venda'] >= 70 else '⚪ NEUTRO')}")

    if df_m5 is not None:
        with placeholder_m5.container():
            st.subheader("M5 - Visão Geral")
            fig2, _ = mpf.plot(df_m5.tail(40), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig2)

    time.sleep(10) # Atualiza a cada 10 segundos
    st.rerun()
