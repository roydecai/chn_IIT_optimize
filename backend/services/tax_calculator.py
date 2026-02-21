from decimal import Decimal, ROUND_HALF_EVEN
from typing import TypedDict

ROUND_DECIMAL_PLACES = 4

def _round(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal('0.0001'), rounding=ROUND_HALF_EVEN)

class ProgressiveTaxBracket(TypedDict):
    min: Decimal
    max: Decimal
    rate: Decimal
    quick_deduction: Decimal

PROGRESSIVE_TAX_BRACKETS = [
    ProgressiveTaxBracket(min=Decimal('0'), max=Decimal('36000'), rate=Decimal('0.03'), quick_deduction=Decimal('0')),
    ProgressiveTaxBracket(min=Decimal('36000'), max=Decimal('144000'), rate=Decimal('0.10'), quick_deduction=Decimal('2520')),
    ProgressiveTaxBracket(min=Decimal('144000'), max=Decimal('300000'), rate=Decimal('0.20'), quick_deduction=Decimal('16920')),
    ProgressiveTaxBracket(min=Decimal('300000'), max=Decimal('420000'), rate=Decimal('0.25'), quick_deduction=Decimal('31920')),
    ProgressiveTaxBracket(min=Decimal('420000'), max=Decimal('660000'), rate=Decimal('0.30'), quick_deduction=Decimal('52920')),
    ProgressiveTaxBracket(min=Decimal('660000'), max=Decimal('960000'), rate=Decimal('0.35'), quick_deduction=Decimal('85920')),
    ProgressiveTaxBracket(min=Decimal('960000'), max=Decimal('999999999'), rate=Decimal('0.45'), quick_deduction=Decimal('181920')),
]

def calc_progressive_tax(amount: Decimal) -> tuple[Decimal, Decimal]:
    if amount <= 0:
        return Decimal('0'), Decimal('0')
    
    amount = _round(amount)
    
    for bracket in PROGRESSIVE_TAX_BRACKETS:
        if amount <= bracket['max']:
            tax = amount * bracket['rate'] - Decimal(str(bracket['quick_deduction']))
            tax = _round(max(Decimal('0'), tax))
            net = amount - tax
            return tax, net
    
    last_bracket = PROGRESSIVE_TAX_BRACKETS[-1]
    tax = amount * last_bracket['rate'] - Decimal(str(last_bracket['quick_deduction']))
    tax = _round(max(Decimal('0'), tax))
    net = amount - tax
    return tax, net

def calc_bonus_tax(bonus_amount: Decimal) -> tuple[Decimal, Decimal]:
    if bonus_amount <= 0:
        return Decimal('0'), Decimal('0')
    
    bonus_amount = _round(bonus_amount)
    
    monthly_equivalent = bonus_amount / Decimal('12')
    
    tax, _ = calc_progressive_tax(monthly_equivalent)
    
    annual_bonus_tax = tax * Decimal('12')
    annual_bonus_tax = _round(annual_bonus_tax)
    
    net = bonus_amount - annual_bonus_tax
    return annual_bonus_tax, net

def calc_dividend_tax(amount: Decimal, rate: Decimal = Decimal('0.20')) -> tuple[Decimal, Decimal]:
    if amount <= 0:
        return Decimal('0'), Decimal('0')
    
    amount = _round(amount)
    
    tax = amount * rate
    tax = _round(tax)
    
    net = amount - tax
    return tax, net

def calc_vat(price_gross: Decimal, vat_rate: Decimal) -> tuple[Decimal, Decimal]:
    if price_gross <= 0 or vat_rate <= 0:
        return Decimal('0'), Decimal('0')
    
    price_gross = _round(price_gross)
    vat_rate = _round(vat_rate)
    
    vat_amount = price_gross / (Decimal('1') + vat_rate) * vat_rate
    vat_amount = _round(vat_amount)
    
    price_net = price_gross - vat_amount
    price_net = _round(price_net)
    
    return vat_amount, price_net

def calc_surtax(vat_amount: Decimal, surtax_rate: Decimal) -> Decimal:
    if vat_amount <= 0 or surtax_rate <= 0:
        return Decimal('0')
    
    vat_amount = _round(vat_amount)
    surtax_rate = _round(surtax_rate)
    
    surtax_amount = vat_amount * surtax_rate
    surtax_amount = _round(surtax_amount)
    
    return surtax_amount

