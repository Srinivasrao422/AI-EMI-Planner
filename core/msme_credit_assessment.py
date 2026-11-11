"""Explainable MSME credit-readiness review from recorded monthly data.

This is a transparent decision-support checklist, not a bureau score,
default prediction, lender rating or loan approval.
"""


def _amount(row, field):
    try:
        value = float(row.get(field, 0) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field.replace('_', ' ').title()} must be numeric.") from exc
    if value < 0:
        raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative.")
    return value


def assess_credit_readiness(records, proposed_monthly_emi=0.0):
    """Assess cash capacity and evidence coverage using up to six saved months.

    Records must be ordered newest first. A minimum of three distinct,
    consecutive reporting months is required for a readiness conclusion.
    """
    if not isinstance(records, (list, tuple)) or len(records) < 3:
        raise ValueError("At least three monthly financial records are required for this review.")

    try:
        proposed_emi = float(proposed_monthly_emi)
    except (TypeError, ValueError) as exc:
        raise ValueError("Proposed monthly EMI must be numeric.") from exc
    if proposed_emi < 0:
        raise ValueError("Proposed monthly EMI cannot be negative.")

    selected = list(records[:6])
    months = [str(row.get("period_month", "")) for row in selected]
    if any(not month for month in months) or len(set(months)) != len(months):
        raise ValueError("Each reporting record must have a distinct reporting month.")

    # Validate chronological continuity for the three latest records.
    parsed = []
    for month in months[:3]:
        try:
            year, month_number = (int(part) for part in month.split("-"))
            if len(month) != 7 or not 1 <= month_number <= 12:
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError("Reporting months must use YYYY-MM format.") from None
        parsed.append(year * 12 + month_number)
    if not (parsed[0] == parsed[1] + 1 and parsed[1] == parsed[2] + 1):
        raise ValueError("The latest three records must be consecutive months.")

    monthly = []
    for row in selected:
        revenue = _amount(row, "revenue")
        other_income = _amount(row, "other_income")
        direct_costs = _amount(row, "cost_of_goods_sold")
        operating_expenses = _amount(row, "operating_expenses")
        drawings = _amount(row, "owner_drawings")
        debt = _amount(row, "existing_debt_service")
        total_income = revenue + other_income
        surplus = total_income - direct_costs - operating_expenses
        headroom = surplus - drawings - debt
        monthly.append({
            "period_month": row["period_month"],
            "revenue": revenue,
            "total_income": total_income,
            "operating_surplus": surplus,
            "cash_headroom": headroom,
            "existing_debt_service": debt,
        })

    latest = monthly[0]
    average_headroom = sum(row["cash_headroom"] for row in monthly[:3]) / 3
    positive_headroom_months = sum(row["cash_headroom"] >= 0 for row in monthly[:3])
    revenue_values = [row["revenue"] for row in monthly[:3]]
    revenue_changes = []
    for newer, older in zip(revenue_values, revenue_values[1:]):
        if older > 0:
            revenue_changes.append((newer - older) / older * 100)
    revenue_trend = revenue_changes[0] if revenue_changes else None

    proposed_headroom = latest["cash_headroom"] - proposed_emi
    coverage = (
        latest["operating_surplus"] / (latest["existing_debt_service"] + proposed_emi)
        if latest["existing_debt_service"] + proposed_emi > 0 else None
    )

    findings = []
    if latest["cash_headroom"] < 0:
        findings.append("Latest month has negative cash headroom after drawings and existing debt.")
    if positive_headroom_months < 3:
        findings.append(
            f"Only {positive_headroom_months} of the latest three months had non-negative cash headroom."
        )
    if proposed_headroom < 0:
        findings.append("The proposed EMI would make latest-month cash headroom negative.")
    if latest["operating_surplus"] < 0:
        findings.append("Latest-month operating costs exceed recorded income.")
    if revenue_trend is not None and revenue_trend < -10:
        findings.append("Revenue fell by more than 10% between the latest two recorded months.")
    if not findings:
        findings.append("No critical cash-headroom warning was identified in the reviewed records.")

    evidence_gaps = []
    if len(records) < 6:
        evidence_gaps.append("Fewer than six months of records are available; a longer history would improve context.")
    if any(row["revenue"] == 0 for row in monthly[:3]):
        evidence_gaps.append("At least one of the latest three months has zero recorded sales revenue.")
    if all(row["existing_debt_service"] == 0 for row in monthly[:3]):
        evidence_gaps.append("No existing monthly debt service was recorded in the latest three months.")
    evidence_gaps.append("Credit bureau history, bank balances, receivables, collateral and statutory filings were not assessed.")

    if proposed_headroom < 0 or positive_headroom_months < 2 or latest["operating_surplus"] < 0:
        status = "High attention required"
    elif proposed_headroom < 0.1 * max(latest["total_income"], 0) or positive_headroom_months < 3:
        status = "Further review recommended"
    else:
        status = "Cash-flow indicators are supportive"

    return {
        "status": status,
        "months_reviewed": [row["period_month"] for row in monthly],
        "latest_month": latest["period_month"],
        "latest_cash_headroom": round(latest["cash_headroom"], 2),
        "average_three_month_headroom": round(average_headroom, 2),
        "positive_headroom_months": positive_headroom_months,
        "proposed_monthly_emi": round(proposed_emi, 2),
        "headroom_after_proposed_emi": round(proposed_headroom, 2),
        "coverage_proxy": round(coverage, 2) if coverage is not None else None,
        "revenue_change_percent": round(revenue_trend, 2) if revenue_trend is not None else None,
        "findings": findings,
        "evidence_gaps": evidence_gaps,
        "limitations": (
            "This review uses entered monthly figures only. The coverage ratio is a "
            "simplified operating-surplus-to-debt-service proxy, not formal DSCR. "
            "It does not verify source documents, credit bureau data, bank balances, "
            "receivables, inventory, collateral, legal eligibility or lender policy. "
            "It is not a credit score, default probability, approval or lending decision."
        ),
    }
