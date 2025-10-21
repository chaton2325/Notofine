-- ===========================================================
-- Base de données : contravention_db
-- Description : Application mobile de rappel de paiement de contraventions
-- ===========================================================

-- 1️⃣ USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================
-- 2️⃣ SUBSCRIPTIONS
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(50) DEFAULT 'basic',
    amount_usd NUMERIC(10,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'paid',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    auto_renew BOOLEAN DEFAULT FALSE
);

-- ===========================================================
-- 3️⃣ TICKETS
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticket_number VARCHAR(50) NOT NULL,
    description TEXT,
    image_url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'en_cours',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================
-- 4️⃣ PAYMENTS
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    amount_usd NUMERIC(10,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, completed
    payment_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================
-- 5️⃣ REMINDERS
CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    frequency_days INTEGER DEFAULT 7,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================
-- 5️⃣.1 REMINDER CHANNELS (canaux de notification pour les rappels)
CREATE TABLE reminder_channels (
    id SERIAL PRIMARY KEY,
    reminder_id INTEGER NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================
-- 6️⃣ NOTIFICATIONS
CREATE TYPE notification_channel AS ENUM ('email', 'sms', 'push');

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticket_id INTEGER REFERENCES tickets(id) ON DELETE SET NULL,
    reminder_id INTEGER REFERENCES reminders(id) ON DELETE SET NULL,
    channel notification_channel NOT NULL,
    message TEXT NOT NULL,
    subject VARCHAR(255), -- Pour les emails
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed
    error_message TEXT, -- En cas d'échec
    sent_at TIMESTAMP, -- NULL si pas encore envoyé
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================
-- 7️⃣ INDEX POUR PERFORMANCE
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_tickets_ticket_number ON tickets(ticket_number);
CREATE INDEX idx_payments_ticket_id ON payments(ticket_id);
CREATE INDEX idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX idx_reminders_user_id ON reminders(user_id);
CREATE INDEX idx_reminder_channels_reminder_id ON reminder_channels(reminder_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_ticket_id ON notifications(ticket_id);
CREATE INDEX idx_notifications_reminder_id ON notifications(reminder_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
