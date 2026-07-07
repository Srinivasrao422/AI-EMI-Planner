from core.emi import calculate_emi

print("========== TEST 1 ==========")

try:
    calculate_emi(-500000, 8.5, 5)
except Exception as e:
    print(e)

print("\n========== TEST 2 ==========")

try:
    calculate_emi(500000, -8.5, 5)
except Exception as e:
    print(e)

print("\n========== TEST 3 ==========")

try:
    calculate_emi(500000, 8.5, 0)
except Exception as e:
    print(e)

print("\n========== TEST 4 ==========")

try:
    emi = calculate_emi(500000, 8.5, 5)
    print("Success!")
    print("EMI:", emi)
except Exception as e:
    print(e)