# Bored No More 3

BoredNoMore3 is a Python desktop application designed to help users discover activities and manage downloadable content when bored.

## Features

- Modular backend architecture
- Desktop frontend
- Debian packaging support
- Scriptable and configurable behavior

## Installation

Clone the repository:

git clone https://github.com/nepamuceno/borednomore3.git
cd borednomore3

Create a virtual environment:

python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

## Running

python3 -m backend.main

## Configuration

Copy the environment template:

cp env-example .env

Edit `.env` to match your setup.

## Testing

pytest

## Tooling

- black
- flake8
- pre-commit
- pytest
