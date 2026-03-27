from datetime import datetime, timezone

from app.extensions import db


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
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

    users = db.relationship("User", back_populates="branch", lazy="dynamic")
    stock_requests = db.relationship(
        "StockRequest", back_populates="branch", lazy="dynamic"
    )
    collections = db.relationship("Collection", back_populates="branch", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Branch id={self.id} code={self.code!r}>"
