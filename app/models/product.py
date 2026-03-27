from datetime import datetime, timezone

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(60), unique=True, nullable=False, index=True)
    internal_code = db.Column(db.String(40), nullable=True, index=True)
    description = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
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

    stock_request_items = db.relationship(
        "StockRequestItem",
        back_populates="product",
        lazy="dynamic",
    )
    collection_items = db.relationship(
        "CollectionItem",
        back_populates="product",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} barcode={self.barcode!r}>"
