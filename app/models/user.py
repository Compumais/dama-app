from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=True, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

    role = db.relationship("Role", back_populates="users")
    branch = db.relationship("Branch", back_populates="users")

    created_stock_requests = db.relationship(
        "StockRequest",
        back_populates="requested_by",
        foreign_keys="StockRequest.requested_by_user_id",
        lazy="dynamic",
    )
    status_changes = db.relationship(
        "RequestStatusHistory",
        back_populates="changed_by",
        foreign_keys="RequestStatusHistory.changed_by_user_id",
        lazy="dynamic",
    )
    collections = db.relationship(
        "Collection",
        back_populates="user",
        foreign_keys="Collection.user_id",
        lazy="dynamic",
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
