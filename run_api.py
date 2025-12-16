#!/usr/bin/env python3
"""
Script de démarrage pour l'API Notofine
"""
import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Démarrage de l'API Notofine...")
    print("📖 Documentation disponible sur: http://localhost:8000/docs")
    print("🔧 Interface alternative: http://localhost:8000/redoc")
    print("=" * 50)

    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info"
        
    )
