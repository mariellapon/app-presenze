import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import os

st.set_page_config(page_title="Rilevazione Presenze & Documenti", page_icon="⏱️", layout="wide")

# File e Cartelle di sistema
DATA_FILE = "presenze_log.csv"
RICHIESTE_FILE = "richieste_log.csv"
DIR_ALLEGATI = "allegati_richieste"
DIR_DOCUMENTI = "documenti_dipendenti"

for directory in [DIR_ALLEGATI, DIR_DOCUMENTI]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Inizializzazione file CSV se non esistono
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo"])
    df_init.to_csv(DATA_FILE, index=False)

if not os.path.exists(RICHIESTE_FILE):
    df_rich = pd.DataFrame(columns=["ID", "Data_Richiesta", "Dipendente", "Tipo", "Data_Inizio", "Data_Fine", "Ora_Inizio", "Ora_Fine", "Ore", "Note", "Allegato", "Stato"])
    df_rich.to_csv(RICHIESTE_FILE, index=False)

# Mappa Dipendenti con PIN personali e dati contrattuali
DIPENDENTI_PIN = {
    "1001": {"nome": "AGOSTINELLI FEDERICA", "ore_std": 8.0, "commerciale": False},
    "1002": {"nome": "BISCHI MICHELE", "ore_std": 8.0, "commerciale": True},
    "1003": {"nome": "BORINI RAFFAELE", "ore_std": 6.0, "commerciale": True}, # Part-time 6h
    "1004": {"nome": "BUGLIONI SARAH", "ore_std": 8.0, "commerciale": False},
    "1005": {"nome": "CUPIDO PATRIZIA", "ore_std": 8.0, "commerciale": False},
    "1006": {"nome": "D'APONTE PAOLO", "ore_std": 8.0, "commerciale": False},
    "1007": {"nome": "MANZOTTI FRANCESCA", "ore_std": 8.0, "commerciale": False},
    "1008": {"nome": "NOVELLI LUCA", "ore_std": 8.0, "commerciale": False},
    "1009": {"nome": "NUZZIELLO CARLO", "ore_std": 8.0, "commerciale": True},
    "1010": {"nome": "PALLOTTA ANNABELLA", "ore_std": 4.0, "commerciale": False}, # Part-time 4h + Smart variabile
    "1011": {"nome": "PIERINI FRANCESCO", "ore_std": 8.0, "commerciale": False},
    "1012": {"nome": "PONTILLO MARIELLA", "ore_std": 8.0, "commerciale": False},
    "1013": {"nome": "SANTOLINI MAURO", "ore_std": 8.0, "commerciale": False}
}

MAPPA_NOMI_PIN = {v["nome"]: k for k, v in DIPENDENTI_PIN.items()}

