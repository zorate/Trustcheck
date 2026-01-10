from pydantic import BaseModel
from uuid import UUID

class IDResponse(BaseModel):
    id: UUID
