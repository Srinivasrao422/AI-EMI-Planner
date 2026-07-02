from core.repayment import generate_repayment_schedule
from utils.dataframe_helper import repayment_schedule_to_dataframe


schedule = generate_repayment_schedule(
    principal=500000,
    annual_interest_rate=8.5,
    tenure_years=5
)

df = repayment_schedule_to_dataframe(schedule)

print("\n========== DATAFRAME ==========\n")

print(df)

print("\n========== FIRST 5 ROWS ==========\n")

print(df.head())

print("\n========== LAST 5 ROWS ==========\n")

print(df.tail())