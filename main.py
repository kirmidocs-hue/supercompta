import streamlit as st
import pandas as pd
import pdfplumber
import google.generativeai as genai
import json
import re

# 1. Configuration
st.set_page_config(page_title="SUPER COMPTA AI", layout="wide")
st.title("🛡️ SUPER COMPTA - Mode IA Activé")

# 2. Votre Clé API (Insérée pour vous)
API_KEY = "AIzaSyDGu4L2kbLtRr7GNCT2-POBR_YqV1Vhboc"
genai.configure(api_key=API_KEY)
# On utilise flash pour la rapidité et la vision des scans
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Fonctions de formatage (Exigences Absolues)
def format_maroc(val):
    try:
        if not val or str(val).strip() in ["0", "0.00", ""]: return "0,00"
        v = str(val).replace(' ', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

# 4. Interface par Onglets
tab1, tab2, tab3 = st.tabs(["📊 Relevés", "🧾 Factures", "💰 Salaires"])

with tab1:
    files = st.file_uploader("Upload Relevés (PDF ou Scan)", type=['pdf', 'jpg', 'png'], accept_multiple_files=True)
    if files and st.button("Lancer l'extraction IA"):
        all_results = []
        for f in files:
            with st.spinner(f"Analyse de {f.name}..."):
                # Extraction du texte (si possible) pour aider l'IA
                with pdfplumber.open(f) as pdf:
                    full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
                
                # Le Prompt qui force le respect de vos règles
                prompt = f"""
                Agis en expert comptable. Extrais TOUTES les lignes de ce relevé.
                EXIGENCES : Ne saute AUCUNE ligne. Libellé max 27 car. Chèque = 6 chiffres.
                RETOURNE UNIQUEMENT UN JSON ARRAY : 
                [{{"date":"jj/mm/aaaa", "libelle":"...", "debit":0.0, "credit":0.0}}]
                CONTENU DU FICHIER : {full_text if full_text else "C'est une image, analyse visuellement."}
                """
                
                try:
                    # Envoi à l'IA
                    response = model.generate_content(prompt)
                    json_data = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if json_data:
                        items = json.loads(json_data.group())
                        for item in items:
                            all_results.append({
                                "Code": "5141",
                                "Date": item.get('date'),
                                "Compte": "44970000",
                                "Libellé": str(item.get('libelle'))[:27],
                                "Débit": format_maroc(item.get('debit')),
                                "Crédit": format_maroc(item.get('credit'))
                            })
                except Exception as e:
                    st.error(f"Erreur sur {f.name}")

        if all_results:
            df = pd.DataFrame(all_results)
            st.dataframe(df)
            st.download_button("Télécharger CSV", df.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv")

with tab3:
    st.header("Journal Salaire (8 lignes)")
    s_file = st.file_uploader("Fichier Excel Salaire", type=['xlsx'])
    if s_file and st.button("Générer Journal"):
        df_s = pd.read_excel(s_file)
        journal = []
        for _, row in df_s.iterrows():
            sb = float(row['Salaire de base'])
            dt = pd.to_datetime(row['Date'])
            # Calculs fixes
            vals = [(sb,0), (row.get('Prime',0),0), (sb*0.1698,0), (sb*0.0411,0), 
                    (0,sb*0.2146), (0,sb*0.0637), (0,row.get('IR',0))]
            net = sum(v[0] for v in vals) - sum(v[1] for v in vals)
            vals.append((0, net))
            
            comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"]
            for i in range(8):
                journal.append({
                    "Type": "OD", "Date": dt.strftime('%d/%m/%Y'), "Compte": comptes[i],
                    "Libellé": f"salaire {dt.strftime('%m/%y')}",
                    "Débit": format_maroc(vals[i][0]), "Crédit": format_maroc(vals[i][1])
                })
        st.dataframe(pd.DataFrame(journal))
