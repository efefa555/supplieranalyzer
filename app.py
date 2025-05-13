import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import (
    load_sample_data, process_data, calculate_penalties,
    calculate_bfr, calculate_dpo, calculate_cash_ratio,
    calculate_current_ratio, get_download_link
)

# Page configuration
st.set_page_config(
    page_title="Tableau de Bord Fournisseurs",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve the look and feel
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Import database module
import database as db

# Session State initialization
if 'data' not in st.session_state:
    st.session_state['data'] = load_sample_data()
if 'processed_data' not in st.session_state:
    # Check if we have data in the database
    if db.db_has_data():
        st.session_state['processed_data'] = db.get_suppliers_dataframe()
    else:
        st.session_state['processed_data'] = pd.DataFrame()

# Header with logo and title
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://pixabay.com/get/gacaf664c28341d3708fc6c969db8be3e45d5a13151ba3767eb6b8eb1f773f53493103eb95eb0ae52e41341c79d2446f697b7edeaf8070ae6b691f85a80a369fa_1280.jpg", width=100)
with col2:
    st.title("Tableau de Bord de Gestion des Paiements Fournisseurs")
    st.write("Analyse et suivi des paiements fournisseurs selon la Loi 69-21")

# Sidebar for data upload and global filters
with st.sidebar:
    st.header("Chargement de données")
    
    uploaded_file = st.file_uploader(
        "Télécharger un fichier Excel ou CSV contenant les données fournisseurs",
        type=["xlsx", "csv"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_excel(uploaded_file)
            
            # Process the data
            st.session_state['data'] = data
            st.session_state['processed_data'] = process_data(data)
            st.success("Données chargées avec succès!")
        except Exception as e:
            st.error(f"Erreur lors du chargement des données: {e}")
    
    # Sample data generation option
    if st.button("Générer des données d'exemple"):
        # Create a sample dataset
        suppliers = ["Fournisseur A", "Fournisseur B", "Fournisseur C", "Fournisseur D", "Fournisseur E"]
        today = datetime.now()
        
        # Generate 50 sample records
        sample_data = []
        for i in range(50):
            supplier = np.random.choice(suppliers)
            order_date = today - timedelta(days=np.random.randint(90, 180))
            amount = np.random.randint(1000, 50000)
            receipt_date = order_date + timedelta(days=np.random.randint(5, 20))
            
            # Some payments are on time, some are late
            delay_factor = np.random.choice([0.8, 1.2, 1.5, 2.0])
            payment_date = order_date + timedelta(days=int(60 * delay_factor))
            
            sample_data.append({
                'Nom du fournisseur': supplier,
                'Date de commande': order_date,
                'Montant de la commande': amount,
                'Date de réception': receipt_date,
                'Date de paiement': payment_date
            })
        
        df = pd.DataFrame(sample_data)
        st.session_state['data'] = df
        st.session_state['processed_data'] = process_data(df)
        st.success("Données d'exemple générées avec succès!")
    
    # Global filters
    st.header("Filtres globaux")
    
    if not st.session_state['processed_data'].empty:
        # Filter by supplier
        suppliers = ["Tous"] + sorted(st.session_state['processed_data']['Nom du fournisseur'].unique().tolist())
        selected_supplier = st.selectbox("Fournisseur", suppliers)
        
        # Filter by date range
        date_min = st.session_state['processed_data']['Date de commande'].min() if 'Date de commande' in st.session_state['processed_data'].columns else datetime.now()
        date_max = st.session_state['processed_data']['Date de commande'].max() if 'Date de commande' in st.session_state['processed_data'].columns else datetime.now()
        
        date_range = st.date_input(
            "Période",
            [date_min, date_max],
            min_value=date_min,
            max_value=date_max,
            format="DD/MM/YYYY"
        )
        
        # Filter by payment status
        statuses = ["Tous", "Dans les délais", "En retard"]
        selected_status = st.selectbox("Statut de paiement", statuses)
        
        # Apply filters to data
        filtered_data = st.session_state['processed_data'].copy()
        
        if selected_supplier != "Tous":
            filtered_data = filtered_data[filtered_data['Nom du fournisseur'] == selected_supplier]
        
        if len(date_range) == 2:
            filtered_data = filtered_data[
                (filtered_data['Date de commande'] >= pd.to_datetime(date_range[0])) &
                (filtered_data['Date de commande'] <= pd.to_datetime(date_range[1]))
            ]
        
        if selected_status != "Tous":
            filtered_data = filtered_data[filtered_data['Statut du paiement'] == selected_status]
        
        st.session_state['filtered_data'] = filtered_data

# Main content area for dashboard
if 'processed_data' in st.session_state and not st.session_state['processed_data'].empty:
    data = st.session_state.get('filtered_data', st.session_state['processed_data'])
    
    # Calculate key metrics
    delay_mean = data['Délai de paiement'].mean() if 'Délai de paiement' in data.columns else 0
    unpaid_amount = data[data['Date de paiement'].isna()]['Montant de la commande'].sum() if 'Date de paiement' in data.columns else 0
    on_time_amount = data[data['Statut du paiement'] == 'Dans les délais']['Montant de la commande'].sum() if 'Statut du paiement' in data.columns else 0
    late_payments_count = data[data['Statut du paiement'] == 'En retard'].shape[0] if 'Statut du paiement' in data.columns else 0
    total_payments = data.shape[0]
    compliance_rate = (total_payments - late_payments_count) / total_payments * 100 if total_payments > 0 else 0
    
    # Display key metrics
    st.header("Aperçu général")
    
    # Create metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Délai moyen de paiement", f"{delay_mean:.1f} jours")
    with col2:
        st.metric("Montant total non réglé", f"{unpaid_amount:,.2f} €")
    with col3:
        st.metric("Paiements dans les délais", f"{on_time_amount:,.2f} €")
    with col4:
        st.metric("Taux de conformité", f"{compliance_rate:.1f}%")
    
    # Create visualization section with tabs
    st.header("Visualisations")
    
    tab1, tab2, tab3 = st.tabs(["Délais de paiement", "Montants", "Statut des paiements"])
    
    with tab1:
        # Payment delay by supplier
        fig_delay = px.bar(
            data.groupby('Nom du fournisseur')['Délai de paiement'].mean().reset_index(),
            x='Nom du fournisseur',
            y='Délai de paiement',
            title="Délai moyen de paiement par fournisseur",
            color='Délai de paiement',
            color_continuous_scale=px.colors.sequential.Blues
        )
        st.plotly_chart(fig_delay, use_container_width=True)
    
    with tab2:
        # Order amounts by supplier
        fig_amount = px.pie(
            data.groupby('Nom du fournisseur')['Montant de la commande'].sum().reset_index(),
            values='Montant de la commande',
            names='Nom du fournisseur',
            title="Répartition des montants de commande par fournisseur"
        )
        st.plotly_chart(fig_amount, use_container_width=True)
    
    with tab3:
        # Payment status distribution
        fig_status = px.bar(
            data.groupby(['Nom du fournisseur', 'Statut du paiement']).size().reset_index(name='count'),
            x='Nom du fournisseur',
            y='count',
            color='Statut du paiement',
            title="Statut des paiements par fournisseur",
            barmode='group'
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Display data table with option to download
    st.header("Données détaillées")
    
    # Display the data table
    st.dataframe(data, use_container_width=True)
    
    # Create a download button for the filtered data
    excel_data = get_download_link(data)
    st.download_button(
        label="Télécharger les données filtrées (Excel)",
        data=excel_data,
        file_name="donnees_fournisseurs_filtrees.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    # Display information on how to get started
    st.info(
        """
        ## Bienvenue dans l'application d'analyse des paiements fournisseurs!
        
        Cette application vous aide à analyser et gérer vos paiements fournisseurs conformément à la loi 69-21.
        
        Pour commencer:
        1. Téléchargez un fichier Excel ou CSV contenant vos données fournisseurs
        2. Ou générez des données d'exemple à des fins de démonstration
        
        ### Structure de données requise:
        Votre fichier doit contenir les colonnes suivantes:
        - Nom du fournisseur
        - Date de commande
        - Montant de la commande
        - Date de réception
        - Date de paiement
        
        ### Fonctionnalités disponibles:
        - Calcul automatique des délais et statuts de paiement
        - Analyse des retards de paiement
        - Calcul des pénalités selon la loi 69-21
        - Gestion du BFR (Besoin en Fonds de Roulement)
        - Tableau de bord fournisseurs
        - Suivi de la trésorerie
        - Calcul des ratios financiers
        - Résumé d'audit
        """
    )
    
    # Display a sample image
    st.image("https://pixabay.com/get/g4253197ef7fdc577e867e3bcb47400bacf3fd3965154d83546368294b1fc2dde3d16a0ee50113d4a8237ec835956cc5ef6cb224f933c44c93b5cb587efd496d9_1280.jpg", 
             caption="Analyse des paiements fournisseurs", 
             use_column_width=True)
