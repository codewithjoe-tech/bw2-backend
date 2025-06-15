

# 🐳 bw2-backend

This is the backend for the **bw2** project, built with Django and containerized using Docker. It can be run locally with ease using Docker Compose.

## 🚀 Quick Start

Follow these steps to run the backend locally on your system.

---

### 📦 Prerequisites

Before you begin, ensure that the following are installed on your machine:

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

---

### 🔧 Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/codewithjoe-tech/bw2-backend.git
cd bw2-backend
```

2. **Start the services**

```bash
docker-compose up --build
```

This will:

* Build the Docker image for the Django project.
* Start all necessary services (including the Django app and PostgreSQL).

3. **Access the application**

* **API root**: [http://localhost:8000/](http://localhost:8000/)
* **Django admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

### ⚙️ Common Docker Commands

* **Stop all running containers**

```bash
docker-compose down
```

* **Run database migrations**

```bash
docker-compose exec web python manage.py migrate
```

* **Create a superuser**

```bash
docker-compose exec web python manage.py createsuperuser
```

* **View logs**

```bash
docker-compose logs -f
```

---

### 🗂️ Project Structure

```
bw2-backend/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── mysite/         
├── authenticate/   
└── chats/          
```

---

### 🛠️ Troubleshooting



```bash
docker-compose up --build
```

* To reset the containers and volumes:

```bash
docker-compose down -v
```

---

### 📝 License

This project is licensed under the [MIT License](LICENSE).

---

Let me know if you'd like this written to a `README.md` file directly or tailored for production deployment as well.
