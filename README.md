# Arii AI Backend

A comprehensive Django REST API backend for a rental property management platform that connects property owners, tenants, and service vendors.

## 🏗️ Project Overview

Arii AI is a multi-tenant rental property management system that facilitates:

- Property listing and management
- Tenant applications and lease management
- Vendor services and invitations
- User authentication with role-based access
- Document management and KYC verification

## 🚀 Features

### Core Functionality

- **Multi-role Authentication**: Property owners, tenants, vendors, and admins
- **Property Management**: Create, list, and manage rental properties with units
- **Rental Applications**: Complete application workflow from submission to approval
- **Vendor Services**: Service provider management and invitation system
- **Document Management**: KYC documents, lease agreements, and property documents
- **Real-time Notifications**: Email-based invitation and notification system

### Technical Features

- JWT-based authentication with refresh tokens
- PostgreSQL database with comprehensive data modeling
- AWS S3 integration for file storage
- Docker containerization for development and deployment
- CORS support for frontend integration

## 🛠️ Technology Stack

- **Framework**: Django 4.2.20 with Django REST Framework 3.16.0
- **Database**: PostgreSQL 13
- **Authentication**: JWT (djangorestframework-simplejwt)
- **File Storage**: AWS S3 (django-storages, boto3)
- **Documentation**: drf-yasg (Swagger/OpenAPI)
- **Image Processing**: Pillow
- **Data Processing**: pandas, openpyxl
- **Containerization**: Docker & Docker Compose

## 🧰 Development Workflow

The project uses a Makefile to simplify common development tasks.

| Command           | Description              |
| ----------------- | ------------------------ |
| make install-deps | Install dependencies     |
| make add-deps     | Update requirements.txt  |
| make format       | Format code using Black  |
| make lint         | Run Ruff linter          |
| make lint-fix     | Auto-fix linting issues  |
| make clean        | Remove cache files       |
| make hooks        | Install pre-commit hooks |

### Example Workflow:

1. make install-deps
2. make hooks
3. make format
4. make lint
5. make lint-fix

## 🧹 Code Quality & Standards

- Black for formatting
- Ruff for linting and import sorting
- Pre-commit hooks for enforcing style before commit

### Commands:

- make format → Format code
- make lint → Check for issues
- make lint-fix → Fix issues
- make hooks → Install hooks
- git commit --no-verify → Bypass hook (only in emergencies)

### 🧑‍💻 Contribution Guidelines

- Use feature-based branches: feature/<description> or fix/<description>
- Use conventional commits:
  - feat(auth): implement refresh token rotation
  - fix(properties): resolve property detail API bug
  - refactor: clean up utility imports
- Ensure all code passes lint and formatting before PRs

### 🧩 Developer Environment

Recommended VS Code Extensions:

- Black Formatter
- Ruff
- Python (Microsoft)
- Prettier
- EditorConfig

## 🧾 Notes

This project enforces a clean, standardized Python codebase.
All contributors must:

- Run make lint and make format before commits
- Keep requirements.txt updated via make add-deps

## 📁 Project Structure

```
rental-guru-backend/
├── rental_guru/              # Main Django project
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── constants.py         # Application constants
│   └── utils.py             # Utility functions
├── user_management/      # User management app
│   ├── models.py            # User, roles, and profile models
│   ├── views.py             # Authentication and profile views
│   ├── serializers.py       # API serializers
│   └── urls.py              # Authentication URLs
├── properties/               # Property management app
│   ├── models.py            # Property, unit, and listing models
│   ├── views.py             # Property CRUD operations
│   ├── serializers.py       # Property serializers
│   └── urls.py              # Property URLs
├── rental_application/       # Application management app
│   ├── models.py            # Rental application models
│   ├── views.py             # Application workflow views
│   ├── serializers.py       # Application serializers
│   └── urls.py              # Application URLs
├── media/                    # Media files storage
│   ├── documents/           # General documents
│   ├── kyc_docs/           # KYC verification documents
│   └── profile_images/      # User profile images
├── logs/                     # Application logs
├── docker-compose-dev.yaml   # Development Docker setup
├── docker-compose-qa.yaml    # QA environment setup
├── docker-compose-stag.yaml  # Staging environment setup
├── Dockerfile               # Docker image configuration
├── entrypoint.sh            # Docker entrypoint script
└── requirements.txt         # Python dependencies
```

