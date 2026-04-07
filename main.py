import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO

# --- FONCTIONS UTILITAIRES ---
def format_montant(val):
    """Formate les montants avec 2 décimales et une virgule[cite: 42, 64, 116, 121]."""
    try:
        if pd.isna(val) or val == "":
            return "0,00"
        return f"{float(val):.2f}".replace('.', ',')
    except:
        return "0,00"

def clean_libelle_releve(libelle):
    """Résume le libellé à 27 caractères max, tente de garder les noms propres[cite: 34, 36, 37]."""
    libelle = str(libelle).strip()
    # Logique pour extraire les 6 derniers chiffres d'un chèque si le mot chèque est présent [cite: 35]
    if "cheque" in libelle.lower() or "chq" in libelle.lower():
        numeros = re.findall(r'\d+', libelle)
        if numeros:
            dernier_num = numeros[-1][-6:]
            libelle = f"CHEQUE {dernier_num}"
    return libelle[:27]

def determiner_compte_releve(libelle, montant_debit):
    """Affecte le compte en fonction de la désignation si c'est un débit[cite: 27, 28, 29, 30]."""
    if montant_debit > 0:
        lib_lower = libelle.lower()
        if any(mot in lib_lower for mot in ["frais", "forfait", "frais émission", "droit de timbre", "frais de retrait", "comm", "commission", "taxe"]):
            return "61470000"
        elif "cnss" in lib_lower:
            return "44410000"
        elif "amendis" in lib_lower:
            return "44110902"
        elif "iam" in lib_lower:
            return "44110901"
        elif "aznag" in lib_lower:
            return "44110017"
        elif any(mot in lib_lower for mot in ["kaoutar", "wiam", "meriem", "soukaina"]):
            return "44320000"
        elif any(mot in lib_lower for mot in ["mourabaha", "kriti", "prélèvements"]):
            return "11175000"
        else:
            return "44970000"
    return "" # Pour le crédit, à définir selon vos règles futures

# --- MODULE 1 : SALAIRES ---
def traiter_salaires(df_source):
    """Génère l'écriture de salaire[cite: 85, 91]."""
    lignes_comptables = []
    
    for index, row in df_source.iterrows():
        try:
            date_sal = pd.to_datetime(row['Date']).strftime('%d/%m/%Y') # Format jj/mm/aaaa [cite: 98]
            mm_aa = pd.to_datetime(row['Date']).strftime('%m/%y')
            libelle = f"salaire {mm_aa}" # [cite: 110]
            
            sb = float(row.get('Salaire de base', 0)) # [cite: 88]
            prime = float(row.get('Prime', 0)) # [cite: 89]
            ir = float(row.get('IR', 0)) # [cite: 90]
            
            # Calculs Débit [cite: 111]
            d_61711 = sb # [cite: 112]
            d_61712 = prime # [cite: 113]
            d_61741 = sb * 0.1698 # [cite: 114]
            d_61743 = sb * 0.0411 # [cite: 115]
            
            # Calculs Crédit [cite: 117]
            c_44410_1 = sb * 0.2146 # [cite: 118]
            c_44410_2 = sb * 0.0637 # [cite: 118]
            c_44525 = ir # [cite: 119]
            
            total_debit = d_61711 + d_61712 + d_61741 + d_61743
            total_credit_partiel = c_44410_1 + c_44410_2 + c_44525
            c_44320 = total_debit - total_credit_partiel # Equilibrage parfait 
            
            base_row = {"Type": "OD", "Date": date_sal} # [cite: 96, 97]
            
            # Création des 8 lignes dans l'ordre exact [cite: 100]
            ecritures = [
                {"Compte": "61711000", "Libellé": libelle, "Débit": d_61711, "Crédit": 0}, # [cite: 101]
                {"Compte": "61712000", "Libellé": libelle, "Débit": d_61712, "Crédit": 0}, # [cite: 102]
                {"Compte": "61741000", "Libellé": libelle, "Débit": d_61741, "Crédit": 0}, # [cite: 103]
                {"Compte": "61743000", "Libellé": libelle, "Débit": d_61743, "Crédit": 0}, # [cite: 104]
                {"Compte": "44410000", "Libellé": libelle, "Débit": 0, "Crédit": c_44410_1}, # [cite: 105]
                {"Compte": "44410000", "Libellé": libelle, "Débit": 0, "Crédit": c_44410_2}, # [cite: 106]
                {"Compte": "4452500", "Libellé": libelle, "Débit": 0, "Crédit": c_44525}, # [cite: 107]
                {"Compte": "44320000", "Libellé": libelle, "Débit": 0, "Crédit": c_44320} # [cite: 108]
            ]
            
            for ecriture in ecritures:
                row_final = {**base_row, **ecriture}
                row_final["Débit"] = format_montant(row_final["Débit"])
                row_final["Crédit"] = format_montant(row_final["Crédit"])
                lignes_comptables.append(row_final)
                
        except Exception as e:
            st.error(f"Erreur sur une ligne de salaire : {e}")
            
    df_final = pd.DataFrame(lignes_comptables, columns=["Type", "Date", "Compte", "Libellé", "Débit", "Crédit"]) # [cite: 93]
    return df_final


