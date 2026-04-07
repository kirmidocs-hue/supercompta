import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="SUPER COMPTA AI", layout="wide")

# --- CONFIGURATION IA ---
# Remplacez par votre clé API réelle de Google AI Studio
API_KEY = "VOTRE_CLE_API_ICI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- FONCTIONS DE SUPPORT ---
def format_montant(val):
    """Règle : Conserver montants identiques, virgules, pas d'espaces[cite: 44]."""
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte_banque(libelle, debit_val):
    """Règle de compte selon désignation[cite: 28, 33]."""
    try:
        d = float(str(debit_val).replace(',', '.'))
    except:
        d = 0
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

# --- INTERFACE ---
st.title("SUPER COMPTA")

tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

# --- ONGLET 1 : RELEVÉS BANCAIRES ---
with tab1:
    st.header("Relevés Bancaires (Extraction IA)")
    # Upload PDF ou Image [cite: 21]
    files = st.file_uploader("Upload PDF / JPG (Max 12)", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if files and st.button("Lancer l'extraction"):
        all_banque_data = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text += text + "\n"
                
                # Prompt IA respectant les exigences absolues [cite: 12-16]
                prompt = (
                    "Tu es un expert comptable. Extrais TOUTES les transactions du texte suivant. "
                    "RÈGLES : Ne saute AUCUNE ligne. Résume les libellés à 27 caractères max. "
                    "Pour les chèques, garde les 6 derniers chiffres. "
                    "Retourne UNIQUEMENT un JSON array. "
                    "Format: [{\"date\":\"dd/mm/yyyy\", \"libelle\":\"...\", \"debit\":0.0, \"credit\":0.0}] "
                    f"Texte: {full_text}"
                )
                
                try:
                    response = model.generate_content(prompt)
                    json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        for item in data:
                            all_banque_data.append({
                                "Code": "5141",
                                "date": item.get('date', ''),
                                "compte": get_compte_banque(item.get('libelle', ''), item.get('debit', 0)),
                                "libellé": str(item.get('libelle', ''))[:27],
                                "débit": format_montant(item.get('debit', 0)),
                                "crédit": format_montant(item.get('credit', 0))
                            })
                except Exception:
                    st.error(f"Erreur sur le fichier {f.name}")

        if all_banque_data:
            df_b = pd.DataFrame(all_banque_data)
            st.dataframe(df_b)
            # Output format: Code/date/compte/libellé/débit/crédit [cite: 25]
            st.download_button("Télécharger CSV Banque", df_b.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv")

# --- ONGLET 3 : TABLE SALAIRE ---
with tab3:
    st.header("Table Salaire")
    s_file = st.file_uploader("Upload Excel Salaire", type=['xlsx'])
    if s_file and st.button("Générer Journal Salaire"):
        df_s = pd.read_excel(s_file)
        sal_results = []
        for _, row in df_s.iterrows():
            sb = float(row['Salaire de base'])
            prime = float(row.get('Prime', 0))
            ir = float(row.get('IR', 0))
            dt = pd.to_datetime(row['Date'])
            lib = f"salaire {dt.strftime('%m/%y')}"
            
            # Écritures (8 lignes) dans l'ordre exact [cite: 101-109]
            d_vals = [sb, prime, round(sb*0.1698, 2), round(sb*0.0411, 2)]
            c_vals = [round(sb*0.2146, 2), round(sb*0.0637, 2), ir]
            net = round(sum(d_vals) - sum(c_vals), 2) # Calcul équilibre [cite: 121, 123]
            
            comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"]
            monts = [(d_vals[0],0), (d_vals[1],0), (d_vals[2],0), (d_vals[3],0), (0,c_vals[0]), (0,c_vals[1]), (0,c_vals[2]), (0,net)]
            
            for i in range(8):
                sal_results.append({
                    "Type": "OD", "Date": dt.strftime('%d/%m/%Y'), "Compte": comptes[i], 
                    "Libellé": lib, "Débit": format_montant(monts[i][0]), "Crédit": format_montant(monts[i][1])
                })
        
        df_sal = pd.DataFrame(sal_results)
        st.dataframe(df_sal)
        st.download_button("Télécharger CSV Salaire", df_sal.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv")
