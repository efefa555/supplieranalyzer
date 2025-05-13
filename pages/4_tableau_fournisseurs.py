import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Tableau Fournisseurs",
    page_icon="👥",
    layout="wide"
)

# Header
st.title("Tableau de Bord Fournisseurs")
st.write("Analysez la répartition des achats et dettes par fournisseur")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# Calculate penalties if not already done
if 'Montant pénalité' not in data.columns:
    # We'll assume a standard delay of 60 days and an interest rate of 3%
    standard_delay = 60
    interest_rate = 0.03
    
    # Calculate days of delay beyond standard
    data['Jours de retard'] = data['Délai de paiement'].apply(
        lambda x: max(0, x - standard_delay)
    )
    
    # Calculate penalty amount
    data['Montant pénalité'] = (
        data['Montant de la commande'] * 
        interest_rate * 
        data['Jours de retard']
    ) / 365

# Calculate unpaid amounts (we'll assume a payment is unpaid if the payment date is missing)
data['Statut de la commande'] = data['Date de paiement'].apply(
    lambda x: 'Payée' if pd.notna(x) else 'Non payée'
)

# Sidebar filters
with st.sidebar:
    st.header("Filtres")
    
    # Filter by date range
    date_min = data['Date de commande'].min()
    date_max = data['Date de commande'].max()
    
    date_range = st.date_input(
        "Période",
        [date_min, date_max],
        min_value=date_min,
        max_value=date_max
    )
    
    # Filter by payment status
    payment_statuses = ["Tous", "Payée", "Non payée"]
    selected_payment_status = st.selectbox("Statut de la commande", payment_statuses)
    
    # Apply filters
    filtered_data = data.copy()
    
    if len(date_range) == 2:
        filtered_data = filtered_data[
            (filtered_data['Date de commande'] >= pd.to_datetime(date_range[0])) &
            (filtered_data['Date de commande'] <= pd.to_datetime(date_range[1]))
        ]
    
    if selected_payment_status != "Tous":
        filtered_data = filtered_data[filtered_data['Statut de la commande'] == selected_payment_status]

# Main content
# Top-level metrics
st.header("Aperçu général")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_suppliers = filtered_data['Nom du fournisseur'].nunique()
    st.metric("Nombre de fournisseurs", total_suppliers)

with col2:
    total_orders = filtered_data.shape[0]
    st.metric("Nombre de commandes", total_orders)

with col3:
    total_amount = filtered_data['Montant de la commande'].sum()
    st.metric("Montant total des commandes", f"{total_amount:,.2f} €")

with col4:
    unpaid_amount = filtered_data[filtered_data['Statut de la commande'] == 'Non payée']['Montant de la commande'].sum()
    st.metric("Montant non payé", f"{unpaid_amount:,.2f} €")

# Supplier analysis section
st.header("Analyse par fournisseur")

# Prepare data for charts
supplier_metrics = filtered_data.groupby('Nom du fournisseur').agg({
    'Montant de la commande': 'sum',
    'Délai de paiement': 'mean',
    'Montant pénalité': 'sum',
    'Statut de la commande': lambda x: (x == 'Non payée').mean() * 100  # Percentage of unpaid orders
}).reset_index()

supplier_metrics.columns = [
    'Nom du fournisseur', 
    'Montant total', 
    'Délai moyen de paiement', 
    'Pénalités totales',
    'Pourcentage non payé'
]

# Sort by total amount for visualization
supplier_metrics = supplier_metrics.sort_values('Montant total', ascending=False)

# Create 2x2 dashboard with different charts
col1, col2 = st.columns(2)

with col1:
    # 1. Bar chart for order amounts by supplier
    fig_amount = px.bar(
        supplier_metrics,
        x='Nom du fournisseur',
        y='Montant total',
        title="Chiffre d'affaires par fournisseur",
        color='Montant total',
        color_continuous_scale=px.colors.sequential.Blues,
        labels={'Montant total': 'Montant total (€)', 'Nom du fournisseur': 'Fournisseur'}
    )
    st.plotly_chart(fig_amount, use_container_width=True)

