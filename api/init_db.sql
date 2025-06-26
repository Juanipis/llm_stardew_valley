-- Inicialización de la base de datos con pgvector
-- Este archivo debe ejecutarse en PostgreSQL después de instalar la extensión pgvector

-- Crear la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar que la extensión está instalada
SELECT * FROM pg_extension WHERE extname = 'vector';
