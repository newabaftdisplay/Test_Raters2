import streamlit as st
import pandas as pd
import numpy as np  # Newly added

# =============================================================================
# FOUNDATIONAL DATA TABLES - These represent the core rating factors from your guide
# =============================================================================

# Architect base information
ARCHITECT_BASE_RATE = 0.01  # 1% as specified in your guide

# Architect discipline factors - risk multipliers for different types of work
ARCHITECT_DISCIPLINES = {
    'Architectural Work - New Build': 2.0,
    'Architectural Work - Non-Structural Refurb': 1.0,
    'Architectural Consultancy': 1.0,
    'Aborted Work': 0.5,
    'Acoustic': 1.0,
    'Building Surveying': 2.5,
    'CDM/Planning Supervision': 0.5,
    'Expert Witness': 0.5,
    'Feasibility Studies': 0.5,
    'Interior Design': 0.5,
    'Landscape Architecture': 0.5,
    'Other Surveys': 3.0,
    'Project Co-ordination': 1.5,
    'Project Management': 2.0,
    'Quantity Surveying': 0.75,
    'Town Planning': 0.5,
    'Other Work': 1.0
}

# Fee size discounts - larger firms get better rates (threshold, discount)
FEE_SIZE_DISCOUNTS = [
    (100000, 0.0),
    (200000, 0.05),
    (300000, 0.10),
    (500000, 0.15),
    (750000, 0.20),
    (1000000, 0.22),
    (float('inf'), 0.25)
]

# No Claims Discount structure
NO_CLAIMS_DISCOUNTS = {
    '0-3 years': 0.00,
    '3-5 years': 0.10,
    '5-10 years': 0.20,
    '10+ years': 0.30
}

# Retroactive Date Discount structure
RETROACTIVE_DISCOUNTS = {
    'Inception': 0.25,
    'After 12 months': 0.10,
    '2+ years coverage': 0.00
}

# Excess multiplier structure
EXCESS_MULTIPLIERS = {
    0.50: {'discount': -0.25, 'description': '50% of Standard - 25% Additional Premium'},
    0.75: {'discount': -0.10, 'description': '75% of Standard - 10% Additional Premium'}, 
    1.00: {'discount': 0.00, 'description': 'Standard Excess - No Adjustment'},
    2.00: {'discount': 0.08, 'description': 'Double Standard - 8% Discount'},
    3.00: {'discount': 0.15, 'description': 'Triple Standard - 15% Discount'},
    4.00: {'discount': 0.20, 'description': 'Quadruple Standard - 20% Discount'},
    5.00: {'discount': 0.23, 'description': 'Five Times Standard - 23% Discount'}
}

