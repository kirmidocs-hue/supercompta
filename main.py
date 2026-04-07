with tab1:
    st.header("Relevés Bancaires")
    files = st.file_uploader("Upload PDF (Max 12)", type=['pdf'], accept_multiple_files=True)
    
    if files and st.button("Extraire avec IA"):
        all_banque_data = []
        for f in files:
            try:
                with pdfplumber.open(f) as pdf:
                    full_text = ""
                    # Extraction de TOUTES les pages pour ne rien oublier
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                
                if not full_text.strip():
                    st.error(f"Le fichier {f.name} semble être une image scannée sans texte lisible.")
                    continue

                # Prompt optimisé pour éviter les erreurs de formatage JSON
                prompt_text = f"""
                Tu es un expert comptable marocain. Extrais TOUTES les lignes d'opérations du relevé suivant.
                RETOURNE UNIQUEMENT UN JSON ARRAY. 
                Format attendu : [{{"date":"dd/mm/yyyy", "libelle":"...", "debit":0.0, "credit":0.0}}]
                
                RÈGLES CRITIQUES :
                1. Ne saute AUCUNE ligne d'opération.
                2. Si le libellé contient un numéro de chèque, garde les 6 derniers chiffres.
                3. Résume le libellé à 27 caractères maximum.
                4. Ignore les lignes de solde ou les messages publicitaires.
                
                TEXTE DU RELEVÉ :
                {full_text}
                """
                
                response = model.generate_content(prompt_text)
                
                # Nettoyage de la réponse pour isoler le JSON
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    for item in data:
                        # Application des règles de sortie
                        all_banque_data.append({
                            "Code": "5141",
                            "date": item.get('date', ''),
                            "compte": get_compte_banque(item.get('libelle', ''), item.get('debit', 0)),
                            "libellé": str(item.get('libelle', ''))[:27],
                            "débit": format_montant(item.get('debit', 0)),
                            "crédit": format_montant(item.get('credit', 0))
                        })
            except Exception as e:
                st.error(f"Erreur technique sur {f.name} : {str(e)}")

        if all_banque_data:
            df_b = pd.DataFrame(all_banque_data)
            st.success(f"Extraction terminée : {len(df_b)} opérations trouvées.")
            st.dataframe(df_b)
            # Export CSV avec séparateur point-virgule
            csv_data = df_b.to_csv(index=False, sep=";").encode('utf-8')
            st.download_button("Télécharger CSV Banque", csv_data, "banque.csv", "text/csv")