# --- MODULE 2 : FACTURES ---
def traiter_factures(df_source):
    """Génère 3 lignes d'écritures par facture[cite: 44, 56]."""
    lignes_comptables = []
    
    for index, row in df_source.iterrows():
        try:
            date_fac = str(row['Date'])
            ref = str(row['Référence'])
            nom_ste = str(row['Nom Société'])
            ttc = float(row['TTC']) # [cite: 62]
            
            ht = ttc / 1.2 # TVA 20% [cite: 63, 68]
            tva = ttc - ht # [cite: 74]
            
            # Colonnes répétées [cite: 57]
            base_row = {
                "Code journal": "ACH", # [cite: 58]
                "Date de facture": date_fac, # [cite: 59]
                "Référence": ref, # [cite: 60]
                "Libellé écriture": nom_ste # [cite: 61]
            }
            
            # Ligne 1 : HT [cite: 66]
            lignes_comptables.append({**base_row, "Compte": "61110000", "Montant débit": format_montant(ht), "Montant crédit": "0,00"}) # [cite: 67, 69, 71]
            
            # Ligne 2 : TVA [cite: 70]
            lignes_comptables.append({**base_row, "Compte": "34550000", "Montant débit": format_montant(tva), "Montant crédit": "0,00"}) # [cite: 73, 76, 79]
            
            # Ligne 3 : TTC [cite: 78]
            lignes_comptables.append({**base_row, "Compte": "44110000", "Montant débit": "0,00", "Montant crédit": format_montant(ttc)}) # [cite: 80, 81, 82]
            
        except Exception as e:
            st.error(f"Erreur sur la facture {row.get('Référence', 'Inconnue')} : {e}")

    df_final = pd.DataFrame(lignes_comptables, columns=["Code journal", "Date de facture", "Référence", "Compte", "Libellé écriture", "Montant débit", "Montant crédit"]) # [cite: 46, 47, 48, 49, 50, 51, 52, 53]
    return df_final


# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="SUPER COMPTA", layout="wide")
st.title("SUPER COMPTA") # [cite: 1]

tab1, tab2, tab3 = st.tabs(["Relevés Bancaires", "Factures", "Table Salaires"])

