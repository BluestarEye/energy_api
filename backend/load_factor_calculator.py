def classify_load_factor(kW, kWh, days_on_bill):
    # Check for missing inputs
    if kW is None or kWh is None or days_on_bill is None:
        return ""

    # Avoid divide-by-zero
    try:
        lf = kWh / (kW * days_on_bill * 24)
    except ZeroDivisionError:
        return "LF ERROR - CHECK INPUTS"

    # Validate LF range
    if lf < 0 or lf > 1:
        return "LF ERROR - CHECK INPUTS"
    elif lf >= 0.6:
        return "HI"
    elif lf >= 0.4:
        return "MED"
    else:
        return "LO"
