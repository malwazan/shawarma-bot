"""Half Million Coffee Shop tools for the voice agent: orders and complaints.

Demo implementations: they validate the input and return a random 4-digit
number instead of calling a real ordering or ticketing system.
"""

import random
from typing import Annotated, Literal

import phonenumbers
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools import Tool
from pydantic import BaseModel, Field

Size = Literal["small", "medium", "large"]
OrderType = Literal["pickup", "delivery"]

PhoneNumber = Annotated[
    str,
    Field(
        description=(
            "The customer's mobile number, as they said it, e.g. 0551234567 or "
            "+966551234567. Read it back to the customer to confirm it first."
        )
    ),
]


def normalize_phone(raw: str) -> str:
    """E.164 (+9665XXXXXXXX). Saudi numbers may be given in local form (05...).
    Raises ToolError, which the agent sees, so it can ask the customer again."""
    try:
        number = phonenumbers.parse(raw, "SA")
    except phonenumbers.NumberParseException:
        number = None
    if number is None or not phonenumbers.is_valid_number(number):
        raise ToolError(
            f"'{raw}' is not a valid phone number. Ask the customer to repeat it."
        )
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def four_digit_number() -> str:
    return str(random.randint(1000, 9999))


# -- create_order -------------------------------------------------------------


class OrderCreated(BaseModel):
    order_number: str
    coffee_name: str
    size: Size | None
    order_type: OrderType
    phone_number: str


async def create_order_fn(
    coffee_name: Annotated[
        str,
        Field(
            min_length=1,
            description="The drink to order, as the customer named it, e.g. 'Spanish latte'.",
        ),
    ],
    order_type: Annotated[
        OrderType,
        Field(description="Whether the customer will pick the order up or wants it delivered."),
    ],
    phone_number: PhoneNumber,
    size: Annotated[
        Size | None,
        Field(
            description=(
                "Cup size. Ask the customer for it; leave it out only for items "
                "that come in a single size."
            )
        ),
    ] = None,
) -> OrderCreated:
    return OrderCreated(
        order_number=four_digit_number(),
        coffee_name=coffee_name.strip(),
        size=size,
        order_type=order_type,
        phone_number=normalize_phone(phone_number),
    )


create_order_tool = Tool.from_function(
    create_order_fn,
    name="create_order",
    description=(
        "Place a coffee order for the customer at Half Million. Call it only "
        "once you have every detail and the customer has confirmed them: the "
        "coffee name, its size (unless the item comes in one size only), "
        "pickup or delivery, and their phone number. Returns the order number "
        "to give to the customer."
    ),
)


# -- create_complaint ---------------------------------------------------------


class ComplaintCreated(BaseModel):
    complaint_id: str
    customer_name: str
    phone_number: str
    complaint_details: str


async def create_complaint_fn(
    customer_name: Annotated[str, Field(min_length=1, description="The customer's name.")],
    phone_number: PhoneNumber,
    complaint_details: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "What went wrong, in the customer's words and summarised clearly: "
                "what happened, which branch, and when, if the customer said."
            ),
        ),
    ],
) -> ComplaintCreated:
    return ComplaintCreated(
        complaint_id=four_digit_number(),
        customer_name=customer_name.strip(),
        phone_number=normalize_phone(phone_number),
        complaint_details=complaint_details.strip(),
    )


create_complaint_tool = Tool.from_function(
    create_complaint_fn,
    name="create_complaint",
    description=(
        "Register a complaint from the customer with Half Million customer care. "
        "Call it once you have the customer's name, their phone number and a "
        "clear description of the problem, and the customer has confirmed them. "
        "Returns the complaint ID to give to the customer."
    ),
)


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(create_order_tool)
    mcp.add_tool(create_complaint_tool)
