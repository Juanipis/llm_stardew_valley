#!/usr/bin/env python3
"""
Script de configuración inicial para StardewEchoes API
Inicializa la base de datos con Prisma y aplica las migraciones necesarias
"""

import os
import subprocess
from pathlib import Path


def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completado")
        if result.stdout:
            print(f"📝 Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}")
        print(f"Error: {e.stderr}")
        return False


def main():
    print("🚀 Configurando StardewEchoes API con sistema de memoria...")

    # Verificar que estamos en el directorio correcto
    api_dir = Path(__file__).parent
    os.chdir(api_dir)

    print(f"📂 Directorio de trabajo: {os.getcwd()}")

    # 1. Instalar dependencias con Poetry
    print("\n=== INSTALANDO DEPENDENCIAS ===")
    if not run_command("poetry install", "Instalación de dependencias con Poetry"):
        print("⚠️  Error instalando dependencias. Continuando...")

    # 2. Verificar archivo .env
    print("\n=== VERIFICANDO CONFIGURACIÓN ===")
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado. Creando plantilla...")
        env_template = """# Configuración de StardewEchoes API
# Copia este archivo a .env y completa los valores

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Base de datos PostgreSQL con pgvector
# Ejemplo: postgresql://username:password@localhost:5432/stardew_echoes
DATABASE_URL=postgresql://username:password@localhost:5432/stardew_echoes

# Configuración opcional
EMBEDDING_MODEL=text-embedding-004
MAX_RELEVANT_MEMORIES=3
CONVERSATION_TIMEOUT_MINUTES=5
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_template)
        print(
            "📝 Plantilla .env creada. Por favor completa los valores antes de continuar."
        )
        print("📍 Especialmente necesitas:")
        print("   - GEMINI_API_KEY: Tu clave de API de Google Gemini")
        print("   - DATABASE_URL: URL de conexión a PostgreSQL con pgvector")
        return
    else:
        print("✅ Archivo .env encontrado")

    # 3. Generar cliente Prisma
    print("\n=== GENERANDO CLIENTE PRISMA ===")
    if not run_command("poetry run prisma generate", "Generación del cliente Prisma"):
        print("❌ Error generando cliente Prisma. Verifica tu configuración.")
        return

    # 4. Aplicar migraciones (si existe DATABASE_URL)
    print("\n=== MIGRACIONES DE BASE DE DATOS ===")

    # Verificar si DATABASE_URL está configurado
    try:
        result = subprocess.run(
            'poetry run python -c "from app.config import settings; print(settings.database_url)"',
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if (
            result.returncode == 0
            and result.stdout.strip()
            and "postgresql" in result.stdout
        ):
            print("🔗 Conexión a PostgreSQL detectada")

            # Aplicar migraciones
            if run_command(
                "poetry run prisma migrate dev --name initial_memory_system",
                "Aplicación de migraciones",
            ):
                print("✅ Base de datos configurada correctamente")
            else:
                print("⚠️  Error en migraciones. Verifica que:")
                print("   - PostgreSQL esté ejecutándose")
                print("   - La extensión pgvector esté instalada")
                print("   - Las credenciales en DATABASE_URL sean correctas")
        else:
            print("⚠️  DATABASE_URL no configurado o no es PostgreSQL")
            print("📝 Configura DATABASE_URL en .env antes de continuar")
    except (subprocess.CalledProcessError, ValueError, ImportError) as e:
        print(f"⚠️  Error verificando configuración: {e}")

    print("\n=== CONFIGURACIÓN COMPLETADA ===")
    print("🎉 StardewEchoes API configurado con sistema de memoria!")
    print("\n📋 Próximos pasos:")
    print("1. Configura tu archivo .env con las credenciales correctas")
    print("2. Asegúrate de que PostgreSQL con pgvector esté ejecutándose")
    print("3. Ejecuta: poetry run uvicorn app.main:app --reload")
    print("\n📚 Funcionalidades del sistema de memoria:")
    print("- 🧠 Perfiles de personalidad adaptativos para cada NPC")
    print("- 💾 Almacenamiento persistente de conversaciones")
    print("- 🔍 Búsqueda semántica de recuerdos relevantes")
    print("- 🔄 Actualización automática de personalidades en segundo plano")


if __name__ == "__main__":
    main()
