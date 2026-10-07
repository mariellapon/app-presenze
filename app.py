import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Rilevazione Presenze", page_icon="⏱️", layout="wide")

DATA_FILE = "presenze_log.csv"

if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
    df_init.to_csv(DATA_FILE, index=False)

DIPENDENTI = [
    "AGOSTINELLI FEDERICA", "BISCHI MICHELE", "BORINI RAFFAELE",
    "BUGLIONI SARAH", "CUPIDO PATRIZIA", "D'APONTE PAOLO", "MANZOTTI FRANCESCA",
    "NOVELLI LUCA", "NUZZIELLO CARLO", "PALLOTTA ANNABELLA", "PIERINI FRANCESCO",
    "PONTILLO MARIELLA", "SANTOLINI MAURO"
]

st.title("⏱️ Sistema Rilevazione Presenze")

tab1, tab2 = st.tabs(["📲 Timbratura Dipendente", "📊 Area Amministratore"])

with tab1:
    st.subheader("Registra il tuo ingresso o la tua uscita")
    
    col_dep, col_mod = st.columns(2)
    with col_dep:
        dipendente = st.selectbox("Seleziona il tuo Nome e Cognome:", ["-- Seleziona --"] + DIPENDENTI)
    with col_mod:
        modalita = st.radio("Modalità di lavoro:", ["In Sede", "Smart Working", "Trasferta"], horizontal=True)

    if dipendente != "-- Seleziona --":
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🟢 INGRESSO", use_container_width=True, type="primary"):
                ora_attuale = datetime.now().strftime("%H:%M:%S")
                data_attuale = datetime.now().strftime("%Y-%m-%d")
                
                nuovo_record = pd.DataFrame([[data_attuale, ora_attuale, dipendente, "INGRESSO", modalita]], 
                                            columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
                nuovo_record.to_csv(DATA_FILE, mode='a', header=False, index=False)
                
                st.success(f"✅ INGRESSO registrato per {dipendente} alle {ora_attuale} ({modalita})")

        with col2:
            if st.button("🔴 USCITA", use_container_width=True):
                ora_attuale = datetime.now().strftime("%H:%M:%S")
                data_attuale = datetime.now().strftime("%Y-%m-%d")
                
                nuovo_record = pd.DataFrame([[data_attuale, ora_attuale, dipendente, "USCITA", modalita]], 
                                            columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
                nuovo_record.to_csv(DATA_FILE, mode='a', header=False, index=False)
                
                st.warning(f"🛑 USCITA registrata per {dipendente} alle {ora_attuale} ({modalita})")

with tab2:
    st.subheader("Registro Timbrature e Download Excel")
    
    password = st.text_input("Inserisci Password Amministratore:", type="password")
    
    if password == "1234":
        df = pd.read_csv(DATA_FILE)
        st.dataframe(df, use_container_width=True)
        
        if not df.empty:
            @st.cache_data
            def convert_df(df_to_convert):
                return df_to_convert.to_csv(index=False).encode('utf-8')

            csv_data = convert_df(df)
            st.download_button(
                label="📥 Scarica Dati (CSV/Excel)",
                data=csv_data,
                file_name=f"Presenze_{datetime.now().strftime('%Y_%m')}.csv",
                mime='text/csv',
            )
    elif password != "":
        st.error("Password errata.")
