import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION INITIALE (Toujours en haut) ---
st.set_page_config(page_title="SUPER COMPTA AI", layout="wide")

# --- 2. CONFIGURATION IA ---
# Remplacez par votre clé API réelle
API_KEY = "VOTRE_CLE_API_ICI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. FONCTIONS DE SUPPORT ---
def format_montant(val):
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte_banque(libelle, debit):
    try:
        d = float(str(debit).replace(',', '.'))
    except:
        d = 0
    if d > 0:
        l = str(libelle).upper()
        # Table de correspondance selon vos exigences
        if any(w in l for w in ["FRAIS", "FORFAIT", "EMISSION", "TIMBRE", "RETRAIT", "COMM", "TAXE"]): return "61470000"
        if "CNSS" in l: return "44410000"
        if "AMENDIS" in l: return "44110902"
        if "IAM" in l: return "44110901"
        if "AZNAG" in l: return "44110017"
        if any(w in l for w in ["KAOUTAR", "WIAM", "MERIEM", "SOUKAINA"]): return "44320000"
        if any(w in l for w in ["MOURABAHA", "KRITI", "PRÉLÈVEMENTS"]): return "11175000"
    return "44970000"

# --- 4. INTERFACE UTILISATEUR ---
st.title("SUPER COMPTA")

# Définition des onglets AVANT leur utilisation
tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

# --- ONGLET 1 : RELEVÉS ---
with tab1:
    st.header("Relevés Bancaires (Extraction IA)")
    files = st.file_uploader("Upload PDF (Max 12)", type=['pdf'], accept_multiple_files=True)
    
    if files and st.button("Lancer l'extraction"):
        all_banque_data = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text += text + "\n"
                
                prompt = (
                    f"Extraire toutes les transactions. Retourner UNIQUEMENT un JSON array. "
                    f"Format: [{{'date':'dd/mm/yyyy', 'libelle':'...', 'debit':0.0, 'credit':0.0}}] "
                    f"Texte: {full_text}"
                )
                
                try:
                    response = model.generate_content(prompt)
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        for item in data:
                            all_banque_data.append({
                                "Code": "5141", #
                                "date": item.get('date', ''),
                                "compte": get_compte_banque(item.get('libelle', ''), item.get('debit', 0)),
                                "libellé": str(item.get('libelle', ''))[:27], #
                                "débit": format_montant(item.get('debit', 0)), #
                                "crédit": format_montant(item.get('credit', 0)) #
                            })
                except Exception as e:
                    st.error(f"Erreur sur le fichier {f.name}")

        if all_banque_data:
            df_b = pd.DataFrame
