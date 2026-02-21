# backend/services/__init__.py
from backend.services.tax_calculator import (
    calc_progressive_tax,
    calc_bonus_tax,
    calc_dividend_tax,
    calc_vat,
    calc_surtax,
    calc_edge_friction,
    calc_comprehensive_income_tax,
)

__all__ = [
    'calc_progressive_tax',
    'calc_bonus_tax',
    'calc_dividend_tax',
    'calc_vat',
    'calc_surtax',
    'calc_edge_friction',
    'calc_comprehensive_income_tax',
]
