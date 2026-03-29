# Simple Agent — Tool-Calling Agents con OpenAI

Proyecto educativo que ilustra el patron de **tool-calling** de OpenAI mediante dos agentes conversacionales construidos con FastAPI:

1. **Math Agent** — Agente con herramientas matematicas (sumas, estadisticas, vectores).
2. **SQL Agent** — Agente Text-to-SQL que convierte lenguaje natural a consultas sobre PostgreSQL.

---

## Arquitectura General

```
Usuario
  │
  ▼
FastAPI (app/main.py)
  ├── POST /chat/agent   →  SimpleAgent      (tools matematicas)
  └── POST /sql/agent    →  SimpleSQLAgent   (tools SQL)
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
             think_tool    get_schema    execute_query
                           (PostgreSQL)
```

Ambos agentes comparten el mismo ciclo:

```
Pregunta → LLM → tool_call? → Ejecutar tool → Resultado → LLM → ... → Respuesta final
```

El loop se repite hasta que el modelo responde sin invocar herramientas o se alcanza el limite de iteraciones.

---

## Estructura del Proyecto

```
simple agent/
├── app/
│   ├── main.py                          # FastAPI + lifespan (init agentes)
│   ├── core/
│   │   └── config.py                    # Logging y rutas base
│   ├── routers/
│   │   ├── chat.py                      # POST /chat/agent  (Math Agent)
│   │   └── sql_chat.py                  # POST /sql/agent   (SQL Agent)
│   ├── services/
│   │   ├── chat_service.py              # Wrapper del Math Agent
│   │   ├── sql_chat_service.py          # Wrapper del SQL Agent
│   │   └── db_service.py               # Conexion PostgreSQL + introspect schema
│   ├── schemas/
│   │   ├── conversation.py              # InputChat, ResponseRAG, MessageItem
│   │   └── errors.py                    # Codigos de error y excepciones
│   └── agents/
│       ├── simple_agent.py              # SimpleAgent (math)
│       ├── sql_agent.py                 # SimpleSQLAgent (text-to-sql)
│       ├── models/
│       │   ├── simple_agent_state.py    # Estado del Math Agent
│       │   └── sql_agent_state.py       # Estado del SQL Agent
│       ├── tools/
│       │   ├── simple_base.py           # BaseAgentTool + ToolRegistry
│       │   ├── simple_math_tools.py     # ThinkTool, SumTool, StatsTool, ...
│       │   └── simple_sql_tools.py      # SQLThinkTool, GetSchema, ExecuteQuery
│       ├── services/
│       │   ├── openai_client.py         # Cliente OpenAI / Azure OpenAI
│       │   └── openai_provider.py       # Resolucion de proveedor
│       └── prompts/
│           ├── simple_sql_agent.py      # System prompt del SQL Agent
│           ├── context.md               # Contexto de negocio (NovaMart)
│           └── database_schema.md       # Esquema de la base de datos
├── docs/                                # Material academico complementario
├── logs/                                # Logs de ejecucion (info + error)
├── requirements.txt
├── Dockerfile
├── .env_example
└── pytest.ini
```

---

## Math Agent

Agente ilustrativo que resuelve operaciones matematicas usando tool-calling.

**Herramientas disponibles:**

| Tool | Descripcion |
|------|-------------|
| `think_tool` | Reflexion y planificacion antes de actuar |
| `sum_numbers` | Suma de una lista de numeros |
| `calculate_stats` | Media, mediana, desviacion estandar, min, max |
| `dot_product` | Producto punto entre dos vectores |
| `magnitude` | Norma L2 de un vector |
| `euclidean_distance` | Distancia euclidiana entre dos vectores |
| `cosine_distance` | Distancia coseno entre dos vectores |

**Configuracion:** `max_iterations=5`, `temperature=0.0`, `seed=42`

---

## SQL Agent

Agente Text-to-SQL que traduce preguntas en lenguaje natural a consultas SELECT sobre una base de datos PostgreSQL.

**Herramientas disponibles:**

| Tool | Descripcion |
|------|-------------|
| `think_tool` | Planificacion de estrategia SQL |
| `get_database_schema` | Obtiene el esquema de tablas desde PostgreSQL |
| `execute_sql_query` | Ejecuta consultas de solo lectura (SELECT/WITH/EXPLAIN) |

**Configuracion:** `max_iterations=10`, `temperature=0.0`, `seed=42`

### Base de datos: NovaMart

E-commerce con datos transaccionales de 2024 (USD). 6 tablas:

```
regions (4)  ←──  customers.region_id (nullable)
categories (4)  ←──  products.category_id
customers (200)  ←──  orders.customer_id
products (30)  ←──  order_items.product_id
orders (~2,000)  ←──  order_items.order_id
```

El system prompt del agente incluye automaticamente el contenido de `context.md` (reglas de negocio) y `database_schema.md` (esquema detallado de tablas).

---

## Inicio Rapido

### Requisitos

- Python 3.12+
- PostgreSQL (requerido para el SQL Agent)
- Cuenta de OpenAI o Azure OpenAI

### Instalacion

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env_example .env
# Editar .env con tus credenciales
```

### Variables de Entorno Principales

```env
# Proveedor LLM: "azure" u "openai"
OPENAI_API_PROVIDER=azure

# OpenAI estandar
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# PostgreSQL (requerido para SQL Agent)
CHALLENGE_DATABASE_URL=postgresql://user:password@localhost:5432/novamart
```

### Ejecutar

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentacion interactiva en: http://localhost:8000/docs

---

## Uso de la API

### Math Agent

```bash
curl -X POST http://localhost:8000/chat/agent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user01",
    "session_id": "session01",
    "history": [
      {"role": "user", "content": "Calcula la suma de [10, 20, 30] y luego la media"}
    ]
  }'
```

### SQL Agent

```bash
curl -X POST http://localhost:8000/sql/agent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user01",
    "session_id": "session01",
    "history": [
      {"role": "user", "content": "Cual es el ingreso total por categoria de producto?"}
    ]
  }'
```

### Formato de respuesta

```json
{
  "response": "El ingreso total por categoria es: Electronics $45,230...",
  "message_id": null,
  "agent_state": {
    "session_id": "session01",
    "user_id": "user01",
    "sql_queries": [...],
    "execution_time_seconds": 1.23
  }
}
```

---

## Docker

```bash
docker build -t simple-agent .
docker run -p 8080:8080 --env-file .env simple-agent
```

---

## Patrones Clave

| Patron | Descripcion |
|--------|-------------|
| **Tool-Calling Loop** | El LLM decide que herramienta usar; el agente la ejecuta y devuelve el resultado al LLM |
| **BaseAgentTool + ToolRegistry** | Clases base para registrar herramientas con JSON Schema auto-generado |
| **State Dataclass** | Cada agente mantiene su estado (mensajes, historial de queries) en un dataclass |
| **Dependency Injection** | FastAPI inyecta agentes y servicios via `app.state` y dependencias |
| **Read-Only SQL** | El SQL Agent solo permite SELECT/WITH/EXPLAIN; nunca escritura |

---

## Stack

| Componente | Tecnologia |
|------------|------------|
| Framework | FastAPI |
| LLM | OpenAI / Azure OpenAI (GPT-4o) |
| Base de Datos | PostgreSQL + SQLAlchemy |
| Validacion | Pydantic |
| Contenedor | Docker |
