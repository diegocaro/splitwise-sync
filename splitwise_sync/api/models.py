"""Data models for the Splitwise Sync API."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EmailData(BaseModel):
    """Model for email data received via API."""

    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Email sender address")
    date: datetime = Field(..., description="Email date ISO format")
    body: str = Field(..., description="Email body content (text or HTML)")


class ExpenseResponse(BaseModel):
    """Model for expense response."""

    success: bool = Field(
        ..., description="Whether the expense was created successfully"
    )
    expense_id: Optional[int] = Field(None, description="ID of the created expense")
    amount: Optional[float] = Field(None, description="Amount of the expense")
    description: Optional[str] = Field(None, description="Description of the expense")
    error: Optional[str] = Field(
        None, description="Error message if expense creation failed"
    )
    transaction: Optional[Dict[str, Any]] = Field(
        None, description="Transaction details extracted from the email"
    )
