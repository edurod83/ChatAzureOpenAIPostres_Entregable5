# Azure AI Chat

Aplicación web de chat de IA conectada a **Azure OpenAI**, con historial de
conversaciones persistido en **PostgreSQL** (Azure).

---

## Stack tecnológico

| Capa            | Tecnología                                |
|-----------------|-------------------------------------------|
| Backend         | Python 3.11+ · FastAPI                    |
| Frontend        | Jinja2 · HTML5 · CSS3 · JavaScript Vanilla|
| Base de datos   | PostgreSQL (Azure Database for PostgreSQL)|
| ORM             | SQLAlchemy 2.x                            |
| Migraciones     | Alembic                                   |
| IA              | Azure OpenAI (SDK oficial `openai`)       |
| Configuración   | pydantic-settings + `.env`               |

---

## Arquitectura del proyecto

```
.
├── app/
│   ├── main.py               # Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py         # Variables de entorno (pydantic-settings)
│   │   └── logging_config.py # Configuración de logging
│   ├── db/
│   │   ├── base.py           # DeclarativeBase de SQLAlchemy
│   │   └── session.py        # Motor, SessionLocal y dependencia get_db
│   ├── models/
│   │   ├── conversation.py   # Modelo ORM → tabla conversations
│   │   └── message.py        # Modelo ORM → tabla messages
│   ├── schemas/
│   │   ├── conversation.py   # Schemas Pydantic para conversaciones
│   │   └── message.py        # Schemas Pydantic para mensajes
│   ├── services/
│   │   ├── conversation_service.py # Lógica de negocio: conversaciones
│   │   ├── message_service.py      # Lógica de negocio: mensajes
│   │   └── openai_service.py       # Cliente Azure OpenAI desacoplado
│   ├── routes/
│   │   ├── chat.py           # Rutas HTML (Jinja2)
│   │   └── api.py            # Rutas JSON (AJAX desde el frontend)
│   ├── templates/
│   │   ├── base.html         # Layout base con sidebar
│   │   ├── index.html        # Pantalla de bienvenida
│   │   └── conversation.html # Vista de chat
│   └── static/
│       ├── css/styles.css    # Hoja de estilos
│       └── js/chat.js        # Lógica del chat en el cliente
├── alembic/
│   ├── env.py                # Entorno Alembic
│   ├── script.py.mako        # Plantilla de revisiones
│   └── versions/
│       └── 001_initial_migration.py
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

---

## Instalación y ejecución

### 1. Clonar / descargar el proyecto

```bash
git clone <url-del-repositorio>
cd ChatAzureOpenAIPostres_Entregable5
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales reales
```

Variables obligatorias en `.env`:

| Variable                      | Descripción                                      |
|-------------------------------|--------------------------------------------------|
| `DATABASE_URL`                | URL de conexión a PostgreSQL                     |
| `AZURE_OPENAI_ENDPOINT`       | Endpoint del recurso Azure OpenAI                |
| `AZURE_OPENAI_API_KEY`        | Clave de API                                     |
| `AZURE_OPENAI_API_VERSION`    | Versión de la API (ej. `2024-02-15-preview`)     |
| `AZURE_OPENAI_DEPLOYMENT`     | Nombre del deployment (ej. `gpt-4`)              |

> **PostgreSQL en Azure:** La URL suele tener el formato
> `postgresql://usuario%40servidor:password@servidor.postgres.database.azure.com:5432/chatdb?sslmode=require`
> (el `@` del nombre de usuario se codifica como `%40`).

### 5. Ejecutar las migraciones

```bash
alembic upgrade head
```

### 6. Iniciar la aplicación

```bash
uvicorn app.main:app --reload
```

La aplicación queda disponible en **http://localhost:7000**.

---

## Endpoints

### Vistas HTML

| Método | Ruta                                     | Descripción                        |
|--------|------------------------------------------|------------------------------------|
| GET    | `/`                                      | Pantalla de bienvenida             |
| POST   | `/conversations/new`                     | Crear nueva conversación           |
| GET    | `/conversations/{id}`                    | Ver conversación                   |
| POST   | `/conversations/{id}/messages`           | Enviar mensaje (fallback sin JS)   |
| POST   | `/conversations/{id}/delete`             | Eliminar conversación              |

### API JSON

| Método | Ruta                                     | Descripción                        |
|--------|------------------------------------------|------------------------------------|
| GET    | `/api/conversations`                     | Listar conversaciones              |
| GET    | `/api/conversations/{id}`                | Obtener conversación con mensajes  |
| POST   | `/api/conversations/{id}/messages`       | Enviar mensaje (AJAX)              |

---

## Comandos Alembic

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Crear una nueva migración (detecta cambios en los modelos)
alembic revision --autogenerate -m "descripcion_del_cambio"

# Revertir la última migración
alembic downgrade -1

# Ver el estado actual
alembic current

# Ver el historial de revisiones
alembic history
```

---

## Decisiones técnicas relevantes

- **Servicio OpenAI desacoplado** (`openai_service.py`): el cliente se inicializa
  de forma lazy para facilitar las pruebas sin conexión real.

- **Doble endpoint de mensajes**: la ruta `/conversations/{id}/messages` (POST form)
  actúa como fallback sin JavaScript; la ruta `/api/…` devuelve JSON y es la que
  usa el frontend por defecto.

- **Timestamp `updated_at`**: como SQLAlchemy no actualiza `onupdate` cuando se
  insertan filas hijas (mensajes), se llama explícitamente a `touch_conversation()`
  en cada envío para mantener el orden de la barra lateral.

- **XSS en el cliente**: el JS escapa el contenido de los mensajes antes de
  insertarlo en el DOM (`escapeHtml`).

- **Pool de conexiones**: configurado con `pool_pre_ping=True` para tolerar
  desconexiones de PostgreSQL en Azure (que pueden cerrar conexiones inactivas).
