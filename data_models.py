from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional, Literal

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