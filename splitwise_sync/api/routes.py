"""API endpoints for Splitwise transaction sync."""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from splitwise_sync.api.models import EmailData, ExpenseResponse
from splitwise_sync.email_parser.email_client import EmailMessage
from splitwise_sync.email_parser.receipt_parser import ReceiptParser
from splitwise_sync.splitwise_api.splitwise_client import SplitwiseClient

logger = logging.getLogger(__name__)


api_router = APIRouter(prefix="/api", tags=["api"])


@api_router.post(
    "/process-email",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def process_email(email_data: EmailData) -> ExpenseResponse:
    """Process an email and create a Splitwise expense.

    Args:
        email_data: Email data to process

    Returns:
        Response with details of the created expense or error
    """
    try:

        email = EmailMessage(
            id="api-request",
            subject=email_data.subject,
            sender=email_data.sender,
            date=email_data.date,
            body=email_data.body,
        )

        logger.info(f"Processing email via API: {email.subject}")

        receipt_parser = ReceiptParser()
        transaction = receipt_parser.parse_email(email)

        if transaction.amount == 0:
            logger.warning("Parsed transaction is empty or amount is zero")

        splitwise_client = SplitwiseClient()
        expense_data = transaction.to_splitwise_expense()
        created_expense = splitwise_client.create_expense(expense_data)

        # Return successful response with expense details
        return ExpenseResponse(
            success=True,
            expense_id=created_expense.getId(),
            amount=float(created_expense.cost),
            description=created_expense.description,
            error=None,
            transaction=transaction.to_dict(),
        )

    except Exception as e:
        logger.exception("Error processing email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@api_router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, str],
)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""

    splitwise_client = SplitwiseClient()
    ret = splitwise_client.check_systems()
    if not ret:
        return {"status": "error", "message": "Splitwise Sync API is not reachable"}
    return {"status": "ok", "message": "Splitwise Sync API is running"}
