import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import (
    calculate_dpo, calculate_bfr, calculate_cash_ratio,
    calculate_current_ratio, create_gauge_chart
)

# Page configuration
st.set_page_config(
    page_title="Ratios Financiers",
    page_icon="📈",
    layout="wide"
)

# Header
st.title("Ratios Financiers")
st.write("Analysez les indicateurs financiers liés aux paiements fournisseurs")

# Check if data exists in session state
if 'processed_data' not in st.session_state or st.session_state['processed_data'].empty:
    st.warning("Aucune donnée n'est chargée. Veuillez retourner à la page principale pour charger des données.")
    st.stop()

# Get data from session state
data = st.session_state['processed_data']

# Inputs for financial ratio calculations
st.header("Données financières pour le calcul des ratios")

col1, col2 = st.columns(2)

with col1:
    total_achats = st.number_input(
        "Total des achats fournisseurs TTC",
        min_value=0.0,
        value=float(data['Montant de la commande'].sum()),
        step=10000.0,
        format="%.2f",
        help="Montant total des achats sur la période"
    )
    
    total_dettes = st.number_input(
        "Total des dettes fournisseurs",
        min_value=0.0,
        value=float(data[data['Date de paiement'].isna()]['Montant de la commande'].sum()),
        step=10000.0,
        format="%.2f",
        help="Montant total des factures non réglées"
    )

with col2:
    stock = st.number_input(
        "Valeur du stock",
        min_value=0.0,
        value=100000.0,
        step=10000.0,
        format="%.2f"
    )
    
    creances_clients = st.number_input(
        "Créances clients",
        min_value=0.0,
        value=75000.0,
        step=10000.0,
        format="%.2f"
    )

# Additional inputs for other ratios
col1, col2 = st.columns(2)

with col1:
    tresorerie = st.number_input(
        "Solde de trésorerie",
        min_value=0.0,
        value=50000.0,
        step=10000.0,
        format="%.2f"
    )

with col2:
    actifs_court_terme = st.number_input(
        "Actifs à court terme",
        min_value=0.0,
        value=stock + creances_clients + tresorerie,  # Pre-calculate based on previous inputs
        step=10000.0,
        format="%.2f",
        help="Total des actifs réalisables à court terme (stock + créances + trésorerie)"
    )
    
    passifs_court_terme = st.number_input(
        "Passifs à court terme",
        min_value=0.0,
        value=total_dettes * 1.5,  # Estimate other current liabilities
        step=10000.0,
        format="%.2f",
        help="Total des dettes à court terme (fournisseurs + autres dettes)"
    )

# Calculate ratios
st.header("Ratios financiers calculés")

# Days Payable Outstanding (DPO)
dpo = calculate_dpo(total_dettes, total_achats)

# Besoin en Fonds de Roulement (BFR)
bfr = calculate_bfr(stock, creances_clients, total_dettes)

# Cash Ratio
cash_ratio = calculate_cash_ratio(tresorerie, total_dettes)

# Current Ratio
current_ratio = calculate_current_ratio(actifs_court_terme, passifs_court_terme)

# Display ratios in a 2x2 grid with gauge charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("DPO (Days Payable Outstanding)")
    st.write("Nombre de jours moyen pour payer les fournisseurs")
    
    dpo_fig = create_gauge_chart(
        value=dpo,
        min_val=0,
        max_val=120,
        threshold_bad=30,  # Too quick payment
        threshold_good=60,  # Good payment time
        title="DPO (jours)"
    )
    st.plotly_chart(dpo_fig, use_container_width=True)
    
    st.markdown(f"""
    **Valeur calculée: {dpo:.1f} jours**
    
    **Interprétation:**
    - < 30 jours: Paiements trop rapides, impact négatif sur la trésorerie
    - 30-60 jours: Zone optimale pour la plupart des entreprises
    - > 60 jours: Délais longs, attention à respecter la loi 69-21
    """)

