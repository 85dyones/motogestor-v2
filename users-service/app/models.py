from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()


class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token_type = db.Column(db.String(20), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    reason = db.Column(db.String(255))


class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # espaço pra evoluir: slug, cnpj, etc

    plan = db.Column(db.String(50), default="BASIC")  # plano por tenant


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    role = db.Column(db.String(50), default="OWNER")
    plan = db.Column(db.String(50), default="BASIC")

    tenant = db.relationship("Tenant", backref="users")
