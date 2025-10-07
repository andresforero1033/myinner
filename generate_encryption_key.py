#!/usr/bin/env python3
"""
Script para generar clave de encriptación segura para Field-Level Encryption
"""
from cryptography.fernet import Fernet
import base64
import os

def generate_encryption_key():
    """Genera una clave de encriptación Fernet de 32 bytes"""
    key = Fernet.generate_key()
    return key.decode('utf-8')

def main():
    print("🔐 Generador de Claves de Encriptación")
    print("=" * 50)
    
    # Generar clave nueva
    key = generate_encryption_key()
    
    print(f"Nueva clave de encriptación generada:")
    print(f"FIELD_ENCRYPTION_KEY={key}")
    print()
    print("⚠️  IMPORTANTE:")
    print("1. Guarda esta clave de forma segura")
    print("2. Añádela a tu archivo .env")
    print("3. NUNCA la subas a control de versiones")
    print("4. Si pierdes esta clave, no podrás desencriptar los datos")
    print()
    print("Para uso en .env:")
    print(f"FIELD_ENCRYPTION_KEY={key}")
    print()
    print("Para testing/desarrollo:")
    print("Puedes usar esta clave generada automáticamente")

if __name__ == "__main__":
    main()