from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional, Literal, Dict

class TransactionModel(BaseModel):
    envelope_id: int
    amount: float = Field(gt=0, description="Amount must be strictly greater than zero")
    transaction_date: date
    note: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def force_two_decimals(cls, value: float) -> float:
        return round(value, 2)
    
class EnvelopeModel(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    allocated_amount: float = Field(ge=0)
    
class LoanModel(BaseModel):
    person_name: str = Field(min_length=1, description="Cannot be an empty string")
    principal_amount: float = Field(gt=0, description="Debt must be greater than zero")
    loan_type: Literal['Lent', 'Borrowed']
    created_at: date
    
    @field_validator('principal_amount')
    @classmethod
    def force_two_decimals(cls, value: float) -> float:
        return round(value, 2)
    
class LoanRepaymentModel(BaseModel):
    loan_id: int
    amount: float = Field(gt=0, description="Repayment must be strictly greater than zero")
    
    @field_validator('amount')
    @classmethod
    def force_two_decimals(cls, value: float) -> float:
        return round(value, 2)
    
class IncomeAllocationModel(BaseModel):
    
    allocations: Dict[int, float]
    
    @field_validator('allocations')
    @classmethod
    def validate_positive_distribution(cls, value: Dict[int, float]) -> Dict[int, float]:
        """System Protocol: Prevents negative fund allocation."""
        for env_id, amount in value.items():
            if amount <= 0:
                raise ValueError(f"Allocation for envelope {env_id} must be strictly greater than zero.")
            
            value[env_id] = round(amount, 2)
            
        return value
    
class TaskModel(BaseModel):
    description: str = Field(min_length=1, max_length=255, description="Task cannot be empty")
    due_date: Optional[date] = None
    is_completed: bool = False