def calc_edge_friction(
    sender_code: str,
    receiver_code: str,
    amount: Decimal,
    mode: str,
    sender_vat_rate: Decimal,
    sender_surtax_rate: Decimal,
    sender_eit_rate: Decimal = None,
    receiver_pit_rate: Decimal = None,
    is_pre_tax: bool = True
) -> dict:
    if amount <= 0:
        return {
            'sender_code': sender_code,
            'receiver_code': receiver_code,
            'mode': mode,
            'input_amount': Decimal('0'),
            'vat_amount': Decimal('0'),
            'surtax_amount': Decimal('0'),
            'eit_amount': Decimal('0'),
            'pit_amount': Decimal('0'),
            'total_friction': Decimal('0'),
            'net_amount': Decimal('0'),
        }
    
    amount = _round(amount)
    total_friction = Decimal('0')
    
    vat_amount = Decimal('0')
    surtax_amount = Decimal('0')
    eit_amount = Decimal('0')
    pit_amount = Decimal('0')
    
    if is_pre_tax:
        if sender_vat_rate and sender_surtax_rate:
            vat_amount, price_net = calc_vat(amount, sender_vat_rate)
            surtax_amount = calc_surtax(vat_amount, sender_surtax_rate)
            
            total_friction = vat_amount + surtax_amount
            
            if sender_eit_rate:
                eit_amount = price_net * sender_eit_rate
                eit_amount = _round(eit_amount)
                total_friction += eit_amount
    else:
        if receiver_pit_rate:
            pit_amount = amount * receiver_pit_rate
            pit_amount = _round(pit_amount)
            total_friction = pit_amount
    
    net_amount = amount - total_friction
    net_amount = _round(net_amount)
    
    return {
        'sender_code': sender_code,
        'receiver_code': receiver_code,
        'mode': mode,
        'input_amount': amount,
        'vat_amount': vat_amount,
        'surtax_amount': surtax_amount,
        'eit_amount': eit_amount,
        'pit_amount': pit_amount,
        'total_friction': total_friction,
        'net_amount': net_amount,
    }

def calc_comprehensive_income_tax(
    salary: Decimal,
    bonus: Decimal,
    service_income: Decimal,
    dividend: Decimal
) -> dict:
    salary_tax, salary_net = calc_progressive_tax(salary) if salary > 0 else (Decimal('0'), Decimal('0'))
    
    bonus_tax, bonus_net = calc_bonus_tax(bonus) if bonus > 0 else (Decimal('0'), Decimal('0'))
    
    service_tax, service_net = calc_progressive_tax(service_income) if service_income > 0 else (Decimal('0'), Decimal('0'))
    
    combined_income = salary + service_income
    combined_tax, combined_net = calc_progressive_tax(combined_income)
    
    salary_tax_adjusted = combined_tax if (salary + service_income) > 0 else Decimal('0')
    service_tax_adjusted = Decimal('0')
    
    if combined_income > 0 and (salary + service_income) > 0:
        ratio = salary / combined_income if combined_income > 0 else Decimal('0')
        salary_tax_adjusted = _round(combined_tax * ratio)
        service_tax_adjusted = _round(combined_tax * (Decimal('1') - ratio))
    
    dividend_tax, dividend_net = calc_dividend_tax(dividend) if dividend > 0 else (Decimal('0'), Decimal('0'))
    
    total_tax = salary_tax_adjusted + service_tax_adjusted + bonus_tax + dividend_tax
    total_tax = _round(total_tax)
    
    total_income = salary + bonus + service_income + dividend
    total_net = total_income - total_tax
    
    return {
        'salary': salary,
        'salary_tax': salary_tax_adjusted,
        'salary_net': salary - salary_tax_adjusted,
        'bonus': bonus,
        'bonus_tax': bonus_tax,
        'bonus_net': bonus_net,
        'service_income': service_income,
        'service_tax': service_tax_adjusted,
        'service_net': service_income - service_tax_adjusted,
        'dividend': dividend,
        'dividend_tax': dividend_tax,
        'dividend_net': dividend_net,
        'total_income': total_income,
        'total_tax': total_tax,
        'total_net': total_net,
        'effective_rate': _round(total_tax / total_income) if total_income > 0 else Decimal('0'),
    }
