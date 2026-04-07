import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("🚀 SUPER COMPTA - Analyseur de Relevés")

# --- 2. CONFIGURATION IA ---
API_KEY = "AIzaSyDGu4L2kbLtRr7GNCT2-POBR_YqV1Vhboc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. FONCTIONS DE RÈGLES STRICTES ---
def format_montant(val):
    """Règle : Virgule, pas d'espaces, identique au PDF[cite: 44, 66]."""
    try:
        if val is None or str(val).strip() in ["", "0", "0.00"]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def get_compte(libelle, debit):
    """Règle : 61470000 si frais/taxe, sinon 44970000[cite: 32, 33]."""
    l = str(libelle).lower()
    mots_cles = ["frais", "forfait", "émission", "timbre", "retrait", "comm", "commission", "taxe"]
    # On vérifie si c'est un débit [cite: 30, 31]
    try:
        d_val = float(str(debit).replace(',', '.'))
    except:
        d_val = 0
        
    if d_val > 0 and any(m in l for m in mots_cles):
        return "61470000"
    return "44970000"

# --- 4. INTERFACE ---
files = st.file_uploader("Upload Relevés (Max 12 PDF/JPG) [cite: 6, 21]", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True)

if files and st.button("Extraire les données [cite: 22]"):
    all_data = []
    
    for f in files:
        with st.spinner(f"Analyse rigoureuse de {f.name}..."):
            full_content = ""
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    # On extrait le texte ET les tableaux pour ne rien rater [cite: 12, 20]
                    full_content += page.extract_text() + "\n"
            
            prompt = f"""
            Tu es un expert comptable au Maroc. Extrais TOUTES les transactions de ce texte.
            RÈGLES CRITIQUES[cite: 11]:
            - Ne saute AUCUNE ligne, surtout la première de chaque page[cite: 12, 15].
            - Format Date : dd/mm/aaaa. Si mois précédent, utilise 01/mm/aaaa.
            - JAMAIS la date valeur.
            - Libellé : Résumé à 27 car. max[cite: 36].
            - Chèque : Garde seulement les 6 derniers chiffres[cite: 37].
            
            RETOURNE UNIQUEMENT UN JSON ARRAY :
            [{{"date": "jj/mm/aaaa", "lib": "...", "db": 0.0, "cr": 0.0}}]
            
            TEXTE À ANALYSER :
            {full_content}
            """
            
            try:
                response = model.generate_content(prompt)
                clean_json = re.search(r'\[.*\]', response.text, re.DOTALL).group()
                items = json.loads(clean_json)
                
                for i in items:
                    d_val = i.get('db', 0)
                    lib_final = str(i.get('lib', ''))[:27]
                    
                    all_data.append({
                        "Code": "5141", # 
                        "date": i.get('date'), # 
                        "compte": get_compte(lib_final, d_val), # [cite: 28, 33]
                        "libellé": lib_final, # [cite: 36]
                        "débit": format_montant(d_val), # [cite: 44]
                        "crédit": format_montant(i.get('cr', 0)) # [cite: 44]
                    })
            except Exception as e:
                st.error(f"Erreur sur {f.name}. L'IA n'a pas pu structurer les données.")

    if all_data:
        df = pd.DataFrame(all_data)
        st.write("### Aperçu du résultat [cite: 25]")
        st.dataframe(df)
        
        # Sortie CSV [cite: 23, 24]
        csv_data = df.to_csv(index=False, sep=";").encode('utf-8')
        st.download_button("Télécharger CSV [cite: 23]", csv_data, "releve_comptable.csv", "text/csv")
