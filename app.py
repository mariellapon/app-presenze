import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import os
import calendar

st.set_page_config(page_title="Rilevazione Presenze & Documenti", page_icon="⏱️", layout="wide")

TZ_ITALIA = ZoneInfo("Europe/Rome")

def get_now_italy():
    return datetime.now(TZ_ITALIA)

# File e Cartelle di sistema
DATA_FILE = "presenze_log.csv"
RICHIESTE_FILE = "richieste_log.csv"
CONFIG_ORARI_FILE = "orari_dipendenti.csv"
DIR_ALLEGATI = "allegati_richieste"
DIR_DOCUMENTI = "documenti_dipendenti"

for directory in [DIR_ALLEGATI, DIR_DOCUMENTI]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Mappa Dipendenti con orari spezzati di default (Mattina + Pausa + Pomeriggio)
DIPENDENTI_DEFAULT = {
    "1001": {"nome": "AGOSTINELLI FEDERICA", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1002": {"nome": "BISCHI MICHELE", "profilo": "Commerciale", "ore_std": 8.0, "commerciale": True, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1003": {"nome": "BORINI RAFFAELE", "profilo": "Part-Time 6h / Commerciale", "ore_std": 6.0, "commerciale": True, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "16:30"},
    "1004": {"nome": "BUGLIONI SARAH", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1005": {"nome": "CUPIDO PATRIZIA", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1006": {"nome": "D'APONTE PAOLO", "profilo": "Stampatore Turnista", "ore_std": 8.0, "commerciale": False, "ing_m": "06:00", "usc_m": "14:00", "ing_p": "--:--", "usc_p": "--:--"},
    "1007": {"nome": "MANZOTTI FRANCESCA", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1008": {"nome": "NOVELLI LUCA", "profilo": "Stampatore Turnista", "ore_std": 8.0, "commerciale": False, "ing_m": "06:00", "usc_m": "14:00", "ing_p": "--:--", "usc_p": "--:--"},
    "1009": {"nome": "NUZZIELLO CARLO", "profilo": "Commerciale", "ore_std": 8.0, "commerciale": True, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1010": {"nome": "PALLOTTA ANNABELLA", "profilo": "Part-Time 4h / Smart", "ore_std": 4.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "--:--", "usc_p": "--:--"},
    "1011": {"nome": "PIERINI FRANCESCO", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1012": {"nome": "PONTILLO MARIELLA", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"},
    "1013": {"nome": "SANTOLINI MAURO", "profilo": "Standard Ufficio", "ore_std": 8.0, "commerciale": False, "ing_m": "08:30", "usc_m": "12:30", "ing_p": "14:30", "usc_p": "18:30"}
}

def carica_orari_dipendenti():
    if os.path.exists(CONFIG_ORARI_FILE):
        try:
            df = pd.read_csv(CONFIG_ORARI_FILE, dtype={'PIN': str})
            orari_dict = {}
            for _, row in df.iterrows():
                orari_dict[str(row['PIN'])] = {
                    "nome": row['Nome'],
                    "profilo": row['Profilo'],
                    "ore_std": float(row['Ore_Std']),
                    "commerciale": bool(row['Commerciale']),
                    "ing_m": str(row.get('Ingresso_Mattina', '08:30')),
                    "usc_m": str(row.get('Uscita_Mattina', '12:30')),
                    "ing_p": str(row.get('Ingresso_Pomeriggio', '14:30')),
                    "usc_p": str(row.get('Uscita_Pomeriggio', '18:30'))
                }
            return orari_dict
        except Exception:
            return DIPENDENTI_DEFAULT
    else:
        rows = []
        for pin, info in DIPENDENTI_DEFAULT.items():
            rows.append({
                "PIN": pin, 
                "Nome": info["nome"], 
                "Profilo": info["profilo"], 
                "Ore_Std": info["ore_std"], 
                "Commerciale": info["commerciale"],
                "Ingresso_Mattina": info["ing_m"],
                "Uscita_Mattina": info["usc_m"],
                "Ingresso_Pomeriggio": info["ing_p"],
                "Uscita_Pomeriggio": info["usc_p"]
            })
        pd.DataFrame(rows).to_csv(CONFIG_ORARI_FILE, index=False)
        return DIPENDENTI_DEFAULT

DIPENDENTI_PIN = carica_orari_dipendenti()
MAPPA_NOMI_PIN = {v["nome"]: k for k, v in DIPENDENTI_PIN.items()}

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo"]).to_csv(DATA_FILE, index=False)

if not os.path.exists(RICHIESTE_FILE):
    pd.DataFrame(columns=["ID", "Data_Richiesta", "Dipendente", "Tipo", "Data_Inizio", "Data_Fine", "Ora_Inizio", "Ora_Fine", "Ore", "Note", "Allegato", "Stato"]).to_csv(RICHIESTE_FILE, index=False)

def elabora_presenze_e_quadratura(df_timb, df_rich):
    if df_timb.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    df = df_timb.copy()
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Ora'])
    df = df.sort_values(['Dipendente', 'Datetime'])
    
    dettagli_rows = []
    giornaliero_dict = {}

    for (dip, dt), group in df.groupby(['Dipendente', 'Data']):
        pin_dip = MAPPA_NOMI_PIN.get(dip)
        ore_std = DIPENDENTI_PIN[pin_dip]["ore_std"] if pin_dip else 8.0
        
        ingressi = group[group['Tipo'] == 'INGRESSO'].to_dict('records')
        uscite = group[group['Tipo'] == 'USCITA'].to_dict('records')
        
        totale_secondi_giorno = 0
        idx_usc = 0
        
        for ing in ingressi:
            while idx_usc < len(uscite) and uscite[idx_usc]['Datetime'] <= ing['Datetime']:
                idx_usc += 1
                
            ora_ing_str = ing['Ora']
            ora_usc_str = "In corso"
            ore_sessione = 0.0
            
            if idx_usc < len(uscite):
                usc = uscite[idx_usc]
                ora_usc_str = usc['Ora']
                sec = (usc['Datetime'] - ing['Datetime']).total_seconds()
                ore_sessione = round(sec / 3600.0, 2)
                totale_secondi_giorno += sec
                idx_usc += 1

            dettagli_rows.append({
                'Data': dt,
                'Dipendente': dip,
                'Ora Ingresso': ora_ing_str,
                'Ora Uscita': ora_usc_str,
                'Ore Sessione': ore_sessione if ora_usc_str != "In corso" else "In corso"
            })

        ore_lavorate = round(totale_secondi_giorno / 3600.0, 2)
        
        ore_giustificate = 0.0
        if not df_rich.empty and "Stato" in df_rich.columns:
            rich_appr = df_rich[(df_rich["Dipendente"] == dip) & (df_rich["Stato"] == "APPROVATO")]
            for _, r in rich_appr.iterrows():
                if str(r["Data_Inizio"]) <= dt <= str(r["Data_Fine"]):
                    ore_giustificate += float(r.get("Ore", 0.0))

        totale_coperto = ore_lavorate + ore_giustificate
        ore_mancanti = max(0.0, round(ore_std - totale_coperto, 2))
        straordinario = max(0.0, round(totale_coperto - ore_std, 2))
        straordinario_30min = (straordinario // 0.5) * 0.5

        giornaliero_dict[(dip, dt)] = {
            'Data': dt,
            'Dipendente': dip,
            'Ore Contratto': ore_std,
            'Ore Lavorate Effettive': ore_lavorate,
            'Ore Giustificate (Approvate)': ore_giustificate,
            'Ore Mancanti da Giustificare': ore_mancanti,
            'Straordinario Calcolato': straordinario_30min
        }

    return pd.DataFrame(dettagli_rows), pd.DataFrame(list(giornaliero_dict.values()))

def genera_calendario_assenze(df_rich, mese, anno):
    nomi_dip = sorted([v["nome"] for v in DIPENDENTI_PIN.values()])
    num_giorni = calendar.monthrange(anno, mese)[1]
    giorni = [date(anno, mese, g) for g in range(1, num_giorni + 1)]
    giorni_str = [g.strftime("%Y-%m-%d") for g in giorni]
    
    df_cal = pd.DataFrame(index=nomi_dip, columns=giorni_str)
    df_cal = df_cal.fillna("")
    
    if not df_rich.empty and "Stato" in df_rich.columns:
        rich_appr = df_rich[df_rich["Stato"] == "APPROVATO"]
        for _, r in rich_appr.iterrows():
            dip = r["Dipendente"]
            tipo = r["Tipo"]
            ore = r["Ore"]
            d_ini = datetime.strptime(str(r["Data_Inizio"]), "%Y-%m-%d").date()
            d_fin = datetime.strptime(str(r["Data_Fine"]), "%Y-%m-%d").date()
            
            for g in giorni:
                if d_ini <= g <= d_fin:
                    g_str = g.strftime("%Y-%m-%d")
                    if dip in df_cal.index and g_str in df_cal.columns:
                        etichetta = f"{tipo}" if tipo != "Permesso (ROL)" else f"ROL ({ore}h)"
                        att_val = df_cal.at[dip, g_str]
                        df_cal.at[dip, g_str] = f"{att_val}, {etichetta}".strip(", ")
                        
    return df_cal

st.title("Sistema Presenze, Giustificativi & Documenti")

tab1, tab2, tab3, tab4 = st.tabs(["Timbratura In Sede", "Richiesta Giustificativo / Smart", "I Miei Documenti (Cedolini/CU)", "Area Amministratore"])

# --- TAB 1: TIMBRATURE IN SEDE ---
with tab1:
    st.subheader("Registra il tuo ingresso o la tua uscita in Sede")
    with st.form(key="form_timbratura"):
        col_pin, col_date = st.columns([2, 1])
        with col_pin:
            pin_timb_in = st.text_input("Inserisci PIN Personale (es. 1012):", type="password", max_chars=4)
        with col_date:
            data_selezionata = st.date_input("Data Timbratura:", get_now_italy().date())

        st.markdown("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            btn_ing = st.form_submit_button("CONFERMA INGRESSO", type="primary", use_container_width=True)
        with col_b2:
            btn_usc = st.form_submit_button("CONFERMA USCITA", use_container_width=True)

    if btn_ing or btn_usc:
        pin_clean = str(pin_timb_in).strip() if pin_timb_in else ""
        if pin_clean in DIPENDENTI_PIN:
            info_dip = DIPENDENTI_PIN[pin_clean]
            dipendente = info_dip["nome"]
            giorno_settimana = data_selezionata.weekday()
            
            if info_dip["commerciale"] and giorno_settimana in [1, 2, 3]:
                st.info(f"Nota: {dipendente} ha la trasferta programmata di default per i giorni dal Martedi al Giovedi.")

            tipo_timb = "INGRESSO" if btn_ing else "USCITA"
            data_str = data_selezionata.strftime("%Y-%m-%d")
            ora_attuale = get_now_italy().strftime("%H:%M:%S")
            
            nuovo_record = pd.DataFrame([[data_str, ora_attuale, dipendente, tipo_timb]], columns=["Data", "Ora", "Dipendente", "Tipo"])
            nuovo_record.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0, index=False)
            
            if tipo_timb == "INGRESSO":
                st.success(f"INGRESSO registrato per **{dipendente}** alle **{ora_attuale}**")
            else:
                st.warning(f"USCITA registrata per **{dipendente}** alle **{ora_attuale}**")
        else:
            st.error("PIN inserito non valido.")

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
        st.write("### Selezione Data e Orario")
        c1, c2 = st.columns(2)
        with c1:
            d_inizio = st.date_input("Data Inizio / Giorno Permesso:", get_now_italy().date())
            t_inizio = st.time_input("Ora Inizio (solo per Permesso):", time(9, 0))
        with c2:
            d_fine = st.date_input("Data Fine (solo per Ferie/Smart/Malattia):", get_now_italy().date())
            t_fine = st.time_input("Ora Fine (solo per Permesso):", time(13, 0))

        note = st.text_area("Note / Motivazione (opzionale):")
        file_allegato = st.file_uploader("Carica Certificato Medico o Documento (opzionale - PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
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
                ora_ini_str, ora_fin_str = "08:30", "18:30"

            req_id = int(get_now_italy().timestamp())
            nome_file_salvato = ""
            
            if file_allegato is not None:
                estensione = file_allegato.name.split(".")[-1]
                nome_file_salvato = f"{req_id}_{pin_clean}_allegato.{estensione}"
                path_salvataggio = os.path.join(DIR_ALLEGATI, nome_file_salvato)
                with open(path_salvataggio, "wb") as f:
                    f.write(file_allegato.getbuffer())

            d_rich = get_now_italy().strftime("%Y-%m-%d %H:%M")
            nuova_richiesta = pd.DataFrame([[req_id, d_rich, dipendente, tipo_giustificativo, 
                                             d_inizio.strftime("%Y-%m-%d"), d_fine_calc.strftime("%Y-%m-%d"), 
                                             ora_ini_str, ora_fin_str, ore_totali, note, nome_file_salvato, "IN ATTESA"]], 
                                           columns=["ID", "Data_Richiesta", "Dipendente", "Tipo", "Data_Inizio", "Data_Fine", "Ora_Inizio", "Ora_Fine", "Ore", "Note", "Allegato", "Stato"])
            
            nuova_richiesta.to_csv(RICHIESTE_FILE, mode='a', header=not os.path.exists(RICHIESTE_FILE) or os.stat(RICHIESTE_FILE).st_size == 0, index=False)
            st.success(f"Richiesta di **{tipo_giustificativo}** ({ore_totali}h) inviata con successo per **{dipendente}**!")
        else:
            st.error("PIN inserito non valido.")

# --- TAB 3: AREA PERSONALE DOCUMENTI DIPENDENTE ---
with tab3:
    st.subheader("Consulta e Scarica i tuoi Document
