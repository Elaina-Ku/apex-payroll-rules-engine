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
import streamlit as st
import pandas as pd
from datetime import datetime

# -------------------------------------------------------------
# 1. Page Configuration & Header
# -------------------------------------------------------------
st.set_page_config(
    page_title="Apex Mining HRIS Suite",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ Apex Mining HRIS & Payroll Architecture Suite")
st.caption("Proof-of-Concept Enterprise Architecture: British Columbia (HQ), Ontario (Plant), and Quebec (Mine)")

# 상단 탭 생성 (두 엔진을 하나의 웹사이트에 통합)
tab1, tab2 = st.tabs([
    "🛡️ Module 1: Pre-Payroll T&A Data Validator",
    "⚙️ Module 2: Multi-Jurisdiction Shift & Statutory Simulator"
])

# =============================================================
# TAB 1: Pre-Payroll T&A Data Ingestion Validator
# =============================================================
with tab1:
    st.header("Pre-Payroll T&A Data Ingestion Validator & Quality Gate")
    st.markdown("""
    This automated quality gate audits raw frontline timecard punch batches before committing data to the gross-to-net engine.
    It intercepts errors across **10 compliance controls**, flags fatal exceptions, auto-remediates CBA minimums, and exports a scrubbed payload.
    """)
    st.write("---")

    # Reference Master Tables
    ACTIVE_EMPLOYEES = {
        "EMP1001": {"Name": "Marc Bouchard", "Site": "QC", "Status": "Active", "Role": "Underground Miner"},
        "EMP1002": {"Name": "Sarah Jenkins", "Site": "ON", "Status": "Active", "Role": "Mill Operator"},
        "EMP1003": {"Name": "David Tremblay", "Site": "QC", "Status": "Active", "Role": "Industrial Electrician"},
        "EMP1004": {"Name": "Elena Rostova", "Site": "BC", "Status": "Active", "Role": "Corporate Mine Engineer"},
        "EMP1005": {"Name": "James Wilson", "Site": "ON", "Status": "Terminated", "Term_Date": "2026-08-31", "Role": "Heavy-Duty Mechanic"}
    }
    VALID_PAY_CODES = ["REG_UN", "SAL_NR", "OT_15U", "OT_20U", "SHFT_GY", "PREM_UG", "CALL_MIN", "STAT_WRK"]
    STAT_HOLIDAYS_2026 = ["2026-09-07", "2026-09-30"]

    def load_sample_timecard_data():
        return pd.DataFrame([
            {"Row_ID": 1, "EE_ID": "EMP1001", "Shift_Date": "2026-09-01", "In_Time": "07:00", "Out_Time": "19:00", "Hours": 12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "Y"},
            {"Row_ID": 2, "EE_ID": "EMP1002", "Shift_Date": "2026-09-01", "In_Time": "07:00", "Out_Time": "19:00", "Hours": 12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "N"},
            {"Row_ID": 3, "EE_ID": "EMP1003", "Shift_Date": "2026-09-01", "In_Time": "07:00", "Out_Time": "", "Hours": 0.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "Y"},
            {"Row_ID": 4, "EE_ID": "EMP1001", "Shift_Date": "2026-09-02", "In_Time": "19:00", "Out_Time": "07:00", "Hours": -12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "Y"},
            {"Row_ID": 5, "EE_ID": "EMP1002", "Shift_Date": "2026-09-01", "In_Time": "07:00", "Out_Time": "19:00", "Hours": 12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "N"},
            {"Row_ID": 6, "EE_ID": "EMP1005", "Shift_Date": "2026-09-05", "In_Time": "07:00", "Out_Time": "19:00", "Hours": 12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "N"},
            {"Row_ID": 7, "EE_ID": "EMP1004", "Shift_Date": "2026-09-03", "In_Time": "08:00", "Out_Time": "16:00", "Hours": 8.0, "Pay_Code": "OT_99_UNKNOWN", "Call_Out": "N", "Underground": "N"},
            {"Row_ID": 8, "EE_ID": "EMP1001", "Shift_Date": "2026-09-04", "In_Time": "07:00", "Out_Time": "01:00", "Hours": 18.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "Y"},
            {"Row_ID": 9, "EE_ID": "EMP1001", "Shift_Date": "2026-09-04", "In_Time": "06:00", "Out_Time": "18:00", "Hours": 12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "Y"},
            {"Row_ID": 10, "EE_ID": "EMP1003", "Shift_Date": "2026-09-05", "In_Time": "22:00", "Out_Time": "23:30", "Hours": 1.5, "Pay_Code": "CALL_MIN", "Call_Out": "Y", "Underground": "N"},
            {"Row_ID": 11, "EE_ID": "EMP1004", "Shift_Date": "2026-09-06", "In_Time": "08:00", "Out_Time": "16:00", "Hours": 8.0, "Pay_Code": "PREM_UG", "Call_Out": "N", "Underground": "Y"},
            {"Row_ID": 12, "EE_ID": "EMP1002", "Shift_Date": "2026-09-07", "In_Time": "07:00", "Out_Time": "19:00", "Hours": 12.0, "Pay_Code": "REG_UN", "Call_Out": "N", "Underground": "N"}
        ])

    col_input1, col_input2 = st.columns([1, 2])
    with col_input1:
        data_source = st.radio("Select Ingestion Mode", ["Load Pre-built Audit Batch (Demo)", "Upload Custom Raw CSV"], key="tab1_source")
    with col_input2:
        if data_source == "Load Pre-built Audit Batch (Demo)":
            raw_df = load_sample_timecard_data()
            st.success("Loaded synthetic audit batch containing 10 real-world data exceptions.")
        else:
            uploaded_file = st.file_uploader("Upload Timecard Raw CSV Payload", type=["csv"], key="tab1_upload")
            if uploaded_file is not None:
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = None

    if raw_df is not None:
        audit_results = []
        clean_rows = []
        seen_punches = set()
        prev_shift_tracker = {}

        raw_df_sorted = raw_df.sort_values(by=["EE_ID", "Shift_Date", "In_Time"]).reset_index(drop=True)

        for idx, row in raw_df_sorted.iterrows():
            row_id = row["Row_ID"]
            ee_id = str(row["EE_ID"]).strip()
            date_str = str(row["Shift_Date"]).strip()
            in_time = str(row["In_Time"]).strip() if pd.notnull(row["In_Time"]) else ""
            out_time = str(row["Out_Time"]).strip() if pd.notnull(row["Out_Time"]) else ""
            hours = float(row["Hours"]) if pd.notnull(row["Hours"]) else 0.0
            pay_code = str(row["Pay_Code"]).strip()
            is_callout = str(row["Call_Out"]).strip().upper() == "Y"
            is_ug = str(row["Underground"]).strip().upper() == "Y"

            # ERR-01
            if not in_time or not out_time:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-01: Missing Punch", "Detail": "Missing In/Out timestamp.", "Action": "Block Ingestion. Route ticket to supervisor."})
                continue
            # ERR-02
            if hours <= 0.0:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-02: Negative/Zero Hours", "Detail": f"Invalid duration: {hours} hrs.", "Action": "Block Ingestion. Recalculate interval."})
                continue
            # ERR-03
            punch_sig = (ee_id, date_str, in_time, out_time)
            if punch_sig in seen_punches:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-03: Duplicate Punch", "Detail": f"Identical punch on {date_str}.", "Action": "Auto-Deduplicate. Purged duplicate record."})
                continue
            seen_punches.add(punch_sig)
            # ERR-04
            if ee_id not in ACTIVE_EMPLOYEES:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-04: Unknown EE ID", "Detail": f"EE {ee_id} not in HR master.", "Action": "Block Ingestion. Verify profile."})
                continue
            elif ACTIVE_EMPLOYEES[ee_id]["Status"] == "Terminated":
                term_d = ACTIVE_EMPLOYEES[ee_id].get("Term_Date", "N/A")
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-04: Terminated EE", "Detail": f"Shift logged post-termination ({term_d}).", "Action": "Block Ingestion. Mandate HRBP sign-off."})
                continue
            # ERR-05
            if pay_code not in VALID_PAY_CODES:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-05: Inactive Pay Code", "Detail": f"Code '{pay_code}' not defined.", "Action": "Block Ingestion. Remap code."})
                continue
            # ERR-06
            if hours > 16.0:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Warning", "Rule": "ERR-06: Fatigue Outlier (>16h)", "Detail": f"Shift of {hours}h exceeds safety cap.", "Action": "Pass with Flag. Requires VP authorization."})
            # ERR-07
            try:
                current_shift_start = datetime.strptime(f"{date_str} {in_time}", "%Y-%m-%d %H:%M")
                if ee_id in prev_shift_tracker:
                    prev_shift_end = prev_shift_tracker[ee_id]
                    rest_hours = (current_shift_start - prev_shift_end).total_seconds() / 3600.0
                    if 0 < rest_hours < 8.0:
                        audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Warning", "Rule": "ERR-07: Rest Period Infringement", "Detail": f"Only {rest_hours:.1f}h rest (ESA min: 8h).", "Action": "Pass with Flag. Verify CBA penalty."})
                prev_shift_tracker[ee_id] = datetime.strptime(f"{date_str} {out_time}", "%Y-%m-%d %H:%M")
            except Exception:
                pass
            # ERR-08
            final_payable_hours = hours
            if is_callout and hours < 4.0:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Warning", "Rule": "ERR-08: Call-Out Minimum Breach", "Detail": f"Punch of {hours}h under CBA Art. 17.01 4h cap.", "Action": "Auto-Remediated to 4.0h @ 2.0x."})
                final_payable_hours = 4.0
            # ERR-09
            ee_role = ACTIVE_EMPLOYEES[ee_id]["Role"]
            if pay_code == "PREM_UG" and "Underground" not in ee_role:
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Fatal", "Rule": "ERR-09: Hazard Tag Mismatch", "Detail": f"Underground premium applied to non-mine role ({ee_role}).", "Action": "Block Ingestion. Void hazard tag."})
                continue
            # ERR-10
            if date_str in STAT_HOLIDAYS_2026 and pay_code == "REG_UN":
                audit_results.append({"Row": row_id, "EE_ID": ee_id, "Severity": "Warning", "Rule": "ERR-10: Stat Holiday Mismatch", "Detail": f"Stat holiday ({date_str}) logged under regular base pay.", "Action": "Pass with Flag. Recommend remapping."})

            clean_rows.append({
                "Row_ID": row_id, "EE_ID": ee_id, "Name": ACTIVE_EMPLOYEES[ee_id]["Name"],
                "Site": ACTIVE_EMPLOYEES[ee_id]["Site"], "Date": date_str, "Pay_Code": pay_code,
                "Final_Hours": final_payable_hours, "Remediated": "Y" if (is_callout and hours < 4.0) else "N"
            })

        audit_df = pd.DataFrame(audit_results)
        clean_df = pd.DataFrame(clean_rows)

        # KPI Dashboard
        total_p = len(raw_df)
        fatal_b = len(audit_df[audit_df["Severity"] == "Fatal"]) if not audit_df.empty else 0
        warn_b = len(audit_df[audit_df["Severity"] == "Warning"]) if not audit_df.empty else 0
        clean_p = len(clean_df)
        yield_rate = (clean_p / total_p * 100) if total_p > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Polled Records", f"{total_p} rows")
        k2.metric("Critical Fatal Blocks", f"{fatal_b} blocked", delta=f"-{fatal_b}", delta_color="inverse")
        k3.metric("Compliance Warnings", f"{warn_b} flagged", delta=f"{warn_b} items", delta_color="off")
        k4.metric("Clean Ingestion Yield", f"{yield_rate:.1f}%", f"{clean_p} ready")

        st.write("---")
        st.subheader("Ingestion Audit Ledger")
        if not audit_df.empty:
            st.dataframe(audit_df, use_container_width=True)
        else:
            st.success("🎉 Zero exceptions detected.")

        st.write("---")
        st.subheader("Clean Staging Payload (Ready for Gross-to-Net Engine)")
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.dataframe(clean_df, use_container_width=True)
        with col_c2:
            st.download_button(
                label="📥 Download Clean CSV",
                data=clean_df.to_csv(index=False).encode('utf-8'),
                file_name="Apex_Clean_Timecard_Ingestion_Payload.csv",
                mime="text/csv"
            )

# =============================================================
# TAB 2: Multi-Jurisdiction Shift & Statutory Simulator
# =============================================================
with tab2:
    st.header("Multi-Jurisdiction Shift & Statutory Gross-to-Net Simulator")
    st.markdown("""
    This engine models complex shift compensations, 12-hour continuous CBA rotations, 
    and multi-provincial tax divergence across **British Columbia, Ontario, and Quebec** (CRA vs. Revenu Québec).
    """)
    st.write("---")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        jurisdiction = st.selectbox(
            "Operating Site (Province of Employment)",
            ["QC - Underground Mine (Metallo Union)", "ON - Concentrator Plant (USW Union)", "BC - Corporate HQ (Non-Union)"],
            key="tab2_jurisdiction"
        )
        if "BC" in jurisdiction:
            emp_type = "Salaried Staff"
            base_salary = st.number_input("Annual Gross Salary ($)", value=95000.0, step=1000.0, key="tab2_sal")
            base_rate = base_salary / 2080.0
            st.caption(f"Equivalent Hourly Rate: ${base_rate:.2f}/hr")
        else:
            emp_type = "Hourly Union"
            base_rate = st.number_input("CBA Base Hourly Wage ($)", value=38.50, step=0.50, key="tab2_wage")

    with col_s2:
        st.markdown("**Active Statutory Framework:**")
        if "QC" in jurisdiction:
            st.info("• Quebec LNT: 12h Continuous Shift Cap\n• Dual Tax: CRA + Revenu Québec (RL-1)\n• QPP & Reduced EI + QPIP (RQAP)\n• CNESST Mining & HSF (4.26%)")
        elif "ON" in jurisdiction:
            st.info("• Ontario ESA: 44h Weekly Overtime Threshold\n• Single Tax: CRA Sole Agency (T4)\n• CPP & Standard EI\n• WSIB Class D & ON EHT (1.95%)")
        else:
            st.info("• BC ESA: Salaried Overtime Exempt\n• Single Tax: CRA Sole Agency (T4)\n• CPP & Standard EI\n• WorkSafeBC CU 761001 & BC EHT (1.95%)")

    st.subheader("Shift Parameters")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        worked_hours = st.number_input("Shift Worked Hours", min_value=0.0, max_value=24.0, value=12.0, step=0.5, key="tab2_hrs")
    with p2:
        is_callout = st.checkbox("Emergency Call-Out (Art. 17.01)", key="tab2_callout")
    with p3:
        is_graveyard = st.checkbox("Graveyard Shift (+$3.50/hr)", value=True, key="tab2_grave")
    with p4:
        is_underground = st.checkbox("Underground Tagged (+$4.25/hr)", value=("QC" in jurisdiction), disabled=("QC" not in jurisdiction), key="tab2_ug")

    # Calculation
    reg_hours = 0.0
    ot15_hours = 0.0
    ot20_hours = 0.0

    if emp_type == "Salaried Staff":
        reg_hours = worked_hours
    else:
        if is_callout:
            ot20_hours = max(worked_hours, 4.0)
        else:
            if "QC" in jurisdiction:
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
                if worked_hours <= 12.0:
                    reg_hours = worked_hours
                else:
                    reg_hours = 12.0
                    ot15_hours = worked_hours - 12.0

    reg_pay = reg_hours * base_rate
    ot15_pay = ot15_hours * (base_rate * 1.5)
    ot20_pay = ot20_hours * (base_rate * 2.0)
    shift_premium_pay = (worked_hours * 3.50) if (is_graveyard and emp_type != "Salaried Staff") else 0.0
    hazard_premium_pay = (worked_hours * 4.25) if (is_underground and "QC" in jurisdiction) else 0.0

    total_gross = reg_pay + ot15_pay + ot20_pay + shift_premium_pay + hazard_premium_pay

    if "QC" in jurisdiction:
        tax_agency = "CRA + Revenu Québec (Dual Tax)"
        pension_lbl = "QPP (RRQ)"
        pension_val = total_gross * 0.064
        ei_lbl = "Reduced EI + QPIP (RQAP)"
        ei_val = (total_gross * 0.0132) + (total_gross * 0.00494)
        er_tax_lbl = "QC HSF (4.26%) + CNT (0.06%)"
        er_tax_val = total_gross * (0.0426 + 0.0006)
        wcb_lbl = "CNESST Mining ($3.95/100)"
        wcb_val = (total_gross / 100) * 3.95
    elif "ON" in jurisdiction:
        tax_agency = "CRA Sole Agency"
        pension_lbl = "CPP"
        pension_val = total_gross * 0.0595
        ei_lbl = "Standard Federal EI (1.66%)"
        ei_val = total_gross * 0.0166
        er_tax_lbl = "ON EHT (1.95%)"
        er_tax_val = total_gross * 0.0195
        wcb_lbl = "WSIB Class D ($2.85/100)"
        wcb_val = (total_gross / 100) * 2.85
    else:
        tax_agency = "CRA Sole Agency"
        pension_lbl = "CPP"
        pension_val = total_gross * 0.0595
        ei_lbl = "Standard Federal EI (1.66%)"
        ei_val = total_gross * 0.0166
        er_tax_lbl = "BC EHT (1.95%)"
        er_tax_val = total_gross * 0.0195
        wcb_lbl = "WorkSafeBC CU 761001 ($0.18/100)"
        wcb_val = (total_gross / 100) * 0.18

    st.write("---")
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Payable Hours", f"{reg_hours + ot15_hours + ot20_hours:.1f} hrs")
    res2.metric("Shift Gross Compensation", f"${total_gross:,.2f}")
    res3.metric("Employee Deductions Est.", f"${pension_val + ei_val:,.2f}", f"{pension_lbl} & EI")
    res4.metric("Employer Liabilities", f"${er_tax_val + wcb_val:,.2f}", f"{er_tax_lbl}")

    col_tbl, col_comp = st.columns([3, 2])
    with col_tbl:
        st.markdown("**Earning Code Breakdown (GL Interface Feed)**")
        calc_summary = [
            {"Code": "REG_PAY", "Description": "Regular Base Allocation", "Hours": reg_hours, "Rate": f"${base_rate:.2f}", "Total": f"${reg_pay:,.2f}"},
            {"Code": "OT_15", "Description": "Daily OT (1.5x Base)", "Hours": ot15_hours, "Rate": f"${base_rate*1.5:.2f}", "Total": f"${ot15_pay:,.2f}"},
            {"Code": "OT_20", "Description": "Double Time (2.0x Base)", "Hours": ot20_hours, "Rate": f"${base_rate*2.0:.2f}", "Total": f"${ot20_pay:,.2f}"},
            {"Code": "SHFT_GY", "Description": "Graveyard Differential", "Hours": worked_hours if is_graveyard else 0, "Rate": "$3.50/hr", "Total": f"${shift_premium_pay:,.2f}"},
            {"Code": "PREM_UG", "Description": "Underground Mine Hazard", "Hours": worked_hours if is_underground else 0, "Rate": "$4.25/hr", "Total": f"${hazard_premium_pay:,.2f}"}
        ]
        st.table(pd.DataFrame(calc_summary))

    with col_comp:
        st.markdown("**Jurisdictional Compliance Output**")
        st.markdown(f"• **Filing Authority:** `{tax_agency}`")
        st.markdown(f"• **Pension Engine:** `{pension_lbl}` -> `${pension_val:.2f}`")
        st.markdown(f"• **Employment Insurance:** `{ei_lbl}` -> `${ei_val:.2f}`")
        st.markdown(f"• **Provincial Health Tax:** `{er_tax_lbl}` -> `${er_tax_val:.2f}`")
        st.markdown(f"• **Workers' Comp Board:** `{wcb_lbl}` -> `${wcb_val:.2f}`")
