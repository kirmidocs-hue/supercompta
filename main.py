import streamlit as st
import pandas as pd
import pdfplumber
import re

# --- FONCTION DE FORMATAGE STRICT (VIRGULE) ---
def format_montant(val):
    try:
        if val is None or str(val).strip() == "": 
            return "0,00"
        # Nettoyage des caractères et conversion
        v = str(val).replace(' ', '').replace(',', '.')
        # Extraction du premier nombre trouvé (pour éviter les textes collés)
        match = re.search(r"(\d+\.?\d*)", v)
        if match:
            return f"{float(match.group(1)):.2f}".replace('.', ',')
        return "0,00"
    except:
        return "0,00"

# --- NETTOYAGE DU LIBELLÉ (MAX 27 CARACTÈRES) ---
def clean_libelle(libelle):
    if not libelle: return ""
    libelle = str(libelle).strip().replace('\n', ' ')
    # Gestion des chèques (6 derniers chiffres)
    if re.search(r'ch[eé]que|chq', libelle, re.IGNORECASE):
        nums = re.findall(r'\d+', libelle)
        if nums:
            libelle = f"CHEQUE {nums[-1][-6:]}"
    return libelle[:27]

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA")

tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

# --- 1. RELEVÉS BANCAIRES (MOTEUR PDF) ---
with tab1:
    st.header("Relevés Bancaires (PDF)")
    fichiers_pdf = st.file_uploader("Charger vos relevés PDF (Max 12)", type=['pdf'], accept_multiple_files=True)
    
    if fichiers_pdf:
        if st.button("Extraire les données du PDF"):
            all_rows = []
            for pdf_file in fichiers_pdf:
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        table = page.extract_table()
                        if not table: continue
                        
                        for row in table:
                            # Ignorer les lignes vides ou de solde
                            if not row or not row[0] or "SOLDE" in str(row).upper():
                                continue
                            
                            # On récupère les valeurs réelles du PDF
                            date_fac = str(row[0])
                            libelle_brut = str(row[1])
                            # On assume Date=0, Libellé=1, Débit=2, Crédit=3
                            val_debit = row[2] if len(row) > 2 else "0"
                            val_credit = row[3] if len(row) > 3 else "0"
                            
                            all_rows.append({
                                "Code": "5141",
                                "date": date_fac,
                                "compte": "44970000", # Compte par défaut à ajuster selon vos règles
                                "libellé": clean_libelle(libelle_brut),
                                "débit": format_montant(val_debit),
                                "crédit": format_montant(val_credit)
                            })
            
            if all_rows:
                df_res = pd.DataFrame(all_rows)
                st.success(f"Extraction réussie : {len(df_res)} opérations trouvées.")
                st.dataframe(df_res)
                # Export CSV avec séparateur point-virgule
                csv = df_res.to_csv(index=False, sep=";").encode('utf-8')
                st.download_button("Télécharger CSV Banque", csv, "banque_compta.csv", "text/csv")

# --- (Les sections Factures et Salaires restent identiques à vos besoins précédents) ---
