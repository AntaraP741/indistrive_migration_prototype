# Migration Accelerator

A full-stack proof of concept for assessing and migrating relational PostgreSQL data to MongoDB. It discovers a source schema, analyzes dependencies and migration risk, recommends an embedding strategy, migrates the selected data, and produces validation reports.

The project includes both a Python command-line pipeline and a React dashboard for demonstrating the workflow.

## What it does

- Connects to a PostgreSQL source database and discovers tables, columns, primary keys, and foreign-key relationships.
- Builds a readiness report with table metadata, row counts, checksums, dependency metrics, sizing information, and a risk assessment.
- Determines a document-model strategy, including opportunities to embed related child records.
- Migrates PostgreSQL tables to MongoDB, converting primary keys to MongoDB `_id` values.
- Creates a post-migration report to compare source and target counts.
- Provides a browser dashboard to test a connection, select tables, run the assessment, and start a migration.

> **Current live connectors:** PostgreSQL as the source and MongoDB as the target. Other connector choices shown in the dashboard are preview/UI options and are not implemented in the backend.

## Architecture

```text
PostgreSQL source
      |
      v
Schema discovery -> dependency / sizing / risk assessment -> readiness report
      |
      v
Canonical model -> relationship analysis -> embedding decision
      |
      v
MongoDB target -> post-migration validation report
```

## Tech stack

- **Backend:** Python, `psycopg2`, PyMongo, Python standard-library HTTP server
- **Frontend:** React, Vite
- **Source database:** PostgreSQL
- **Target database:** MongoDB

## Project structure

```text
assessment/       Schema crawling, dependency analysis, sizing, and risk scoring
migration/        PostgreSQL reader, MongoDB writer, and migration orchestration
transformation/   Canonical model, relationship analysis, embedding, and document building
validation/       Post-migration report generation
ui/react-dashboard/ React/Vite dashboard
outputs/          Generated readiness and post-migration JSON reports
main.py           Command-line migration entry point
app_api.py        Local API used by the dashboard
```

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer (dashboard only)
- A running PostgreSQL database
- A running MongoDB instance or MongoDB Atlas database

## Run the command-line migration

1. Clone the repository and open PowerShell in the project folder.

2. Install the Python dependencies:

```powershell
py -m pip install -r requirements.txt
```

3. Set the database configuration for the current terminal session:

```powershell
$env:PG_HOST="localhost"
$env:PG_PORT="5432"
$env:PG_DATABASE="your_postgres_database"
$env:PG_USER="your_postgres_user"
$env:PG_PASSWORD="your_postgres_password"
$env:PG_SCHEMA="public"

$env:MONGO_URI="mongodb://localhost:27017/"
$env:MONGO_DATABASE="your_mongo_database"
```

4. Run the pipeline:

```powershell
py main.py
```
## Live Demo

[Open the Migration Accelerator dashboard](https://indistrive-migration-prototype-p76v.vercel.app/)
