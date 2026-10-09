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
    st.subheader("Consulta e Scarica i tuoi Documenti Personali (Cedolini, CU)")
    col_p1, _ = st.columns([1.5, 2])
    with col_p1:
        pin_doc = st.text_input("Inserisci il tuo PIN Personale:", type="password", max_chars=4, key="pin_doc_view")
    
    pin_doc_clean = str(pin_doc).strip() if pin_doc else ""
    if pin_doc_clean in DIPENDENTI_PIN:
        dip_nome = DIPENDENTI_PIN[pin_doc_clean]["nome"]
        st.info(f"Area Personale di: **{dip_nome}**")
        files_dip = [f for f in os.listdir(DIR_DOCUMENTI) if f.startswith(f"{pin_doc_clean}_")]
        
        if files_dip:
            st.write("### Documenti Disponibili:")
            for f in files_dip:
                path_f = os.path.join(DIR_DOCUMENTI, f)
                nome_visibile = f.replace(f"{pin_doc_clean}_", "")
                with open(path_f, "rb") as file_data:
                    st.download_button(label=f"Scarica: {nome_visibile}", data=file_data, file_name=nome_visibile, key=f"dl_{f}")
        else:
            st.warning("Nessun documento caricato al momento per il tuo profilo.")
    elif pin_doc_clean != "":
        st.error("PIN errato.")

