import streamlit as st
import pandas as pd

st.set_page_config(page_title="Apex Mining HRIS Engine", layout="wide")

st.title("⛏️ Apex Mining Multi-Jurisdiction T&A & Payroll Engine")
st.caption("Proof-of-Concept Architecture: BC HQ, ON Processing Plant & QC Underground Mine")

st.markdown("""
This engine dynamically evaluates distinct provincial employment standards across jurisdictions (BC, ON, QC), 12-hour continuous shift rotations, CBA 4-hour call-out guarantees, and dual-tax authority frameworks (CRA vs. Revenu Québec) in real time.
""")

st.write("---")

# 1. 사이드바 설정
with st.sidebar:
    st.header("1. Employee & Site Scope")
    jurisdiction = st.selectbox(
        "Operating Site (Province of Employment)",
        ["QC - Underground Mine (Metallo Union)", "ON - Concentrator Plant (USW Union)", "BC - Corporate HQ (Non-Union)"]
    )
    
    if "BC" in jurisdiction:
        emp_type = "Salaried Staff"
        base_salary = st.number_input("Annual Gross Salary ($)", value=95000.0, step=1000.0)
        base_rate = base_salary / 2080.0
        st.caption(f"Equivalent Hourly Rate: ${base_rate:.2f}/hr")
    else:
        emp_type = "Hourly Union"
        base_rate = st.number_input("CBA Base Hourly Wage ($)", value=38.50, step=0.50)
        
    st.markdown("---")
    st.markdown("**Active Statutory Framework:**")
    if "QC" in jurisdiction:
        st.info("• Quebec LNT: 12h Daily Cap\n• Dual Tax: CRA + Revenu Québec\n• QPP & Reduced EI + QPIP\n• CNESST & HSF (4.26%)")
    elif "ON" in jurisdiction:
        st.info("• Ontario ESA: 44h Weekly OT\n• Single Tax: CRA\n• CPP & Standard EI\n• WSIB Class D & ON EHT")
    else:
        st.info("• BC ESA: Salaried Overtime Exempt\n• BC EHT (1.95%)\n• WorkSafeBC CU 761001")

# 2. 근무 시간 입력
st.subheader("2. Shift & Timecard Parameters")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    worked_hours = st.number_input("Actual Worked Hours in Shift", min_value=0.0, max_value=24.0, value=12.0, step=0.5)
with col_b:
    is_callout = st.checkbox("Emergency Call-Out Outside Shift", help="Article 17.01: Triggers minimum 4.0-hour credit at 2.0x")
with col_c:
    is_graveyard = st.checkbox("Graveyard Shift (19:00 - 07:00)", value=True, help="Adds flat $3.50/hr premium")
with col_d:
    is_underground = st.checkbox("Underground Tagged (QC Site Only)", value=("QC" in jurisdiction), disabled=("QC" not in jurisdiction))

# 3. 계산 엔진 (Rules Engine)
reg_hours = 0.0
ot15_hours = 0.0
ot20_hours = 0.0
callout_credit_hours = 0.0

if emp_type == "Salaried Staff":
    reg_hours = worked_hours
else:
    if is_callout:
        effective_hours = max(worked_hours, 4.0)
        ot20_hours = effective_hours
        callout_credit_hours = effective_hours
    else:
        if "QC" in jurisdiction:
            # Quebec Site: 12h Continuous shift cap
            if worked_hours <= 12.0:
                reg_hours = worked_hours
            elif worked_hours <= 14.0:
                reg_hours = 12.0
                ot15_hours = worked_hours - 12.0
            else:
                reg_hours = 12.0
                ot15_hours = 2.0
                ot20_hours = worked_hours - 14.0
        else:
            # Ontario Site: Shift scheduled hours
            if worked_hours <= 12.0:
                reg_hours = worked_hours
            else:
                reg_hours = 12.0
                ot15_hours = worked_hours - 12.0

# 금액 산출 (Anti-Pyramiding Logic 적용)
reg_pay = reg_hours * base_rate
ot15_pay = ot15_hours * (base_rate * 1.5)
ot20_pay = ot20_hours * (base_rate * 2.0)

# Premiums (Flat additions)
shift_premium_pay = (worked_hours * 3.50) if (is_graveyard and emp_type != "Salaried Staff") else 0.0
hazard_premium_pay = (worked_hours * 4.25) if (is_underground and "QC" in jurisdiction) else 0.0

