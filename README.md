# To-Do List API

A simple REST API for managing tasks built with Flask and SQLite.

## Features

- User registration and login
- Password hashing with SHA-256
- Task management (add, list, edit, delete)
- Task status tracking (pending, in_progress, done)
- Task priority (low, medium, high)
- Categories for organizing tasks
- Foreign key relationships between tables

## Technologies

- Python 3
- Flask
- SQLite
- RESTful API design

## API Endpoints

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Login and get user info |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/<user_id>` | Get user tasks |
| POST | `/api/tasks` | Add a new task |
| PUT | `/api/tasks/<id>` | Update a task |
| PUT | `/api/tasks/<id>/complete` | Mark task as done |
| DELETE | `/api/tasks/<id>` | Delete a task |

## How to Run

```bash
pip install -r requirements.txt
python todo_api.py
