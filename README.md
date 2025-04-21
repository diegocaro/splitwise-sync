# Splitwise Sync

Automatically sync bank transactions to Splitwise based on email receipts.

## Overview

This application automates the process of adding transactions to Splitwise by parsing bank emails. It's designed to work in phases:

1. **Phase 1a Batch (Current)**: Parse bank emails from Gmail "Receipts" folder and add expenditures to Splitwise for yourself
2. **Phase 1b Event-driven (Future)**: Implement an event-driven solution to add transactions to Splitwise
3. **Phase 2 (Future)**: Intelligently determine if a transaction was shared with a partner and create split transactions accordingly
4. **Phase 3 (Future)**: Automatically tag transactions with appropriate categories using machine learning

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
python -m splitwise_sync.batch
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