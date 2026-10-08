import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
import os

# Impostazione pagina
st.set_page_config(page_title="Rilevazione Presenze & Documenti", page_icon="⏱️", layout="wide")

# Fuso Orario Italiano
TZ_ITALIA = ZoneInfo("Europe/Rome")

def get_now_italy():
    return datetime.now(TZ_ITALIA)

# File e Cartelle di sistema
DATA_FILE = "presenze_log.csv"
RICHIESTE_FILE = "richieste_log.csv"
DIR_ALLEGATI = "allegati_richieste"
DIR_DOCUMENTI = "documenti_dipendenti"

for directory in [DIR_ALLEGATI, DIR_DOCUMENTI]:
    if not os.path.exists(directory):
        os.makedirs(directory)

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
    "1003": {"nome": "BORINI RAFFAELE", "ore_std": 6.0, "commerciale": True},
    "1004": {"nome": "BUGLIONI SARAH", "ore_std": 8.0, "commerciale": False},
    "1005": {"nome": "CUPIDO PATRIZIA", "ore_std": 8.0, "commerciale": False},
    "1006": {"nome": "D'APONTE PAOLO", "ore_std": 8.0, "commerciale": False},
    "1007": {"nome": "MANZOTTI FRANCESCA", "ore_std": 8.0, "commerciale": False},
    "1008": {"nome": "NOVELLI LUCA", "ore_std": 8.0, "commerciale": False},
    "1009": {"nome": "NUZZIELLO CARLO", "ore_std": 8.0, "commerciale": True},
    "1010": {"nome": "PALLOTTA ANNABELLA", "ore_std": 4.0, "commerciale": False},
    "1011": {"nome": "PIERINI FRANCESCO", "ore_std": 8.0, "commerciale": False},
    "1012": {"nome": "PONTILLO MARIELLA", "ore_std": 8.0, "commerciale": False},
    "1013": {"nome": "SANTOLINI MAURO", "ore_std": 8.0, "commerciale": False}
}

MAPPA_NOMI_PIN = {v["nome"]: k for k, v in DIPENDENTI_PIN.items()}

def elabora_presenze_e_dettagli(df_timb):
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

        ore_totali_giorno = round(totale_secondi_giorno / 3600.0, 2)
        straordinario_grezzo = max(0.0, ore_totali_giorno - ore_std)
        straordinario_30min = (straordinario_grezzo // 0.5) * 0.5

        giornaliero_dict[(dip, dt)] = {
            'Data': dt,
            'Dipendente': dip,
            'Ore Lavorate Totali': ore_totali_giorno,
            'Ore Contratto': ore_std,
            'Straordinario Calcolato': straordinario_30min
        }

    df_dettaglio = pd.DataFrame(dettagli_rows)
    df_riepilogo = pd.DataFrame(list(giornaliero_dict.values()))
    
    return df_dettaglio, df_riepilogo

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
                ora_ini_str, ora_fin_str = "08:00", "17:00"

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
                    st.download_button(
                        label=f"Scarica: {nome_visibile}",
                        data=file_data,
                        file_name=nome_visibile,
                        key=f"dl_{f}"
                    )
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
        st.write("### Quadro Contratti e Inquadramenti Part-Time / Trasferte")
        
        inquadr_rows = []
        for p, d in DIPENDENTI_PIN.items():
            inquadr_rows.append({
                "PIN": p,
                "Dipendente": d["nome"],
                "Ore Standard/Giorno": f"{d['ore_std']} h",
                "Ruolo / Note Speciali": "Commerciale (Trasferta Mar-Gio)" if d["commerciale"] else ("Part-time 4h (Smart 2 gg var.)" if p == "1010" else ("Part-time 6h" if p == "1003" else "Standard Full-Time"))
            })
        st.dataframe(pd.DataFrame(inquadr_rows), use_container_width=True)

        st.markdown("---")
        st.write("### Richieste In Sospeso e Gestione Allegati")
        
        try:
            df_rich = pd.read_csv(RICHIESTE_FILE)
        except Exception:
            df_rich = pd.DataFrame()
            
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
                                st.download_button(
                                    label="Scarica / Visualizza Certificato Allegato",
                                    data=af,
                                    file_name=str(row['Allegato']),
                                    key=f"down_att_{row['ID']}"
                                )
                    
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
        st.write("### Storico Timbrature Dettagliate e Calcolo Presenze")
        try:
            df_timb = pd.read_csv(DATA_FILE)
        except Exception:
            df_timb = pd.DataFrame()
            
        df_dettaglio, df_riepilogo = elabora_presenze_e_dettagli(df_timb)

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
            st.write("#### 📊 Riepilogo Giornaliero Totale e Straordinari")
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
        st.caption("Usa questo pulsante per svuotare lo storico delle timbrature di prova.")
        if st.button("️ Svuota Storico Timbrature (Reset)", type="secondary"):
            df_init = pd.DataFrame(columns=["Data", "Ora", "Dipendente", "Tipo"])
            df_init.to_csv(DATA_FILE, index=False)
            st.success("Storico timbrature resettato con successo!")
            st.rerun()

    elif password != "":
        st.error("Password errata.")
