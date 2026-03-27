from datetime import datetime, timezone

from app.extensions import db


class StockRequestItem(db.Model):
    __tablename__ = "stock_request_items"

    id = db.Column(db.Integer, primary_key=True)
    stock_request_id = db.Column(
        db.Integer,
        db.ForeignKey("stock_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    scanned_code = db.Column(db.String(60), nullable=False, index=True)
    quantity = db.Column(db.Numeric(10, 3), nullable=False, default=1)
    notes = db.Column(db.String(255), nullable=True)
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

    stock_request = db.relationship("StockRequest", back_populates="items")
    product = db.relationship("Product", back_populates="stock_request_items")

    def __repr__(self) -> str:
        return f"<StockRequestItem id={self.id} request_id={self.stock_request_id}>"