# --- TAB 4: AREA AMMINISTRATORE ---
with tab4:
    st.subheader("Gestione Amministrazione, Approvazioni & Documenti")
    password = st.text_input("Password Amministratore:", type="password", key="pass_admin")
    
    if password == "1234":
        
        st.markdown("---")
        st.write("### 📅 Calendario Mensile Assenze & Permessi Approvati")
        
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            mese_sel = st.selectbox("Seleziona Mese:", list(range(1, 13)), index=get_now_italy().month - 1)
        with c_m2:
            anno_sel = st.number_input("Seleziona Anno:", min_value=2024, max_value=2030, value=get_now_italy().year)
            
        try:
            df_rich = pd.read_csv(RICHIESTE_FILE)
        except Exception:
            df_rich = pd.DataFrame()

        df_cal_assenze = genera_calendario_assenze(df_rich, mese_sel, anno_sel)
        st.dataframe(df_cal_assenze, use_container_width=True)

        st.markdown("---")
        st.write("### ⚙️ Gestione Orari Personalizzati, Pausa Pranzo e Turni")
        
        with st.expander("Modifica Orario e Fasce Lavorative di un Dipendente"):
            with st.form(key="form_edit_orario"):
                pin_edit = st.selectbox("Seleziona Dipendente da Modificare:", list(DIPENDENTI_PIN.keys()), format_func=lambda x: f"{x} - {DIPENDENTI_PIN[x]['nome']}")
                info_att = DIPENDENTI_PIN[pin_edit]
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    nuovo_profilo = st.selectbox("Profilo / Ruolo:", ["Standard Ufficio", "Stampatore Turnista", "Commerciale", "Part-Time 6h", "Part-Time 4h", "Personalizzato"])
                    nuove_ore_std = st.number_input("Ore Contrattuali Giornaliere:", min_value=1.0, max_value=12.0, value=float(info_att["ore_std"]), step=0.5)
                    is_comm = st.checkbox("Commerciale (Trasferta Mar-Gio)?", value=bool(info_att["commerciale"]))
                
                with col_e2:
                    st.write("**Fasce Orarie e Pausa Pranzo:**")
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        n_ing_m = st.text_input("Ingresso Mattina:", value=info_att.get("ing_m", "08:30"))
                        n_ing_p = st.text_input("Ingresso Pomeriggio (dopo pausa):", value=info_att.get("ing_p", "14:30"))
                    with c_m2:
                        n_usc_m = st.text_input("Uscita Mattina (inizio pausa):", value=info_att.get("usc_m", "12:30"))
                        n_usc_p = st.text_input("Uscita Pomeriggio:", value=info_att.get("usc_p", "18:30"))

                btn_save_orario = st.form_submit_button("Salva Configurazione Orario", type="primary")
                
                if btn_save_orario:
                    DIPENDENTI_PIN[pin_edit] = {
                        "nome": DIPENDENTI_PIN[pin_edit]["nome"],
                        "profilo": nuovo_profilo,
                        "ore_std": nuove_ore_std,
                        "commerciale": is_comm,
                        "ing_m": n_ing_m,
                        "usc_m": n_usc_m,
                        "ing_p": n_ing_p,
                        "usc_p": n_usc_p
                    }
                    rows = []
                    for p, d in DIPENDENTI_PIN.items():
                        rows.append({
                            "PIN": p, 
                            "Nome": d["nome"], 
                            "Profilo": d["profilo"], 
                            "Ore_Std": d["ore_std"], 
                            "Commerciale": d["commerciale"],
                            "Ingresso_Mattina": d["ing_m"],
                            "Uscita_Mattina": d["usc_m"],
                            "Ingresso_Pomeriggio": d["ing_p"],
                            "Uscita_Pomeriggio": d["usc_p"]
                        })
                    pd.DataFrame(rows).to_csv(CONFIG_ORARI_FILE, index=False)
                    st.success(f"Orario e Pausa Pranzo aggiornati per {DIPENDENTI_PIN[pin_edit]['nome']}!")
                    st.rerun()

        inquadr_rows = []
        for p, d in DIPENDENTI_PIN.items():
            inquadr_rows.append({
                "PIN": p,
                "Dipendente": d["nome"],
                "Profilo": d["profilo"],
                "Ore Contratto": f"{d['ore_std']} h",
                "Mattina": f"{d['ing_m']} - {d['usc_m']}",
                "Pausa Pranzo": f"{d['usc_m']} - {d['ing_p']}" if d['ing_p'] != "--:--" else "Nessuna",
                "Pomeriggio": f"{d['ing_p']} - {d['usc_p']}" if d['ing_p'] != "--:--" else "Nessuno"
            })
        st.dataframe(pd.DataFrame(inquadr_rows), use_container_width=True)

        st.markdown("---")
        st.write("### Richieste In Sospeso e Gestione Allegati")
        
        richieste_sospese = df_rich[df_rich["Stato"] == "IN ATTESA"] if not df_rich.empty and "Stato" in df_rich.columns else pd.DataFrame()
        
        if richieste_sospese.empty:
            st.success("Nessuna richiesta in attesa di approvazione.")
        else:
            for idx, row in richieste_sospese.iterrows():
                with st.expander(f"{row['Tipo']} - {row['Dipendente']} ({row['Data_Inizio']})"):
                    st.write(f"**Dipendente:** {row['Dipendente']}")
                    st.write(f"**Tipo:** {row['Tipo']}")
                    st.write(f"**Periodo:** dal {row['Data_Inizio']} al {row['Data_Fine']} ({row['Ore']} ore)")
                    st.write(f"**Note:** {row['Note']}")
                    
                    if pd.notna(row.get('Allegato')) and str(row['Allegato']).strip() != "":
                        file_path = os.path.join(DIR_ALLEGATI, str(row['Allegato']))
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as af:
                                st.download_button(label="Scarica Certificato Allegato", data=af, file_name=str(row['Allegato']), key=f"down_att_{row['ID']}")
                    
                    col_app, col_rif = st.columns(2)
                    with col_app:
                        if st.button("Approva", key=f"app_{row['ID']}"):
                            df_rich.loc[df_rich["ID"] == row["ID"], "Stato"] = "APPROVATO"
                            df_rich.to_csv(RICHIESTE_FILE, index=False)
                            st.success("Approvato!")
                            st.rerun()
                    with col_rif:
                        if st.button("Rifiuta", key=f"rif_{row['ID']}"):
                            df_rich.loc[df_rich["ID"] == row["ID"], "Stato"] = "RIFIUTATO"
                            df_rich.to_csv(RICHIESTE_FILE, index=False)
                            st.error("Rifiutato!")
                            st.rerun()

        st.markdown("---")
        st.write("### ⏱️ Storico Timbrature & Quadratura Presenze/Assenze")
        try:
            df_timb = pd.read_csv(DATA_FILE)
        except Exception:
            df_timb = pd.DataFrame()
            
        df_dettaglio, df_riepilogo = elabora_presenze_e_quadratura(df_timb, df_rich)

        if not df_dettaglio.empty:
            nomicompleti = ["TUTTI"] + sorted([d["nome"] for d in list(DIPENDENTI_PIN.values())])
            dip_filtro = st.selectbox("Filtra Storico per Dipendente:", nomicompleti)
            
            if dip_filtro != "TUTTI":
                df_det_show = df_dettaglio[df_dettaglio["Dipendente"] == dip_filtro]
                df_riep_show = df_riepilogo[df_riepilogo["Dipendente"] == dip_filtro]
            else:
                df_det_show = df_dettaglio
                df_riep_show = df_riepilogo

            st.write("#### 📍 Dettaglio Singole Sessioni (Ora Ingresso - Ora Uscita)")
            st.dataframe(df_det_show, use_container_width=True)

            st.markdown("---")
            st.write("#### 📊 Bilancio Quadratura Giornaliera (Lavorate vs Mancanti/Straordinari)")
            st.dataframe(df_riep_show, use_container_width=True)
        else:
            st.info("Nessuna timbratura registrata al momento.")

        st.markdown("---")
        st.write("### Carica Cedolini / CU per un Dipendente")
        with st.form(key="form_upload_admin"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                pin_destinatario = st.selectbox("Seleziona Dipendente:", list(DIPENDENTI_PIN.keys()), format_func=lambda x: f"{x} - {DIPENDENTI_PIN[x]['nome']}")
            with col_d2:
                doc_upload = st.file_uploader("Carica Documento PDF (es. Cedolino_Ottobre.pdf):", type=["pdf", "png", "jpg"])
            
            btn_pubblica = st.form_submit_button("Pubblica Documento nell'Area Dipendente", type="primary")
            
        if btn_pubblica:
            if doc_upload is not None:
                nome_salvato = f"{pin_destinatario}_{doc_upload.name}"
                dest_path = os.path.join(DIR_DOCUMENTI, nome_salvato)
                with open(dest_path, "wb") as f:
                    f.write(doc_upload.getbuffer())
                st.success(f"Documento caricato con successo per **{DIPENDENTI_PIN[pin_destinatario]['nome']}**!")
            else:
                st.error("Seleziona prima un file da caricare.")

        st.markdown("---")
        st.write("### Storico Completo Giustificativi")
        if not df_rich.empty:
            st.dataframe(df_rich, use_container_width=True)

        st.markdown("---")
        st.write("### ⚠️ Manutenzione Dati Presenze")
        if st.button("🗑️ Svuota Storico Timbrature di Prova (Reset)", type="secondary"):
            pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo"]).to_csv(DATA_FILE, index=False)
            st.success("Storico timbrature resettato con successo!")
            st.rerun()

    elif password != "":
        st.error("Password errata.")
