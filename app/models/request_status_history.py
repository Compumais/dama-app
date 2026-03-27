from datetime import datetime, timezone

from app.extensions import db
from app.models.stock_request import StockRequestStatus


class RequestStatusHistory(db.Model):
    __tablename__ = "request_status_history"

    id = db.Column(db.Integer, primary_key=True)
    stock_request_id = db.Column(
        db.Integer,
        db.ForeignKey("stock_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_status = db.Column(
        db.Enum(StockRequestStatus, name="stock_request_status"),
        nullable=True,
    )
    new_status = db.Column(
        db.Enum(StockRequestStatus, name="stock_request_status"),
        nullable=False,
        index=True,
    )
    changed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    notes = db.Column(db.String(255), nullable=True)
    changed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    stock_request = db.relationship("StockRequest", back_populates="status_history")
    changed_by = db.relationship(
        "User",
        back_populates="status_changes",
        foreign_keys=[changed_by_user_id],
    )

    def __repr__(self) -> str:
        return f"<RequestStatusHistory id={self.id} request_id={self.stock_request_id}>"
