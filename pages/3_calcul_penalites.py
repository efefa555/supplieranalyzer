import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import calculate_penalties, PENALTY_INTEREST_RATE

# Page configuration
st.set_page_config(
    page_title="Calcul des Pénalités",
    page_icon="⚖️",
    layout="wide"
)

# Header
st.title("Calcul des Pénalités de Retard")
st.write("Calculez les pénalités de retard selon la loi 69-21")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# Information about the law
with st.expander("Informations sur la loi 69-21"):
    st.markdown("""
    ### Loi 69-21 sur les délais de paiement
    
    Cette loi encadre les délais de paiement entre entreprises et prévoit des pénalités en cas de retard de paiement.
    
    #### Points clés:
    - **Délai légal standard**: 60 jours à compter de la date de facturation, sauf accord spécifique
    - **Taux d'intérêt applicable**: 3% (dans le cadre de cette application)
    - **Calcul des pénalités**: (Montant de la facture × Taux d'intérêt × Jours de retard) / 365
    
    #### Exemple:
    Pour une facture de 10 000 € payée avec 15 jours de retard:
    - Pénalité = (10 000 € × 3% × 15) / 365 = 12,33 €
    
    #### Obligations:
    - Les pénalités sont dues sans qu'un rappel soit nécessaire
    - L'entreprise doit mentionner ces pénalités sur ses factures
    """)

# Parameters for penalty calculation
st.header("Paramètres de calcul")

col1, col2 = st.columns(2)

with col1:
    standard_delay = st.number_input(
        "Délai standard de paiement (jours)",
        min_value=0,
        max_value=120,
        value=60,
        help="Délai standard de paiement selon la loi ou les accords commerciaux"
    )

with col2:
    interest_rate = st.number_input(
        "Taux d'intérêt applicable (%)",
        min_value=0.0,
        max_value=10.0,
        value=PENALTY_INTEREST_RATE * 100,
        step=0.1,
        format="%.1f",
        help="Taux d'intérêt applicable pour le calcul des pénalités"
    ) / 100  # Convert percentage to decimal

# Calculate penalties
data_with_penalties = data.copy()

# Calculate days of delay beyond standard
data_with_penalties['Jours de retard'] = data_with_penalties['Délai de paiement'].apply(
    lambda x: max(0, x - standard_delay)
)

# Calculate penalty amount based on the law
data_with_penalties['Montant pénalité'] = (
    data_with_penalties['Montant de la commande'] * 
    interest_rate * 
    data_with_penalties['Jours de retard']
) / 365

# Filters
st.header("Filtrer les résultats")

col1, col2 = st.columns(2)

with col1:
    # Filter by supplier
    suppliers = ["Tous"] + sorted(data_with_penalties['Nom du fournisseur'].unique().tolist())
    selected_supplier = st.selectbox("Fournisseur", suppliers, key="supplier_filter_penalties")

with col2:
    # Filter to show only late payments
    show_only_late = st.checkbox("Afficher uniquement les paiements en retard", value=True)

# Apply filters
filtered_data = data_with_penalties.copy()

if selected_supplier != "Tous":
    filtered_data = filtered_data[filtered_data['Nom du fournisseur'] == selected_supplier]

if show_only_late:
    filtered_data = filtered_data[filtered_data['Jours de retard'] > 0]

# Summary metrics
st.header("Résumé des pénalités")

col1, col2, col3 = st.columns(3)

with col1:
    total_penalties = filtered_data['Montant pénalité'].sum()
    st.metric("Total des pénalités", f"{total_penalties:,.2f} €")

with col2:
    late_payments_count = filtered_data[filtered_data['Jours de retard'] > 0].shape[0]
    total_payments = filtered_data.shape[0]
    late_ratio = late_payments_count / total_payments if total_payments > 0 else 0
    st.metric("Paiements en retard", f"{late_payments_count} ({late_ratio*100:.1f}%)")

with col3:
    avg_delay = filtered_data[filtered_data['Jours de retard'] > 0]['Jours de retard'].mean() if late_payments_count > 0 else 0
    st.metric("Retard moyen", f"{avg_delay:.1f} jours")

# Visualization
st.header("Visualisation des pénalités")

col1, col2 = st.columns(2)

