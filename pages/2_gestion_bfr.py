import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import calculate_bfr

# Page configuration
st.set_page_config(
    page_title="Gestion du BFR",
    page_icon="💰",
    layout="wide"
)

# Header
st.title("Gestion du Besoin en Fonds de Roulement (BFR)")
st.write("Analysez et suivez l'évolution de votre BFR")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# BFR calculation section
st.header("Calcul du BFR")

# Inputs for BFR calculation
col1, col2, col3 = st.columns(3)

with col1:
    stock = st.number_input("Valeur du stock", min_value=0.0, value=100000.0, step=1000.0, format="%.2f")

with col2:
    creances_clients = st.number_input("Créances clients", min_value=0.0, value=75000.0, step=1000.0, format="%.2f")

with col3:
    # Calculate total supplier debt from the data
    dettes_fournisseurs_default = data['Montant de la commande'].sum() if not data.empty else 50000.0
    dettes_fournisseurs = st.number_input(
        "Dettes fournisseurs", 
        min_value=0.0, 
        value=dettes_fournisseurs_default, 
        step=1000.0, 
        format="%.2f"
    )

# Calculate BFR
bfr = calculate_bfr(stock, creances_clients, dettes_fournisseurs)

# Display BFR result
st.subheader("Résultat du calcul")
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("BFR actuel", f"{bfr:,.2f} €")
    
    # Add interpretation
    if bfr > 0:
        st.info("BFR positif: Votre entreprise a besoin de financement pour son cycle d'exploitation.")
    elif bfr < 0:
        st.success("BFR négatif: Votre entreprise dégage un excédent de trésorerie.")
    else:
        st.warning("BFR nul: Votre entreprise est à l'équilibre.")

with col2:
    # Create a waterfall chart for BFR components
    fig = go.Figure(go.Waterfall(
        name="BFR",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Stock", "Créances clients", "Dettes fournisseurs", "BFR"],
        text=[f"+{stock:,.0f} €", f"+{creances_clients:,.0f} €", f"-{dettes_fournisseurs:,.0f} €", f"{bfr:,.0f} €"],
        textposition="outside",
        y=[stock, creances_clients, -dettes_fournisseurs, 0],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="Composition du BFR",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

# BFR evolution simulation
st.header("Simulation de l'évolution du BFR")

# Input parameters for simulation
col1, col2, col3 = st.columns(3)

with col1:
    stock_growth = st.slider("Évolution mensuelle du stock (%)", -10.0, 10.0, 1.0, 0.1)

with col2:
    creances_growth = st.slider("Évolution mensuelle des créances (%)", -10.0, 10.0, 1.5, 0.1)

with col3:
    dettes_growth = st.slider("Évolution mensuelle des dettes (%)", -10.0, 10.0, 2.0, 0.1)

# Number of months to simulate
months = st.slider("Nombre de mois à simuler", 3, 24, 12)

# Calculate BFR evolution
bfr_evolution = []
current_stock = stock
current_creances = creances_clients
current_dettes = dettes_fournisseurs

for i in range(months + 1):  # +1 to include the starting point
    current_bfr = calculate_bfr(current_stock, current_creances, current_dettes)
    
    bfr_evolution.append({
        'Mois': i,
        'Stock': current_stock,
        'Créances clients': current_creances,
        'Dettes fournisseurs': current_dettes,
        'BFR': current_bfr
    })
    
    # Update values for next month
    current_stock *= (1 + stock_growth / 100)
    current_creances *= (1 + creances_growth / 100)
    current_dettes *= (1 + dettes_growth / 100)

# Convert to DataFrame
bfr_df = pd.DataFrame(bfr_evolution)

# Create visualizations
col1, col2 = st.columns(2)

with col1:
    # BFR evolution line chart
    fig_bfr = px.line(
        bfr_df,
        x='Mois',
        y='BFR',
        title="Évolution du BFR sur la période",
        markers=True,
        labels={'BFR': 'BFR (€)', 'Mois': 'Mois'}
    )
    
    # Add a horizontal line at 0 for reference
    fig_bfr.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Équilibre",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig_bfr, use_container_width=True)

with col2:
    # Components evolution
    components_df = pd.melt(
        bfr_df, 
        id_vars=['Mois'], 
        value_vars=['Stock', 'Créances clients', 'Dettes fournisseurs'],
        var_name='Composant', 
        value_name='Valeur'
    )
    
    fig_components = px.line(
        components_df,
        x='Mois',
        y='Valeur',
        color='Composant',
        title="Évolution des composants du BFR",
        labels={'Valeur': 'Montant (€)', 'Mois': 'Mois'}
    )
    
    st.plotly_chart(fig_components, use_container_width=True)

# Display data table
st.subheader("Données détaillées de la simulation")
st.dataframe(bfr_df.round(2), use_container_width=True)

# Strategies to optimize BFR
st.header("Stratégies d'optimisation du BFR")

st.markdown("""
### Recommandations pour optimiser votre BFR:

#### Pour réduire le BFR (libérer de la trésorerie):

1. **Gestion des stocks:**
   - Optimiser les niveaux de stock
   - Mettre en place un système just-in-time
   - Négocier des délais de livraison plus courts avec les fournisseurs

2. **Gestion des créances clients:**
   - Réduire les délais de paiement accordés aux clients
   - Mettre en place des incitations pour les paiements anticipés
   - Facturer plus rapidement
   - Suivre activement les relances

3. **Gestion des dettes fournisseurs:**
   - Négocier des délais de paiement plus longs (tout en respectant la loi 69-21)
   - Centraliser les achats pour obtenir de meilleures conditions
   - Planifier les paiements de manière stratégique

#### Si le BFR est négatif:

- Vérifier que cette situation ne résulte pas d'un déséquilibre temporaire
- S'assurer que les relations avec les fournisseurs restent saines
- Évaluer si ce surplus de trésorerie peut être investi efficacement

### Impact sur la trésorerie:

Une réduction du BFR de 10% pourrait libérer environ **{bfr * 0.1:,.2f} €** de trésorerie supplémentaire pour votre entreprise.
""")

# Final note
st.info("""
**Note importante:** Les calculs et simulations présentés ici sont des estimations basées sur les données fournies et les hypothèses d'évolution. 
Ils servent à visualiser les tendances potentielles, mais doivent être complétés par une analyse financière plus approfondie.
""")
