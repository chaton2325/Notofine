# 🚀 API Notofine

API de gestion des contraventions avec système de notifications automatisées.

## 📋 Fonctionnalités

- ✅ **Authentification** : Inscription et connexion sécurisées
- ✅ **Gestion des utilisateurs** : Profils avec localisation (état)
- ✅ **Système de rappels** : Notifications automatiques
- ✅ **Multi-canaux** : Email, SMS, Push notifications
- ✅ **API REST** : Documentation interactive

## 🛠️ Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration de la base de données

```bash
# Créer la base de données
psql -U postgres -c "CREATE DATABASE notofine_db;"

# Exécuter le schéma
psql -U postgres -d notofine_db -f database/databaseoneschema.sql

# Si vous avez des données existantes, exécuter la migration
psql -U postgres -d notofine_db -f database/migration_add_state_to_users.sql
```

### 3. Configuration des variables d'environnement

```bash
# Copier le fichier de configuration
cp config.env.example .env

# Modifier les valeurs dans .env
```

### 4. Démarrer l'API

```bash
# Méthode 1: Script de démarrage
python run_api.py

# Méthode 2: Uvicorn directement
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 Documentation de l'API

Une fois l'API démarrée, accédez à :

- **Documentation interactive** : http://localhost:8000/docs
- **Documentation alternative** : http://localhost:8000/redoc

## 🔐 Endpoints d'authentification

### Inscription
```http
POST /auth/register
Content-Type: application/json

{
    "full_name": "Jean Dupont",
    "email": "jean@example.com",
    "password": "motdepasse123",
    "phone": "+33123456789",
    "state": "Île-de-France"
}
```

### Connexion
```http
POST /auth/login
Content-Type: application/json

{
    "email": "jean@example.com",
    "password": "motdepasse123"
}
```

### Profil utilisateur
```http
GET /auth/me
Authorization: Bearer <token>
```

### Mise à jour du profil
```http
PUT /auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
    "full_name": "Jean Dupont Modifié",
    "state": "Provence-Alpes-Côte d'Azur"
}
```

## 📱 Endpoints de gestion

### Créer un rappel
```http
POST /users/{user_id}/reminders
Content-Type: application/json

{
    "frequency_days": 7,
    "channels": ["email", "sms"]
}
```

### Envoyer une notification
```http
POST /notifications/send
Content-Type: application/json

{
    "user_id": 1,
    "message": "Votre contravention est due",
    "channel": "email",
    "subject": "Rappel de paiement"
}
```

### Consulter les notifications
```http
GET /users/{user_id}/notifications?limit=10
```

## 🔧 Configuration

### Variables d'environnement importantes

- `SECRET_KEY` : Clé secrète pour JWT (changez en production)
- `DATABASE_URL` : URL de connexion à la base de données
- `SMTP_*` : Configuration pour l'envoi d'emails
- `TWILIO_*` : Configuration pour l'envoi de SMS

## 🚀 Déploiement

### Production

```bash
# Installer les dépendances de production
pip install -r requirements.txt

# Démarrer avec Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (optionnel)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Structure du projet

```
Notofine/
├── controller/           # Contrôleurs API
│   ├── __init__.py
│   └── auth_controller.py
├── database/            # Schémas et migrations
│   ├── databaseoneschema.sql
│   └── migration_add_state_to_users.sql
├── models/             # Modèles SQLAlchemy
│   └── models.py
├── main.py             # Application FastAPI
├── run_api.py          # Script de démarrage
├── requirements.txt    # Dépendances Python
└── config.env.example # Configuration
```

## 🐛 Dépannage

### Erreurs courantes

1. **Erreur de connexion à la base de données**
   - Vérifiez `DATABASE_URL` dans `.env`
   - Assurez-vous que PostgreSQL est démarré

2. **Erreur d'import**
   - Vérifiez que tous les modules sont installés
   - Vérifiez les chemins d'import

3. **Erreur JWT**
   - Vérifiez que `SECRET_KEY` est défini
   - Utilisez un token valide pour les routes protégées

## 📞 Support

Pour toute question ou problème, consultez la documentation interactive à http://localhost:8000/docs
