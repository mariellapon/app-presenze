import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import os

st.set_page_config(page_title="Rilevazione Presenze & Giustificativi", page_icon="⏱️", layout="wide")

DATA_FILE = "presenze_log.csv"
RICHIESTE_FILE = "richieste_log.csv"

# Inizializzazione file CSV se non esistono
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
    df_init.to_csv(DATA_FILE, index=False)

if not os.path.exists(RICHIESTE_FILE):
    df_rich = pd.DataFrame(columns=["ID", "Data_Richiesta", "Dipendente", "Tipo", "Data_Inizio", "Data_Fine", "Ora_Inizio", "Ora_Fine", "Ore", "Note", "Stato"])
    df_rich.to_csv(RICHIESTE_FILE, index=False)

# Mappa Dipendenti con PIN personali
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

# Funzione per calcolare gli straordinari arrotondati ai 30 minuti
def calcola_ore_e_straordinari(df_timb, ore_giornaliere_standard=8.0):
    if df_timb.empty:
        return pd.DataFrame()
    
    df = df_timb.copy()
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Ora'])
    df = df.sort_values(['Dipendente', 'Datetime'])
    
    report_rows = []
    
    for (dip, dt), group in df.groupby(['Dipendente', 'Data']):
        ingressi = group[group['Tipo'] == 'INGRESSO']['Datetime'].tolist()
        uscite = group[group['Tipo'] == 'USCITA']['Datetime'].tolist()
        
        totale_secondi = 0
        for ing, usc in zip(ingressi, uscite):
            if usc > ing:
                totale_secondi += (usc - ing).total_seconds()
        
        ore_effettive = totale_secondi / 3600.0
        straordinario_grezzo = max(0.0, ore_effettive - ore_giornaliere_standard)
        straordinario_approvato = (straordinario_grezzo // 0.5) * 0.5
        
        report_rows.append({
            'Data': dt,
            'Dipendente': dip,
            'Ore Lavorate Effettive': round(ore_effettive, 2),
            'Ore Standard': ore_giornaliere_standard,
            'Straordinario Calcolato (30 min pieni)': straordinario_approvato
        })
        
    return pd.DataFrame(report_rows)

st.title("⏱️ Sistema Presenze & Gestione Giustificativi")

tab1, tab2, tab3 = st.tabs(["📲 Timbratura", "📝 Richiesta Ferie / Permessi / Malattia", "📊 Area Amministratore"])

# --- TAB 1: TIMBRATURE ---
with tab1:
    st.subheader("Registra il tuo ingresso o la tua uscita")
    
    with st.form(key="form_timbratura"):
        col_pin, col_date, col_mod = st.columns([1.5, 1, 1.5])
        with col_pin:
            pin_timb_in = st.text_input("Inserisci PIN Personale (es. 1012):", type="password", max_chars=4)
        with col_date:
            data_selezionata = st.date_input("Data Timbratura:", datetime.now())
        with col_mod:
            modalita = st.radio("Modalità di lavoro:", ["In Sede", "Smart Working", "Trasferta"], horizontal=True)

        st.markdown("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            btn_ing = st.form_submit_button("✅ CONFERMA INGRESSO", type="primary", use_container_width=True)
        with col_b2:
            btn_usc = st.form_submit_button("🛑 CONFERMA USCITA", use_container_width=True)

    if btn_ing or btn_usc:
        pin_timb_clean = str(pin_timb_in).strip() if pin_timb_in else ""
        if pin_timb_clean in DIPENDENTI_PIN:
            dipendente_timb = DIPENDENTI_PIN[pin_timb_clean]
            tipo_timb = "INGRESSO" if btn_ing else "USCITA"
            data_str = data_selezionata.strftime("%Y-%m-%d")
            data_formatted = data_selezionata.strftime("%d/%m/%Y")
            ora_attuale = datetime.now().strftime("%H:%M:%S")
            
            nuovo_record = pd.DataFrame([[data_str, ora_attuale, dipendente_timb, tipo_timb, modalita]], 
                                        columns=["Data", "Ora", "Dipendente", "Tipo", "Modalita"])
            nuovo_record.to_csv(DATA_FILE, mode='a', header=False, index=False)
            
            if tipo_timb == "INGRESSO":
                st.success(f"✅ INGRESSO registrato per **{dipendente_timb}** il **{data_formatted}** alle **{ora_attuale}** ({modalita})")
            else:
                st.warning(f"🛑 USCITA registrata per **{dipendente_timb}** il **{data_formatted}** alle **{ora_attuale}** ({modalita})")
        else:
            st.error("❌ PIN inserito non valido. Digita un PIN corretto (es. 1012 per PONTILLO MARIELLA).")

# --- TAB 2: RICHIESTE FERIE / PERMESSI / MALATTIA ---
with tab2:
    st.subheader("Invia una richiesta di Giustificativo")
    
    with st.form(key="form_richiesta_giustificativo"):
        col_pin_r, col_tipo_r = st.columns([1.5, 2])
        with col_pin_r:
            pin_req_in = st.text_input("Inserisci PIN Personale (es. 1012):", type="password", max_chars=4)
        with col_tipo_r:
            tipo_giustificativo = st.selectbox("Tipo Giustificativo:", ["Permesso (ROL)", "Ferie", "Malattia", "Altro"])

        st.markdown("---")
        st.write("### 📅 Selezione Data e Orario della Richiesta")
        
        c1, c2 = st.columns(2)
        with c1:
            d_inizio = st.date_input("Data Inizio / Giorno Permesso:", date.today())
            t_inizio = st.time_input("Ora Inizio (solo per Permesso):", time(9, 0))
        with c2:
            d_fine = st.date_input("Data Fine (solo per Ferie/Malattia):", date.today())
            t_fine = st.time_input("Ora Fine (solo per Permesso):", time(13, 0))

        note = st.text_area("Note / Motivazione (opzionale):")
        
        btn_send_req = st.form_submit_button("Invia Richiesta all'Amministratore", type="primary", use_container_width=True)

    if btn_send_req:
        pin_req_clean = str(pin_req_in).strip() if pin_req_in else ""
        if pin_req_clean in DIPENDENTI_PIN:
            dipendente_final = DIPENDENTI_PIN[pin_req_clean]
            
            if tipo_giustificativo == "Permesso (ROL)":
                d_fine_calc = d_inizio
                dt_i = datetime.combine(d_inizio, t_inizio)
                dt_f = datetime.combine(d_inizio, t_fine)
                ore_totali = round((dt_f - dt_i).total_seconds() / 3600.0, 2) if dt_f > dt_i else 0.0
                ora_ini_str = t_inizio.strftime("%H:%M")
                ora_fin_str = t_fine.strftime("%H:%M")
            else:
                d_fine_calc = d_fine
                giorni_totali = (d_fine - d_inizio).days + 1
                ore_totali = 8.0 * max(1, giorni_totali)
                ora_ini_str = "08:00"
                ora_fin_str = "17:00"

            req_id = int(datetime.now().timestamp())
            d_rich = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            nuova_richiesta = pd.DataFrame([[req_id, d_rich, dipendente_final, tipo_giustificativo, 
                                             d_inizio.strftime("%Y-%m-%d"), d_fine_calc.strftime("%Y-%m-%d"), 
                                             ora_ini_str, ora_fin_str, ore_totali, note, "IN ATTESA"]], 
                                           columns=["ID", "Data_Richiesta", "Dipendente", "Tipo", "Data_Inizio", "Data_Fine", "Ora_Inizio", "Ora_Fine", "Ore", "Note", "Stato"])
            
            nuova_richiesta.to_csv(RICHIESTE_FILE, mode='a', header=not os.path.exists(RICHIESTE_FILE) or os.stat(RICHIESTE_FILE).st_size == 0, index=False)
            st.success(f"✅ Richiesta di **{tipo_giustificativo}** inviata con successo per **{dipendente_final}**! (Totale: {ore_totali} ore)")
        else:
            st.error("❌ PIN inserito non valido. Digita un PIN corretto (es. 1012 per PONTILLO MARIELLA).")

# --- TAB 3: AREA AMMINISTRATORE ---
with tab3:
    st.subheader("Gestione Amministrazione & Calcolo Ore")
    
    password = st.text_input("Inserisci Password Amministratore:", type="password", key="pass_admin")
    
    if password == "1234":
        st.markdown("---")
        st.write("### Richieste In Sospeso (Ferie, Permessi, Malattia)")
        
        try:
            df_rich = pd.read_csv(RICHIESTE_FILE)
        except Exception:
            df_rich = pd.DataFrame()
            
        if not df_rich.empty and "Stato" in df_rich.columns:
            richieste_sospese = df_rich[df_rich["Stato"] == "IN ATTESA"]
        else:
            richieste_sospese = pd.DataFrame()
        
        if richieste_sospese.empty:
            st.success("Nessuna richiesta in attesa di approvazione.")
        else:
            for idx, row in richieste_sospese.iterrows():
                ora_info = f" dalle {row['Ora_Inizio']} alle {row['Ora_Fine']}" if 'Ora_Inizio' in row and pd.notna(row['Ora_Inizio']) else ""
                with st.expander(f"{row['Tipo']} - {row['Dipendente']} ({row['Data_Inizio']} -> {row['Data_Fine']}{ora_info})"):
                    st.write(f"**Dipendente:** {row['Dipendente']}")
                    st.write(f"**Tipo:** {row['Tipo']}")
                    st.write(f"**Periodo:** dal {row['Data_Inizio']} al {row['Data_Fine']} {ora_info} ({row['Ore']} ore)")
                    st.write(f"**Note:** {row['Note']}")
                    
                    col_app, col_rif = st.columns(2)
                    with col_app:
                        if st.button("Approva", key=f"app_{row['ID']}"):
                            df_rich.loc[df_rich["ID"] == row["ID"], "Stato"] = "APPROVATO"
                            df_rich.to_csv(RICHIESTE_FILE, index=False)
                            st.success("Richiesta Approvata!")
                            st.rerun()
                    with col_rif:
                        if st.button("Rifiuta", key=f"rif_{row['ID']}"):
                            df_rich.loc[df_rich["ID"] == row["ID"], "Stato"] = "RIFIUTATO"
                            df_rich.to_csv(RICHIESTE_FILE, index=False)
                            st.error("Richiesta Rifiutata!")
                            st.rerun()
        
        st.markdown("---")
        st.write("### Conteggio Automatico Ore & Straordinari (Soglia 30 min)")
        try:
            df_timb = pd.read_csv(DATA_FILE)
        except Exception:
            df_timb = pd.DataFrame()
        
        df_calcolo = calcola_ore_e_straordinari(df_timb)
        if not df_calcolo.empty:
            st.dataframe(df_calcolo, use_container_width=True)
        else:
            st.info("Nessun dato di timbratura sufficiente per il calcolo.")

        st.markdown("---")
        st.write("### Registro Timbri Grezzi")
        st.dataframe(df_timb, use_container_width=True)
        
        col_dn1, col_dn2 = st.columns(2)
        with col_dn1:
            if not df_timb.empty:
                st.download_button(
                    label="Scarica Report Presenze / Straordinari (CSV)",
                    data=df_calcolo.to_csv(index=False).encode('utf-8') if not df_calcolo.empty else df_timb.to_csv(index=False).encode('utf-8'),
                    file_name=f"Report_Presenze_{datetime.now().strftime('%Y_%m')}.csv",
                    mime='text/csv',
                )
        with col_dn2:
            if not df_rich.empty:
                st.download_button(
                    label="Scarica Giustificativi (CSV)",
                    data=df_rich.to_csv(index=False).encode('utf-8'),
                    file_name=f"Giustificativi_{datetime.now().strftime('%Y_%m')}.csv",
                    mime='text/csv',
                )

    elif password != "":
        st.error("Password errata.")
