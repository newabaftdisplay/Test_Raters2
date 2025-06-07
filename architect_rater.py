import streamlit as st
import pandas as pd

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
    (100000, 0.0),      # £0-£100k gets 0% discount
    (200000, 0.05),     # £100k-£200k gets 5% discount
    (300000, 0.10),     # £200k-£300k gets 10% discount
    (500000, 0.15),     # £300k-£500k gets 15% discount
    (750000, 0.20),     # £500k-£750k gets 20% discount
    (1000000, 0.22),    # £750k-£1M gets 22% discount
    (float('inf'), 0.25) # Above £1M gets 25% discount
]

# Limit of Indemnity factors - applies to ALL professions
# These percentages are based on £1,000,000 being the baseline (100%)
LIMIT_OF_INDEMNITY_FACTORS = {
    100000: 0.40,    # £100k = 40% of base premium
    250000: 0.50,    # £250k = 50% of base premium  
    500000: 0.76,    # £500k = 76% of base premium
    750000: 0.90,    # £750k = 90% of base premium
    1000000: 1.00,   # £1M = 100% of base premium (our baseline)
    2000000: 1.30,   # £2M = 130% of base premium
    3000000: 1.45,   # £3M = 145% of base premium
    4000000: 1.57,   # £4M = 157% of base premium
    5000000: 1.65    # £5M = 165% of base premium
}

# No Claims Discount structure - rewards demonstrated risk management
NO_CLAIMS_DISCOUNTS = {
    '0-3 years': 0.00,      # No discount for newer track records
    '3-5 years': 0.10,      # 10% discount for established practices  
    '5-10 years': 0.20,     # 20% discount for strong track records
    '10+ years': 0.30       # 30% discount for exceptional longevity
}

# Retroactive Date Discount structure - reflects historical exposure limits
RETROACTIVE_DISCOUNTS = {
    'Inception': 0.25,      # 25% discount for no historical coverage
    'After 12 months': 0.10, # 10% discount for limited historical coverage
    '2+ years coverage': 0.00 # No discount for full historical coverage
}

# Excess multiplier structure - balances risk retention with premium cost
EXCESS_MULTIPLIERS = {
    0.50: {'discount': -0.25, 'description': '50% of Standard - 25% Additional Premium'},
    0.75: {'discount': -0.10, 'description': '75% of Standard - 10% Additional Premium'}, 
    1.00: {'discount': 0.00, 'description': 'Standard Excess - No Adjustment'},
    2.00: {'discount': 0.08, 'description': 'Double Standard - 8% Discount'},
    3.00: {'discount': 0.15, 'description': 'Triple Standard - 15% Discount'},
    4.00: {'discount': 0.20, 'description': 'Quadruple Standard - 20% Discount'},
    5.00: {'discount': 0.23, 'description': 'Five Times Standard - 23% Discount'}
}

# Special aggregate excess options for sophisticated risk management
AGGREGATE_EXCESS_OPTIONS = {
    'standard': {'discount': 0.00, 'description': 'Standard Per-Claim Excess'},
    'agg_cap_no_thereafter': {'discount': 0.15, 'description': 'Aggregate Cap (3x Standard) - No Thereafter Excess'},
    'agg_cap_reduced_thereafter': {'discount': 0.10, 'description': 'Aggregate Cap (3x Standard) - 50% Thereafter Excess'}
}

# =============================================================================
# HELPER FUNCTIONS - These handle specific calculation components
# =============================================================================

def get_fee_size_discount(fee_income):
    """
    Determines the appropriate discount percentage based on firm's fee income.
    Larger firms receive better rates reflecting their generally more stable risk profiles.
    """
    for threshold, discount in FEE_SIZE_DISCOUNTS:
        if fee_income <= threshold:
            return discount
    return 0.25  # Maximum discount for very large firms

def get_limit_factor(limit_of_indemnity):
    """
    Returns the pricing factor for any given limit of indemnity.
    All calculations are based on £1M being the baseline (factor = 1.00).
    """
    if limit_of_indemnity in LIMIT_OF_INDEMNITY_FACTORS:
        return LIMIT_OF_INDEMNITY_FACTORS[limit_of_indemnity]
    else:
        # If someone requests a limit not in our table, default to £1M factor
        st.warning(f"Warning: £{limit_of_indemnity:,} is not a standard limit. Using £1M factor.")
        return 1.00

