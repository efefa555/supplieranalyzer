import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils import process_data
import database as db

# Page configuration
st.set_page_config(
    page_title="Saisie Manuelle",
    page_icon="✏️",
    layout="wide"
)

# Header
st.title("Saisie Manuelle des Données")
st.write("Ajoutez et modifiez des données sans importer de fichier Excel")

# Charger les données depuis la base de données lors de l'initialisation
if 'manual_data' not in st.session_state:
    # Vérifier si la base de données contient des données
    if db.db_has_data():
        st.session_state['manual_data'] = db.get_suppliers_dataframe()
    else:
        # Si la base de données est vide, créer un dataframe vide
        st.session_state['manual_data'] = pd.DataFrame({
            'Nom du fournisseur': [],
            'Date de commande': [],
            'Montant de la commande': [],
            'Date de réception': [],
            'Date de paiement': []
        })

# Create a function to add data to the session state and database
def add_entry_to_data():
    new_entry = {
        'Nom du fournisseur': st.session_state.supplier_name,
        'Date de commande': st.session_state.order_date,
        'Montant de la commande': st.session_state.order_amount,
        'Date de réception': st.session_state.reception_date,
        'Date de paiement': st.session_state.payment_date if st.session_state.is_paid else None
    }
    
    # Process the entry to calculate delays and status
    processed_entry = process_data(pd.DataFrame([new_entry])).iloc[0].to_dict()
    
    # Add to database
    if db.add_supplier(processed_entry):
        # Append to the manual data
        st.session_state['manual_data'] = pd.concat([
            st.session_state['manual_data'], 
            pd.DataFrame([processed_entry])
        ], ignore_index=True)
        
        # Add to the main processed data
        if 'processed_data' in st.session_state:
            # If processed_data exists, append the new entry
            st.session_state['processed_data'] = pd.concat([
                st.session_state['processed_data'],
                pd.DataFrame([processed_entry])
            ], ignore_index=True)
        else:
            # If processed_data doesn't exist, create it from the manual data
            st.session_state['processed_data'] = st.session_state['manual_data'].copy()
        
        # Reset the form fields
        st.session_state.supplier_name = ""
        st.session_state.order_amount = 0.0
        st.success("Données ajoutées avec succès à la base de données!")
    else:
        st.error("Erreur lors de l'ajout des données à la base de données.")

# Section for adding a new entry
st.header("Ajouter une nouvelle entrée")

# Create a form for data entry
with st.form(key='data_entry_form'):
    col1, col2 = st.columns(2)
    
    with col1:
        # If there are existing suppliers, offer them in a dropdown
        existing_suppliers = []
        if 'processed_data' in st.session_state and not st.session_state['processed_data'].empty:
            existing_suppliers = sorted(st.session_state['processed_data']['Nom du fournisseur'].unique().tolist())
        
        if existing_suppliers:
            supplier_options = ["Nouveau fournisseur"] + existing_suppliers
            supplier_selection = st.selectbox(
                "Sélectionner un fournisseur",
                options=supplier_options,
                key="supplier_selection"
            )
            
            if supplier_selection == "Nouveau fournisseur":
                st.text_input("Nom du fournisseur", key="supplier_name")
            else:
                st.session_state.supplier_name = supplier_selection
        else:
            st.text_input("Nom du fournisseur", key="supplier_name")
        
        st.date_input(
            "Date de commande",
            value=datetime.now(),
            key="order_date"
        )
        
        st.number_input(
            "Montant de la commande (€)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            key="order_amount"
        )
    
    with col2:
        st.date_input(
            "Date de réception",
            value=datetime.now() + timedelta(days=7),
            key="reception_date"
        )
        
        is_paid = st.checkbox("Commande payée", key="is_paid")
        
        if is_paid:
            st.date_input(
                "Date de paiement",
                value=datetime.now() + timedelta(days=30),
                key="payment_date"
            )
    
    submit_button = st.form_submit_button(label="Ajouter l'entrée")
    if submit_button:
        add_entry_to_data()
        st.rerun()

# Display the current data
st.header("Données en base")

