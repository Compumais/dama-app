import enum
from datetime import datetime, timezone

from app.extensions import db


class CollectionStatus(str, enum.Enum):
    ABERTA = "aberta"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class Collection(db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=True, index=True)
    status = db.Column(
        db.Enum(CollectionStatus, name="collection_status"),
        default=CollectionStatus.ABERTA,
        nullable=False,
        index=True,
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", back_populates="collections", foreign_keys=[user_id])
    branch = db.relationship("Branch", back_populates="collections")
    items = db.relationship(
        "CollectionItem",
        back_populates="collection",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Collection id={self.id} status={self.status.value}>"
