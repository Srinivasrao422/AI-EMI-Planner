from core.repayment import generate_repayment_schedule

schedule = generate_repayment_schedule(
    principal=500000,
    annual_interest_rate=8.5,
    tenure_years=5
)

print("\n========== REPAYMENT SCHEDULE ==========\n")

for row in schedule[:5]:
    print(row)

print("\n............")

print("\nLast Month")

print(schedule[-1])