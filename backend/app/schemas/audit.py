from pydantic import BaseModel, ConfigDict, Field


class AuditLogPublic(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str
    metadata: dict = Field(validation_alias="log_metadata")
    created_at: str

    model_config = ConfigDict(from_attributes=True)
