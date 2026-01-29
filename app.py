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
    except: return None

def analisar(df):
    if df is None or len(df) < 30: return None
    c = df['Close']
    ema9 = ta.ema(c, length=9)
    ema21 = ta.ema(c, length=21)
    rsi = ta.rsi(c, length=14)
    macd = ta.macd(c)
    stoch = ta.stoch(df['High'], df['Low'], c)
    bbands = ta.bbands(c, length=20)
    
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

# --- Estrutura da Tela ---
st.title("🛡️ MONITOR DE CONFLUÊNCIA EUR/USD")
topo = st.empty()
tabela = st.empty()
st.markdown("---")
grafico = st.empty()

while True:
    df1 = obter_dados("1m")
    df5 = obter_dados("5m")
    
    if df1 is not None and df5 is not None:
        # Preço no topo
        topo.metric("EUR/USD LIVE", f"{df1['Close'].iloc[-1]:.5f}")
        
        # Tabela de Dados (Topo)
        with tabela.container():
            s1, s5 = analisar(df1), analisar(df5)
            if s1 and s5:
                df_mostra = pd.DataFrame({
                    "INDICADOR": [x[0] for x in s1],
                    "SINAL M1": [x[1] for x in s1],
                    "SINAL M5": [x[1] for x in s5]
                })
                st.table(df_mostra)
                
                # Força de Confluência
                c = sum(1 for x in s1+s5 if "COMPRA" in x[1])
                v = sum(1 for x in s1+s5 if "VENDA" in x[1])
                st.write(f"**CONFLUÊNCIA:** 🟢 {c*100/12:.0f}% COMPRA | 🔴 {v*100/12:.0f}% VENDA")

        # Gráfico (Baixo)
        with grafico.container():
            st.subheader("Tendência Visual (M5)")
            fig, _ = mpf.plot(df5.tail(35), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig)

    time.sleep(2)
    st.rerun()

    return [
        ("Média (EMA 9)", sinal(c.iloc[-1] > ema9.iloc[-1], c.iloc[-1] < ema9.iloc[-1])),
        ("Média (EMA 21)", sinal(c.iloc[-1] > ema21.iloc[-1], c.iloc[-1] < ema21.iloc[-1])),
        ("RSI (14)", sinal(rsi.iloc[-1] < 30, rsi.iloc[-1] > 70)),
        ("MACD", sinal(macd.iloc[-1, 0] > macd.iloc[-1, 2], macd.iloc[-1, 0] < macd.iloc[-1, 2])),
        ("Estocástico", sinal(stoch.iloc[-1, 0] < 20, stoch.iloc[-1, 0] > 80)),
        ("Bollinger", sinal(c.iloc[-1] < bbands.iloc[-1, 0], c.iloc[-1] > bbands.iloc[-1, 2]))
    ]

# --- INTERFACE NA ORDEM SOLICITADA ---
st.title("📈 MONITOR ESTRATÉGICO EUR/USD")

# 1. PREÇO E DADOS (EM CIMA)
preco_spot = st.empty()
tabela_spot = st.empty()
st.markdown("---")

# 2. GRÁFICO (EM BAIXO)
graf_spot = st.empty()

while True:
    df1 = obter_dados("1m")
    df5 = obter_dados("5m")
    
    if df1 is not None and df5 is not None:
        # Atualiza Preço
        preco_spot.metric("EUR/USD AO VIVO", f"{df1['Close'].iloc[-1]:.5f}")
        
        # Atualiza Tabela Técnica (Primeiro)
        with tabela_spot.container():
            st.subheader("🔍 Monitor de 10 Indicadores (M1 vs M5)")
            sinais1 = analisar(df1)
            sinais5 = analisar(df5)
            
            if sinais1 and sinais5:
                df_final = pd.DataFrame({
                    "INDICADOR": [s[0] for s in sinais1],
                    "SINAL M1": [s[1] for s in sinais1],
                    "SINAL M5": [s[1] for s in sinais5]
                })
                st.table(df_final)
                
                # Cálculo de Força
                compra = sum(1 for s in sinais1 + sinais5 if "COMPRA" in s[1])
                venda = sum(1 for s in sinais1 + sinais5 if "VENDA" in s[1])
                total = len(sinais1 + sinais5)
                st.write(f"**FORÇA DE MERCADO:** 🟢 {compra*100/total:.0f}% COMPRA | 🔴 {venda*100/total:.0f}% VENDA")

        # Atualiza Gráfico (Depois)
        with graf_spot.container():
            st.subheader("📊 Tendência Visual M5")
            fig, _ = mpf.plot(df5.tail(30), type='candle', style='charles', returnfig=True, tight_layout=True)
            st.pyplot(fig)

    time.sleep(2)
    st.rerun()

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
