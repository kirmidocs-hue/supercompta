import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="SUPER COMPTA AI", layout="wide")

# --- 2. CONFIGURATION IA AVEC VOTRE CLÉ ---
API_KEY = "AIzaSyDGu4L2kbLtRr7GNCT2-POBR_YqV1Vhboc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. FONCTIONS DE FORMATAGE ---
def format_montant(val):
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte_banque(libelle, debit_val):
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

# --- 4. INTERFACE ---
st.title("SUPER COMPTA")

tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaire"])

# --- ONGLET 1 : RELEVÉS BANCAIRES ---
with tab1:
    st.header("Relevés Bancaires (Extraction IA)")
    files = st.file_uploader("Upload PDF / JPG (Max 12)", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if files and st.button("Extraire les données"):
        all_banque_data = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text += text + "\n"
            
            prompt = (
                "Tu es un expert comptable marocain. Extrais TOUTES les transactions du texte suivant. "
                "RÈGLES CRITIQUES : Ne saute AUCUNE ligne. Résume les libellés à 27 caractères max. "
                "Pour les chèques, garde seulement les 6 derniers chiffres. "
                "Retourne UNIQUEMENT un JSON array. "
                "Format: [{\"date\":\"dd/mm/yyyy\", \"libelle\":\"...\", \"debit\":0.0, \"credit\":0.0}] "
                f"Texte: {full_text}"
            )
            
            try:
                response = model.generate_content(prompt)
                match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    for item in data:
                        all_banque_data.append({
                            "Code": "5141",
                            "date": item.get('date', ''),
                            "compte": get_compte_banque(item.get('libelle', ''), item.get('debit', 0)),
                            "libellé": str(item.
