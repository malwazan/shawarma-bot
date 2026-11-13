from uuid import UUID

from pydantic import BaseModel


class LiveKitRoomMetadata(BaseModel):
    call_id: UUID
    from_: str
    to: str

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "LiveKitRoomMetadata":
        return cls.model_validate_json(raw)


class LiveKitAgentInit(BaseModel):
    room_name: str
    livekit_token: str
    room_metadata: str

    def parse_room_metadata(self) -> "LiveKitRoomMetadata":
        return LiveKitRoomMetadata.from_json(self.room_metadata)


class CallMetadata(BaseModel):
    call_id: UUID
    from_: str
    to: str
