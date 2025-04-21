# Splitwise Sync

Manda tus gastos al Splitwise desde los mails del banco.

[English version below | Versión en inglés más abajo](#english-version)

## Descripción general

Esta aplicación automatiza el proceso de agregar transacciones a Splitwise analizando emails bancarios. Está diseñada para funcionar en fases:

1. **Fase 1 (wip)**: Analiza emails bancarios desde la carpeta "Recibos" de Gmail y agrega gastos a Splitwise para ti mismo. Al menos para mi banco.
2. **Fase 2 (wip)**: Determina inteligentemente si una transacción fue compartida con una pareja y crea transacciones divididas según corresponda.
3. **Fase 3**: Etiqueta automáticamente las transacciones con categorías apropiadas usando aprendizaje automático.
4. **Fase 4 event-driven**: Implementa una solución basada en eventos para agregar transacciones a Splitwise.

## Bancos chilenos soportados

1. (listo) Banco de Chile
2. Banco BCI
3. Banco Santander
4. Banco del Estado

## Configuración

### Prerrequisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) para gestión de paquetes
- Cuenta de Gmail con emails de recibos bancarios
- Cuenta de Splitwise y credenciales API

### Instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/yourusername/splitwise-sync.git
   cd splitwise-sync
   ```

2. Crea un entorno virtual e instala dependencias usando uv:
   ```
   uv venv --python 3.12.0
   source .venv/bin/activate 
   uv pip install .           # Instala dependencias principales
   uv pip install ".[dev]"    # (opcional) Instala dependencias de desarrollo
   ```

3. Crea un archivo `.env` basado en el ejemplo proporcionado:
   ```
   cp .env.example .env
   ```

4. Edita el archivo `.env` con tus credenciales de Gmail y API de Splitwise

### Acceso IMAP de Gmail

1. Crea una Contraseña de Aplicación:
   - Asegúrate de que la Verificación en dos pasos esté habilitada para tu cuenta de Google
   - Ve a [Contraseñas de aplicación](https://myaccount.google.com/apppasswords)
   - Selecciona "Correo" y tu dispositivo
   - Haz clic en "Generar"
   - Usa la contraseña de 16 caracteres generada en tu archivo `.env` en lugar de tu contraseña regular

2. Configura las variables de entorno apropiadas en tu archivo `.env`:
   ```
   GMAIL_USERNAME=tu.email@gmail.com
   GMAIL_APP_PASSWORD=tu-contraseña-de-aplicación
   ```

### Configuración de API de Splitwise

1. Crea una nueva aplicación en [Portal de Desarrolladores de Splitwise](https://secure.splitwise.com/apps)
2. Obtén tu Consumer Key y Secret
3. Agrega estas credenciales a tu archivo `.env`

## Uso

### Versión por lotes

Ejecuta la aplicación para procesar nuevos emails y sincronizar transacciones:

```bash
splitwise-sync
```


### Integración Continua

Este proyecto usa GitHub Actions para integración continua. El flujo de trabajo ejecuta automáticamente pruebas y verificaciones de calidad al hacer push a la rama principal o al crear pull requests. El flujo de trabajo:

1. Configura Python 3.12
2. Instala dependencias usando uv
3. Ejecuta pytest para realizar todas las pruebas

~~4. Realiza verificaciones de calidad de código con ruff, black, isort y mypy~~

Puedes ver la configuración del flujo de trabajo en `.github/workflows/tests.yml`.

## Licencia

MIT

---

<a name="english-version"></a>
# Splitwise Sync (English version)

Send your expenses to Splitwise from bank emails.

## Overview

This application automates the process of adding transactions to Splitwise by parsing bank emails. It's designed to work in phases:

1. **Phase 1 Batch (Done)**: Parse bank emails from Gmail "Receipts" folder and add expenditures to Splitwise for yourself. At least for my bank.
3. **Phase 2 (Current)**: Intelligently determine if a transaction was shared with a partner and create split transactions accordingly.
4. **Phase 3 (Future)**: Automatically tag transactions with appropriate categories using machine learning.
2. **Phase 4 Event-driven (Future)**: Implement an event-driven solution to add transactions to Splitwise.

## Chilean banks supported

1. (done) Banco de Chile
2. Banco BCI
3. Banco Santander
4. Banco del Estado

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for package management
- Gmail account with bank receipt emails
- Splitwise account and API credentials

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/splitwise-sync.git
   cd splitwise-sync
   ```

2. Create a virtual environment and install dependencies using uv:
   ```
   uv venv --python 3.12.0
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install .           # Install main dependencies
   uv pip install ".[dev]"    # Install development dependencies
   ```

3. Create a `.env` file based on the provided example:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file with your Gmail and Splitwise API credentials

### Gmail IMAP Access

1. Create an App Password:
   - Ensure 2-Step Verification is enabled for your Google Account
   - Go to [App passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Click "Generate"
   - Use the generated 16-character password in your `.env` file instead of your regular password

2. Set the appropriate environment variables in your `.env` file:
   ```
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   ```

### Splitwise API Setup

1. Create a new app at [Splitwise Developer Portal](https://secure.splitwise.com/apps)
2. Get your Consumer Key and Secret
3. Add these credentials to your `.env` file

## Usage

### Batch version

Run the application to process new emails and sync transactions:

```
splitwise-sync
```

Or alternatively:
```
python -m splitwise_sync.cli.batch
```

## Testing

Run tests with pytest:

```
pytest
```

## Development

This project uses:
- `pytest` for testing
- `black` and `isort` for formatting
- `mypy` for type checking
- `ruff` for linting

### Continuous Integration

This project uses GitHub Actions for continuous integration. The workflow automatically runs tests and quality checks on push to the main branch or when creating pull requests. The workflow:

1. Sets up Python 3.12
2. Installs dependencies using uv
3. Runs pytest to execute all tests
~~4. Performs code quality checks with ruff, black, isort, and mypy~~

You can see the workflow configuration in `.github/workflows/tests.yml`.

## License

MIT