# Aggregate excess options
AGGREGATE_EXCESS_OPTIONS = {
    'standard': {'discount': 0.00, 'description': 'Standard Per-Claim Excess'},
    'agg_cap_no_thereafter': {'discount': 0.15, 'description': 'Aggregate Cap (3x Standard) - No Thereafter Excess'},
    'agg_cap_reduced_thereafter': {'discount': 0.10, 'description': 'Aggregate Cap (3x Standard) - 50% Thereafter Excess'}
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_fee_size_discount(fee_income):
    for threshold, discount in FEE_SIZE_DISCOUNTS:
        if fee_income <= threshold:
            return discount
    return 0.25

def get_limit_factor(limit_of_indemnity):
    if limit_of_indemnity < 100000:
        st.warning("Minimum limit of indemnity is £100,000. Using £100,000 for rating.")
        limit_of_indemnity = 100000
    return round(0.3433 * np.log(limit_of_indemnity) - 3.689, 4)

def calculate_standard_excess(fee_income):
    raw_excess = fee_income * 0.005
    rounded_excess = round(raw_excess / 500) * 500
    final_excess = max(rounded_excess, 500)
    return final_excess

# =============================================================================
# MAIN STREAMLIT APP ENTRY POINT (Expanded)
# =============================================================================

def main():
    st.set_page_config(page_title="Professional Indemnity Insurance Quotation System", 
                       page_icon="🏢", layout="wide")
    st.title("🏢 Professional Indemnity Insurance Quotation System")
    st.markdown("### Architect Premium Calculator")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Basic Information")
        fee_income = st.number_input("Annual Fee Income (£)", min_value=1000, max_value=10000000, value=250000, step=1000)
        limit_of_indemnity = st.number_input("Limit of Indemnity (£)", min_value=100000, max_value=10000000, value=1000000, step=50000)
        st.subheader("Risk Profile")
        no_claims_period = st.selectbox("No Claims History", list(NO_CLAIMS_DISCOUNTS.keys()))
        retroactive_coverage = st.selectbox("Retroactive Coverage", list(RETROACTIVE_DISCOUNTS.keys()), index=2)

    with col2:
        st.subheader("Discipline Breakdown")
        visible_disciplines = list(ARCHITECT_DISCIPLINES.keys())[:6]
        hidden_disciplines = list(ARCHITECT_DISCIPLINES.keys())[6:]
        discipline_percentages = {}
        total_pct = 0

        for d in visible_disciplines:
            pct = st.number_input(f"{d} (%)", min_value=0.0, max_value=100.0, step=5.0, value=0.0, key=f"vis_{d}")
            discipline_percentages[d] = pct
            total_pct += pct

        with st.expander("Additional Disciplines (click to expand)"):
            for d in hidden_disciplines:
                pct = st.number_input(f"{d} (%)", min_value=0.0, max_value=100.0, step=5.0, value=0.0, key=f"hid_{d}")
                discipline_percentages[d] = pct
                total_pct += pct

        if total_pct != 100:
            st.warning(f"Discipline total: {total_pct}%. Must total 100%.")

    with st.expander("Advanced Options"):
        excess_level = st.selectbox("Excess Level", list(EXCESS_MULTIPLIERS.keys()), index=2)
        agg_option = st.selectbox("Aggregate Excess Option", list(AGGREGATE_EXCESS_OPTIONS.keys()))
        uw_factor = st.number_input("Underwriter Discretion Factor", value=1.0, step=0.05, min_value=0.1, max_value=10.0)

    if st.button("Calculate Premium") and total_pct == 100:
        result = calculate_architect_premium(
            fee_income=fee_income,
            discipline_percentages=discipline_percentages,
            limit_of_indemnity=limit_of_indemnity,
            no_claims_period=no_claims_period,
            retroactive_coverage=retroactive_coverage,
            excess_multiplier=excess_level,
            aggregate_excess_option=agg_option,
            underwriter_discretion_factor=uw_factor
        )
        st.success("Premium Calculation Complete")
        st.metric("Final Premium", f"£{result['final_premium']:,.2f}")
        st.metric("Excess Amount", f"£{result['actual_excess']:,.0f}")
        st.metric("Limit of Indemnity", f"£{result['limit_of_indemnity']:,.0f}")

        with st.expander("🔍 Calculation Breakdown"):
            breakdown = pd.DataFrame({
                "Step": [
                    "Base Premium (1% of Fee Income)",
                    "Discipline Factor",
                    "Fee Size Discount",
                    "Limit Factor",
                    "No Claims Discount",
                    "Retroactive Discount",
                    "Excess Discount",
                    "Aggregate Excess Discount",
                    "Underwriter Discretion"
                ],
                "Value": [
                    f"£{result['base_premium']:,.2f}",
                    f"×{result['discipline_factor']:.3f}",
                    f"-{result['fee_size_discount']:.0%}",
                    f"×{result['limit_factor']:.3f}",
                    f"-{result['no_claims_discount']:.0%}",
                    f"-{result['retroactive_discount']:.0%}",
                    f"-{result['excess_discount']:.0%}",
                    f"-{result['aggregate_excess_discount']:.0%}",
                    f"×{result['underwriter_discretion_factor']:.2f}"
                ]
            })
            st.dataframe(breakdown, hide_index=True)

# Dummy function to avoid error — replace with real logic

def calculate_architect_premium(fee_income, discipline_percentages, limit_of_indemnity, no_claims_period, retroactive_coverage, excess_multiplier, aggregate_excess_option, underwriter_discretion_factor):
    base_premium = fee_income * ARCHITECT_BASE_RATE
    discipline_factor = sum(ARCHITECT_DISCIPLINES[d] * (v / 100) for d, v in discipline_percentages.items())
    premium_after_disciplines = base_premium * discipline_factor
    fee_size_discount = get_fee_size_discount(fee_income)
    premium_after_fee_discount = premium_after_disciplines * (1 - fee_size_discount)
    limit_factor = get_limit_factor(limit_of_indemnity)
    premium_after_limit = premium_after_fee_discount * limit_factor
    no_claims_discount = NO_CLAIMS_DISCOUNTS[no_claims_period]
    premium_after_no_claims = premium_after_limit * (1 - no_claims_discount)
    retro_discount = RETROACTIVE_DISCOUNTS[retroactive_coverage]
    premium_after_retro = premium_after_no_claims * (1 - retro_discount)
    excess_discount = EXCESS_MULTIPLIERS[excess_multiplier]['discount']
    premium_after_excess = premium_after_retro * (1 - excess_discount)
    agg_discount = AGGREGATE_EXCESS_OPTIONS[aggregate_excess_option]['discount']
    premium_after_agg = premium_after_excess * (1 - agg_discount)
    final_premium = premium_after_agg * underwriter_discretion_factor
    standard_excess = calculate_standard_excess(fee_income)
    actual_excess = standard_excess * excess_multiplier
    return {
        'final_premium': final_premium,
        'actual_excess': actual_excess,
        'limit_of_indemnity': limit_of_indemnity,
        'base_premium': base_premium,
        'discipline_factor': discipline_factor,
        'fee_size_discount': fee_size_discount,
        'limit_factor': limit_factor,
        'no_claims_discount': no_claims_discount,
        'retroactive_discount': retro_discount,
        'excess_discount': excess_discount,
        'aggregate_excess_discount': agg_discount,
        'underwriter_discretion_factor': underwriter_discretion_factor
    }

if __name__ == "__main__":
    main()