def calculate_standard_excess(fee_income):
    """
    Calculate the standard excess as 0.5% of fee income, rounded to nearest £500.
    
    This creates appropriate financial incentive for risk management while
    scaling proportionally with the firm's ability to absorb small losses.
    """
    # Calculate 0.5% of fee income
    raw_excess = fee_income * 0.005
    
    # Round to nearest £500 for practical administration
    rounded_excess = round(raw_excess / 500) * 500
    
    # Ensure minimum excess of £500 for very small practices
    final_excess = max(rounded_excess, 500)
    
    return final_excess

# =============================================================================
# MAIN CALCULATION ENGINE - This applies all business rules systematically
# =============================================================================

def calculate_architect_premium(fee_income, discipline_percentages, 
                               limit_of_indemnity=1000000,
                               no_claims_period='0-3 years',
                               retroactive_coverage='2+ years coverage',
                               excess_multiplier=1.0,
                               aggregate_excess_option='standard',
                               underwriter_discretion_factor=1.0):
    """
    Comprehensive premium calculation that applies all discount mechanisms
    following your guide's methodology exactly.
    
    Each step builds logically on the previous one, creating a transparent
    audit trail of exactly how each premium was determined.
    """
    
    # Step 1: Calculate base premium at £1M limit (our universal baseline)
    base_premium = fee_income * ARCHITECT_BASE_RATE
    
    # Step 2: Apply discipline factors (weighted average across all activities)
    total_discipline_factor = 0
    for discipline, percentage in discipline_percentages.items():
        if percentage > 0:
            factor = ARCHITECT_DISCIPLINES[discipline]
            total_discipline_factor += factor * (percentage / 100)
    
    premium_after_disciplines = base_premium * total_discipline_factor
    
    # Step 3: Apply fee size discount (rewards larger, more stable practices)
    fee_discount = get_fee_size_discount(fee_income)
    premium_after_fee_discount = premium_after_disciplines * (1 - fee_discount)
    
    # Step 4: Apply limit of indemnity factor
    limit_factor = get_limit_factor(limit_of_indemnity)
    premium_after_limit = premium_after_fee_discount * limit_factor
    
    # Step 5: Apply no claims discount (compound basis)
    no_claims_discount = NO_CLAIMS_DISCOUNTS[no_claims_period]
    premium_after_no_claims = premium_after_limit * (1 - no_claims_discount)
    
    # Step 6: Apply retroactive coverage discount (compound basis)  
    retro_discount = RETROACTIVE_DISCOUNTS[retroactive_coverage]
    premium_after_retro = premium_after_no_claims * (1 - retro_discount)
    
    # Step 7: Apply excess-related discount (compound basis)
    excess_discount = EXCESS_MULTIPLIERS[excess_multiplier]['discount']
    premium_after_excess = premium_after_retro * (1 - excess_discount)
    
    # Step 8: Apply aggregate excess option discount (compound basis)
    agg_excess_discount = AGGREGATE_EXCESS_OPTIONS[aggregate_excess_option]['discount']
    premium_after_agg_excess = premium_after_excess * (1 - agg_excess_discount)
    
    # Step 9: Apply underwriter discretion factor (can be above or below 1.0)
    final_premium = premium_after_agg_excess * underwriter_discretion_factor
    
    # Calculate the actual excess amount for quotation purposes
    standard_excess = calculate_standard_excess(fee_income)
    actual_excess = standard_excess * excess_multiplier
    
    # Return comprehensive breakdown for transparency and audit purposes
    return {
        'fee_income': fee_income,
        'base_premium': base_premium,
        'discipline_factor': total_discipline_factor,
        'premium_after_disciplines': premium_after_disciplines,
        'fee_size_discount': fee_discount,
        'premium_after_fee_discount': premium_after_fee_discount,
        'limit_factor': limit_factor,
        'premium_after_limit': premium_after_limit,
        'no_claims_discount': no_claims_discount,
        'premium_after_no_claims': premium_after_no_claims,
        'retroactive_discount': retro_discount,
        'premium_after_retro': premium_after_retro,
        'excess_discount': excess_discount,
        'premium_after_excess': premium_after_excess,
        'aggregate_excess_discount': agg_excess_discount,
        'premium_after_agg_excess': premium_after_agg_excess,
        'underwriter_discretion_factor': underwriter_discretion_factor,
        'final_premium': final_premium,
        'standard_excess': standard_excess,
        'actual_excess': actual_excess,
        'limit_of_indemnity': limit_of_indemnity
    }

