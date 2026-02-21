from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from backend.models.entities import Entity, HHYRule, FlowConstraint, TransferMode, EntityType
from data.database import get_company_by_code, get_hhy_rule, get_flow_constraint, get_active_rule_version, get_all_companies

@dataclass
class GlobalState:
    rule_version: str = "v1.0"
    entities: dict[str, Entity] = field(default_factory=dict)
    hhy_rules: dict[str, HHYRule] = field(default_factory=dict)
    flow_constraints: dict[str, FlowConstraint] = field(default_factory=dict)
    initial_funds: dict[str, Decimal] = field(default_factory=dict)
    total_initial_amount: Decimal = Decimal('0')
    
    @classmethod
    def load_from_db(cls) -> 'GlobalState':
        state = cls()
        state.rule_version = get_active_rule_version()
        
        companies = get_all_companies()
        for company_data in companies:
            entity = Entity.from_dict(company_data)
            state.entities[entity.code] = entity
        
        for code in state.entities:
            hhy_rule = get_hhy_rule(code, state.rule_version)
            if hhy_rule:
                state.hhy_rules[code] = HHYRule.from_dict(hhy_rule)
        
        for from_code in state.entities:
            for to_code in state.entities:
                if from_code == to_code:
                    continue
                constraint = get_flow_constraint(from_code, to_code, state.rule_version)
                if constraint:
                    key = f"{from_code}->{to_code}"
                    state.flow_constraints[key] = FlowConstraint(
                        from_company=constraint['from_company'],
                        to_company=constraint['to_company'],
                        max_amount=Decimal(str(constraint['max_amount'])),
                        constraint_type=constraint.get('constraint_type', 'annual_limit'),
                        rule_version=constraint.get('rule_version', state.rule_version),
                    )
        
        return state
    
    def get_entity(self, code: str) -> Optional[Entity]:
        return self.entities.get(code)
    
    def get_hhy_rule(self, hhy_code: str) -> Optional[HHYRule]:
        return self.hhy_rules.get(hhy_code)
    
    def get_flow_constraint(self, from_code: str, to_code: str) -> Optional[FlowConstraint]:
        key = f"{from_code}->{to_code}"
        return self.flow_constraints.get(key)
    
    def set_initial_funds(self, pxa_amount: Decimal, pxu_amount: Decimal):
        self.initial_funds['PXA'] = pxa_amount
        self.initial_funds['PXU'] = pxu_amount
        self.total_initial_amount = pxa_amount + pxu_amount
    
    def get_children(self, parent_code: str) -> list[Entity]:
        parent = self.get_entity(parent_code)
        if not parent:
            return []
        return [e for e in self.entities.values() if e.parent_code == parent_code]
    
    def get_individuals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_individual()]
    
    def get_companies(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_company()]
    
    def validate_flow(self, from_code: str, to_code: str) -> tuple[bool, str]:
        from_entity = self.get_entity(from_code)
        to_entity = self.get_entity(to_code)
        
        if not from_entity or not to_entity:
            return False, "主体不存在"
        
        if not from_entity.can_transfer_to(to_entity):
            return False, f"资金流转违反层级约束: {from_code}({from_entity.level}) -> {to_code}({to_entity.level})"
        
        constraint = self.get_flow_constraint(from_code, to_code)
        if constraint:
            return True, "通过"
        
        return True, "通过"
    
    def get_source_entities(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.level == 1]
    
    def get_endpoint_entities(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_individual()]

@dataclass
class SimulationResult:
    flow_edges: list
    szw_net: Decimal = Decimal('0')
    sxp_net: Decimal = Decimal('0')
    total_tax: Decimal = Decimal('0')
    total_friction: Decimal = Decimal('0')
    szw_tax_detail: dict = field(default_factory=dict)
    sxp_tax_detail: dict = field(default_factory=dict)
    
    @property
    def total_net(self) -> Decimal:
        return self.szw_net + self.sxp_net
    
    @property
    def effective_rate(self) -> Decimal:
        if self.total_friction + self.total_net == 0:
            return Decimal('0')
        return self.total_friction / (self.total_friction + self.total_net)
    
    def to_dict(self) -> dict:
        return {
            'flow_edges': [edge.to_dict() for edge in self.flow_edges],
            'szw_net': str(self.szw_net),
            'sxp_net': str(self.sxp_net),
            'total_net': str(self.total_net),
            'total_tax': str(self.total_tax),
            'total_friction': str(self.total_friction),
            'effective_rate': str(self.effective_rate),
            'szw_tax_detail': self.szw_tax_detail,
            'sxp_tax_detail': self.sxp_tax_detail,
        }
