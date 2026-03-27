from datetime import datetime, timezone

from app.extensions import db


class CollectionItem(db.Model):
    __tablename__ = "collection_items"

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    scanned_code = db.Column(db.String(60), nullable=False, index=True)
    quantity = db.Column(db.Numeric(10, 3), nullable=False, default=1)
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

    collection = db.relationship("Collection", back_populates="items")
    product = db.relationship("Product", back_populates="collection_items")

    def __repr__(self) -> str:
        return f"<CollectionItem id={self.id} collection_id={self.collection_id}>"
