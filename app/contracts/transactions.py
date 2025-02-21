from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class Transaction(BaseModel):
    title: str = Field(..., description="Nome ou título da transação")
    description: Optional[str] = Field(None, description="Detalhes adicionais sobre a transação")
    type: TransactionType = Field(..., description="INCOME ou EXPENSE")
    amount: float = Field(..., description="Valor da transação")
    paidDate: datetime = Field(..., description="Data e hora (ISO) em que a transação foi paga")
    dueDate: Optional[datetime] = Field(None, description="Data e hora (ISO) para vencimento da transação")
    categories: Optional[List[str]] = Field(None, description="Lista de categorias associadas à transação")
