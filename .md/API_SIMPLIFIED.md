# 🔐 API Notofine - Version Simplifiée

API d'authentification simplifiée basée sur l'email uniquement (sans JWT).

## 📋 Endpoints disponibles

### 🔑 Authentification

#### 1. Inscription
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

**Réponse :**
```json
{
    "id": 1,
    "full_name": "Jean Dupont",
    "email": "jean@example.com",
    "phone": "+33123456789",
    "state": "Île-de-France",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00"
}
```

#### 2. Connexion
```http
POST /auth/login
Content-Type: application/json

{
    "email": "jean@example.com",
    "password": "motdepasse123"
}
```

**Réponse :**
```json
{
    "user": {
        "id": 1,
        "full_name": "Jean Dupont",
        "email": "jean@example.com",
        "phone": "+33123456789",
        "state": "Île-de-France",
        "is_active": true,
        "created_at": "2024-01-01T10:00:00"
    },
    "message": "Connexion réussie"
}
```

#### 3. Récupérer un utilisateur par email
```http
GET /auth/user/{email}
```

**Exemple :**
```http
GET /auth/user/jean@example.com
```

**Réponse :**
```json
{
    "id": 1,
    "full_name": "Jean Dupont",
    "email": "jean@example.com",
    "phone": "+33123456789",
    "state": "Île-de-France",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00"
}
```

#### 4. Mettre à jour un utilisateur par email
```http
PUT /auth/user/{email}
Content-Type: application/json

{
    "full_name": "Jean Dupont Modifié",
    "phone": "+33987654321",
    "state": "Provence-Alpes-Côte d'Azur"
}
```

#### 5. Déconnexion
```http
POST /auth/logout
```

**Réponse :**
```json
{
    "message": "Déconnexion réussie"
}
```

## 🎯 Utilisation côté Frontend

### Exemple avec JavaScript/Fetch

```javascript
// 1. Inscription
const registerUser = async (userData) => {
    const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    });
    return await response.json();
};

// 2. Connexion
const loginUser = async (email, password) => {
    const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
    });
    return await response.json();
};

// 3. Récupérer les infos utilisateur
const getUserInfo = async (email) => {
    const response = await fetch(`/auth/user/${email}`);
    return await response.json();
};

// 4. Mettre à jour le profil
const updateUserProfile = async (email, updates) => {
    const response = await fetch(`/auth/user/${email}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
    });
    return await response.json();
};
```

### Exemple avec Axios

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000'
});

// Inscription
const register = (userData) => api.post('/auth/register', userData);

// Connexion
const login = (email, password) => api.post('/auth/login', { email, password });

// Récupérer utilisateur
const getUser = (email) => api.get(`/auth/user/${email}`);

// Mettre à jour
const updateUser = (email, updates) => api.put(`/auth/user/${email}`, updates);
```

## 🔧 Gestion des erreurs

### Codes d'erreur courants

- **400** : Données invalides (email déjà utilisé, etc.)
- **401** : Email/mot de passe incorrect
- **404** : Utilisateur non trouvé
- **500** : Erreur serveur

### Exemple de gestion d'erreur

```javascript
try {
    const user = await loginUser('jean@example.com', 'password123');
    console.log('Connexion réussie:', user);
} catch (error) {
    if (error.status === 401) {
        console.log('Email ou mot de passe incorrect');
    } else if (error.status === 404) {
        console.log('Utilisateur non trouvé');
    } else {
        console.log('Erreur:', error.message);
    }
}
```

## 🚀 Démarrage rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Démarrer l'API
python run_api.py

# 3. Accéder à la documentation
# http://localhost:8000/docs
```

## 📝 Notes importantes

- ✅ **Pas de JWT** : Authentification basée sur l'email uniquement
- ✅ **Sécurité** : Mots de passe hashés avec bcrypt
- ✅ **Simplicité** : API REST simple pour le frontend
- ✅ **Validation** : Validation automatique des données avec Pydantic
- ✅ **Documentation** : Documentation interactive disponible

## 🔄 Workflow typique

1. **Inscription** : `POST /auth/register`
2. **Connexion** : `POST /auth/login`
3. **Récupérer infos** : `GET /auth/user/{email}`
4. **Mettre à jour** : `PUT /auth/user/{email}`
5. **Déconnexion** : `POST /auth/logout`
