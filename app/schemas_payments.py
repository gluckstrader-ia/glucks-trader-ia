from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    plan: str


class CreateCheckoutResponse(BaseModel):
    checkout_url: str
    reference_id: str
    provider: str = "pagbank"