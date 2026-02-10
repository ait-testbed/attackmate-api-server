# AttackMate API Server

**AttackMate API Server** is a RESTful API built with FastAPI for remotely controlling AttackMate instances and executing attack playbooks. It provides secure endpoints to orchestrate attack chains, execute commands, and run attack playbook.


## Features

- Execute AttackMate commands or playbooks remotely
- Automatic logging for requests, command execution, and playbooks.
- Supports SSL/TLS for secure communication.


## Requirements

- Python 3.10+
- pip

## Installation

```bash
git clone https://github.com/ait-testbed/attackmate-api-server.git
cd attackmate-api-server
```

With uv (recommended):

```bash
uv sync --dev
```

Using pip and virtualenv:
```
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Developer setup

If you plan to contribute to the development of this package, follow these steps to set up the dev environment and install pre-commit hooks (using [prek](https://github.com/j178/prek))

```bash
uv sync --dev
uv run --dev prek install
```

Run the tests:

```bash
uv run --dev pytest -q
```

Run the tests with coverage (add `--cov-report=html` to generate an HTML report):

```bash
uv run --dev pytest --cov=. --cov-report=term-missing
```

## Certificate generation
with open ssl
```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

Common Name: server IP adress

Clients receive the cert.pem SSL certificate

## Running the application
```bash
uv run attackmate-api
```

The server will run on https://0.0.0.0:8445 by default.

Swagger UI: https://<host>:8445/docs – interactive API documentation.

## Authentication
The API uses token-based authentication.

Endpoint: POST /login

Request:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "<TOKEN>",
  "token_type": "bearer"
}
```

Use the token in the Authorization header for all protected endpoints

## API Endpoints
POST /playbooks/execute/yaml – Execute a playbook provided as YAML content on an AttackMate instantiated for the duration of playbook execution.

POST /command/execute – Execute a command on a persistent AttackMate instance.
Request body must follow the RemotelyExecutableCommand schema

## License
This project is licensed under [EUPL-1.2](LICENSE)
