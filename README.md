# Splitwise Sync

**Gastos del banco directo al Splitwise.**  
Automatiza tu vida financiera con solo leer tus mails.

[English version below | Versión en inglés más abajo](#english-version)

## ¿Qué hace?

Esta app lee los recibos bancarios que llegan a tu Gmail y los convierte en transacciones en Splitwise. Todo sin mover un dedo (bueno, casi).

## Roadmap

Esto va por fases. La idea es ir de algo útil a algo mágico:

1. **Fase 1 (en progreso)**  
   🔍 Escanea los mails en la carpeta "Recibos" y crea gastos en tu Splitwise personal.

2. **Fase 2 (en progreso)**  
   💑 Detecta si el gasto fue compartido (ej: con tu pareja) y lo divide automáticamente.

3. **Fase 3 (próxima)**  
   🧠 Usa machine learning para categorizar tus gastos sin que tengas que hacer nada.

4. **Fase 4 (a futuro)**  
   ⚡ Se vuelve event-driven: todo se sincroniza solo, en tiempo real.


## ¿Qué bancos chilenos soporta?

- ✅ Banco de Chile  
- ⚙️ Banco BCI  
- ⚙️ Banco Santander  
- ⚙️ Banco Estado  

*(más por venir)*

## ¿Qué necesito?

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) para instalar cosas
- Una cuenta de Gmail con mails de tu banco
- Tu cuenta de Splitwise con acceso API

## ¿Cómo lo instalo?

```bash
git clone https://github.com/yourusername/splitwise-sync.git
cd splitwise-sync

uv venv --python 3.12
uv sync 

cp .env.example .env
```

Edita el `.env` con tus credenciales de Gmail y Splitwise.

## Conecta Gmail (IMAP)

1. Activa la verificación en 2 pasos en tu cuenta Google  
2. Crea una contraseña de aplicación [aquí](https://myaccount.google.com/apppasswords)  
3. Usa esa contraseña en tu `.env`

```env
GMAIL_USERNAME=tu.email@gmail.com
GMAIL_APP_PASSWORD=contraseña-generada
```

## Conecta Splitwise

1. Crea una app en [Splitwise Developer Portal](https://secure.splitwise.com/apps)  
2. Copia tu Consumer Key y Secret  
3. Agrega esto a tu `.env`

## ¿Cómo lo uso?

```bash
splitwise-sync
```

Eso es todo. Si todo está bien, tus gastos van directo a Splitwise.

## Dev y CI

Este proyecto usa:

- `pytest` para tests
- `ruff`, `black`, `isort` y `mypy` para calidad de código

Además, tiene GitHub Actions para correr pruebas automáticamente al hacer push o PRs. Mira `.github/workflows/tests.yml`.

## ML y datos: cómo está organizado el proyecto

Así se organiza la parte nerd del proyecto: datos, modelos y notebooks bien separados para no perderse entre CSVs y experimentos.

```
├── data
│   ├── external       <- Datos de fuentes externas.
│   ├── interim        <- Datos intermedios que han sido transformados.
│   ├── processed      <- Conjuntos de datos finales y canónicos para modelado.
│   └── raw            <- Datos originales e inmutables.
├── models             <- Modelos entrenados y serializados para predicción de gastos.
├── notebooks          <- Jupyter notebooks para análisis exploratorio y desarrollo de modelos.
```

Esta estructura sigue las mejores prácticas de ciencia de datos para mantener la separación entre datos crudos, procesamiento y modelado.

## Licencia

MIT

---

<a name="english-version"></a>

# Splitwise Sync (English version)

**Bank expenses straight to Splitwise.**  
Automate your finances by just reading your emails.

## What does it do?

This app reads bank receipt emails in your Gmail and turns them into Splitwise transactions. Magic? Nope. Just code.


## Roadmap

This is a work in progress — step by step towards full automation:

1. **Phase 1 (in progress)**  
   🔍 Scans the “Receipts” folder in Gmail and logs personal expenses to Splitwise.

2. **Phase 2 (in progress)**  
   💑 Detects if the expense was shared (e.g., with your partner) and splits it for you.

3. **Phase 3 (next)**  
   🧠 Uses machine learning to auto-categorize your expenses.

4. **Phase 4 (future)**  
   ⚡ Goes event-driven: everything syncs automatically, in real time.


## Supported Chilean banks

- ✅ Banco de Chile  
- ⚙️ Banco BCI  
- ⚙️ Banco Santander  
- ⚙️ Banco Estado

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for package management
- Gmail account with receipt emails
- Splitwise account with API access

## Setup

```bash
git clone https://github.com/yourusername/splitwise-sync.git
cd splitwise-sync

uv venv --python 3.12
uv sync

cp .env.example .env
```

Edit `.env` with your Gmail and Splitwise credentials.

## Gmail setup (IMAP)

1. Enable 2FA on your Google account  
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)  
3. Generate a password and use it in `.env`:

```env
GMAIL_USERNAME=your.email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

## Splitwise setup

1. Create an app at [Splitwise Developer Portal](https://secure.splitwise.com/apps)  
2. Copy your consumer key and secret  
3. Add them to `.env`

## How to run it

```bash
splitwise-sync
```

That’s it. Your bank transactions will appear in Splitwise.

## Dev & CI

Uses:

- `pytest` for testing  
- `black`, `isort`, `ruff`, `mypy` for code quality  

CI runs on GitHub Actions for every push or PR. Config is in `.github/workflows/tests.yml`.

## License

MIT
