# 🗓️ Event Management Microservice System

A microservice-based event management system built with **FastAPI**, **MongoDB (Beanie)**, **RabbitMQ**, and **WebSockets**. Includes JWT-based authentication, real-time notifications, and modular service separation.

---

## 🚀 Features

### 🔹 Event Service
- Create, read, update, delete (CRUD) events
- MongoDB integration via **Beanie** ODM
- Publishes events to **RabbitMQ** on changes
- JWT-based authentication (register/login)

### 🔹 Notification Service
- Listens to RabbitMQ event messages
- Sends **WebSocket notifications** to connected users
- Stores notification history in MongoDB

---

## 🧱 Architecture

```
[Client]                        [User]
   ↓                              ↓ 
 WebSocket                      REST API
   ↓                              ↓
Notification Service ← RabbitMQ ← Event Service
            ↓                        ↓
          MongoDB                  MongoDB
```

---

## ⚙️ Tech Stack
- **FastAPI** for web framework
- **MongoDB** with **Beanie** (async ODM)
- **RabbitMQ** for messaging
- **JWT** for secure authentication
- **WebSockets** for real-time updates
- **Docker** and **Docker Compose** for containerization

---

## 📦 Setup Instructions

### 🔧 Prerequisites
- Docker + Docker Compose installed (⚠️ currently not supported)
- Python 3.10+ (if running locally)

### 🚀 Run with Docker Compose (⚠️ currently not supported)
```bash
docker-compose up --build
```

### 🔄 Services exposed
- Event Service: [http://localhost:8000](http://localhost:8000)
- Notification Service: [http://localhost:8001](http://localhost:8001)
- RabbitMQ Admin: [http://localhost:15672](http://localhost:15672)
  - Default: `guest:guest`

---

## 🔐 Authentication

### Registration
```http
POST /register
```
Fields:
- `username`, `email`, `password`, `full_name`

### Login
```http
POST /login
```
Returns:
- `access_token`
Rate Limits:
- 5 requests/minute per IP

Use token in headers:
```http
Authorization: Bearer <token>
```

---

## 📘 API Docs

- Event Service: [http://localhost:8000/docs](http://localhost:8000/docs)
- Notification Service: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## ✅ Testing

### Run tests (not implemented yet)
```bash
pytest
```

Mocked tests for:
- Event creation
- User login
- Notification propagation


---

## 📝 Todo / Improvements
- Role-based permissions
- Owner events notifications
- Redis-based rate limiting

---

## 📄 Scaling
To increase throughput, you can consider the option of increasing the number of consumers, as well as dividing queues by event type.

Horizontal scaling is possible by balancing the load by IP and allocating a separate exchange for each worker, and each worker must also send events to all exchanges.