if not st.session_state['manual_data'].empty:
    # Add an option to edit or delete entries
    edited_data = st.data_editor(
        st.session_state['manual_data'],
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "Nom du fournisseur": st.column_config.TextColumn("Fournisseur"),
            "Date de commande": st.column_config.DateColumn("Date commande", format="DD/MM/YYYY"),
            "Montant de la commande": st.column_config.NumberColumn("Montant (€)", format="%.2f €"),
            "Date de réception": st.column_config.DateColumn("Date réception", format="DD/MM/YYYY"),
            "Date de paiement": st.column_config.DateColumn("Date paiement", format="DD/MM/YYYY"),
            "Délai de paiement": st.column_config.NumberColumn("Délai (jours)"),
            "Statut du paiement": st.column_config.TextColumn("Statut"),
            "Jours de retard": st.column_config.NumberColumn("Jours retard"),
            "Montant pénalité": st.column_config.NumberColumn("Pénalité (€)", format="%.2f €")
        }
    )
    
    # Button to save edited data
    if st.button("Enregistrer les modifications en base de données"):
        try:
            # Update the database with edited data
            success_count = 0
            
            # Process the edited data to recalculate delays and status
            processed_edited_data = process_data(edited_data)
            
            for _, row in processed_edited_data.iterrows():
                row_dict = row.to_dict()
                
                if 'id' in row_dict and row_dict['id'] is not None:
                    # Update existing supplier
                    if db.update_supplier(row_dict['id'], row_dict):
                        success_count += 1
                else:
                    # Add new supplier
                    if db.add_supplier(row_dict):
                        success_count += 1
            
            # Get fresh data from database
            fresh_data = db.get_suppliers_dataframe()
            
            # Update session states
            st.session_state['manual_data'] = fresh_data
            
            if 'processed_data' in st.session_state:
                # Update the main processed data
                # Preserve any data from file imports, only update or add the database entries
                db_ids = fresh_data['id'].tolist() if 'id' in fresh_data.columns else []
                
                # Get processed data without the database entries
                if db_ids and 'id' in st.session_state['processed_data'].columns:
                    non_db_data = st.session_state['processed_data'][~st.session_state['processed_data']['id'].isin(db_ids)]
                else:
                    # No way to distinguish, so replace all
                    non_db_data = pd.DataFrame()
                
                # Combine with fresh data
                st.session_state['processed_data'] = pd.concat([non_db_data, fresh_data], ignore_index=True)
            else:
                st.session_state['processed_data'] = fresh_data.copy()
            
            st.success(f"{success_count} entrées mises à jour avec succès dans la base de données!")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur lors de la mise à jour des données: {e}")
else:
    st.info("Aucune donnée n'a encore été saisie. Utilisez le formulaire ci-dessus pour ajouter des entrées.")

# Section to bulk import data from a text input
st.header("Import rapide de données")
st.write("""
Vous pouvez saisir plusieurs entrées à la fois en utilisant le format CSV ci-dessous.
Format: Nom du fournisseur, Date de commande (JJ/MM/AAAA), Montant, Date de réception (JJ/MM/AAAA), Date de paiement (JJ/MM/AAAA)
""")

csv_data = st.text_area(
    "Collez vos données au format CSV (une ligne par entrée)",
    height=150,
    placeholder="Fournisseur A, 01/05/2025, 10000, 10/05/2025, 01/06/2025\nFournisseur B, 05/05/2025, 25000, 15/05/2025, 05/07/2025"
)

