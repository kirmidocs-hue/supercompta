import streamlit as st
import pandas as pd
import pdfplumber
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA")

# --- FONCTIONS DE FORMATAGE ---
def format_montant(val):
    """Règles strictes : virgule, 2 décimales, pas d'espaces."""
    try:
        if val is None or str(val).strip() == "": return "0,00"
        # Nettoyage pour garder uniquement les chiffres et points/virgules
        v = str(val).replace(' ', '').replace('\xa0', '')
        # Si la valeur contient une virgule, on la remplace temporairement par un point pour le float
        v = v.replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def clean_libelle(libelle):
    """Max 27 car., 6 derniers chiffres chèque, noms propres."""
    if not libelle: return ""
    text = str(libelle).replace('\n', ' ').strip()
    if re.search(r'ch[eé]que|chq', text, re.IGNORECASE):
        nums = re.findall(r'\d+', text)
        if nums:
            return f"CHEQUE {nums[-1][-6:]}"
    return text[:27]

def get_compte(libelle, montant_debit):
    """Règle de compte selon désignation."""
    try:
        m = float(str(montant_debit).replace(',', '.'))
    except:
        m = 0
    if m > 0:
        l = str(libelle).upper()
        if any(w in l for w in ["FRAIS", "FORFAIT", "EMISSION", "TIMBRE", "RETRAIT", "COMM", "TAXE"]): return "61470000"
        if "CNSS" in l: return "44410000"
        if "AMENDIS" in l: return "44110902"
        if "IAM" in l: return "44110901"
        if "AZNAG" in l: return "44110017"
        if any(w in l for w in ["KAOUTAR", "WIAM", "MERIEM", "SOUKAINA"]): return "44320000"
        if any(w in l for w in ["MOURABAHA", "KRITI", "PRÉLÈVEMENTS"]): return "11175000"
    return "44970000"

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

with tab1:
    st.header("Relevés Bancaires")
    files = st.file_uploader("Upload PDF (Max 12)", type=['pdf'], accept_multiple_files=True)
    
    if files and st.button("Extraire les données"):
        all_rows = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    # Stratégie de détection par le texte (plus robuste que les lignes)
                    table = page.extract_table({
                        "vertical_strategy": "text", 
                        "horizontal_strategy": "text"
                    })
                    
                    if table:
                        for row in table:
                            # Nettoyer les cellules
                            r = [str(c).strip() if c else "" for c in row]
                            
                            # RÈGLES D'EXTRACTION
                            # On cherche une ligne qui commence par une date (ex: 01/03)
                            if r and re.match(r'\d{2}/\d{2}', r[0]):
                                libelle_raw = r[1] if len(r) > 1 else ""
                                
                                # Débit/Crédit sont généralement en fin de ligne
                                debit = r[-2] if len(r) > 2 else "0"
                                credit = r[-1] if len(r) > 2 else "0"
                                
                                all_rows.append({
                                    "Code": "5141",
                                    "date": r[0],
                                    "compte": get_compte(libelle_raw, debit),
                                    "libellé": clean_libelle(libelle_raw),
                                    "débit": format_montant(debit),
                                    "crédit": format_montant(credit)
                                })

        if all_rows:
            df = pd.DataFrame(all_rows)
            st.success(f"Extraction réussie : {len(df)} lignes.")
            st.dataframe(df)
            st.download_button("Télécharger CSV", df.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv")
        else:
            st.error("Structure non détectée. Essayez d'ajuster les colonnes dans le code.")
