# Kukuri Protocol

**Kukuri Protocol** is a real-time chat application built with Python, utilizing WebSocket for server-client communication. The client-side UI is developed using PyQt6, while the server manages message handling and user data with SQLite as the persistent storage solution.

## Features
- Real-time messaging via WebSocket
- User registration and login system
- Persistent chat history stored in SQLite
- PyQt6-based user interface with custom themes
- Profile management and status updates
- Image and text message support
- Theme Manager

## Information
- **(Client)**: PyQt6
- **Server)**: Python, WebSocket, SQLite
- **(Database)**: SQLite
- **(Theme)**: Python, CSS

## Setup & Installation

### Prerequisites
- Python 3.7 or above
- `pip` package manager

### Required Libraries
Install the required dependencies with:

```bash
$ pip install -r requirements.txt
```
## Running the Application
### 1. Server:
Run the WebSocket server by:
```
$ py server.py
```
### 2. Client:
Launch the chat client with:
```
$ py client.py
```
## Folder Structure
```
Kukuri.Protocol/
├── client.py        # Client-side code with PyQt6 UI
├── server.py        # WebSocket server handling connections
├── database.py      # SQLite database operations
├── theme_manager.py # (Optional) Theme management for UI
├── README.md        # Project overview
└── requirements.txt # List of required dependencies
```
## How It Works
- The client connects to the WebSocket server and allows users to send and receive messages in real-time.
- The server authenticates users, manages their profiles, stores chat history, and ensures message delivery between online users.
- The SQLite database stores user information, chat history, and profile data, enabling message persistence across sessions.
## Contributing
Feel free to contribute to this project by submitting a pull request or reporting issues.
