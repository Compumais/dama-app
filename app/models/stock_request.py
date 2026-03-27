import enum
from datetime import datetime, timezone

from app.extensions import db


class StockRequestStatus(str, enum.Enum):
    PENDENTE = "pendente"
    EM_SEPARACAO = "em_separacao"
    PRONTO = "pronto"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class StockRequest(db.Model):
    __tablename__ = "stock_requests"

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=False, index=True)
    requested_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum(StockRequestStatus, name="stock_request_status"),
        default=StockRequestStatus.PENDENTE,
        nullable=False,
        index=True,
    )
    notes = db.Column(db.Text, nullable=True)
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

    branch = db.relationship("Branch", back_populates="stock_requests")
    requested_by = db.relationship(
        "User",
        back_populates="created_stock_requests",
        foreign_keys=[requested_by_user_id],
    )
    items = db.relationship(
        "StockRequestItem",
        back_populates="stock_request",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    status_history = db.relationship(
        "RequestStatusHistory",
        back_populates="stock_request",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StockRequest id={self.id} status={self.status.value}>"