with col2:
    st.subheader("BFR (Besoin en Fonds de Roulement)")
    st.write("Capital nécessaire pour financer le cycle d'exploitation")
    
    # For BFR, positive is generally considered less favorable
    bfr_fig = create_gauge_chart(
        value=bfr,
        min_val=-100000,
        max_val=300000,
        threshold_bad=200000,  # High BFR is challenging
        threshold_good=50000,  # Low BFR is good
        title="BFR (€)"
    )
    st.plotly_chart(bfr_fig, use_container_width=True)
    
    st.markdown(f"""
    **Valeur calculée: {bfr:,.2f} €**
    
    **Interprétation:**
    - BFR positif: Besoin de financement pour le cycle d'exploitation
    - BFR négatif: Excédent de trésorerie généré par le cycle d'exploitation
    - Plus le BFR est bas, meilleure est la situation de trésorerie
    """)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cash Ratio")
    st.write("Capacité à rembourser les dettes à court terme avec la trésorerie disponible")
    
    cash_ratio_fig = create_gauge_chart(
        value=cash_ratio,
        min_val=0,
        max_val=2,
        threshold_bad=0.2,  # Low liquidity
        threshold_good=0.5,  # Good liquidity
        title="Cash Ratio"
    )
    st.plotly_chart(cash_ratio_fig, use_container_width=True)
    
    st.markdown(f"""
    **Valeur calculée: {cash_ratio:.2f}**
    
    **Interprétation:**
    - < 0.2: Liquidité insuffisante, risque de problèmes de paiement
    - 0.2-0.5: Liquidité acceptable
    - > 0.5: Bonne liquidité, capacité à faire face aux obligations immédiates
    """)

with col2:
    st.subheader("Current Ratio")
    st.write("Capacité à rembourser les dettes à court terme avec l'ensemble des actifs à court terme")
    
    current_ratio_fig = create_gauge_chart(
        value=current_ratio,
        min_val=0,
        max_val=3,
        threshold_bad=1,  # Below 1 is risky
        threshold_good=1.5,  # Above 1.5 is good
        title="Current Ratio"
    )
    st.plotly_chart(current_ratio_fig, use_container_width=True)
    
    st.markdown(f"""
    **Valeur calculée: {current_ratio:.2f}**
    
    **Interprétation:**
    - < 1: Risque d'incapacité à honorer les dettes à court terme
    - 1-1.5: Situation acceptable mais à surveiller
    - > 1.5: Bonne capacité à honorer les engagements à court terme
    """)

# Historical trends
st.header("Évolution historique des ratios")

st.write("""
Pour visualiser l'évolution de ces ratios dans le temps, vous pouvez saisir des valeurs historiques ou prévisionnelles.
""")

# Create a table for historical data
if "historical_ratios" not in st.session_state:
    # Initialize with current values and some previous periods
    today = datetime.now()
    st.session_state["historical_ratios"] = pd.DataFrame([
        {"Date": (today - timedelta(days=90)).strftime("%Y-%m-%d"), "DPO": dpo * 0.9, "BFR": bfr * 1.1, "Cash Ratio": cash_ratio * 0.9, "Current Ratio": current_ratio * 0.9},
        {"Date": (today - timedelta(days=60)).strftime("%Y-%m-%d"), "DPO": dpo * 0.95, "BFR": bfr * 1.05, "Cash Ratio": cash_ratio * 0.95, "Current Ratio": current_ratio * 0.95},
        {"Date": (today - timedelta(days=30)).strftime("%Y-%m-%d"), "DPO": dpo * 0.98, "BFR": bfr * 1.02, "Cash Ratio": cash_ratio * 0.98, "Current Ratio": current_ratio * 0.98},
        {"Date": today.strftime("%Y-%m-%d"), "DPO": dpo, "BFR": bfr, "Cash Ratio": cash_ratio, "Current Ratio": current_ratio}
    ])

# Display the historical data table with editable cells
with st.expander("Données historiques des ratios"):
    edited_df = st.data_editor(
        st.session_state["historical_ratios"],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "DPO": st.column_config.NumberColumn("DPO (jours)", format="%.1f"),
            "BFR": st.column_config.NumberColumn("BFR (€)", format="%.2f"),
            "Cash Ratio": st.column_config.NumberColumn("Cash Ratio", format="%.2f"),
            "Current Ratio": st.column_config.NumberColumn("Current Ratio", format="%.2f")
        }
    )
    
    # Update the session state with the edited data
    st.session_state["historical_ratios"] = edited_df

# Sort by date for proper time series
historical_data = st.session_state["historical_ratios"].sort_values("Date")

# Create time series charts for each ratio
col1, col2 = st.columns(2)