if st.button("Importer ces données"):
    if csv_data:
        # Parse the CSV data
        rows = csv_data.strip().split('\n')
        new_data = []
        errors = []
        
        for row in rows:
            try:
                parts = [part.strip() for part in row.split(',')]
                if len(parts) >= 3:  # At minimum, we need supplier, date, and amount
                    entry = {
                        'Nom du fournisseur': parts[0],
                        'Date de commande': pd.to_datetime(parts[1], format='%d/%m/%Y', errors='coerce'),
                        'Montant de la commande': float(parts[2]),
                        'Date de réception': pd.to_datetime(parts[3], format='%d/%m/%Y', errors='coerce') if len(parts) > 3 else None,
                        'Date de paiement': pd.to_datetime(parts[4], format='%d/%m/%Y', errors='coerce') if len(parts) > 4 else None
                    }
                    new_data.append(entry)
            except Exception as e:
                errors.append(f"Ligne: {row}. Erreur: {e}")
        
        if errors:
            st.error(f"Erreurs lors du traitement de {len(errors)} ligne(s):")
            for error in errors[:5]:  # Show first 5 errors
                st.error(error)
            if len(errors) > 5:
                st.error(f"... et {len(errors) - 5} autres erreurs.")
        
        # Add the new data to the database
        if new_data:
            # Process the data to calculate delays and status
            new_df = process_data(pd.DataFrame(new_data))
            
            # Add to database
            success_count, total_count = db.add_suppliers_from_dataframe(new_df)
            
            if success_count > 0:
                # Get fresh data from database
                fresh_data = db.get_suppliers_dataframe()
                
                # Update session states
                st.session_state['manual_data'] = fresh_data
                
                # Update the main processed data
                if 'processed_data' in st.session_state:
                    # Identify database entries vs imported data
                    db_ids = fresh_data['id'].tolist() if 'id' in fresh_data.columns else []
                    
                    # Get processed data without the database entries
                    if db_ids and 'id' in st.session_state['processed_data'].columns:
                        non_db_data = st.session_state['processed_data'][~st.session_state['processed_data']['id'].isin(db_ids)]
                    else:
                        # No way to distinguish, so replace all
                        non_db_data = pd.DataFrame()
                    
                    # Combine with fresh data
                    st.session_state['processed_data'] = pd.concat([non_db_data, fresh_data], ignore_index=True)
                else:
                    st.session_state['processed_data'] = fresh_data.copy()
                
                st.success(f"{success_count}/{total_count} entrées importées avec succès dans la base de données!")
                st.rerun()
            else:
                st.error("Aucune entrée n'a pu être ajoutée à la base de données.")
    else:
        st.warning("Aucune donnée à importer. Veuillez saisir des données au format CSV.")

# Section for data persistence options
st.header("Gestion des données")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Exporter les données")
    
    # Download as CSV
    if not st.session_state['manual_data'].empty:
        csv = st.session_state['manual_data'].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger les données (CSV)",
            data=csv,
            file_name=f"donnees_fournisseurs_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aucune donnée à exporter.")

with col2:
    st.subheader("Effacer les données")
    
    if st.button("Effacer toutes les données de la base de données", type="secondary"):
        # Ask for confirmation with a checkbox
        confirm = st.checkbox("Je confirme vouloir supprimer toutes les données (cette action est irréversible)")
        
        if confirm:
            # Delete all data from the database
            if db.delete_all_suppliers():
                # Remove manual data from processed_data
                if 'processed_data' in st.session_state and not st.session_state['manual_data'].empty:
                    manual_suppliers = st.session_state['manual_data']['Nom du fournisseur'].tolist()
                    manual_dates = st.session_state['manual_data']['Date de commande'].tolist()
                    
                    # Keep only rows that are not from manual entry
                    mask = ~(
                        (st.session_state['processed_data']['Nom du fournisseur'].isin(manual_suppliers)) & 
                        (st.session_state['processed_data']['Date de commande'].isin(manual_dates))
                    )
                    
                    st.session_state['processed_data'] = st.session_state['processed_data'][mask].reset_index(drop=True)
                
                # Clear manual data
                st.session_state['manual_data'] = pd.DataFrame({
                    'Nom du fournisseur': [],
                    'Date de commande': [],
                    'Montant de la commande': [],
                    'Date de réception': [],
                    'Date de paiement': []
                })
                
                st.success("Les données ont été supprimées avec succès de la base de données.")
                st.rerun()
            else:
                st.error("Erreur lors de la suppression des données.")

# Information sur la persistance des données
st.info("""
**Note sur la persistance des données**: 
Les données sont maintenant stockées de manière permanente dans une base de données.
Elles seront disponibles à chaque fois que vous ouvrirez l'application.
Vous pouvez toujours exporter vos données en CSV pour les manipuler avec d'autres outils comme Excel.
""")