total_gross = reg_pay + ot15_pay + ot20_pay + shift_premium_pay + hazard_premium_pay

# 세무 및 부담금 시뮬레이션
if "QC" in jurisdiction:
    tax_authority = "CRA + Revenu Québec"
    pension_name = "QPP (RRQ)"
    pension_ee = total_gross * 0.064
    ei_name = "Reduced EI (1.32%) + QPIP (0.494%)"
    ei_ee = (total_gross * 0.0132) + (total_gross * 0.00494)
    er_tax_name = "QC HSF (4.26%) + CNT (0.06%)"
    er_tax_amt = total_gross * (0.0426 + 0.0006)
    wcb_name = "CNESST Mining ($3.95/100)"
    wcb_amt = (total_gross / 100) * 3.95
elif "ON" in jurisdiction:
    tax_authority = "CRA Sole Agency"
    pension_name = "CPP"
    pension_ee = total_gross * 0.0595
    ei_name = "Standard Federal EI (1.66%)"
    ei_ee = total_gross * 0.0166
    er_tax_name = "ON EHT (1.95%)"
    er_tax_amt = total_gross * 0.0195
    wcb_name = "WSIB Class D ($2.85/100)"
    wcb_amt = (total_gross / 100) * 2.85
else:
    tax_authority = "CRA Sole Agency"
    pension_name = "CPP"
    pension_ee = total_gross * 0.0595
    ei_name = "Standard Federal EI (1.66%)"
    ei_ee = total_gross * 0.0166
    er_tax_name = "BC EHT (1.95%)"
    er_tax_amt = total_gross * 0.0195
    wcb_name = "WorkSafeBC CU 761001 ($0.18/100)"
    wcb_amt = (total_gross / 100) * 0.18

# 4. 화면 출력
st.write("---")
st.subheader("3. Shift Execution & Compensation Output")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Payable Hours", f"{reg_hours + ot15_hours + ot20_hours:.1f} hrs")
m2.metric("Shift Gross Pay", f"${total_gross:,.2f}")
m3.metric("Employee Statutory Est.", f"${pension_ee + ei_ee:,.2f}", f"{pension_name} & EI")
m4.metric("Employer Liabilities", f"${er_tax_amt + wcb_amt:,.2f}", f"{er_tax_name}")

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("**Earning Code Breakdown (GL Interface Source)**")
    summary_data = [
        {"Code": "REG_PAY", "Description": "Regular Base Allocation", "Hours": reg_hours, "Rate": f"${base_rate:.2f}", "Total": f"${reg_pay:,.2f}"},
        {"Code": "OT_15", "Description": "Daily OT (1.5x Base)", "Hours": ot15_hours, "Rate": f"${base_rate*1.5:.2f}", "Total": f"${ot15_pay:,.2f}"},
        {"Code": "OT_20", "Description": "Double Time (2.0x Base)", "Hours": ot20_hours, "Rate": f"${base_rate*2.0:.2f}", "Total": f"${ot20_pay:,.2f}"},
        {"Code": "SHFT_GY", "Description": "Graveyard Differential", "Hours": worked_hours if is_graveyard else 0, "Rate": "$3.50/hr", "Total": f"${shift_premium_pay:,.2f}"},
        {"Code": "PREM_UG", "Description": "Underground Mine Hazard", "Hours": worked_hours if is_underground else 0, "Rate": "$4.25/hr", "Total": f"${hazard_premium_pay:,.2f}"}
    ]
    st.table(pd.DataFrame(summary_data))

with col_right:
    st.markdown("**Jurisdictional Compliance Matrix**")
    st.markdown(f"**Tax Filing Target:** `{tax_authority}`")
    st.markdown(f"**Pension Engine:** `{pension_name}` -> `${pension_ee:.2f}`")
    st.markdown(f"**Employment Insurance:** `{ei_name}` -> `${ei_ee:.2f}`")
    st.markdown(f"**Provincial Health Tax:** `{er_tax_name}` -> `${er_tax_amt:.2f}`")
    st.markdown(f"**Workers' Compensation:** `{wcb_name}` -> `${wcb_amt:.2f}`")

if is_callout and worked_hours < 4.0:
    st.warning(f"⚡ **CBA Audit Flag:** Emergency Call-out punch of {worked_hours}h auto-expanded to 4.0h minimum credit at 2.0x rate (${ot20_pay:,.2f}).")