with col1:
    # DPO time series
    fig_dpo = px.line(
        historical_data,
        x="Date",
        y="DPO",
        title="Évolution du DPO",
        markers=True,
        labels={"DPO": "DPO (jours)", "Date": "Date"}
    )
    
    # Add reference lines
    fig_dpo.add_hline(
        y=30,
        line_dash="dash",
        line_color="orange",
        annotation_text="Minimum recommandé",
        annotation_position="bottom right"
    )
    
    fig_dpo.add_hline(
        y=60,
        line_dash="dash",
        line_color="red",
        annotation_text="Maximum légal",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig_dpo, use_container_width=True)

with col2:
    # BFR time series
    fig_bfr = px.line(
        historical_data,
        x="Date",
        y="BFR",
        title="Évolution du BFR",
        markers=True,
        labels={"BFR": "BFR (€)", "Date": "Date"}
    )
    
    # Add a reference line at 0
    fig_bfr.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Équilibre",
        annotation_position="bottom right"
    )
    
    st.plotly_chart(fig_bfr, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    # Cash Ratio time series
    fig_cash = px.line(
        historical_data,
        x="Date",
        y="Cash Ratio",
        title="Évolution du Cash Ratio",
        markers=True,
        labels={"Cash Ratio": "Ratio", "Date": "Date"}
    )
    
    # Add reference lines
    fig_cash.add_hline(
        y=0.2,
        line_dash="dash",
        line_color="orange",
        annotation_text="Minimum critique",
        annotation_position="bottom right"
    )
    
    fig_cash.add_hline(
        y=0.5,
        line_dash="dash",
        line_color="green",
        annotation_text="Niveau optimal",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig_cash, use_container_width=True)

with col2:
    # Current Ratio time series
    fig_current = px.line(
        historical_data,
        x="Date",
        y="Current Ratio",
        title="Évolution du Current Ratio",
        markers=True,
        labels={"Current Ratio": "Ratio", "Date": "Date"}
    )
    
    # Add reference lines
    fig_current.add_hline(
        y=1,
        line_dash="dash",
        line_color="red",
        annotation_text="Minimum critique",
        annotation_position="bottom right"
    )
    
    fig_current.add_hline(
        y=1.5,
        line_dash="dash",
        line_color="green",
        annotation_text="Niveau optimal",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig_current, use_container_width=True)

# Benchmark comparison
st.header("Comparaison avec les benchmarks sectoriels")

st.write("""
Comparez vos ratios financiers avec les références de votre secteur pour évaluer votre performance relative.
""")

# Let the user select their industry
industries = [
    "Commerce de détail",
    "Commerce de gros",
    "Industrie manufacturière",
    "Services aux entreprises",
    "Construction",
    "Transport et logistique",
    "Technologies de l'information",
    "Santé",
    "Hôtellerie et restauration"
]

selected_industry = st.selectbox("Sélectionnez votre secteur d'activité", industries)

# Benchmark data (example values - in a real app, this would come from a database)
benchmarks = {
    "Commerce de détail": {"DPO": 45, "BFR": 120000, "Cash Ratio": 0.3, "Current Ratio": 1.2},
    "Commerce de gros": {"DPO": 52, "BFR": 200000, "Cash Ratio": 0.25, "Current Ratio": 1.3},
    "Industrie manufacturière": {"DPO": 58, "BFR": 250000, "Cash Ratio": 0.2, "Current Ratio": 1.4},
    "Services aux entreprises": {"DPO": 42, "BFR": 80000, "Cash Ratio": 0.4, "Current Ratio": 1.6},
    "Construction": {"DPO": 55, "BFR": 180000, "Cash Ratio": 0.3, "Current Ratio": 1.3},
    "Transport et logistique": {"DPO": 48, "BFR": 150000, "Cash Ratio": 0.3, "Current Ratio": 1.4},
    "Technologies de l'information": {"DPO": 40, "BFR": 100000, "Cash Ratio": 0.5, "Current Ratio": 1.8},
    "Santé": {"DPO": 50, "BFR": 120000, "Cash Ratio": 0.35, "Current Ratio": 1.5},
    "Hôtellerie et restauration": {"DPO": 35, "BFR": 60000, "Cash Ratio": 0.25, "Current Ratio": 1.1}
}

# Get benchmarks for selected industry
industry_benchmarks = benchmarks[selected_industry]

# Create comparison charts
col1, col2 = st.columns(2)

with col1:
    # DPO comparison
    fig_dpo_comp = go.Figure()
    
    fig_dpo_comp.add_trace(go.Bar(
        x=["Votre entreprise", "Benchmark sectoriel"],
        y=[dpo, industry_benchmarks["DPO"]],
        marker_color=["#1E88E5", "#FFC107"]
    ))
    
    fig_dpo_comp.update_layout(
        title="DPO: Comparaison avec le benchmark",
        yaxis_title="Jours",
        xaxis_title="",
        showlegend=False
    )
    
    st.plotly_chart(fig_dpo_comp, use_container_width=True)
    
    # Interpretation
    if dpo < industry_benchmarks["DPO"] * 0.8:
        st.warning("Votre DPO est significativement inférieur à la moyenne du secteur. Vous payez peut-être trop rapidement vos fournisseurs.")
    elif dpo > industry_benchmarks["DPO"] * 1.2:
        st.warning("Votre DPO est significativement supérieur à la moyenne du secteur. Attention aux risques de non-conformité avec la loi 69-21.")
    else:
        st.success("Votre DPO est aligné avec les pratiques du secteur.")

with col2:
    # Cash Ratio comparison
    fig_cash_comp = go.Figure()
    
    fig_cash_comp.add_trace(go.Bar(
        x=["Votre entreprise", "Benchmark sectoriel"],
        y=[cash_ratio, industry_benchmarks["Cash Ratio"]],
        marker_color=["#1E88E5", "#FFC107"]
    ))
    
    fig_cash_comp.update_layout(
        title="Cash Ratio: Comparaison avec le benchmark",
        yaxis_title="Ratio",
        xaxis_title="",
        showlegend=False
    )
    
    st.plotly_chart(fig_cash_comp, use_container_width=True)
    
    # Interpretation
    if cash_ratio < industry_benchmarks["Cash Ratio"] * 0.8:
        st.warning("Votre Cash Ratio est inférieur à la moyenne du secteur. Votre liquidité immédiate pourrait être insuffisante.")
    elif cash_ratio > industry_benchmarks["Cash Ratio"] * 1.5:
        st.info("Votre Cash Ratio est supérieur à la moyenne du secteur. Vous disposez d'une bonne liquidité, mais des ressources pourraient être sous-utilisées.")
    else:
        st.success("Votre Cash Ratio est aligné avec les pratiques du secteur.")

col1, col2 = st.columns(2)

with col1:
    # Current Ratio comparison
    fig_current_comp = go.Figure()
    
    fig_current_comp.add_trace(go.Bar(
        x=["Votre entreprise", "Benchmark sectoriel"],
        y=[current_ratio, industry_benchmarks["Current Ratio"]],
        marker_color=["#1E88E5", "#FFC107"]
    ))
    
    fig_current_comp.update_layout(
        title="Current Ratio: Comparaison avec le benchmark",
        yaxis_title="Ratio",
        xaxis_title="",
        showlegend=False
    )
    
    st.plotly_chart(fig_current_comp, use_container_width=True)
    
    # Interpretation
    if current_ratio < industry_benchmarks["Current Ratio"] * 0.8:
        st.warning("Votre Current Ratio est inférieur à la moyenne du secteur. Votre solvabilité à court terme pourrait être à risque.")
    elif current_ratio > industry_benchmarks["Current Ratio"] * 1.5:
        st.info("Votre Current Ratio est supérieur à la moyenne du secteur. Vous disposez d'une bonne solvabilité à court terme.")
    else:
        st.success("Votre Current Ratio est aligné avec les pratiques du secteur.")

with col2:
    # BFR comparison normalized to company size
    # For simplicity, we'll normalize by dividing by total_achats
    normalized_bfr = bfr / total_achats if total_achats > 0 else 0
    normalized_benchmark_bfr = industry_benchmarks["BFR"] / (total_achats * 0.8)  # Assume benchmark is based on 80% of your activity
    
    fig_bfr_comp = go.Figure()
    
    fig_bfr_comp.add_trace(go.Bar(
        x=["Votre entreprise", "Benchmark sectoriel"],
        y=[normalized_bfr, normalized_benchmark_bfr],
        marker_color=["#1E88E5", "#FFC107"]
    ))
    
    fig_bfr_comp.update_layout(
        title="BFR/CA: Comparaison avec le benchmark",
        yaxis_title="Ratio BFR/Achats",
        xaxis_title="",
        showlegend=False
    )
    
    st.plotly_chart(fig_bfr_comp, use_container_width=True)
    
    # Interpretation
    if normalized_bfr > normalized_benchmark_bfr * 1.2:
        st.warning("Votre BFR est proportionnellement plus élevé que la moyenne du secteur. Vous pourriez optimiser votre cycle d'exploitation.")
    elif normalized_bfr < normalized_benchmark_bfr * 0.8:
        st.success("Votre BFR est proportionnellement plus bas que la moyenne du secteur, ce qui est positif pour votre trésorerie.")
    else:
        st.info("Votre BFR est proportionnellement aligné avec les pratiques du secteur.")

# Recommendations
st.header("Analyse et recommandations")

# Generate recommendations based on the ratios
recommendations = []

# DPO recommendations
if dpo < 30:
    recommendations.append("🔴 **DPO trop bas**: Négociez des délais de paiement plus longs avec vos fournisseurs pour améliorer votre trésorerie.")
elif dpo > 60:
    recommendations.append("🔴 **DPO élevé**: Attention aux risques de non-conformité avec la loi 69-21. Planifiez vos paiements pour respecter les délais légaux.")
else:
    recommendations.append("🟢 **DPO optimal**: Maintenez cette performance tout en respectant les délais légaux.")

# BFR recommendations
if bfr > 200000:
    recommendations.append("🔴 **BFR élevé**: Réduisez votre BFR en optimisant vos stocks, en accélérant le recouvrement client et en négociant de meilleures conditions avec vos fournisseurs.")
elif bfr < 0:
    recommendations.append("🟡 **BFR négatif**: Bien que cela soit favorable pour votre trésorerie, vérifiez que cette situation est durable et n'affecte pas vos relations fournisseurs.")
else:
    recommendations.append("🟢 **BFR maîtrisé**: Continuez à surveiller l'évolution de votre BFR pour maintenir cette performance.")

# Cash Ratio recommendations
if cash_ratio < 0.2:
    recommendations.append("🔴 **Cash Ratio faible**: Augmentez vos liquidités immédiatement disponibles pour faire face à vos obligations à court terme.")
elif cash_ratio > 1:
    recommendations.append("🟡 **Cash Ratio très élevé**: Vous disposez d'une trésorerie importante qui pourrait être mieux utilisée pour générer des rendements.")
else:
    recommendations.append("🟢 **Cash Ratio satisfaisant**: Votre niveau de liquidité vous permet de faire face à vos obligations à court terme.")

# Current Ratio recommendations
if current_ratio < 1:
    recommendations.append("🔴 **Current Ratio critique**: Votre capacité à honorer vos dettes à court terme est à risque. Prenez des mesures pour augmenter vos liquidités.")
elif current_ratio > 2:
    recommendations.append("🟡 **Current Ratio très élevé**: Vos actifs à court terme pourraient être utilisés de manière plus productive.")
else:
    recommendations.append("🟢 **Current Ratio satisfaisant**: Votre solvabilité à court terme est bonne.")

# Display recommendations
for rec in recommendations:
    st.markdown(rec)

# Final summary and action plan
st.subheader("Plan d'action recommandé")

st.markdown("""
### Actions prioritaires:

1. **Optimisation du DPO**:
   - Établir un calendrier de paiement aligné sur les délais légaux
   - Négocier des conditions de paiement favorables avec les fournisseurs stratégiques

2. **Réduction du BFR**:
   - Optimiser la gestion des stocks
   - Améliorer le processus de recouvrement des créances clients
   - Renégocier les délais fournisseurs dans le cadre légal

3. **Suivi et reporting**:
   - Mettre en place un tableau de bord mensuel pour suivre l'évolution des ratios
   - Comparer régulièrement vos performances avec les benchmarks sectoriels
   - Anticiper les besoins de trésorerie en fonction des tendances observées
""")

# Related resources
with st.expander("Ressources additionnelles"):
    st.markdown("""
    ### Pour approfondir:
    
    - **Loi 69-21**: Consultez les dispositions légales sur les délais de paiement
    - **Optimisation de la trésorerie**: Guides pratiques pour améliorer votre gestion de trésorerie
    - **Analyse financière**: Méthodes avancées pour interpréter vos ratios financiers
    
    ### Outils complémentaires:
    
    - Budget de trésorerie prévisionnel
    - Analyse de crédit fournisseur
    - Simulation d'impact des délais de paiement sur la performance financière
    """)