def calcola_ore_e_straordinari(df_timb):
    if df_timb.empty:
        return pd.DataFrame()
    
    df = df_timb.copy()
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Ora'])
    df = df.sort_values(['Dipendente', 'Datetime'])
    
    report_rows = []
    for (dip, dt), group in df.groupby(['Dipendente', 'Data']):
        pin_dip = MAPPA_NOMI_PIN.get(dip)
        ore_std = DIPENDENTI_PIN[pin_dip]["ore_std"] if pin_dip else 8.0
        
        ingressi = group[group['Tipo'] == 'INGRESSO']['Datetime'].tolist()
        uscite = group[group['Tipo'] == 'USCITA']['Datetime'].tolist()
        
        totale_secondi = 0
        for ing, usc in zip(ingressi, uscite):
            if usc > ing:
                totale_secondi += (usc - ing).total_seconds()
        
        ore_effettive = totale_secondi / 3600.0
        straordinario_grezzo = max(0.0, ore_effettive - ore_std)
        straordinario_approvato = (straordinario_grezzo // 0.5) * 0.5
        
        report_rows.append({
            'Data': dt,
            'Dipendente': dip,
            'Ore Lavorate Effettive': round(ore_effettive, 2),
            'Ore Standard Contratto': ore_std,
            'Straordinario Calcolato (30 min pieni)': straordinario_approvato
        })
        
    return pd.DataFrame(report_rows)

st.title("⏱️ Sistema Presenze, Giustificativi & Documenti")

tab1, tab2, tab3, tab4 = st.tabs(["📲 Timbratura In Sede", "📝 Richiesta Giustificativo / Smart", "📁 I Miei Documenti (Cedolini/CU)", "📊 Area Amministratore"])

# --- TAB 1: TIMBRATURE IN SEDE ---
with tab1:
    st.subheader("Registra il tuo ingresso o la tua uscita in Sede")
    with st.form(key="form_timbratura"):
        col_pin, col_date = st.columns([2, 1])
        with col_pin:
            pin_timb_in = st.text_input("Inserisci PIN Personale (es. 1012):", type="password", max_chars=4)
        with col_date:
            data_selezionata = st.date_input("Data Timbratura:", datetime.now())

        st.markdown("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            btn_ing = st.form_submit_button("✅ CONFERMA INGRESSO", type="primary", use_container_width=True)
        with col_b2:
            btn_usc = st.form_submit_button("🛑 CONFERMA USCITA", use_container_width=True)

    if btn_ing or btn_usc:
        pin_clean = str(pin_timb_in).strip() if pin_timb_in else ""
        if pin_clean in DIPENDENTI_PIN:
            info_dip = DIPENDENTI_PIN[pin_clean]
            dipendente = info_dip["nome"]
            giorno_settimana = data_selezionata.weekday()
            
            if info_dip["commerciale"] and giorno_settimana in [1, 2, 3]:
                st.info(f"ℹ️ Nota: {dipendente} ha la trasferta programmata di default per i giorni dal Martedì al Giovedì.")

            tipo_timb = "INGRESSO" if btn_ing else "USCITA"
            data_str = data_selezionata.strftime("%Y-%m-%d")
            ora_attuale = datetime.now().strftime("%H:%M:%S")
            
            nuovo_record = pd.DataFrame([[data_str, ora_attuale, dipendente, tipo_timb]], columns=["Data", "Ora", "Dipendente", "Tipo"])
            nuovo_record.to_csv(DATA_FILE, mode='a', header=False, index=False)
            
            if tipo_timb == "INGRESSO":
                st.success(f"✅ INGRESSO registrato per **{dipendente}** alle **{ora_attuale}**")
            else:
                st.warning(f"🛑 USCITA registrata per **{dipendente}** alle **{ora_attuale}**")
        else:
            st.error("❌ PIN inserito non valido.")

# --- TAB 2: RICHIESTE & ALLEGATI ---
with tab2:
    st.subheader("Invia una richiesta di Giustificativo o Smart Working")
    
    with st.form(key="form_richiesta"):
        col_pin_r, col_tipo_r = st.columns([1.5, 2])
        with col_pin_r:
            pin_req_in = st.text_input("Inserisci PIN Personale (es. 1012):", type="password", max_chars=4)
        with col_tipo_r:
            tipo_giustificativo = st.selectbox("Tipo Richiesta:", ["Permesso (ROL)", "Ferie", "Smart Working", "Malattia", "Lutto", "Altro"])

        st.markdown("---")
        st.write("### 📅 Selezione Data e Orario")
        c1, c2 = st.columns(2)
        with c1:
            d_inizio = st.date_input("Data Inizio / Giorno Permesso:", date.today())
            t_inizio = st.time_input("Ora Inizio (solo per Permesso):", time(9, 0))
        with c2:
            d_fine = st.date_input("Data Fine (solo per Ferie/Smart/Malattia):", date.today())
            t_fine = st.time_input("Ora Fine (solo per Permesso):", time(13, 0))

        note = st.text_area("Note / Motivazione (opzionale):")
        
        file_allegato = st.file_uploader("📎 Carica Certificato Medico o Documento (opzionale - PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
        
        btn_send_req = st.form_submit_button("Invia Richiesta all'Amministratore", type="primary", use_container_width=True)

    if btn_send_req:
        pin_clean = str(pin_req_in).strip() if pin_req_in else ""
        if pin_clean in DIPENDENTI_PIN:
            info_dip = DIPENDENTI_PIN[pin_clean]
            dipendente = info_dip["nome"]
            ore_std = info_dip["ore_std"]
            
            if tipo_giustificativo in ["Permesso (ROL)"]:
                d_fine_calc = d_inizio
                ore_totali = round((datetime.combine(d_inizio, t_fine) - datetime.combine(d_inizio, t_inizio)).total_seconds() / 3600.0, 2)
                ora_ini_str, ora_fin_str = t_inizio.strftime("%H:%M"), t_fine.strftime("%H:%M")
            else:
                d_fine_calc = d_fine
                giorni_totali = max(1, (d_fine - d_inizio).days + 1)
                ore_totali = ore_std * giorni_totali
                ora_ini_str, ora_fin_str = "08:00", "17:00"

            req_id = int(datetime.now().timestamp())
            nome_file_salvato = ""
            
            if file_allegato is not None:
                estensione = file_allegato.name.split(".")[-1]
                nome_file_salvato = f"{req_id}_{pin_clean}_allegato.{estensione}"
                path_salvataggio = os.path.join(DIR_ALLEGATI, nome_file_salvato)
                with open(path_salvataggio, "wb") as f:
                    f.write(file_allegato.getbuffer())

            d_rich = datetime.now().strftime("%Y-%m-%d %H:%M")
            nuova_richiesta = pd.DataFrame([[req_id, d_rich, dipendente, tipo_giustificativo, 
                                             d_inizio.strftime("%Y-%m-%d"), d_fine_calc.strftime("%Y-%m-%d"), 
                                             ora_ini_str, ora_fin_str, ore_totali, note, nome_file_salvato, "IN ATTESA"]], 
                                           columns=["ID", "Data_Richiesta", "Dipendente", "Tipo", "Data_Inizio", "Data_Fine", "Ora_Inizio", "Ora_Fine", "Ore", "Note", "Allegato", "Stato"])
            
            nuova_richiesta.to_csv(RICHIESTE_FILE, mode='a', header=not os.path.exists(RICHIESTE_FILE) or os.stat(RICHIESTE_FILE).st_size == 0, index=False)
            st.success(f"✅ Richiesta di **{tipo_giustificativo}** ({ore_totali}h) inviata con successo per **{dipendente}**!")
        else:
            st.error("❌ PIN inserito non valido.")

# --- TAB 3: AREA PERSONALE DOCUMENTI DIPENDENTE ---
with tab3:
    st.subheader("📥 Consulta e Scarica i tuoi Documenti