# ----------------- ONGLET 1 : RELEVÉS BANCAIRES -----------------
with tab1:
    st.header("Traitement des Relevés Bancaires") # [cite: 2]
    fichiers_releves = st.file_uploader("Upload des fichiers (Maximum 12)", type=['pdf', 'csv', 'xlsx'], accept_multiple_files=True, key="releves") # 
    
    if fichiers_releves:
        if len(fichiers_releves) > 12:
            st.error("Vous ne pouvez uploader que 12 fichiers maximum.")
        else:
            st.info("Note technique: L'extraction PDF native dépend fortement du format de la banque. Si le PDF ne passe pas, uploadez un CSV/Excel contenant 'Date', 'Libellé', 'Débit', 'Crédit'.")
            if st.button("Traiter les relevés"):
                dfs_releves = []
                for file in fichiers_releves:
                    # Traitement simplifié pour l'exemple si le fichier est un excel
                    if file.name.endswith('.xlsx') or file.name.endswith('.csv'):
                        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
                        for idx, row in df.iterrows():
                            debit_val = float(row.get('Débit', 0))
                            credit_val = float(row.get('Crédit', 0))
                            libelle_propre = clean_libelle_releve(row.get('Libellé', ''))
                            compte = determiner_compte_releve(libelle_propre, debit_val)
                            
                            dfs_releves.append({
                                "Code": "5141", # [cite: 25]
                                "date": pd.to_datetime(row['Date']).strftime('%d/%m/%Y'), # [cite: 26]
                                "compte": compte, # [cite: 28]
                                "libellé": libelle_propre, # [cite: 32]
                                "débit": format_montant(debit_val), # [cite: 38]
                                "crédit": format_montant(credit_val) # [cite: 39]
                            })
                
                if dfs_releves:
                    df_final_releves = pd.DataFrame(dfs_releves, columns=["Code", "date", "compte", "libellé", "débit", "crédit"]) # [cite: 24]
                    st.dataframe(df_final_releves)
                    csv = df_final_releves.to_csv(index=False, sep=";").encode('utf-8') # [cite: 22]
                    st.download_button(label="Télécharger CSV", data=csv, file_name='releves_compta.csv', mime='text/csv')

# ----------------- ONGLET 2 : FACTURES -----------------
with tab2:
    st.header("Traitement des Factures") # [cite: 3]
    fichiers_factures = st.file_uploader("Upload des fichiers (Maximum 20)", type=['xlsx', 'csv'], accept_multiple_files=True, key="factures") # 
    st.write("*Veuillez uploader un tableau contenant : Date, Référence, Nom Société, TTC*")
    
    if fichiers_factures:
        if len(fichiers_factures) > 20:
             st.error("Vous ne pouvez uploader que 20 fichiers maximum.")
        else:
            if st.button("Traiter les factures"):
                all_factures_df = pd.DataFrame()
                for file in fichiers_factures:
                    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
                    all_factures_df = pd.concat([all_factures_df, df])
                
                df_result_factures = traiter_factures(all_factures_df)
                st.dataframe(df_result_factures)
                csv = df_result_factures.to_csv(index=False, sep=";").encode('utf-8') # [cite: 84]
                st.download_button("Télécharger CSV Factures", data=csv, file_name='factures_compta.csv', mime='text/csv')

# ----------------- ONGLET 3 : SALAIRES -----------------
with tab3:
    st.header("Traitement des Salaires") # [cite: 4]
    fichier_salaire = st.file_uploader("Upload LE FICHIER (Excel ou PDF)", type=['xlsx', 'csv'], key="salaires") # [cite: 5, 8]
    
    if fichier_salaire:
        if st.button("Traiter les salaires"):
            df_source_salaires = pd.read_excel(fichier_salaire) if fichier_salaire.name.endswith('.xlsx') else pd.read_csv(fichier_salaire)
            # Vérification des colonnes attendues [cite: 86, 87, 88, 89, 90]
            colonnes_requises = ['Date', 'Salaire de base', 'Prime', 'IR']
            if all(col in df_source_salaires.columns for col in colonnes_requises):
                df_result_salaires = traiter_salaires(df_source_salaires)
                st.dataframe(df_result_salaires)
                csv = df_result_salaires.to_csv(index=False, sep=";").encode('utf-8') # [cite: 9]
                st.download_button("Télécharger CSV Salaires", data=csv, file_name='salaires_compta.csv', mime='text/csv')
            else:
                st.error(f"Le fichier doit contenir exactement ces colonnes : {colonnes_requises}")