# =============================================================================
# USER INTERFACE - This creates the web application that makes the system accessible
# =============================================================================

def main():
    """
    Creates the Streamlit web interface for the insurance rating system.
    This transforms our calculation engine into an intuitive tool that
    anyone can use without understanding the underlying code.
    """
    
    # Configure the page layout and title
    st.set_page_config(page_title="Professional Indemnity Insurance Quotation System", 
                       page_icon="🏢", layout="wide")
    
    st.title("🏢 Professional Indemnity Insurance Quotation System")
    st.markdown("### Architect Premium Calculator")
    st.markdown("---")
    
    # Create two columns for better layout organization
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Basic Information")
        
        # Fee income input with helpful formatting
        fee_income = st.number_input(
            "Annual Fee Income (£)", 
            min_value=1000, 
            max_value=10000000, 
            value=250000,
            step=1000,
            help="Enter the firm's gross annual fee income"
        )
        
        # Limit of indemnity selection
        limit_options = list(LIMIT_OF_INDEMNITY_FACTORS.keys())
        limit_labels = [f"£{limit:,}" for limit in limit_options]
        
        selected_limit_index = st.selectbox(
            "Limit of Indemnity",
            range(len(limit_options)),
            index=4,  # Default to £1M
            format_func=lambda x: limit_labels[x],
            help="Maximum amount the insurance will pay for any one claim"
        )
        limit_of_indemnity = limit_options[selected_limit_index]
        
        st.subheader("Risk Profile")
        
        # No claims history
        no_claims_period = st.selectbox(
            "No Claims History",
            list(NO_CLAIMS_DISCOUNTS.keys()),
            help="Continuous period without professional indemnity claims"
        )
        
        # Retroactive coverage
        retroactive_coverage = st.selectbox(
            "Retroactive Coverage",
            list(RETROACTIVE_DISCOUNTS.keys()),
            index=2,  # Default to full coverage
            help="How far back in time the policy covers previous work"
        )
    
    with col2:
        st.subheader("Discipline Breakdown")
        st.write("Enter the percentage of fee income from each discipline:")
        
        # Create input fields for each discipline
        discipline_percentages = {}
        total_percentage = 0
        
        # Group disciplines for better organization
        main_disciplines = ['Architectural Work - New Build', 'Architectural Work - Non-Structural Refurb', 
                          'Architectural Consultancy', 'Building Surveying', 'Project Management']
        
        st.write("**Main Disciplines:**")
        for discipline in main_disciplines:
            if discipline in ARCHITECT_DISCIPLINES:
                percentage = st.number_input(
                    f"{discipline} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=5.0,
                    key=discipline
                )
                discipline_percentages[discipline] = percentage
                total_percentage += percentage
        
        # Show remaining disciplines in an expander
        with st.expander("Additional Disciplines"):
            for discipline in ARCHITECT_DISCIPLINES:
                if discipline not in main_disciplines:
                    percentage = st.number_input(
                        f"{discipline} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=5.0,
                        key=discipline
                    )
                    discipline_percentages[discipline] = percentage
                    total_percentage += percentage
        
        # Validate total percentage
        if total_percentage != 100.0:
            st.warning(f"Total percentage is {total_percentage}%. Should equal 100%.")
    
    # Advanced options in an expander
    with st.expander("Advanced Options"):
        col3, col4 = st.columns(2)
        
        with col3:
            # Excess options
            excess_options = list(EXCESS_MULTIPLIERS.keys())
            excess_labels = [f"{mult}x Standard - {EXCESS_MULTIPLIERS[mult]['description'].split(' - ')[1]}" 
                           for mult in excess_options]
            
            selected_excess_index = st.selectbox(
                "Excess Level",
                range(len(excess_options)),
                index=2,  # Default to standard
                format_func=lambda x: excess_labels[x]
            )
            excess_multiplier = excess_options[selected_excess_index]
            
            # Aggregate excess options
            agg_excess_options = list(AGGREGATE_EXCESS_OPTIONS.keys())
            agg_excess_labels = [AGGREGATE_EXCESS_OPTIONS[opt]['description'] for opt in agg_excess_options]
            
            selected_agg_index = st.selectbox(
                "Aggregate Excess Structure",
                range(len(agg_excess_options)),
                format_func=lambda x: agg_excess_labels[x]
            )
            aggregate_excess_option = agg_excess_options[selected_agg_index]
        
        with col4:
            # Underwriter discretion factor
            underwriter_discretion_factor = st.number_input(
                "Underwriter Discretion Factor",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.05,
                help="Factor above 1.0 increases premium, below 1.0 decreases it"
            )
    
    # Calculate and display results
    st.markdown("---")
    
    if st.button("Calculate Premium", type="primary", use_container_width=True):
        if total_percentage == 100.0:
            # Perform the calculation
            result = calculate_architect_premium(
                fee_income=fee_income,
                discipline_percentages=discipline_percentages,
                limit_of_indemnity=limit_of_indemnity,
                no_claims_period=no_claims_period,
                retroactive_coverage=retroactive_coverage,
                excess_multiplier=excess_multiplier,
                aggregate_excess_option=aggregate_excess_option,
                underwriter_discretion_factor=underwriter_discretion_factor
            )
            
            # Display results in an organized format
            st.success("Premium Calculation Complete!")
            
            # Summary box
            col5, col6, col7 = st.columns(3)
            
            with col5:
                st.metric("Final Premium", f"£{result['final_premium']:,.2f}")
            
            with col6:
                st.metric("Excess Amount", f"£{result['actual_excess']:,.0f}")
            
            with col7:
                st.metric("Limit of Indemnity", f"£{result['limit_of_indemnity']:,}")
            
            # Detailed breakdown
            with st.expander("Detailed Calculation Breakdown", expanded=True):
                breakdown_data = {
                    'Calculation Step': [
                        'Base Premium (1% of fees)',
                        'After Discipline Factors',
                        'After Fee Size Discount',
                        'After Limit Adjustment',
                        'After No Claims Discount',
                        'After Retroactive Discount',
                        'After Excess Discount',
                        'After Aggregate Excess Discount',
                        'Final Premium (After Discretion)'
                    ],
                    'Amount (£)': [
                        f"{result['base_premium']:,.2f}",
                        f"{result['premium_after_disciplines']:,.2f}",
                        f"{result['premium_after_fee_discount']:,.2f}",
                        f"{result['premium_after_limit']:,.2f}",
                        f"{result['premium_after_no_claims']:,.2f}",
                        f"{result['premium_after_retro']:,.2f}",
                        f"{result['premium_after_excess']:,.2f}",
                        f"{result['premium_after_agg_excess']:,.2f}",
                        f"{result['final_premium']:,.2f}"
                    ],
                    'Factor/Discount': [
                        f"×{ARCHITECT_BASE_RATE:.1%}", 
                        f"{result['discipline_factor']:.3f}",
                        f"-{result['fee_size_discount']:.1%}",
                        f"×{result['limit_factor']:.3f}",
                        f"-{result['no_claims_discount']:.1%}",
                        f"-{result['retroactive_discount']:.1%}",
                        f"{result['excess_discount']:+.1%}",
                        f"-{result['aggregate_excess_discount']:.1%}",
                        f"×{result['underwriter_discretion_factor']:.3f}"
                    ]
                }
                
                df = pd.DataFrame(breakdown_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        else:
            st.error("Please ensure discipline percentages total exactly 100% before calculating.")

# Run the application
if __name__ == "__main__":
    main()