# Système de Notifications - Notofine

## Vue d'ensemble

Le système de notifications de Notofine permet d'envoyer des rappels automatiques aux utilisateurs selon leurs préférences de canal (email, SMS, push). L'application s'adapte aux choix de l'utilisateur pour chaque type de notification.

## Architecture

### Modèles de données

#### 1. **Reminder** (Rappels)
- `id`: Identifiant unique
- `user_id`: ID de l'utilisateur
- `frequency_days`: Fréquence en jours (ex: 7 = hebdomadaire)
- `active`: Statut actif/inactif
- `created_at`: Date de création

#### 2. **ReminderChannel** (Canaux de rappel)
- `id`: Identifiant unique
- `reminder_id`: ID du rappel associé
- `channel`: Canal (email, sms, push)
- `enabled`: Canal activé/désactivé
- `created_at`: Date de création

#### 3. **Notification** (Logs des notifications)
- `id`: Identifiant unique
- `user_id`: ID de l'utilisateur
- `ticket_id`: ID du ticket (optionnel)
- `reminder_id`: ID du rappel (optionnel)
- `channel`: Canal utilisé
- `message`: Message envoyé
- `subject`: Sujet (pour emails)
- `status`: Statut (pending, sent, failed)
- `error_message`: Message d'erreur (si échec)
- `sent_at`: Date d'envoi
- `created_at`: Date de création

## Fonctionnalités

### 1. Configuration des canaux par utilisateur

Chaque utilisateur peut configurer ses préférences de notification :

```python
# Créer un rappel avec plusieurs canaux
POST /users/{user_id}/reminders
{
    "frequency_days": 7,
    "channels": ["email", "sms", "push"]
}
```

### 2. Envoi automatique de rappels

Le système traite automatiquement les rappels selon la fréquence configurée :

```python
# Traiter tous les rappels en attente
POST /reminders/process
```

### 3. Envoi manuel de notifications

```python
# Envoyer une notification spécifique
POST /notifications/send
{
    "user_id": 1,
    "message": "Votre contravention est due",
    "channel": "email",
    "subject": "Rappel de paiement",
    "ticket_id": 123
}
```

### 4. Consultation des notifications

```python
# Récupérer les notifications d'un utilisateur
GET /users/{user_id}/notifications?limit=10

# Récupérer les rappels d'un utilisateur
GET /users/{user_id}/reminders
```

## Service de Notification

### NotificationService

La classe `NotificationService` centralise toute la logique d'envoi :

```python
from fonctions_utiles import NotificationService

service = NotificationService(db_session)

# Envoyer une notification
success = service.send_notification(
    user_id=1,
    message="Rappel de paiement",
    channel=NotificationChannel.email,
    subject="Contravention due"
)
```

### Canaux supportés

1. **Email** : Envoi via SMTP (à configurer)
2. **SMS** : Envoi via service SMS (Twilio, etc.)
3. **Push** : Notifications push via Firebase Cloud Messaging

## Configuration

### Base de données

Le schéma SQL est disponible dans `database/databaseoneschema.sql`. Exécutez-le pour créer les tables :

```sql
-- Créer les tables
\i database/databaseoneschema.sql
```

### Services externes

Pour activer l'envoi réel des notifications, configurez :

1. **SMTP** (pour emails) dans `fonctions_utiles.py`
2. **Service SMS** (Twilio, etc.) dans `_send_sms()`
3. **Firebase** (pour push) dans `_send_push_notification()`

## Exemples d'utilisation

### 1. Créer un utilisateur avec rappels

```python
# 1. Créer un utilisateur
user = User(
    full_name="Jean Dupont",
    email="jean@example.com",
    phone="+33123456789",
    password_hash="hashed_password"
)

# 2. Créer un rappel hebdomadaire
reminder = Reminder(
    user_id=user.id,
    frequency_days=7,
    active=True
)

# 3. Configurer les canaux
channels = [
    ReminderChannel(reminder_id=reminder.id, channel=NotificationChannel.email, enabled=True),
    ReminderChannel(reminder_id=reminder.id, channel=NotificationChannel.sms, enabled=True)
]
```

### 2. Traitement automatique

```python
# Script de traitement des rappels (à exécuter périodiquement)
from fonctions_utiles import process_reminders

results = process_reminders(db_session)
print(f"Traité {results['processed']} rappels")
print(f"Envoyé via: {results['channels']}")
```

### 3. Notification pour un ticket

```python
# Envoyer une notification pour un ticket spécifique
service = NotificationService(db_session)
results = service.send_ticket_notification(
    ticket_id=123,
    message="Votre contravention #ABC123 est due",
    subject="Rappel de paiement"
)
```

## Monitoring

### Statuts des notifications

- `pending` : En attente d'envoi
- `sent` : Envoyée avec succès
- `failed` : Échec de l'envoi

### Logs

Toutes les notifications sont loggées dans la table `notifications` avec :
- Le canal utilisé
- Le statut d'envoi
- Les messages d'erreur (si applicable)
- Les timestamps

## Sécurité

- Les mots de passe sont hashés
- Les tokens FCM doivent être stockés de manière sécurisée
- Les clés API des services externes doivent être protégées
- Validation des entrées utilisateur

## Performance

- Index sur les colonnes fréquemment utilisées
- Requêtes optimisées avec relations SQLAlchemy
- Traitement par batch pour les rappels
- Cache des préférences utilisateur (optionnel)

## Déploiement

1. Configurer la base de données PostgreSQL
2. Installer les dépendances Python
3. Configurer les services externes (SMTP, SMS, Push)
4. Déployer l'API FastAPI
5. Configurer un cron job pour le traitement des rappels

```bash
# Exemple de cron job (toutes les heures)
0 * * * * /usr/bin/python3 /path/to/process_reminders.py
```
