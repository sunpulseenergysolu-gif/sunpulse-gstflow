# Indian Rupee Number to Words Converter

ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"]

TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

def _two_digits(num: int) -> str:
    if num == 0:
        return ""
    elif num < 20:
        return ONES[num]
    else:
        tens = TENS[num // 10]
        ones = ONES[num % 10]
        return f"{tens} {ones}".strip()

def _three_digits(num: int) -> str:
    hundred = num // 100
    remainder = num % 100
    res = []
    if hundred > 0:
        res.append(f"{ONES[hundred]} Hundred")
    if remainder > 0:
        res.append(_two_digits(remainder))
    return " ".join(res).strip()

def number_to_words_inr(amount: float) -> str:
    """Converts a numerical amount into Indian Rupee Words (e.g. INR 1,25,450.50 -> One Lakh Twenty Five Thousand Four Hundred Fifty Rupees and Fifty Paise Only)"""
    try:
        amount = round(float(amount), 2)
    except (ValueError, TypeError):
        return "Zero Rupees Only"
        
    if amount == 0:
        return "Zero Rupees Only"

    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    if rupees == 0 and paise > 0:
        return f"{_two_digits(paise)} Paise Only"

    parts = []
    
    # Crores (10,000,000)
    crores = rupees // 10000000
    rupees %= 10000000
    if crores > 0:
        parts.append(f"{_three_digits(crores)} Crore")

    # Lakhs (100,000)
    lakhs = rupees // 100000
    rupees %= 100000
    if lakhs > 0:
        parts.append(f"{_two_digits(lakhs)} Lakh")

    # Thousands (1,000)
    thousands = rupees // 1000
    rupees %= 1000
    if thousands > 0:
        parts.append(f"{_two_digits(thousands)} Thousand")

    # Hundreds and below
    if rupees > 0:
        parts.append(_three_digits(rupees))

    rupees_str = " ".join(parts).strip()
    result = f"{rupees_str} Rupees"

    if paise > 0:
        result += f" and {_two_digits(paise)} Paise"

    result += " Only"
    return result
