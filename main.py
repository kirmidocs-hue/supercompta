import streamlit as st
import pandas as pd
import pdfplumber
import re

# 1. Configuration de base
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("💼 SUPER COMPTA")

# 2. Fonctions de formatage strictes
def format_maroc(val):
    try:
        if not val: return "0,00"
        # Nettoyage des caractères parasites
        v = str(val).replace(' ', '').replace('DH', '').replace(',', '.')
        return f"{float(v):.2f}".replace('.', ',')
    except:
        return "0,00"

def clean_libelle(txt):
    if not txt: return ""
    txt = txt.strip().replace('\n', ' ')
    # Gestion des chèques : garde les 6 chiffres
    match_chq = re.search(r'\d{6}', txt)
    if match_chq:
        return f"CHQ {match_chq.group()}"[:27]
    return txt[:27]

# 3. Interface par Onglets
tab1, tab2, tab3 = st.tabs(["📊 Relevés", "🧾 Factures", "💰 Salaires"])

with tab1:
    st.header("Extraction Relevés")
    files = st.file_uploader("Uploader les relevés (PDF)", type=['pdf'], accept_multiple_files=True)
    
    if files and st.button("Extraire maintenant"):
        all_rows = []
        for f in files:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    # On extrait le texte ligne par ligne pour plus de précision
                    text = page.extract_text()
                    if text:
                        for line in text.split('\n'):
                            # On cherche une date au format DD/MM/YYYY ou DD/MM
                            date_match = re.match(r'(\d{2}/\d{2}(?:/\d{4})?)', line)
                            if date_match:
                                # On essaie de séparer la ligne pour trouver les montants à la fin
                                parts = line.split()
                                if len(parts) >= 3:
                                    all_rows.append({
                                        "Code": "5141",
                                        "Date": date_match.group(1),
                                        "Compte": "44970000",
                                        "Libellé": clean_libelle(line),
                                        "Débit": "0,00", # À ajuster selon la position
                                        "Crédit": "0,00"
                                    })
        
        if all_rows:
            df = pd.DataFrame(all_rows)
            st.write("Aperçu des données :")
            st.dataframe(df)
            st.download_button("Télécharger CSV", df.to_csv(index=False, sep=";").encode('utf-8'), "banque.csv")
        else:
            st.warning("Aucune donnée trouvée. Vérifiez que le PDF n'est pas un scan (image).")

with tab3:
    st.header("Calcul des Salaires")
    s_file = st.file_uploader("Fichier Excel Salaires", type=['xlsx'])
    if s_file and st.button("Générer Écritures"):
        df_s = pd.read_excel(s_file)
        results = []
        for _, row in df_s.iterrows():
            sb = float(row['Salaire de base'])
            prime = float(row.get('Prime', 0))
            ir = float(row.get('IR', 0))
            dt = pd.to_datetime(row['Date'])
            lib = f"salaire {dt.strftime('%m/%y')}"
            
            # Calculs selon vos EXIGENCES ABSOLUES
            d3 = round(sb * 0.1698, 2)
            d4 = round(sb * 0.0411, 2)
            c1 = round(sb * 0.2146, 2)
            c2 = round(sb * 0.0637, 2)
            net = round((sb + prime + d3 + d4) - (c1 + c2 + ir), 2)
            
            comptes = ["61711000", "61712000", "61741000", "61743000", "44410000", "44410000", "4452500", "44320000"]
            montants = [(sb,0), (prime,0), (d3,0), (d4,0), (0,c1), (0,c2), (0,ir), (0,net)]
            
            for i in range(8):
                results.append({
                    "Type": "OD", "Date": dt.strftime('%d/%m/%Y'), "Compte": comptes[i],
                    "Libellé": lib, "Débit": format_maroc(montants[i][0]), "Crédit": format_maroc(montants[i][1])
                })
        
        df_res = pd.DataFrame(results)
        st.dataframe(df_res)
        st.download_button("Télécharger CSV Salaires", df_res.to_csv(index=False, sep=";").encode('utf-8'), "salaires.csv")
