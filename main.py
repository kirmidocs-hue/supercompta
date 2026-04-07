import streamlit as st
import pandas as pd
import pdfplumber
import re

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA")

# --- FONCTIONS DE FORMATAGE ---
def format_montant(val):
    """Règle : Conserver montants identiques, virgules, pas d'espaces."""
    try:
        if val is None or str(val).strip() == "" or str(val).strip() == "0":
            return "0,00"
        # Nettoyage des espaces des milliers et conversion 
        v = str(val).replace(' ', '').replace(',', '.')
        # Extraction du nombre uniquement
        match = re.search(r"(\d+[\.\,]\d{2})|(\d+)", v)
        if match:
            return f"{float(match.group(0).replace(',', '.')):.2f}".replace('.', ',')
        return "0,00"
    except:
        return "0,00"

def clean_libelle_banque(libelle):
    """Règle : Max 27 car., 6 derniers chiffres chèque, noms propres[cite: 35, 36, 37]."""
    if not libelle: return ""
    lib_clean = str(libelle).strip().replace('\n', ' ')
    if re.search(r'ch[eé]que|chq', lib_clean, re.IGNORECASE):
        nums = re.findall(r'\d+', lib_clean)
        if nums:
            lib_clean = f"CHEQUE {nums[-1][-6:]}"
    return lib_clean[:27]

def determiner_compte_banque(libelle, montant_debit):
    """Règle : Selon désignation si débit, sinon 44970000[cite: 30, 31]."""
    try:
        m_debit = float(str(montant_debit).replace(' ', '').replace(',', '.'))
    except:
        m_debit = 0
    
    if m_debit > 0:
        l = str(libelle).upper()
        # Table de correspondance [cite: 32]
        if any(m in l for m in ["FRAIS", "FORFAIT", "EMISSION", "TIMBRE", "RETRAIT", "COMM", "TAXE"]): return "61470000"
        elif "CNSS" in l: return "44410000"
        elif "AMENDIS" in l: return "44110902"
        elif "IAM" in l: return "44110901"
        elif "AZNAG" in l: return "44110017"
        elif any(m in l for m in ["KAOUTAR", "WIAM", "MERIEM", "SOUKAINA"]): return "44320000"
        elif any(m in l for m in ["MOURABAHA", "KRITI", "PRÉLÈVEMENTS", "PRELEVEMENTS"]): return "11175000"
    return "44970000"

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

with tab1:
    st.header("Relevés Bancaires")
    fichiers_pdf = st.file_uploader("Upload PDF (Max 12)", type=['pdf'], accept_multiple_files=True)
    
    if fichiers_pdf:
        if st.button("Extraire les données du PDF"):
            all_banque_rows = []
            
            for pdf_file in fichiers_pdf:
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        # Paramètres de table plus flexibles pour capturer toutes les lignes [cite: 12, 15]
                        table = page.extract_table({
                            "vertical_strategy": "lines", 
                            "horizontal_strategy": "lines",
                            "snap_tolerance": 3,
                        })
                        
                        if not table:
                            # Tentative sans les lignes si le PDF est un flux de texte
                            table = page.extract_table()
                            
                        if table:
                            for row in table:
                                # Nettoyage de la ligne
                                row = [str(cell).strip() if cell else "" for cell in row]
                                
                                # Ignorer les entêtes et les lignes de solde 
                                if not row[0] or any(x in row[0].upper() for x in ["DATE", "SOLDE", "VALEUR"]):
                                    continue
                                
                                # Identification dynamique des colonnes
                                # On cherche la date en début de ligne [cite: 17, 27]
                                if re.search(r'\d{2}/\d{2}', row[0]):
                                    date_op = row[0]
                                    libelle_brut = row[1] if len(row) > 1 else ""
                                    
                                    # Dans bcp de relevés, débit/crédit sont les 2 dernières colonnes [cite: 39, 40]
                                    debit_raw = row[-2] if len(row) > 2 else "0"
                                    credit_raw = row[-1] if len(row) > 2 else "0"
                                    
                                    # Sécurité : si le libellé contient des chiffres de montant, on décale
                                    if any(c.isdigit() for c in libelle_brut) and len(row) > 4:
                                         libelle_brut = " ".join(row[1:-2])
                                    
                                    all_banque_rows.append({
                                        "Code": "5141", # [cite: 26]
                                        "date": date_op, # [cite: 27]
                                        "compte": determiner_compte_banque(libelle_brut, debit_raw), # [cite: 31]
                                        "libellé": clean_libelle_banque(libelle_brut), # [cite: 35]
                                        "débit": format_montant(debit_raw), # 
                                        "crédit": format_montant(credit_raw) # 
                                    })

            if all_banque_rows:
                df_res = pd.DataFrame(all_banque_rows)
                st.success(f"Extraction terminée : {len(df_res)} lignes trouvées.")
                st.dataframe(df_res)
                st.download_button("Télécharger CSV Banque", df_res.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv")
            else:
                st.warning("Aucune donnée trouvée. Vérifiez que le PDF contient un tableau lisible.")
