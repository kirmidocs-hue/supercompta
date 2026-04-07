import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA") # [cite: 1]

# --- FONCTIONS DE FORMATAGE ---
def format_montant(val):
    """
    RÈGLES STRICTES : Virgule comme séparateur, 2 décimales, pas d'espaces.
    """
    try:
        if pd.isna(val) or val == "":
            return "0,00"
        return f"{float(val):.2f}".replace('.', ',')
    except:
        return "0,00"

def clean_libelle_banque(libelle):
    """
    RÈGLES LIBELLÉ : Max 27 caractères, 6 derniers chiffres chèque[cite: 35, 36].
    """
    libelle = str(libelle).strip()
    if re.search(r'ch[eé]que|chq', libelle, re.IGNORECASE):
        numeros = re.findall(r'\d+', libelle)
        if numeros:
            dernier_num = numeros[-1][-6:]
            libelle = f"CHEQUE {dernier_num}"
    return libelle[:27]

def determiner_compte_banque(libelle, montant_debit):
    """
    RÈGLES COMPTES : Selon désignation si débit, sinon 44970000[cite: 30, 31, 32].
    """
    if montant_debit > 0:
        l = str(libelle).upper()
        if any(m in l for m in ["FRAIS", "FORFAIT", "EMISSION", "TIMBRE", "RETRAIT", "COMM", "TAXE"]): return "61470000" # [cite: 32]
        elif "CNSS" in l: return "44410000" # [cite: 32]
        elif "AMENDIS" in l: return "44110902" # [cite: 32]
        elif "IAM" in l: return "44110901" # [cite: 32]
        elif "AZNAG" in l: return "44110017" # [cite: 32]
        elif any(m in l for m in ["KAOUTAR", "WIAM", "MERIEM", "SOUKAINA"]): return "44320000" # [cite: 32]
        elif any(m in l for m in ["MOURABAHA", "KRITI", "PRÉLÈVEMENTS", "PRELEVEMENTS"]): return "11175000" # [cite: 32]
        return "44970000" # [cite: 31]
    return ""

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"]) # [cite: 2, 3, 4]

# --- 1. RELEVÉS BANCAIRES ---
with tab1:
    st.header("Relevés Bancaires")
    fichiers = st.file_uploader("Upload PDF ou Images (Max 12)", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True) # [cite: 6, 21]
    
    if fichiers:
        if len(fichiers) > 12:
            st.error("Maximum 12 fichiers.")
        else:
            if st.button("Extraire les données"): # [cite: 22]
                st.info("Extraction en cours...")
                # Ici la logique d'extraction (PDF/JPG vers DataFrame)
                # Le format de sortie CSV sera : Code/date/compte/libellé/débit/crédit 

# --- 2. FACTURES ---
with tab2:
    st.header("Factures")
    f_files = st.file_uploader("Upload Factures (Max 20)", type=['xlsx', 'csv'], accept_multiple_files=True) # [cite: 7]
    
    if f_files:
        if st.button("Traiter les factures"):
            all_rows = []
            for f in f_files:
                df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
                for _, row in df.iterrows():
                    ttc = float(row.get('TTC', 0))
                    ht = ttc / 1.2 # [cite: 64]
                    tva = ttc - ht # [cite: 76]
                    base = {"Code journal": "ACH", "Date de facture": row.get('Date'), "Référence": row.get('Référence'), "Libellé écriture": row.get('Nom Société')}
                    
                    # Exactement 3 lignes [cite: 45, 57]
                    all_rows.append({**base, "Compte": "61110000", "Montant débit": format_montant(ht), "Montant crédit": "0,00"})
                    all_rows.append({**base, "Compte": "34550000", "Montant débit": format_montant(tva), "Montant crédit": "0,00"})
                    all_rows.append({**base, "Compte": "44110000", "Montant débit": "0,00", "Montant crédit": format_montant(ttc)})
            
            df_fac = pd.DataFrame(all_rows, columns=["Code journal", "Date de facture", "Référence", "Compte", "Libellé écriture", "Montant débit", "Montant crédit"])
            st.dataframe(df_fac)
            st.download_button("Télécharger CSV Factures", df_fac.to_csv(index=False, sep=";").encode('utf-8'), "factures.csv") # [cite: 83]

# --- 3. TABLE SALAIRE ---
with tab3:
    st.header("Table Salaire")
    s_file = st.file_uploader("UPLOAD LE FICHIER (Excel/PDF)", type=['xlsx', 'pdf']) # [cite: 5, 8]
    
    if s_file and s_file.name.endswith('.xlsx'):
        if st.button("Générer écritures"):
            df_s = pd.read_excel(s_file)
            sal_rows = []
            for _, row in df_s.iterrows():
                dt = pd.to_datetime(row['Date'])
                dt_str = dt.strftime('%d/%m/%Y') # [cite: 98]
                lib = f"salaire {dt.strftime('%m/%y')}" # [cite: 110]
                sb = float(row['Salaire de base'])
                
                # Calculs débit/crédit [cite: 112, 113, 114, 117, 118, 119]
                d = [sb, float(row['Prime']), sb*0.1698, sb*0.0411]
                c = [sb*0.2146, sb*0.0637, float(row['IR'])]
                c_eq = sum(d) - sum(c) # Équilibre 44320000 [cite: 120, 122]
                
                comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"] # [cite: 101-108]
                vals = [(d[0],0), (d[1],0), (d[2],0), (d[3],0), (0,c[0]), (0,c[1]), (0,c[2]), (0,c_eq)]
                
                for i in range(8): # [cite: 100]
                    sal_rows.append({
                        "Type": "OD", "Date": dt_str, "Compte": comptes[i], "Libellé": lib,
                        "Débit": format_montant(vals[i][0]), "Crédit": format_montant(vals[i][1])
                    })
            
            df_sal = pd.DataFrame(sal_rows, columns=["Type", "Date", "Compte", "Libellé", "Débit", "Crédit"]) # [cite: 92]
            st.dataframe(df_sal)
            st.download_button("Télécharger CSV Salaires", df_sal.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv") # [cite: 9]
