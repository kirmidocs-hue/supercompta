import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA")

# --- FONCTIONS DE FORMATAGE ---
def format_montant(val):
    """Formatage strict : virgule, 2 décimales, pas d'espaces."""
    try:
        if pd.isna(val) or val == "" or float(val) == 0:
            return "0,00"
        return f"{float(val):.2f}".replace('.', ',')
    except:
        return "0,00"

def clean_libelle_banque(libelle):
    """Max 27 caractères + gestion chèques."""
    libelle = str(libelle).strip()
    if re.search(r'ch[eé]que|chq', libelle, re.IGNORECASE):
        numeros = re.findall(r'\d+', libelle)
        if numeros:
            dernier_num = numeros[-1][-6:]
            libelle = f"CHEQUE {dernier_num}"
    return libelle[:27]

def determiner_compte_banque(libelle, montant_debit):
    """Règle de compte selon désignation pour débit, sinon 44970000."""
    if montant_debit > 0:
        l = str(libelle).upper()
        if any(m in l for m in ["FRAIS", "FORFAIT", "EMISSION", "TIMBRE", "RETRAIT", "COMM", "TAXE"]): return "61470000"
        elif "CNSS" in l: return "44410000"
        elif "AMENDIS" in l: return "44110902"
        elif "IAM" in l: return "44110901"
        elif "AZNAG" in l: return "44110017"
        elif any(m in l for m in ["KAOUTAR", "WIAM", "MERIEM", "SOUKAINA"]): return "44320000"
        elif any(m in l for m in ["MOURABAHA", "KRITI", "PRÉLÈVEMENTS", "PRELEVEMENTS"]): return "11175000"
        return "44970000"
    return ""

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

# --- 1. RELEVÉS BANCAIRES ---
with tab1:
    st.header("Relevés Bancaires")
    fichiers_banque = st.file_uploader("Upload Relevés (Excel/CSV - Max 12)", type=['xlsx', 'csv'], accept_multiple_files=True)
    
    if fichiers_banque:
        if len(fichiers_banque) > 12:
            st.error("Maximum 12 fichiers.")
        else:
            if st.button("Extraire les données Banque"):
                all_banque_rows = []
                for f in fichiers_banque:
                    df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
                    # Nettoyage colonnes (minuscules et sans espaces)
                    df.columns = df.columns.str.strip().str.lower()
                    
                    for _, row in df.iterrows():
                        # Lecture des montants réels
                        d_val = float(row.get('débit', 0) if pd.notna(row.get('débit', 0)) else 0)
                        c_val = float(row.get('crédit', 0) if pd.notna(row.get('crédit', 0)) else 0)
                        
                        libelle_brut = row.get('libellé', row.get('désignation', ''))
                        libelle_final = clean_libelle_banque(libelle_brut)
                        
                        all_banque_rows.append({
                            "Code": "5141",
                            "date": pd.to_datetime(row.get('date')).strftime('%d/%m/%Y') if pd.notna(row.get('date')) else "",
                            "compte": determiner_compte_banque(libelle_brut, d_val),
                            "libellé": libelle_final,
                            "débit": format_montant(d_val),
                            "crédit": format_montant(c_val)
                        })
                
                if all_banque_rows:
                    df_res_banque = pd.DataFrame(all_banque_rows)
                    st.success("Extraction terminée !")
                    st.dataframe(df_res_banque)
                    st.download_button("Télécharger CSV Banque", df_res_banque.to_csv(index=False, sep=";").encode('utf-8'), "banque_resultat.csv")

# --- 2. FACTURES ---
with tab2:
    st.header("Factures")
    f_files = st.file_uploader("Upload Factures (Max 20)", type=['xlsx', 'csv'], accept_multiple_files=True)
    
    if f_files:
        if st.button("Traiter les Factures"):
            all_fac_rows = []
            for f in f_files:
                df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
                for _, row in df.iterrows():
                    ttc = float(row.get('TTC', 0))
                    ht = ttc / 1.2
                    tva = ttc - ht
                    base = {"Code journal": "ACH", "Date de facture": row.get('Date'), "Référence": row.get('Référence'), "Libellé écriture": row.get('Nom Société')}
                    
                    all_fac_rows.append({**base, "Compte": "61110000", "Montant débit": format_montant(ht), "Montant crédit": "0,00"})
                    all_fac_rows.append({**base, "Compte": "34550000", "Montant débit": format_montant(tva), "Montant crédit": "0,00"})
                    all_fac_rows.append({**base, "Compte": "44110000", "Montant débit": "0,00", "Montant crédit": format_montant(ttc)})
            
            df_fac = pd.DataFrame(all_fac_rows)
            st.dataframe(df_fac)
            st.download_button("Télécharger CSV Factures", df_fac.to_csv(index=False, sep=";").encode('utf-8'), "factures.csv")

# --- 3. TABLE SALAIRE ---
with tab3:
    st.header("Table Salaire")
    s_file = st.file_uploader("Upload Salaire (1 seul fichier)", type=['xlsx'])
    
    if s_file:
        if st.button("Traiter les Salaires"):
            df_s = pd.read_excel(s_file)
            sal_rows = []
            for _, row in df_s.iterrows():
                dt = pd.to_datetime(row['Date'])
                dt_str = dt.strftime('%d/%m/%Y')
                lib = f"salaire {dt.strftime('%m/%y')}"
                sb = float(row['Salaire de base'])
                
                d = [sb, float(row.get('Prime',0)), sb*0.1698, sb*0.0411]
                c = [sb*0.2146, sb*0.0637, float(row.get('IR',0))]
                c_eq = sum(d) - sum(c)
                
                comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"]
                vals = [(d[0],0), (d[1],0), (d[2],0), (d[3],0), (0,c[0]), (0,c[1]), (0,c[2]), (0,c_eq)]
                
                for i in range(8):
                    sal_rows.append({
                        "Type": "OD", "Date": dt_str, "Compte": comptes[i], "Libellé": lib,
                        "Débit": format_montant(vals[i][0]), "Crédit": format_montant(vals[i][1])
                    })
            
            df_sal = pd.DataFrame(sal_rows)
            st.dataframe(df_sal)
            st.download_button("Télécharger CSV Salaires", df_sal.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv")
