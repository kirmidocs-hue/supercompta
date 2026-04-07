import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("💼 SUPER COMPTA - Extracteur de Relevés")

# --- 2. CONFIGURATION IA (Votre Clé) ---
API_KEY = "AIzaSyDGu4L2kbLtRr7GNCT2-POBR_YqV1Vhboc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. FONCTIONS DE FORMATAGE ET RÈGLES ---
def format_montant_maroc(val):
    """Conserver les montants identiques, virgules au lieu de points."""
    try:
        if val is None or str(val).strip() in ["", "0", "0,00"]: return "0,00"
        # Supprimer les espaces des milliers 
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def detecter_compte(libelle, debit_val):
    """Affectation du compte selon les mots-clés du libellé[cite: 31, 33]."""
    try:
        d = float(str(debit_val).replace(',', '.'))
    except:
        d = 0
        
    if d > 0:
        l = str(libelle).lower()
        mots_frais = ["frais", "forfait", "émission", "timbre", "retrait", "comm", "commission", "taxe"]
        if any(mot in l for mot in mots_frais):
            return "61470000" [cite: 33]
    return "44970000" [cite: 32]

# --- 4. INTERFACE UTILISATEUR ---
# Espace pour upload maximum 12 fichiers 
files = st.file_uploader("Upload des relevés bancaires (PDF, JPG, JPEG)", type=['pdf', 'jpg', 'jpeg'], accept_multiple_files=True)

if files and st.button("Extraire les données"):
    all_data = []
    
    for f in files:
        with st.spinner(f"Analyse de {f.name}..."):
            # Extraction du texte brut pour aider l'IA
            text_content = ""
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    text_content += page.extract_text() + "\n"
            
            # Prompt forçant le respect des EXIGENCES ABSOLUES [cite: 11, 12]
            prompt = f"""
            Tu es un expert comptable. Extrais TOUTES les transactions de ce relevé bancaire.
            RÈGLES CRITIQUES :
            1. Ne saute AUCUNE ligne d'opération[cite: 12].
            2. La première ligne de chaque page doit être extraite[cite: 15].
            3. Date : format jj/mm/aaaa. Si la date est du mois précédent, utilise le 01 du mois actuel.
            4. Libellé : maximum 27 caractères.
            5. Ne jamais extraire la 'date valeur'.
            
            Retourne UNIQUEMENT un tableau JSON :
            [{{"date": "jj/mm/aaaa", "libelle": "...", "debit": 0.0, "credit": 0.0}}]
            
            TEXTE : {text_content}
            """
            
            try:
                response = model.generate_content(prompt)
                # Nettoyage de la réponse pour extraire le JSON
                raw_res = re.search(r'\[.*\]', response.text, re.DOTALL).group()
                json_items = json.loads(raw_res)
                
                for item in json_items:
                    lib = str(item.get('libelle', ''))[:27] # Max 27 car. 
                    deb = item.get('debit', 0)
                    cre = item.get('credit', 0)
                    
                    all_data.append({
                        "Code": "5141", # Code fixe [cite: 26]
                        "date": item.get('date', ''),
                        "compte": detecter_compte(lib, deb),
                        "libellé": lib,
                        "débit": format_montant_maroc(deb),
                        "crédit": format_montant_maroc(cre)
                    })
            except Exception as e:
                st.error(f"Erreur lors de l'analyse de {f.name}")

    if all_data:
        df = pd.DataFrame(all_data)
        # Affichage du résultat [cite: 24, 25]
        st.write("### Résultat de l'extraction")
        st.dataframe(df)
        
        # Téléchargement en CSV [cite: 6, 23]
        csv = df.to_csv(index=False, sep=";").encode('utf-8')
        st.download_button("Télécharger le fichier CSV", csv, "releve_compta.csv", "text/csv")
