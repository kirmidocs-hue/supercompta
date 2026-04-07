import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="SUPER COMPTA AI", layout="wide")

# --- CONFIGURATION IA (Gemini) ---
# Remplacez par votre clé API obtenue sur Google AI Studio
API_KEY = "VOTRE_CLE_API_ICI" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- FONCTIONS DE FORMATAGE ET RÈGLES ---
def format_montant(val):
    """Force le format : virgule, 2 décimales, sans espaces."""
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte_banque(libelle, debit_val):
    """Règle de compte selon désignation pour les débits [cite: 28-33]."""
    try: d = float(str(debit_val).replace(',', '.'))
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
    return "44970000" [cite: 32]

# --- INTERFACE ---
st.title("SUPER COMPTA")

tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

# --- 1. RELEVÉS BANCAIRES ---
with tab1:
    st.header("Relevés Bancaires (Extraction IA)")
    files = st.file_uploader("Upload PDF (Max 12)", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True) [cite: 6, 21]
    
    if files and st.button("Extraire les données"):
        all_banque_data = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text += text + "\n"
                
                # Le prompt force l'IA à respecter vos règles de libellés et de dates [cite: 27, 36, 37]
                prompt = (
                    f"Tu es un expert comptable. Extrais TOUTES les transactions du relevé suivant. "
                    f"RÈGLES : Ne saute AUCUNE ligne. Résume les libellés à 27 caractères max. "
                    f"Pour les chèques, garde les 6 derniers chiffres. "
                    f"Retourne UNIQUEMENT un JSON array. Format: [{{'date':'dd/mm/yyyy', 'libelle':'...', 'debit':0.0, 'credit':0.0}}] "
                    f"Texte: {full_text}"
                )
                
                try:
                    response = model.generate_content(prompt)
                    json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        for item in data:
                            all_banque_data.append({
                                "Code": "5141", [cite: 26]
                                "date": item.get('date', ''),
                                "compte": get_compte_banque(item.get('libelle', ''), item.get('debit', 0)),
                                "libellé": str(item.get('libelle', ''))[:27], [cite: 36]
                                "débit": format_montant(item.get('debit', 0)),
                                "crédit": format_montant(item.get('credit', 0))
                            })
                except Exception as e:
                    st.error(f"Erreur sur le fichier {f.name}")

        if all_banque_data:
            df_b = pd.DataFrame(all_banque_data)
            st.dataframe(df_b)
            st.download_button("Télécharger CSV Banque", df_b.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv") [cite: 23]

# --- 3. TABLE SALAIRE ---
with tab3:
    st.header("Table Salaire")
    s_file = st.file_uploader("Upload Excel Salaire", type=['xlsx']) [cite: 8]
    if s_file and st.button("Générer Journal Salaire"):
        df_s = pd.read_excel(s_file)
        sal_results = []
        for _, row in df_s.iterrows():
            sb = float(row['Salaire de base']) [cite: 89]
            prime = float(row.get('Prime', 0)) [cite: 89]
            ir = float(row.get('IR', 0)) [cite: 90]
            dt = pd.to_datetime(row['Date'])
            date_f = dt.strftime('%d/%m/%Y') [cite: 99]
            lib = f"salaire {dt.strftime('%m/%y')}" [cite: 111]
            
            # Écritures selon l'ordre exact (8 lignes) [cite: 101-109]
            # Débits [cite: 113-115]
            d_vals = [sb, prime, round(sb*0.1698, 2), round(sb*0.0411, 2)]
            # Crédits [cite: 118-120]
            c_vals = [round(sb*0.2146, 2), round(sb*0.0637, 2), ir]
            
            # Calcul du net (44320000) pour l'équilibre 
            net = round(sum(d_vals) - sum(c_vals), 2)
            
            comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"]
            montants = [(d_vals[0],0), (d_vals[1],0), (d_vals[2],0), (d_vals[3],0), (0,c_vals[0]), (0,c_vals[1]), (0,c_vals[2]), (0,net)]
            
            for i in range(8):
                sal_results.append({
                    "Type": "OD", "Date": date_f, "Compte": comptes[i], "Libellé": lib, 
                    "Débit": format_montant(montants[i][0]), "Crédit": format_montant(montants[i][1])
                })
        
        df_sal = pd.DataFrame(sal_results)
        st.dataframe(df_sal)
        st.download_button("Télécharger CSV Salaires", df_sal.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv") [cite: 9]