## 🔧 Installation & Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (for containerized setup)
- AWS S3 bucket (for file storage)

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd rental-guru-backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:

   ```env
   # Database Configuration
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=rental_guru_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432

   # CORS and Security
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   CORS_ORIGIN_WHITELIST=http://localhost:3000,http://127.0.0.1:3000

   # AWS S3 Configuration (Optional)
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_STORAGE_BUCKET_NAME=your_bucket_name
   AWS_S3_REGION_NAME=us-east-1

   # Superuser Configuration (Optional)
   SUPERUSER_EMAIL=admin@example.com
   SUPERUSER_PASSWORD=admin123
   ```

5. **Database Setup**

   ```bash
   # Create PostgreSQL database
   createdb rental_guru_db

   # Run migrations
   python manage.py migrate

   # Create superuser
   python manage.py createsuperuser
   ```

6. **Install Git Hooks**

   ```bash
   pre-commit install
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

### Docker Development Setup

1. **Using Docker Compose**

   ```bash
   # Start all services (API + Database + Adminer)
   docker-compose -f docker-compose-dev.yaml up -d

   # View logs
   docker-compose -f docker-compose-dev.yaml logs -f

   # Stop services
   docker-compose -f docker-compose-dev.yaml down
   ```

2. **Access Services**
   - API: http://localhost:8000
   - Swagger Documentation: http://localhost:8000/swagger/
   - Adminer (Database UI): http://localhost:8080
   - Django Admin: http://localhost:8000/admin/

## 📚 API Documentation

### Base URL

- Development: `http://localhost:8000/v1/api/`
- Swagger UI: `http://localhost:8000/swagger/`

### Main Endpoints

#### Authentication (`/v1/api/`)

- `POST /signup/` - User registration
- `POST /token/` - Login (JWT token)
- `POST /token/refresh/` - Refresh JWT token
- `POST /logout/` - Logout
- `POST /otp/` - Generate OTP
- `POST /otp-verify/` - Verify OTP
- `POST /forgot-password/` - Password reset request
- `POST /reset-password/` - Reset password

#### Properties (`/v1/api/property/`)

- `GET /summary/` - Property listings
- `POST /detail/` - Create property
- `GET /detail/{id}/` - Property details
- `PUT /detail/{id}/` - Update property
- `DELETE /detail/{id}/` - Delete property
- `POST /listing/` - Create listing info
- `POST /rental/` - Create rental details
- `GET /amenities/` - Available amenities

#### Rental Applications (`/v1/api/rental-application/`)

- `POST /apply/` - Submit application
- `GET /my-applications/` - User's applications
- `GET /received-applications/` - Property owner's received applications
- `GET /applications/{id}/` - Application details
- `POST /submit-lease-agreement/` - Submit lease agreement

## 🗄️ Database Schema

### Key Models

#### User Authentication

- **CustomUser**: Extended user model with business info and subscription plans
- **PropertyOwner**: Property owner profile with KYC information
- **Tenant**: Tenant profile with income and employment details
- **Vendor**: Service provider profile with specializations
- **VendorInvitation**: Vendor invitation system
- **TenantInvitation**: Tenant invitation system

#### Properties

- **Property**: Main property information
- **Unit**: Individual units within properties
- **ListingInfo**: Detailed listing information
- **RentDetails**: Pricing and rental terms
- **PropertyDocument**: Document management
- **CalendarSlot**: Availability scheduling

#### Applications

- **RentalApplication**: Rental application submissions
- **ApplicationLeaseAgreement**: Lease agreement documents

## 🔐 Authentication & Authorization

The system uses JWT-based authentication with role-based access control:

- **Property Owners**: Can create/manage properties, review applications
- **Tenants**: Can browse properties, submit applications
- **Vendors**: Can provide services, respond to invitations
- **Admins**: Full system access

### JWT Configuration

- Access token lifetime: 1 day
- Refresh token lifetime: 1 day
- Token blacklisting supported

---

**Note**: This README provides a comprehensive overview of the Arii AI Backend. For detailed API documentation, please refer to the Postman Collection.
