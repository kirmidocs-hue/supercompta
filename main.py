import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA (Version Standard)")

# --- FONCTIONS DE FORMATAGE ---
def format_montant(val):
    """Force le format: virgule, 2 décimales, pas d'espaces."""
    try:
        if not val: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def clean_libelle(text):
    """Nettoie le libellé : max 27 car, garde 6 chiffres si chèque."""
    if not text: return ""
    text = text.strip().replace('\n', ' ')
    # Detection chèque (6 chiffres consécutifs)
    cheque = re.search(r'\d{6}', text)
    if cheque:
        return f"CHQ {cheque.group()}"[:27]
    return text[:27]

# --- LOGIQUE BANQUE (SANS IA) ---
def extraire_banque(pdf_file):
    rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    # On cherche une ligne qui commence par une date (JJ/MM)
                    if row and row[0] and re.match(r'\d{2}/\d{2}', str(row[0])):
                        rows.append({
                            "Code": "5141",
                            "date": row[0],
                            "compte": "44970000", # Compte par défaut
                            "libellé": clean_libelle(row[1]),
                            "débit": format_montant(row[2] if len(row) > 2 else 0),
                            "crédit": format_montant(row[3] if len(row) > 3 else 0)
                        })
    return rows

# --- INTERFACE ---
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

with tab1:
    st.header("Relevés Bancaires")
    files = st.file_uploader("Upload PDF", type=['pdf'], accept_multiple_files=True)
    if files and st.button("Extraire"):
        all_data = []
        for f in files:
            all_data.extend(extraire_banque(f))
        
        if all_data:
            df = pd.DataFrame(all_data)
            st.dataframe(df)
            st.download_button("Télécharger CSV", df.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv")

with tab3:
    st.header("Table Salaire")
    s_file = st.file_uploader("Upload Excel Salaire", type=['xlsx'])
    if s_file and st.button("Générer Journal"):
        df_s = pd.read_excel(s_file)
        sal_results = []
        for _, row in df_s.iterrows():
            sb = float(row['Salaire de base'])
            prime = float(row.get('Prime', 0))
            ir = float(row.get('IR', 0))
            dt = pd.to_datetime(row['Date'])
            
            # Calculs automatiques selon vos règles
            d1, d2 = sb, prime
            d3, d4 = round(sb * 0.1698, 2), round(sb * 0.0411, 2)
            c1, c2 = round(sb * 0.2146, 2), round(sb * 0.0637, 2)
            net = round((d1+d2+d3+d4) - (c1+c2+ir), 2)
            
            comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"]
            montants = [(d1,0), (d2,0), (d3,0), (d4,0), (0,c1), (0,c2), (0,ir), (0,net)]
            
            for i in range(8):
                sal_results.append({
                    "Type": "OD", "Date": dt.strftime('%d/%m/%Y'), "Compte": comptes[i],
                    "Libellé": f"salaire {dt.strftime('%m/%y')}",
                    "Débit": format_montant(montants[i][0]),
                    "Crédit": format_montant(montants[i][1])
                })
        
        df_sal = pd.DataFrame(sal_results)
        st.dataframe(df_sal)
        st.download_button("Télécharger CSV Salaire", df_sal.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv")
