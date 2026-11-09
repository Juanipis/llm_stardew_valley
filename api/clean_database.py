#!/usr/bin/env python3
"""
Script para limpiar completamente la base de datos de StardewEchoes
Útil para testing y desarrollo - ELIMINA TODOS LOS DATOS
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


async def clean_database():
    """Limpia toda la base de datos eliminando todos los registros"""

    # Cambiar al directorio del proyecto
    api_dir = Path(__file__).parent
    os.chdir(api_dir)

    try:
        # Importar después de cambiar directorio
        from app.db import db
        from app.config import settings

        logger.info("🗑️ Iniciando limpieza completa de la base de datos...")
        logger.info("📊 Database URL: %s", settings.database_url)

        # Conectar a la base de datos
        logger.info("🔗 Conectando a la base de datos...")
        await db.connect()
        logger.info("✅ Conexión exitosa!")

        # Orden de eliminación para respetar las claves foráneas
        tables_to_clean = [
            "DialogueEntry",  # Debe ir primero (referencia a Conversation)
            "Conversation",  # Segundo (referencia a Player y Npc)
            "PlayerPersonalityProfile",  # Tercero (referencia a Player y Npc)
            "Interaction",  # Cuarto (referencia a World)
            "World",  # Quinto (referencia a User)
            "Player",  # Sexto (sin dependencias externas)
            "Npc",  # Séptimo (sin dependencias externas)
            "User",  # Último (referenciado por World)
        ]

        logger.info("🧹 Eliminando registros en orden correcto...")

        total_deleted = 0
        for table in tables_to_clean:
            try:
                # Contar registros antes
                count_result = await db.query_raw(
                    f'SELECT COUNT(*) as count FROM "{table}"'
                )
                count_before = count_result[0]["count"] if count_result else 0

                if count_before > 0:
                    # Eliminar todos los registros
                    await db.execute_raw(f'DELETE FROM "{table}"')
                    logger.info(
                        "   ✅ %s: %d registros eliminados", table, count_before
                    )
                    total_deleted += count_before
                else:
                    logger.info("   ➖ %s: ya estaba vacía", table)

            except Exception as e:
                logger.error("   ❌ Error limpiando %s: %s", table, e)

        # Verificar que todo esté limpio
        logger.info("\n🔍 Verificando limpieza...")

        all_clean = True
        for table in tables_to_clean:
            try:
                count_result = await db.query_raw(
                    f'SELECT COUNT(*) as count FROM "{table}"'
                )
                count = count_result[0]["count"] if count_result else 0

                if count == 0:
                    logger.info("   ✅ %s: vacía", table)
                else:
                    logger.warning("   ⚠️ %s: aún tiene %d registros", table, count)
                    all_clean = False

            except Exception as e:
                logger.error("   ❌ Error verificando %s: %s", table, e)
                all_clean = False

        # Reiniciar secuencias de IDs (para tablas con autoincrement)
        logger.info("\n🔄 Reiniciando secuencias de IDs...")

        autoincrement_tables = ["User", "World", "Interaction"]
        for table in autoincrement_tables:
            try:
                # Reiniciar la secuencia de ID
                await db.execute_raw(f'ALTER SEQUENCE "{table}_id_seq" RESTART WITH 1')
                logger.info("   ✅ Secuencia de %s reiniciada", table)
            except Exception as e:
                logger.warning(
                    "   ⚠️ No se pudo reiniciar secuencia de %s: %s", table, e
                )

        await db.disconnect()

        if all_clean:
            logger.info("\n🎉 ¡Limpieza completada exitosamente!")
            logger.info("📊 Total de registros eliminados: %d", total_deleted)
            logger.info(
                "🆕 La base de datos está completamente limpia y lista para usar"
            )
        else:
            logger.warning(
                "\n⚠️ Limpieza parcialmente completada - algunos registros pueden persistir"
            )

    except Exception as e:
        logger.error("❌ Error durante la limpieza: %s", e)
        logger.error("\n🔧 Posibles soluciones:")
        logger.error("1. Verifica que PostgreSQL esté ejecutándose")
        logger.error("2. Verifica las credenciales en DATABASE_URL")
        logger.error("3. Asegúrate de que las tablas existan")


async def clean_with_confirmation():
    """Limpia la base de datos con confirmación del usuario"""

    print(
        "⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos de la base de datos"
    )
    print("📊 Esto incluye:")
    print("   - Todos los jugadores y NPCs")
    print("   - Todas las conversaciones y diálogos")
    print("   - Todos los perfiles de personalidad")
    print("   - Todas las interacciones guardadas")
    print("   - Todos los usuarios y mundos")
    print()

    confirmation = input(
        "¿Estás seguro de que quieres continuar? Escribe 'LIMPIAR' para confirmar: "
    )

    if confirmation.strip().upper() == "LIMPIAR":
        await clean_database()
    else:
        logger.info("❌ Operación cancelada por el usuario")


if __name__ == "__main__":
    import sys

    # Permitir limpieza directa con flag --force
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        logger.warning("🚨 Modo forzado activado - limpiando sin confirmación")
        asyncio.run(clean_database())
    else:
        asyncio.run(clean_with_confirmation())
