from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
