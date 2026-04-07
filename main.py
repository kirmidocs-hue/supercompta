import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("🚀 SUPER COMPTA - Mode Expert")

# --- 2. CONFIGURATION IA ---
API_KEY = "AIzaSyDGu4L2kbLtRr7GNCT2-POBR_YqV1Vhboc"
genai.configure(api_key=API_KEY)
# Utilisation de gemini-1.5-flash pour la lecture des tableaux complexes
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. FONCTIONS DE RÈGLES STRICTES ---
def format_montant(val):
    """Règle : Virgule, pas d'espaces, 2 décimales[cite: 44, 66]."""
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte(libelle, debit):
    """Règle de compte selon désignation[cite: 33]."""
    l = str(libelle).lower()
    mots_frais = ["frais", "forfait", "émission", "timbre", "retrait", "comm", "commission", "taxe"]
    try:
        d_val = float(str(debit).replace(',', '.'))
    except:
        d_val = 0
    if d_val > 0 and any(m in l for m in mots_frais):
        return "61470000"
    return "44970000"

# --- 4. INTERFACE ---
files = st.file_uploader("Upload Relevés (Max 12 PDF/JPG) [cite: 6]", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True)

if files and st.button("Extraire les données [cite: 22]"):
    all_data = []
    
    for f in files:
        with st.spinner(f"Analyse de {f.name}..."):
            full_text = ""
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
            
            # Prompt optimisé pour éviter les erreurs de structure
            prompt = f"""
            Tu es un expert comptable marocain. Extrais TOUTES les transactions.
            RÈGLES ABSOLUES :
            - Ne saute AUCUNE ligne[cite: 12].
            - Date au format jj/mm/aaaa. Si mois précédent, utilise 01/mm/aaaa[cite: 27].
            - Pas de 'date valeur'[cite: 27].
            - Libellé max 27 car[cite: 36]. Chèque = 6 derniers chiffres[cite: 37].
            
            RETOURNE UNIQUEMENT UN ARRAY JSON SANS TEXTE AVANT OU APRÈS :
            [{{"date": "jj/mm/aaaa", "lib": "...", "db": 0.0, "cr": 0.0}}]
            
            CONTENU :
            {full_text}
            """
            
            try:
                response = model.generate_content(prompt)
                # Nettoyage du texte pour ne garder que le bloc JSON [...]
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                
                if json_match:
                    items = json.loads(json_match.group())
                    for i in items:
                        lib_final = str(i.get('lib', ''))[:27]
                        all_data.append({
                            "Code": "5141", # [cite: 26]
                            "date": i.get('date'), # 
                            "compte": get_compte(lib_final, i.get('db', 0)), # [cite: 29]
                            "libellé": lib_final, # [cite: 36]
                            "débit": format_montant(i.get('db', 0)), # [cite: 44]
                            "crédit": format_montant(i.get('cr', 0)) # [cite: 44]
                        })
                else:
                    st.error(f"Format de réponse invalide pour {f.name}")
            except Exception as e:
                st.error(f"Erreur technique sur {f.name} : {str(e)}")

    if all_data:
        df = pd.DataFrame(all_data)
        st.dataframe(df)
        csv = df.to_csv(index=False, sep=";").encode('utf-8')
        st.download_button("Télécharger CSV [cite: 23]", csv, "banque.csv", "text/csv")