with col2:
    # 2. Pie chart for proportion of total purchases by supplier
    fig_pie = px.pie(
        supplier_metrics,
        values='Montant total',
        names='Nom du fournisseur',
        title="Répartition des achats par fournisseur",
        hole=0.4
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    # 3. Bar chart for average payment delay by supplier
    fig_delay = px.bar(
        supplier_metrics.sort_values('Délai moyen de paiement', ascending=False),
        x='Nom du fournisseur',
        y='Délai moyen de paiement',
        title="Délai moyen de paiement par fournisseur",
        color='Délai moyen de paiement',
        color_continuous_scale=px.colors.sequential.Reds,
        labels={'Délai moyen de paiement': 'Jours', 'Nom du fournisseur': 'Fournisseur'}
    )
    
    # Add a horizontal line for the standard delay (e.g., 60 days)
    fig_delay.add_hline(
        y=60,
        line_dash="dash",
        line_color="red",
        annotation_text="Délai standard (60 jours)",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig_delay, use_container_width=True)

with col2:
    # 4. Scatter plot relating total amount to payment delay
    fig_scatter = px.scatter(
        supplier_metrics,
        x='Montant total',
        y='Délai moyen de paiement',
        size='Pénalités totales',
        color='Pourcentage non payé',
        hover_name='Nom du fournisseur',
        title="Relation entre montant, délai et pénalités",
        labels={
            'Montant total': 'Montant total (€)',
            'Délai moyen de paiement': 'Délai moyen (jours)',
            'Pourcentage non payé': '% non payé'
        }
    )
    
    # Add a horizontal line for the standard delay
    fig_scatter.add_hline(
        y=60,
        line_dash="dash",
        line_color="red",
        annotation_text="Délai standard",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

# Supplier KPI table
st.header("Indicateurs clés par fournisseur")

# Calculate additional metrics
supplier_counts = filtered_data.groupby('Nom du fournisseur').size().reset_index(name='Nombre de commandes')
supplier_late_payments = filtered_data[filtered_data['Statut du paiement'] == 'En retard'].groupby('Nom du fournisseur').size().reset_index(name='Commandes en retard')
supplier_unpaid = filtered_data[filtered_data['Statut de la commande'] == 'Non payée'].groupby('Nom du fournisseur')['Montant de la commande'].sum().reset_index(name='Montant non payé')

# Merge all metrics
supplier_kpis = supplier_metrics.merge(supplier_counts, on='Nom du fournisseur', how='left')
supplier_kpis = supplier_kpis.merge(supplier_late_payments, on='Nom du fournisseur', how='left')
supplier_kpis = supplier_kpis.merge(supplier_unpaid, on='Nom du fournisseur', how='left')

# Fill NaN values with 0
supplier_kpis['Commandes en retard'] = supplier_kpis['Commandes en retard'].fillna(0)
supplier_kpis['Montant non payé'] = supplier_kpis['Montant non payé'].fillna(0)

# Calculate late payment rate
supplier_kpis['Taux de retard (%)'] = (supplier_kpis['Commandes en retard'] / supplier_kpis['Nombre de commandes'] * 100).round(1)

# Select and order columns for display
display_cols = [
    'Nom du fournisseur',
    'Nombre de commandes',
    'Montant total',
    'Montant non payé',
    'Délai moyen de paiement',
    'Taux de retard (%)',
    'Pénalités totales'
]

# Sort by total amount by default
supplier_kpis_sorted = supplier_kpis[display_cols].sort_values('Montant total', ascending=False)

# Display the table
st.dataframe(supplier_kpis_sorted.style.format({
    'Montant total': '{:,.2f} €',
    'Montant non payé': '{:,.2f} €',
    'Délai moyen de paiement': '{:.1f} jours',
    'Pénalités totales': '{:,.2f} €'
}), use_container_width=True)

# Supplier risk analysis
st.header("Analyse des risques fournisseurs")

# Create a risk score based on multiple factors
supplier_kpis['Score de risque'] = (
    # High weight for late payment rate
    supplier_kpis['Taux de retard (%)'] * 0.4 +
    # Medium weight for percentage unpaid
    supplier_kpis['Pourcentage non payé'] * 0.3 +
    # Lower weight for average delay over 60 days
    (supplier_kpis['Délai moyen de paiement'].apply(lambda x: max(0, x - 60)) / 10) * 0.3
).round(1)

# Categorize suppliers based on risk score
def risk_category(score):
    if score < 15:
        return 'Faible'
    elif score < 35:
        return 'Moyen'
    else:
        return 'Élevé'

supplier_kpis['Catégorie de risque'] = supplier_kpis['Score de risque'].apply(risk_category)

# Create a visualization of risk
fig_risk = px.bar(
    supplier_kpis.sort_values('Score de risque', ascending=False),
    x='Nom du fournisseur',
    y='Score de risque',
    color='Catégorie de risque',
    title="Score de risque par fournisseur",
    color_discrete_map={
        'Faible': 'green',
        'Moyen': 'orange',
        'Élevé': 'red'
    },
    labels={'Score de risque': 'Score de risque (0-100)', 'Nom du fournisseur': 'Fournisseur'}
)

st.plotly_chart(fig_risk, use_container_width=True)

# Display top-risk suppliers
high_risk_suppliers = supplier_kpis[supplier_kpis['Catégorie de risque'] == 'Élevé']

if not high_risk_suppliers.empty:
    st.subheader("Fournisseurs à risque élevé")
    st.dataframe(
        high_risk_suppliers[['Nom du fournisseur', 'Score de risque', 'Montant total', 'Taux de retard (%)', 'Pourcentage non payé']].style.format({
            'Montant total': '{:,.2f} €',
            'Taux de retard (%)': '{:.1f}%',
            'Pourcentage non payé': '{:.1f}%'
        }),
        use_container_width=True
    )
    
    st.warning("""
    **Attention!** Les fournisseurs à risque élevé doivent faire l'objet d'une attention particulière:
    
    - Réévaluer les conditions de paiement
    - Prévoir des plans d'action pour réduire les retards
    - Initier un dialogue pour améliorer les relations commerciales
    """)
else:
    st.success("Aucun fournisseur n'est actuellement classé en risque élevé.")

# Recommendations section
st.header("Recommandations")

st.markdown("""
### Stratégies de gestion fournisseurs

#### Pour les fournisseurs stratégiques (montants élevés):
- Privilégier des accords cadres avec planification des paiements
- Mettre en place un suivi spécifique pour éviter les retards
- Négocier des conditions avantageuses en contrepartie de paiements réguliers

#### Pour réduire les retards de paiement:
- Mettre en place des alertes automatiques avant échéance
- Optimiser le processus d'approbation des factures
- Prévoir des dates fixes de paiement pour une meilleure planification

#### Pour améliorer la performance globale:
- Concentrer les achats sur moins de fournisseurs pour obtenir de meilleures conditions
- Établir des KPIs de performance par fournisseur et les suivre régulièrement
- Évaluer périodiquement la valeur ajoutée de chaque relation fournisseur
""")
