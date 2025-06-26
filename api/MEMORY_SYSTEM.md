# StardewEchoes - Sistema de Memoria y Personalidad para NPCs

## 🧠 Visión General

El sistema de memoria de StardewEchoes transforma los NPCs de simples respondedores reactivos a entidades con memoria persistente y personalidades adaptativas. Cada NPC desarrolla una percepción única de cada jugador basada en sus interacciones pasadas.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **Almacenamiento Persistente** (PostgreSQL + pgvector)

   - Conversaciones completas con embeddings semánticos
   - Perfiles de personalidad adaptativos
   - Búsqueda eficiente de recuerdos relevantes

2. **Servicio de Memoria** (`memory_service.py`)

   - Gestión de jugadores y NPCs
   - Generación y búsqueda de embeddings
   - Actualización de perfiles de personalidad

3. **Pipeline Asíncrono**
   - Procesamiento en segundo plano de conversaciones
   - Actualización automática de perfiles

## 📊 Modelo de Datos

### PlayerPersonalityProfile

Cada NPC mantiene un perfil de personalidad único para cada jugador:

```python
{
    "summary": "Descripción textual de la personalidad percibida",
    "friendliness": 7.5,    # 0-10: Amistoso vs Hostil
    "extroversion": 6.0,    # 0-10: Extrovertido vs Tímido
    "sincerity": 5.0,       # 0-10: Sincero vs Sarcástico
    "curiosity": 8.0        # 0-10: Curioso vs Directo
}
```

### Conversation & DialogueEntry

- **Conversation**: Sesión completa de diálogo con contexto del juego
- **DialogueEntry**: Cada línea de diálogo con embedding vectorial para búsqueda semántica

## 🔄 Flujo de Funcionamiento

### 1. Generación de Diálogo (`/generate_dialogue`)

```mermaid
flowchart TD
    A[Solicitud de diálogo] --> B[Obtener/crear jugador y NPC]
    B --> C[Recuperar perfil de personalidad]
    C --> D[Buscar recuerdos relevantes]
    D --> E[Generar prompt enriquecido]
    E --> F[Llamar a Gemini]
    F --> G[Guardar en memoria]
    G --> H[Retornar respuesta]
```

**Características del prompt enriquecido:**

- Perfil de personalidad actual del jugador
- 2-3 recuerdos más relevantes al contexto
- Historia de conversación actual
- Contexto del juego (estación, clima, amistad, etc.)

### 2. Actualización de Personalidad (Asíncrono)

Cuando termina una conversación (`/end_conversation`):

```mermaid
flowchart TD
    A[Fin de conversación] --> B[Tarea en segundo plano]
    B --> C[Analizar transcripción completa]
    C --> D[Generar nuevo perfil con LLM]
    D --> E[Actualizar base de datos]
    E --> F[Guardar embeddings]
```

**Análisis psicológico:**

- Evalúa cambios en amistosidad, extroversión, sinceridad y curiosidad
- Ajustes graduales (0.5-2.0 puntos por conversación)
- Resumen narrativo desde la perspectiva del NPC

### 3. Búsqueda de Recuerdos

Utiliza **pgvector** para búsqueda semántica:

- Convierte la respuesta actual del jugador en embedding
- Busca las 3 entradas de diálogo más similares semánticamente
- Inyecta estos recuerdos en el prompt para contexto

## 🛠️ Configuración e Instalación

### Prerrequisitos

1. **PostgreSQL** con extensión **pgvector**
2. **Google Gemini API Key**
3. **Python 3.9+** con Poetry

### Instalación

1. **Instalar pgvector en PostgreSQL:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Configurar variables de entorno:**

```bash
GEMINI_API_KEY=tu_clave_de_api_aquí
DATABASE_URL=postgresql://user:pass@localhost:5432/stardew_echoes
```

3. **Ejecutar script de configuración:**

```bash
cd api
python setup.py
```

4. **Iniciar servidor:**

```bash
poetry run uvicorn app.main:app --reload
```

## 📡 Endpoints de la API

### `POST /generate_dialogue`

Genera diálogo con memoria y personalidad.

**Request:**

```json
{
  "npc_name": "Abigail",
  "player_name": "Juan",
  "friendship_hearts": 6,
  "player_response": "I've been exploring the mines lately",
  "season": "Spring",
  "day_of_month": 15
  // ... más contexto
}
```

**Response:**

```json
{
  "npc_message": "Oh, the mines! I remember you mentioning your love for adventure. Find anything interesting down there?",
  "response_options": [
    "Actually yes! I found some rare gems I thought you might like.",
    "Just the usual ores and stones. Nothing too exciting.",
    "Why, looking for an excuse to tag along again?"
  ]
}
```

### `POST /end_conversation`

Marca el fin de una conversación y dispara actualización de personalidad.

**Parameters:**

- `player_name`: Nombre del jugador
- `npc_name`: Nombre del NPC

## 🧪 Ejemplos de Evolución de Personalidad

### Ejemplo 1: Jugador Amistoso

**Conversación inicial:**

- Personalidad base: Friendliness 5.0
- Jugador: "Hi Abigail! How's your day going?"
- Abigail: "Oh, hi there! It's going well, thanks for asking."

**Después de varias interacciones amistosas:**

- Personalidad actualizada: Friendliness 7.5
- Abigail: "Hey! It's always great to see you. You always brighten my day!"

### Ejemplo 2: Jugador Sarcástico

**Conversación inicial:**

- Personalidad base: Sincerity 5.0
- Jugador: "Nice purple hair. Very... unique."
- Abigail: "Thanks... I think?"

**Después de interacciones sarcásticas:**

- Personalidad actualizada: Sincerity 3.0
- Abigail: "Oh, another witty comment from you. How original."

## 🎯 Beneficios del Sistema

1. **Personalización Profunda**: Cada jugador experimenta NPCs únicos
2. **Narrativa Emergente**: Las relaciones evolucionan naturalmente
3. **Inmersión Mejorada**: Los NPCs "recuerdan" y referencian el pasado
4. **Rejugabilidad**: Diferentes personalidades de jugador = diferentes experiencias

## 🔧 Configuración Avanzada

### Variables de Entorno Adicionales

```bash
EMBEDDING_MODEL=text-embedding-004
MAX_RELEVANT_MEMORIES=3
CONVERSATION_TIMEOUT_MINUTES=5
```

### Personalización de Dimensiones de Embedding

En `schema.prisma`, ajusta la dimensión del vector según el modelo:

```prisma
embedding Unsupported("vector(768)")  // Para text-embedding-004
```

## 🚀 Próximas Mejoras

1. **Emociones Contextuales**: Estado emocional temporal de NPCs
2. **Memoria Social**: NPCs que comparten información entre ellos
3. **Eventos Especiales**: Recuerdos de eventos importantes (bodas, festivales)
4. **Análisis Temporal**: Cómo cambian las personalidades a lo largo del tiempo

---

_Este sistema convierte a StardewEchoes en una experiencia verdaderamente dinámica donde cada interacción importa y cada relación es única._
