# utils/luhn.py
def luhn_check(card):
    digits = [int(d) for d in card]
    for i in range(len(digits)-2, -1, -2):
        digits[i] = digits[i]*2 if digits[i]*2 < 10 else digits[i]*2 - 9
    return sum(digits) % 10 == 0