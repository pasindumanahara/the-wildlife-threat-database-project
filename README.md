# The Wildlife Threat Database Project

A full-stack web application designed to document, manage, and analyze threats to wildlife and biodiversity. The Wildlife Threat Database Project aims to support wildlife conservation through a centralized platform for managing wildlife-related information and identifying potential threats.

## Tech Stack

| Layer           | Technologies                 |
| --------------- | ---------------------------- |
| Frontend        | React.js, Tailwind CSS, Vite |
| Backend         | Django                       |
| Database        | PostgreSQL                   |
| Version Control | Git, GitHub                  |

## Project Structure

```text
the-wildlife-threat-database-project/
├── client/                 # React + Tailwind CSS frontend
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── server/                 # Django backend
├── database/               # PostgreSQL application schema
├── scripts/                # Local setup and run scripts
│
├── .gitignore
└── README.md
```

## Features

## API Documentation

The Django backend provides signup, login, logout, CSRF, and current-user
endpoints under `/api/auth/`. The client calls these endpoints through Vite's
`/api` proxy.

The application tables come from `database/001_initial_schema.sql`. Django's
separate admin and session tables are created by its migrations.

## Local setup on Windows

From PowerShell in the project root:

```powershell
.\scripts\setup-database.ps1
```

If `server/.env` does not exist, copy `server/.env.example` to it. Generate a
key with `.\server\.venv\Scripts\python.exe scripts\gen_key.py` and paste it
into `NIC_ENCRYPTION_KEY` in `server/.env`. Keep any existing key; replacing it
would make stored NICs unreadable. Then run:

```powershell
.\scripts\run-project.ps1
```

The setup script installs backend dependencies, creates `wildlife_threat_db`,
and runs the SQL and Django migrations. The run script starts Django and Vite
and asks for your PostgreSQL password. Open `http://127.0.0.1:5173/`.

## Environment Variables

Environment variables should be used for database credentials, secret keys, and other sensitive configuration.

Never commit actual `.env` files containing secrets.

## NIC encryption

The backend encrypts NIC values before saving them to `users.nic_encrypted`.
Set a separate `NIC_ENCRYPTION_KEY` in `server/.env` (see `server/.env.example`).
Generate a key with `.\server\.venv\Scripts\python.exe scripts\gen_key.py` from
the project root. Keep a secure backup of that key: changing or losing it
prevents existing NIC values from being decrypted.

## Contributing

Pasindu Manahara
Dulith Siriwardane
Yohan Kaushalya
Damiru Amaneth
Saliha Thalhan
Sanduni Nimeshika

## Development Status

**Status:** Under Development

Project functionality and documentation will be updated as implementation progresses.
