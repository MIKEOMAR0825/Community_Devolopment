from datetime import datetime
from extensions import db


class Subscriber(db.Model):

    __tablename__ = "subscribers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):

        return f"<Subscriber {self.email}>"


# -----------------------------
# CONTACT
# -----------------------------

class ContactMessage(db.Model):

    __tablename__ = "contact_messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(255),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        nullable=False
    )

    phone = db.Column(
        db.String(100)
    )

    service = db.Column(
        db.String(255)
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
    
    


class Donation(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_id = db.Column(
        db.String(120),
        unique=True
    )

    donor_name = db.Column(
        db.String(150)
    )

    email = db.Column(
        db.String(150)
    )

    amount = db.Column(
        db.Float
    )

    payment_method = db.Column(
        db.String(50)
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )