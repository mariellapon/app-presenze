import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Rilevazione Presenze", page_icon="⏱️", layout="wide")

DATA_FILE = "presenze_log.csv"

# Inizializzazione file se non esiste
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
    df_init.to_csv(DATA_FILE, index=False)

# Mappa Dipendenti con i rispettivi PIN personali
DIPENDENTI_PIN = {
    "1001": "AGOSTINELLI FEDERICA",
    "1002": "BISCHI MICHELE",
    "1003": "BORINI RAFFAELE",
    "1004": "BUGLIONI SARAH",
    "1005": "CUPIDO PATRIZIA",
    "1006": "D'APONTE PAOLO",
    "1007": "MANZOTTI FRANCESCA",
    "1008": "NOVELLI LUCA",
    "1009": "NUZZIELLO CARLO",
    "1010": "PALLOTTA ANNABELLA",
    "1011": "PIERINI FRANCESCO",
    "1012": "PONTILLO MARIELLA",
    "1013": "SANTOLINI MAURO"
}

st.title("⏱️ Sistema Rilevazione Presenze")

tab1, tab2 = st.tabs(["📲 Timbratura Dipendente", "📊 Area Amministratore"])

with tab1:
    st.subheader("Registra il tuo ingresso o la tua uscita")
    
    col_pin, col_date, col_mod = st.columns([1.5, 1, 1.5])
    
    with col_pin:
        pin_inserito = st.text_input("Inserisci il tuo PIN Personale:", type="password", max_chars=4)
    with col_date:
        data_selezionata = st.date_input("Data:", datetime.now())
    with col_mod:
        modalita = st.radio("Modalità di lavoro:", ["In Sede", "Smart Working", "Trasferta"], horizontal=True)

    if pin_inserito:
        if pin_inserito in DIPENDENTI_PIN:
            dipendente = DIPENDENTI_PIN[pin_inserito]
            st.info(f"👤 Dipendente riconosciuto: **{dipendente}**")
            
            col1, col2 = st.columns(2)
            
            data_str = data_selezionata.strftime("%Y-%m-%d")
            data_formatted = data_selezionata.strftime("%d/%m/%Y")
            
            with col1:
                if st.button("🟢 INGRESSO", use_container_width=True, type="primary"):
                    ora_attuale = datetime.now().strftime("%H:%M:%S")
                    
                    nuovo_record = pd.DataFrame([[data_str, ora_attuale, dipendente, "INGRESSO", modalita]], 
                                                columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
                    nuovo_record.to_csv(DATA_FILE, mode='a', header=False, index=False)
                    
                    st.success(f"✅ INGRESSO registrato per **{dipendente}** il **{data_formatted}** alle **{ora_attuale}** ({modalita})")

            with col2:
                if st.button("🔴 USCITA", use_container_width=True):
                    ora_attuale = datetime.now().strftime("%H:%M:%S")
                    
                    nuovo_record = pd.DataFrame([[data_str, ora_attuale, dipendente, "USCITA", modalita]], 
                                                columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
                    nuovo_record.to_csv(DATA_FILE, mode='a', header=False, index=False)
                    
                    st.warning(f"🛑 USCITA registrata per **{dipendente}** il **{data_formatted}** alle **{ora_attuale}** ({modalita})")
        else:
            st.error("❌ PIN non valido. Riprova.")

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
