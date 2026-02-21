from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from enum import Enum

class EntityType(Enum):
    COMPANY = "company"
    PARTNERSHIP = "partnership"
    INDIVIDUAL = "individual"

class TransferMode(Enum):
    PRE_TAX = "pre_tax"
    POST_TAX = "post_tax"
    DIVIDEND = "dividend"
    BONUS = "bonus"

@dataclass
class Entity:
    code: str
    name: str
    level: int
    entity_type: EntityType
    vat_rate: Optional[Decimal] = None
    surtax_rate: Optional[Decimal] = None
    eit_rate: Optional[Decimal] = None
    pit_rate: Optional[Decimal] = None
    is_vat_general_taxpayer: bool = False
    parent_code: Optional[str] = None
    description: str = ""
    
    def is_company(self) -> bool:
        return self.entity_type == EntityType.COMPANY
    
    def is_partnership(self) -> bool:
        return self.entity_type == EntityType.PARTNERSHIP
    
    def is_individual(self) -> bool:
        return self.entity_type == EntityType.INDIVIDUAL
    
    def can_transfer_to(self, target: 'Entity') -> bool:
        if self.level >= target.level:
            return False
        if target.level - self.level > 1:
            return False
        return True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Entity':
        entity_type_str = data.get('entity_type', 'company')
        if isinstance(entity_type_str, str):
            entity_type = EntityType(entity_type_str)
        else:
            entity_type = EntityType.COMPANY
        
        def to_decimal(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return Decimal(str(val))
            if isinstance(val, str):
                return Decimal(val) if val else None
            return val
        
        return cls(
            code=data['code'],
            name=data['name'],
            level=data['level'],
            entity_type=entity_type,
            vat_rate=to_decimal(data.get('vat_rate')),
            surtax_rate=to_decimal(data.get('surtax_rate')),
            eit_rate=to_decimal(data.get('eit_rate')),
            pit_rate=to_decimal(data.get('pit_rate')),
            is_vat_general_taxpayer=bool(data.get('is_vat_general_taxpayer', 0)),
            parent_code=data.get('parent_code'),
            description=data.get('description', ''),
        )

@dataclass
class FlowEdge:
    from_entity: Entity
    to_entity: Entity
    amount: Decimal
    mode: TransferMode = TransferMode.POST_TAX
    
    @property
    def is_pre_tax(self) -> bool:
        return self.mode == TransferMode.PRE_TAX
    
    @property
    def is_dividend(self) -> bool:
        return self.mode == TransferMode.DIVIDEND
    
    @property
    def is_bonus(self) -> bool:
        return self.mode == TransferMode.BONUS

@dataclass
class HHYRule:
    hhy_code: str
    rule_version: str
    allocations: dict
    income_nature: dict
    merge_policy: dict
    validation_rules: dict
    
    def get_allocation_ratio(self, individual_code: str) -> Decimal:
        ratio = self.allocations.get(individual_code, '0')
        if isinstance(ratio, str):
            return Decimal(ratio)
        return Decimal('0')
    
    def get_income_nature(self, individual_code: str) -> str:
        return self.income_nature.get(individual_code, 'comprehensive')
    
    def should_merge_to_szw(self) -> bool:
        return self.merge_policy.get('merge_to_szw', False)
    
    def should_apply_bonus_special_tax(self) -> bool:
        return self.merge_policy.get('bonus_special_tax', False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HHYRule':
        import json
        
        allocations = json.loads(data.get('allocations', '{}'))
        income_nature = json.loads(data.get('income_nature', '{}'))
        merge_policy = json.loads(data.get('merge_policy', '{}'))
        validation_rules = json.loads(data.get('validation_rules', '{}'))
        
        return cls(
            hhy_code=data['hhy_code'],
            rule_version=data['rule_version'],
            allocations=allocations,
            income_nature=income_nature,
            merge_policy=merge_policy,
            validation_rules=validation_rules,
        )

@dataclass
class FlowConstraint:
    from_company: str
    to_company: str
    max_amount: Decimal
    constraint_type: str = "annual_limit"
    rule_version: str = "v1.0"

@dataclass
class TaxResult:
    vat_amount: Decimal = Decimal('0')
    surtax_amount: Decimal = Decimal('0')
    eit_amount: Decimal = Decimal('0')
    pit_amount: Decimal = Decimal('0')
    total_friction: Decimal = Decimal('0')
    net_amount: Decimal = Decimal('0')
    
    def to_dict(self) -> dict:
        return {
            'vat_amount': str(self.vat_amount),
            'surtax_amount': str(self.surtax_amount),
            'eit_amount': str(self.eit_amount),
            'pit_amount': str(self.pit_amount),
            'total_friction': str(self.total_friction),
            'net_amount': str(self.net_amount),
        }

@dataclass
class IndividualTaxResult:
    code: str
    salary: Decimal = Decimal('0')
    salary_tax: Decimal = Decimal('0')
    bonus: Decimal = Decimal('0')
    bonus_tax: Decimal = Decimal('0')
    service_income: Decimal = Decimal('0')
    service_tax: Decimal = Decimal('0')
    dividend: Decimal = Decimal('0')
    dividend_tax: Decimal = Decimal('0')
    total_income: Decimal = Decimal('0')
    total_tax: Decimal = Decimal('0')
    total_net: Decimal = Decimal('0')
    effective_rate: Decimal = Decimal('0')
    
    @property
    def comprehensive_income(self) -> Decimal:
        return self.salary + self.service_income
    
    @property
    def comprehensive_tax(self) -> Decimal:
        return self.salary_tax + self.service_tax
    
    def to_dict(self) -> dict:
        return {
            'code': self.code,
            'salary': str(self.salary),
            'salary_tax': str(self.salary_tax),
            'bonus': str(self.bonus),
            'bonus_tax': str(self.bonus_tax),
            'service_income': str(self.service_income),
            'service_tax': str(self.service_tax),
            'dividend': str(self.dividend),
            'dividend_tax': str(self.dividend_tax),
            'total_income': str(self.total_income),
            'total_tax': str(self.total_tax),
            'total_net': str(self.total_net),
            'effective_rate': str(self.effective_rate),
        }