with col1:
    # Penalties by supplier
    penalties_by_supplier = filtered_data.groupby('Nom du fournisseur')['Montant pénalité'].sum().reset_index()
    penalties_by_supplier = penalties_by_supplier.sort_values('Montant pénalité', ascending=False)
    
    fig_penalties = px.bar(
        penalties_by_supplier,
        x='Nom du fournisseur',
        y='Montant pénalité',
        title="Pénalités par fournisseur",
        color='Montant pénalité',
        color_continuous_scale=px.colors.sequential.Reds,
        labels={'Montant pénalité': 'Montant des pénalités (€)', 'Nom du fournisseur': 'Fournisseur'}
    )
    st.plotly_chart(fig_penalties, use_container_width=True)

with col2:
    # Relationship between delay and penalties
    fig_scatter = px.scatter(
        filtered_data[filtered_data['Jours de retard'] > 0],
        x='Jours de retard',
        y='Montant pénalité',
        color='Nom du fournisseur',
        size='Montant de la commande',
        hover_data=['Date de commande', 'Date de paiement', 'Délai de paiement'],
        title="Relation entre retard et pénalités",
        labels={
            'Jours de retard': 'Jours de retard',
            'Montant pénalité': 'Montant des pénalités (€)'
        }
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# Detailed data table
st.header("Tableau détaillé des pénalités")

# Sort by penalty amount in descending order
sorted_data = filtered_data.sort_values('Montant pénalité', ascending=False)

# Format the table for better readability
display_cols = [
    'Nom du fournisseur', 
    'Date de commande', 
    'Date de paiement', 
    'Montant de la commande', 
    'Délai de paiement', 
    'Jours de retard', 
    'Montant pénalité'
]

# Custom formatter for the dataframe
def highlight_late(val):
    if isinstance(val, (int, float)) and val > 0:
        return 'color: red'
    return ''

# Display with styling
st.dataframe(
    sorted_data[display_cols].style.applymap(highlight_late, subset=['Jours de retard', 'Montant pénalité']),
    use_container_width=True
)

# Summary analysis
st.header("Analyse et impact financier")

# Calculate impact metrics
total_order_amount = filtered_data['Montant de la commande'].sum()
penalty_ratio = total_penalties / total_order_amount if total_order_amount > 0 else 0

col1, col2 = st.columns(2)

with col1:
    st.subheader("Impact financier")
    st.markdown(f"""
    - **Montant total des commandes**: {total_order_amount:,.2f} €
    - **Montant total des pénalités**: {total_penalties:,.2f} €
    - **Ratio pénalités/commandes**: {penalty_ratio*100:.4f}%
    
    Si tous les fournisseurs réclamaient leurs pénalités de retard, cela représenterait un coût supplémentaire de **{total_penalties:,.2f} €**.
    """)

with col2:
    st.subheader("Recommandations")
    st.markdown("""
    ### Pour réduire les pénalités:
    
    1. **Prioriser les paiements** avec les montants les plus élevés pour minimiser les pénalités
    2. **Mettre en place un système d'alerte** pour les factures approchant de l'échéance
    3. **Négocier des délais de paiement** adaptés avec les fournisseurs stratégiques
    4. **Améliorer le processus de validation** des factures pour réduire les délais internes
    5. **Analyser périodiquement** les causes des retards pour des améliorations ciblées
    """)

# Penalty projection
st.header("Projection des pénalités")

# Calculate penalties over time (by month)
filtered_data['Mois paiement'] = pd.to_datetime(filtered_data['Date de paiement']).dt.to_period('M').astype(str)
penalties_by_month = filtered_data.groupby('Mois paiement')['Montant pénalité'].sum().reset_index()

if not penalties_by_month.empty:
    fig_time = px.line(
        penalties_by_month,
        x='Mois paiement',
        y='Montant pénalité',
        title="Évolution des pénalités par mois",
        markers=True,
        labels={'Montant pénalité': 'Montant des pénalités (€)', 'Mois paiement': 'Mois'}
    )
    st.plotly_chart(fig_time, use_container_width=True)
else:
    st.info("Données insuffisantes pour afficher l'évolution des pénalités par mois.")

# Warning about legal implications
st.warning("""
**Note importante**: Les calculs de pénalités présentés sont basés sur les paramètres fournis et les données disponibles. 
Ces estimations sont à titre indicatif et pourraient différer des montants exigibles dans un contexte légal. 
Consultez un expert juridique ou financier pour une évaluation précise dans le cadre de la loi 69-21.
""")
