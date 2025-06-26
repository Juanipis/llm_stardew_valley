#!/usr/bin/env python3
"""
Script rápido para limpiar solo los datos de memoria (conversaciones y personalidades)
Mantiene usuarios y configuraciones, solo limpia las interacciones de los NPCs
"""

import asyncio
import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def clean_memory_only():
    """Limpia solo los datos de memoria, manteniendo usuarios y configuraciones"""

    # Cambiar al directorio del proyecto
    api_dir = Path(__file__).parent
    os.chdir(api_dir)

    try:
        # Importar después de cambiar directorio
        from app.db import db
        from app.config import settings

        logger.info("🧠 Limpiando solo datos de memoria...")
        logger.info("Database URL: %s", settings.database_url)

        # Conectar a la base de datos
        await db.connect()
        logger.info("✅ Conectado!")

        # Solo limpiar tablas relacionadas con memoria y conversaciones
        memory_tables = [
            "DialogueEntry",  # Entradas de diálogo
            "Conversation",  # Conversaciones
            "PlayerPersonalityProfile",  # Perfiles de personalidad
            "Player",  # Jugadores (se recrearán automáticamente)
            "Npc",  # NPCs (se recrearán automáticamente)
        ]

        total_deleted = 0
        for table in memory_tables:
            try:
                # Contar registros antes
                count_result = await db.query_raw(
                    f'SELECT COUNT(*) as count FROM "{table}"'
                )
                count_before = count_result[0]["count"] if count_result else 0

                if count_before > 0:
                    # Eliminar todos los registros
                    await db.execute_raw(f'DELETE FROM "{table}"')
                    logger.info("✅ %s: %d registros eliminados", table, count_before)
                    total_deleted += count_before
                else:
                    logger.info("➖ %s: ya estaba vacía", table)

            except Exception as e:
                logger.error("❌ Error limpiando %s: %s", table, e)

        await db.disconnect()

        logger.info("\n🎉 ¡Memoria limpiada exitosamente!")
        logger.info("📊 Registros eliminados: %d", total_deleted)
        logger.info("💾 Usuarios y mundos mantenidos")
        logger.info("🆕 Los NPCs empezarán con memoria fresca")

    except Exception as e:
        logger.error("❌ Error durante la limpieza: %s", e)


if __name__ == "__main__":
    asyncio.run(clean_memory_only())
