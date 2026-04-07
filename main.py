import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- CONFIGURATION IA ---
# Remplacez par votre clé API Google AI (https://aistudio.google.com/)
API_KEY = "VOTRE_CLE_API_ICI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="SUPER COMPTA AI", layout="wide")
st.title("SUPER COMPTA") # [cite: 1]

# --- FONCTIONS DE FORMATAGE ---
def format_montant(val):
    """Règle : Virgule, 2 décimales, pas d'espaces des milliers[cite: 42, 43, 65]."""
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte_banque(libelle, debit):
    """Règle de compte selon désignation[cite: 28, 29, 31, 32]."""
    try: d = float(str(debit).replace(',', '.'))
    except: d = 0
    if d > 0:
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
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"]) # [cite: 2, 3, 4]

# --- 1. RELEVÉS BANCAIRES (IA) ---
with tab1:
    st.header("Relevés Bancaires")
    files = st.file_uploader("Upload PDF (Max 12)", type=['pdf'], accept_multiple_files=True) # [cite: 6, 21]
    
    if files and st.button("Extraire avec IA"): # [cite: 22]
        all_banque_data = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                prompt = f"""
                Extrais TOUTES les transactions de ce relevé bancaire.
                RETOURNE UNIQUEMENT UN JSON ARRAY. Format: [{"date":"dd/mm/yyyy", "libelle":"...", "debit":0.0, "credit":0.0}]
                RÈGLES:
                - Ne saute aucune ligne.
                - Si chèque, garde les 6 derniers chiffres[cite: 36].
                - Résume le libellé à 27 caractères max[cite: 35].
                TEXTE: {full_text}
                """
                
                response = model.generate_content(prompt)
                try:
                    # Nettoyage de la réponse IA pour extraire le JSON
                    raw_json = re.search(r'\[.*\]', response.text, re.DOTALL).group()
                    data = json.loads(raw_json)
                    for item in data:
                        all_banque_data.append({
                            "Code": "5141", # 
                            "date": item['date'], # [cite: 27]
                            "compte": get_compte_banque(item['libelle'], item['debit']), # [cite: 31]
                            "libellé": item['libelle'], # [cite: 35]
                            "débit": format_montant(item['debit']), # [cite: 39]
                            "crédit": format_montant(item['credit']) # [cite: 40]
                        })
                except: st.error("Erreur d'analyse de l'IA sur un fichier.")

        if all_banque_data:
            df_b = pd.DataFrame(all_banque_data)
            st.dataframe(df_b)
            st.download_button("Télécharger CSV", df_b.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv") # [cite: 23]

# --- 2. FACTURES ---
with tab2:
    st.header("Factures")
    f_files = st.file_uploader("Upload Factures (Max 20)", accept_multiple_files=True) # [cite: 7]
    if f_files and st.button("Générer écritures ACH"):
        # Logique simplifiée : Extraction du TTC pour générer 3 lignes [cite: 45, 57]
        # (Nécessite OCR ou saisie pour le TTC réel)
        st.info("Module configuré pour générer Code journal/Date/Référence/Compte/Libellé/Débit/Crédit [cite: 47]")

# --- 3. TABLE SALAIRE ---
with tab3:
    st.header("Table Salaire")
    s_file = st.file_uploader("Upload Excel Salaire", type=['xlsx']) # [cite: 8]
    if s_file:
        df_s = pd.read_excel(s_file)
        sal_results = []
        for _, row in df_s.iterrows():
            sb = float(row['Salaire de base']) # [cite: 88]
            prime = float(row['Prime']) # [cite: 88]
            ir = float(row['IR']) # [cite: 89]
            date_str = pd.to_datetime(row['Date']).strftime('%d/%m/%Y') # [cite: 98]
            lib = f"salaire {pd.to_datetime(row['Date']).strftime('%m/%y')}" # [cite: 110]
            
            # Débits [cite: 112, 113, 114]
            d = [sb, prime, round(sb*0.1698, 2), round(sb*0.0411, 2)]
            # Crédits [cite: 117, 118, 119]
            c = [round(sb*0.2146, 2), round(sb*0.0637, 2), ir]
            c_net = round(sum(d) - sum(c), 2) # 
            
            comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"] # [cite: 101-108]
            vals = [(d[0],0), (d[1],0), (d[2],0), (d[3],0), (0,c[0]), (0,c[1]), (0,c[2]), (0,c_net)]
            
            for i in range(8):
                sal_results.append({
                    "Type": "OD", "Date": date_str, "Compte": comptes[i], "Libellé": lib, 
                    "Débit": format_montant(vals[i][0]), "Crédit": format_montant(vals[i][1])
                })
        
        df_sal = pd.DataFrame(sal_results) # [cite: 92]
        st.dataframe(df_sal)
        st.download_button("Télécharger CSV Salaires", df_sal.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv")
