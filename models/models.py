# models.py
from datetime import datetime
import enum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    Float,
    Numeric,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy import Enum as SAEnum

Base = declarative_base()


# ---------------------------
# ENUMs
# ---------------------------
class NotificationChannel(enum.Enum):
    email = "email"
    sms = "sms"
    push = "push"


class TicketStatus(enum.Enum):
    en_cours = "en_cours"
    regle = "regle"


class PaymentStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class SubscriptionStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    canceled = "canceled"


class DeviceType(enum.Enum):
    ios = "ios"
    android = "android"
    web = "web"


# ---------------------------
# State
# ---------------------------

class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Relation inverse vers les utilisateurs
    users = relationship("User", back_populates="state")

    def __repr__(self) -> str:
        return f"<State id={self.id} name={self.name}>"




# ---------------------------
# USERS
# ---------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)

    # ✅ Clé étrangère vers State
    state_id = Column(Integer, ForeignKey("states.id"))  # 👈 clé étrangère correcte
    state = relationship("State", back_populates="users")

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    abonnement_finish = Column(DateTime(timezone=True), nullable=True)  # Date de fin de l'abonnement actif

    # Relations existantes
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    device_tokens = relationship("UserDeviceToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


# ---------------------------
# PLANS (plans de souscription)
# ---------------------------
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # e.g., "basic_monthly", "premium_yearly"
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False) # e.g., 30 for monthly, 365 for yearly
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relation inverse vers les abonnements
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self) -> str:
        return f"<Plan id={self.id} name={self.name} price={self.price}>"


# ---------------------------
# SUBSCRIPTIONS (abonnements)
# ---------------------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    payment_status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.paid, nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} user_id={self.user_id} plan_id={self.plan_id}>"


# ---------------------------
# TICKETS (contraventions)
# ---------------------------
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_number = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    amount_usd = Column(Numeric(10, 2), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    dispute_url = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=True)
    payment_url = Column(String(255), nullable=True)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.en_cours, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    user = relationship("User", back_populates="tickets")
    payments = relationship("Payment", back_populates="ticket", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="ticket", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} ticket_number={self.ticket_number} user_id={self.user_id}>"


# ---------------------------
# PAYMENTS (pour ticket ou abonnement)
# ---------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    amount_usd = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(SAEnum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    payment_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    ticket = relationship("Ticket", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self) -> str:
        target = "ticket" if self.ticket_id else "subscription"
        return f"<Payment id={self.id} amount={self.amount_usd} target={target}>"


# ---------------------------
# REMINDERS (configuration des rappels)
# ---------------------------
class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    frequency_days = Column(Integer, default=7, nullable=False)  # ex: 7 = hebdomadaire
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    ticket = relationship("Ticket", back_populates="reminders")
    notification_channels = relationship("ReminderChannel", back_populates="reminder", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} ticket_id={self.ticket_id} freq={self.frequency_days}>"


# ---------------------------
# REMINDER CHANNELS (canaux de notification pour les rappels)
# ---------------------------
class ReminderChannel(Base):
    __tablename__ = "reminder_channels"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(SAEnum(NotificationChannel, name="notification_channel"), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    reminder = relationship("Reminder", back_populates="notification_channels")

    def __repr__(self) -> str:
        return f"<ReminderChannel id={self.id} reminder_id={self.reminder_id} channel={self.channel.value}>"


# ---------------------------
# NOTIFICATIONS (logs)
# ---------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(SAEnum(NotificationChannel, name="notification_channel"), nullable=False)
    message = Column(Text, nullable=False)
    subject = Column(String(255), nullable=True)  # Pour les emails
    status = Column(String(20), default="pending", nullable=False)  # pending, sent, failed
    error_message = Column(Text, nullable=True)  # En cas d'échec
    sent_at = Column(DateTime(timezone=True), nullable=True)  # NULL si pas encore envoyé
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    user = relationship("User", back_populates="notifications")
    ticket = relationship("Ticket", back_populates="notifications")
    reminder = relationship("Reminder")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} channel={self.channel.value} status={self.status}>"


# ---------------------------
# USER DEVICE TOKENS (pour les notifications push)
# ---------------------------
class UserDeviceToken(Base):
    __tablename__ = "user_device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_token = Column(String(255), unique=True, nullable=False, index=True)
    device_type = Column(SAEnum(DeviceType, name="device_type"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relation
    user = relationship("User", back_populates="device_tokens")

    def __repr__(self) -> str:
        return f"<UserDeviceToken id={self.id} user_id={self.user_id} type={self.device_type.value}>"


# ---------------------------
# Indexes / Table args (optimisations simples)
# ---------------------------
# Indexes are already created via index=True on columns above.


# ---------------------------
# PASSWORD RESET TOKENS
# ---------------------------
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relation
    user = relationship("User", back_populates="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id} expires_at={self.expires_at}>"


# ---------------------------
# EMAIL VERIFICATION CODES (pour les inscriptions et autres vérifications)
# ---------------------------
class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<EmailVerificationCode email={self.email} expires_at={self.expires_at}>"


# If you want composite indexes or additional tuning, add them here:
# Example: Index('ix_ticket_user_ticketnum', Ticket.user_id, Ticket.ticket_number)

# ---------------------------
# End of models.py
# ---------------------------
