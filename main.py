import streamlit as st
import pandas as pd
import io
from datetime import datetime

# --- DESIGN & CONFIGURATION ---
st.set_page_config(page_title="SUPER COMPTA - FAISAL KARMI", layout="wide")

# Style CSS pour un look professionnel
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; background-color: #004a99; color: white; }
    .stHeader { color: #004a99; font-family: 'Helvetica'; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 SUPER COMPTA - Système Expert")
st.sidebar.info(f"Utilisateur : FAISAL KARMI\nLocalisation : TANGER\nVersion : 2.0 (Multi-lignes)")

# --- FONCTION DE FORMATAGE MAROC ---
def format_maroc(n):
    return f"{n:.2f}".replace('.', ',')

def convert_df_to_csv(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

tabs = st.tabs(["📊 Relevés Bancaires", "💰 Salaires (Journal OD)"])

# --- 1. MODULE BANQUE (Multi-lignes) ---
with tabs[0]:
    st.header("Traitement Multi-lignes - Relevés")
    uploaded_bank = st.file_uploader("Glissez votre relevé Excel/CSV ici", type=['csv', 'xlsx'])
    
    if uploaded_bank:
        # Lecture automatique de toutes les lignes
        df_input = pd.read_excel(uploaded_bank) if uploaded_bank.name.endswith('xlsx') else pd.read_csv(uploaded_bank, sep=';')
        
        # Transformation (Règles Faisal Karmi)
        df_output = pd.DataFrame()
        df_output['Date'] = df_input.iloc[:, 0] # Prend la 1ère colonne
        df_output['Compte'] = "51410000" # Règle fixe
        df_output['Libellé'] = df_input.iloc[:, 1].str[:27] # Max 27 car.
        df_output['Débit'] = df_input.iloc[:, 2].apply(lambda x: format_maroc(float(x)) if x > 0 else "0,00")
        df_output['Crédit'] = df_input.iloc[:, 3].apply(lambda x: format_maroc(float(x)) if x > 0 else "0,00")
        
        st.write(f"✅ {len(df_output)} lignes détectées et formatées.")
        st.dataframe(df_output)
        st.download_button("📥 Télécharger le Relevé Formaté", convert_df_to_csv(df_output), "releve_tanger.csv")

# --- 2. MODULE SALAIRES (Génération des 8 lignes par employé) ---
with tabs[1]:
    st.header("Journal OD - Traitement Global")
    uploaded_salaires = st.file_uploader("Charger votre fichier de paie (Excel)", type=['xlsx'])
    
    if uploaded_salaires:
        df_paie = pd.read_excel(uploaded_salaires)
        all_rows = []
        lib = f"salaire {datetime.now().strftime('%m/%y')}"
        date_paie = datetime.now().strftime("%d/%m/%Y")

        for index, row in df_paie.iterrows():
            sb = float(row['SB'])
            prime = float(row.get('PRIME', 0))
            ir = float(row.get('IR', 0))
            
            # Application des taux Faisal Karmi
            d61741 = sb * 0.1698 # Patronal CNSS
            d61743 = sb * 0.0411 # Patronal AMO
            c4441_1 = sb * 0.2146
            c4441_2 = sb * 0.0637
            c44320 = (sb + prime + d61741 + d61743) - (c4441_1 + c4441_2 + ir)

            # Les 8 lignes obligatoires par employé
            all_rows.extend([
                ["OD", date_paie, "61711000", lib, format_maroc(sb), "0,00"],
                ["OD", date_paie, "61712000", lib, format_maroc(prime), "0,00"],
                ["OD", date_paie, "61741000", lib, format_maroc(d61741), "0,00"],
                ["OD", date_paie, "61743000", lib, format_maroc(d61743), "0,00"],
                ["OD", date_paie, "44410000", lib, "0,00", format_maroc(c4441_1)],
                ["OD", date_paie, "44410000", lib, "0,00", format_maroc(c4441_2)],
                ["OD", date_paie, "44525000", lib, "0,00", format_maroc(ir)],
                ["OD", date_paie, "44320000", lib, "0,00", format_maroc(c44320)]
            ])
            
        df_final_od = pd.DataFrame(all_rows, columns=["Journal", "Date", "Compte", "Libellé", "Débit", "Crédit"])
        st.dataframe(df_final_od)
        st.download_button("📥 Télécharger Journal OD Complet", convert_df_to_csv(df_final_od), "journal_od_global.csv")
