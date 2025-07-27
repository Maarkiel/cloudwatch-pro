# CloudWatch Pro - Dokumentacja API

## Spis Treści

1. [Przegląd API](#przegląd-api)
2. [Uwierzytelnianie](#uwierzytelnianie)
3. [User Service API](#user-service-api)
4. [Metrics Collector API](#metrics-collector-api)
5. [Alert Manager API](#alert-manager-api)
6. [Dashboard Service API](#dashboard-service-api)
7. [Kody Błędów](#kody-błędów)
8. [Przykłady Użycia](#przykłady-użycia)
9. [SDK i Biblioteki](#sdk-i-biblioteki)

## Przegląd API

CloudWatch Pro udostępnia RESTful API zbudowane w oparciu o FastAPI. Wszystkie endpointy są dostępne przez API Gateway pod adresem `https://api.cloudwatch-pro.example.com`.

### Podstawowe Informacje

- **Base URL**: `https://api.cloudwatch-pro.example.com`
- **Protokół**: HTTPS
- **Format danych**: JSON
- **Uwierzytelnianie**: JWT Bearer Token
- **Rate Limiting**: 1000 żądań/godzinę na użytkownika
- **Wersjonowanie**: v1 (w URL path)

### Nagłówki HTTP

Wszystkie żądania powinny zawierać następujące nagłówki:

```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
X-API-Version: v1
```

### Struktura Odpowiedzi

Wszystkie odpowiedzi API mają spójną strukturę:

```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

W przypadku błędu:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Uwierzytelnianie

### Rejestracja Użytkownika

**POST** `/auth/register`

Rejestruje nowego użytkownika w systemie.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "organization": "Example Corp"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_123456789",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "User registered successfully"
}
```

### Logowanie

**POST** `/auth/login`

Uwierzytelnia użytkownika i zwraca JWT token.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "user_id": "usr_123456789",
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user"
    }
  },
  "message": "Login successful"
}
```

### Odświeżanie Tokenu

**POST** `/auth/refresh`

Odświeża wygasły access token używając refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "message": "Token refreshed successfully"
}
```

### Wylogowanie

**POST** `/auth/logout`

Unieważnia aktualny token użytkownika.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

## User Service API

### Profil Użytkownika

**GET** `/users/me`

Pobiera profil aktualnie zalogowanego użytkownika.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_123456789",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "organization": "Example Corp",
    "is_active": true,
    "last_login": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-10T08:00:00Z",
    "preferences": {
      "timezone": "UTC",
      "language": "en",
      "notifications": {
        "email": true,
        "push": false,
        "sms": false
      }
    }
  }
}
```

### Aktualizacja Profilu

**PUT** `/users/me`

Aktualizuje profil użytkownika.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "preferences": {
    "timezone": "Europe/Warsaw",
    "language": "pl",
    "notifications": {
      "email": true,
      "push": true,
      "sms": false
    }
  }
}
```

### Lista Użytkowników (Admin)

**GET** `/users`

Pobiera listę wszystkich użytkowników (tylko dla administratorów).

**Query Parameters:**
- `page` (int): Numer strony (domyślnie 1)
- `limit` (int): Liczba elementów na stronę (domyślnie 20)
- `search` (string): Wyszukiwanie po username/email
- `role` (string): Filtrowanie po roli
- `is_active` (bool): Filtrowanie po statusie aktywności

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "user_id": "usr_123456789",
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "user",
        "is_active": true,
        "last_login": "2024-01-15T10:30:00Z",
        "created_at": "2024-01-10T08:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

## Metrics Collector API

### Pobieranie Metryk

**GET** `/metrics`

Pobiera metryki systemu z określonego przedziału czasowego.

**Query Parameters:**
- `start_time` (string): Czas początkowy (ISO 8601)
- `end_time` (string): Czas końcowy (ISO 8601)
- `metric_type` (string): Typ metryki (cpu, memory, disk, network)
- `resource_id` (string): ID zasobu
- `aggregation` (string): Typ agregacji (avg, max, min, sum)
- `interval` (string): Interwał agregacji (1m, 5m, 1h, 1d)

**Example Request:**
```http
GET /metrics?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&metric_type=cpu&aggregation=avg&interval=5m
```

**Response:**
```json
{
  "success": true,
  "data": {
    "metric_type": "cpu",
    "aggregation": "avg",
    "interval": "5m",
    "time_range": {
      "start": "2024-01-15T00:00:00Z",
      "end": "2024-01-15T23:59:59Z"
    },
    "data_points": [
      {
        "timestamp": "2024-01-15T00:00:00Z",
        "value": 45.2,
        "resource_id": "i-1234567890abcdef0",
        "tags": {
          "instance_type": "t3.medium",
          "availability_zone": "us-west-2a"
        }
      },
      {
        "timestamp": "2024-01-15T00:05:00Z",
        "value": 52.8,
        "resource_id": "i-1234567890abcdef0",
        "tags": {
          "instance_type": "t3.medium",
          "availability_zone": "us-west-2a"
        }
      }
    ],
    "metadata": {
      "total_points": 288,
      "unit": "percent"
    }
  }
}
```

### Wysyłanie Metryk

**POST** `/metrics`

Wysyła nowe metryki do systemu.

**Request Body:**
```json
{
  "metrics": [
    {
      "metric_name": "cpu_usage",
      "value": 75.5,
      "timestamp": "2024-01-15T10:30:00Z",
      "resource_id": "i-1234567890abcdef0",
      "tags": {
        "instance_type": "t3.medium",
        "availability_zone": "us-west-2a",
        "environment": "production"
      },
      "unit": "percent"
    },
    {
      "metric_name": "memory_usage",
      "value": 8589934592,
      "timestamp": "2024-01-15T10:30:00Z",
      "resource_id": "i-1234567890abcdef0",
      "tags": {
        "instance_type": "t3.medium",
        "availability_zone": "us-west-2a",
        "environment": "production"
      },
      "unit": "bytes"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "accepted_metrics": 2,
    "rejected_metrics": 0,
    "processing_time_ms": 45
  },
  "message": "Metrics ingested successfully"
}
```

### Lista Dostępnych Metryk

**GET** `/metrics/types`

Pobiera listę dostępnych typów metryk.

**Response:**
```json
{
  "success": true,
  "data": {
    "metric_types": [
      {
        "name": "cpu_usage",
        "description": "CPU utilization percentage",
        "unit": "percent",
        "category": "system"
      },
      {
        "name": "memory_usage",
        "description": "Memory usage in bytes",
        "unit": "bytes",
        "category": "system"
      },
      {
        "name": "disk_io_read",
        "description": "Disk read operations per second",
        "unit": "ops/sec",
        "category": "storage"
      },
      {
        "name": "network_in",
        "description": "Network bytes received",
        "unit": "bytes/sec",
        "category": "network"
      }
    ]
  }
}
```

## Alert Manager API

### Lista Alertów

**GET** `/alerts`

Pobiera listę alertów.

**Query Parameters:**
- `status` (string): Status alertu (active, resolved, suppressed)
- `severity` (string): Poziom ważności (critical, warning, info)
- `start_time` (string): Czas początkowy
- `end_time` (string): Czas końcowy
- `page` (int): Numer strony
- `limit` (int): Liczba elementów na stronę

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "alert_id": "alert_123456789",
        "name": "High CPU Usage",
        "description": "CPU usage is above 80% for more than 5 minutes",
        "severity": "warning",
        "status": "active",
        "resource_id": "i-1234567890abcdef0",
        "metric_name": "cpu_usage",
        "threshold": 80,
        "current_value": 85.2,
        "triggered_at": "2024-01-15T10:25:00Z",
        "last_updated": "2024-01-15T10:30:00Z",
        "tags": {
          "environment": "production",
          "service": "web-server"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5,
      "pages": 1
    }
  }
}
```

### Tworzenie Reguły Alertu

**POST** `/alerts/rules`

Tworzy nową regułę alertu.

**Request Body:**
```json
{
  "name": "High Memory Usage",
  "description": "Alert when memory usage exceeds 85%",
  "metric_name": "memory_usage",
  "condition": "greater_than",
  "threshold": 85,
  "duration": "5m",
  "severity": "warning",
  "enabled": true,
  "tags": {
    "environment": "production"
  },
  "notification_channels": [
    "email_admin",
    "slack_devops"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rule_id": "rule_123456789",
    "name": "High Memory Usage",
    "description": "Alert when memory usage exceeds 85%",
    "metric_name": "memory_usage",
    "condition": "greater_than",
    "threshold": 85,
    "duration": "5m",
    "severity": "warning",
    "enabled": true,
    "created_at": "2024-01-15T10:30:00Z",
    "created_by": "usr_123456789"
  },
  "message": "Alert rule created successfully"
}
```

### Aktualizacja Statusu Alertu

**PUT** `/alerts/{alert_id}/status`

Aktualizuje status alertu (np. oznacza jako rozwiązany).

**Request Body:**
```json
{
  "status": "resolved",
  "resolution_note": "Issue resolved by restarting the service"
}
```

## Dashboard Service API

### Lista Dashboardów

**GET** `/dashboards`

Pobiera listę dashboardów użytkownika.

**Response:**
```json
{
  "success": true,
  "data": {
    "dashboards": [
      {
        "dashboard_id": "dash_123456789",
        "name": "System Overview",
        "description": "Main system monitoring dashboard",
        "is_public": false,
        "created_at": "2024-01-10T08:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "widgets_count": 8,
        "tags": ["system", "overview"]
      }
    ]
  }
}
```

### Szczegóły Dashboardu

**GET** `/dashboards/{dashboard_id}`

Pobiera szczegóły konkretnego dashboardu.

**Response:**
```json
{
  "success": true,
  "data": {
    "dashboard_id": "dash_123456789",
    "name": "System Overview",
    "description": "Main system monitoring dashboard",
    "layout": {
      "columns": 12,
      "rows": 8
    },
    "widgets": [
      {
        "widget_id": "widget_123",
        "type": "line_chart",
        "title": "CPU Usage",
        "position": {
          "x": 0,
          "y": 0,
          "width": 6,
          "height": 4
        },
        "config": {
          "metric_name": "cpu_usage",
          "time_range": "1h",
          "aggregation": "avg"
        }
      }
    ],
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Tworzenie Dashboardu

**POST** `/dashboards`

Tworzy nowy dashboard.

**Request Body:**
```json
{
  "name": "Custom Dashboard",
  "description": "My custom monitoring dashboard",
  "is_public": false,
  "layout": {
    "columns": 12,
    "rows": 8
  },
  "widgets": [
    {
      "type": "line_chart",
      "title": "CPU Usage",
      "position": {
        "x": 0,
        "y": 0,
        "width": 6,
        "height": 4
      },
      "config": {
        "metric_name": "cpu_usage",
        "time_range": "1h",
        "aggregation": "avg"
      }
    }
  ],
  "tags": ["custom", "monitoring"]
}
```

## Kody Błędów

### HTTP Status Codes

| Kod | Znaczenie | Opis |
|-----|-----------|------|
| 200 | OK | Żądanie wykonane pomyślnie |
| 201 | Created | Zasób utworzony pomyślnie |
| 400 | Bad Request | Nieprawidłowe dane wejściowe |
| 401 | Unauthorized | Brak autoryzacji |
| 403 | Forbidden | Brak uprawnień |
| 404 | Not Found | Zasób nie znaleziony |
| 409 | Conflict | Konflikt danych |
| 422 | Unprocessable Entity | Błąd walidacji |
| 429 | Too Many Requests | Przekroczony limit żądań |
| 500 | Internal Server Error | Błąd serwera |
| 503 | Service Unavailable | Serwis niedostępny |

### Kody Błędów Aplikacji

| Kod | Opis |
|-----|------|
| `VALIDATION_ERROR` | Błąd walidacji danych wejściowych |
| `AUTHENTICATION_FAILED` | Niepowodzenie uwierzytelniania |
| `AUTHORIZATION_FAILED` | Brak uprawnień do zasobu |
| `RESOURCE_NOT_FOUND` | Zasób nie został znaleziony |
| `DUPLICATE_RESOURCE` | Zasób już istnieje |
| `RATE_LIMIT_EXCEEDED` | Przekroczony limit żądań |
| `INVALID_TOKEN` | Nieprawidłowy token |
| `TOKEN_EXPIRED` | Token wygasł |
| `METRIC_INGESTION_FAILED` | Błąd podczas przyjmowania metryk |
| `ALERT_RULE_INVALID` | Nieprawidłowa reguła alertu |
| `DASHBOARD_SAVE_FAILED` | Błąd podczas zapisywania dashboardu |

## Przykłady Użycia

### Python SDK

```python
import requests
from datetime import datetime, timedelta

class CloudWatchProClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_metrics(self, metric_type, start_time, end_time):
        params = {
            'metric_type': metric_type,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'aggregation': 'avg',
            'interval': '5m'
        }
        response = requests.get(
            f'{self.base_url}/metrics',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def create_alert_rule(self, name, metric_name, threshold):
        data = {
            'name': name,
            'metric_name': metric_name,
            'condition': 'greater_than',
            'threshold': threshold,
            'duration': '5m',
            'severity': 'warning',
            'enabled': True
        }
        response = requests.post(
            f'{self.base_url}/alerts/rules',
            headers=self.headers,
            json=data
        )
        return response.json()

# Użycie
client = CloudWatchProClient(
    'https://api.cloudwatch-pro.example.com',
    'your_api_token_here'
)

# Pobieranie metryk CPU z ostatniej godziny
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)
cpu_metrics = client.get_metrics('cpu_usage', start_time, end_time)

# Tworzenie reguły alertu
alert_rule = client.create_alert_rule(
    'High CPU Alert',
    'cpu_usage',
    80
)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class CloudWatchProClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async getMetrics(metricType, startTime, endTime) {
        const params = {
            metric_type: metricType,
            start_time: startTime.toISOString(),
            end_time: endTime.toISOString(),
            aggregation: 'avg',
            interval: '5m'
        };

        const response = await axios.get(`${this.baseUrl}/metrics`, {
            headers: this.headers,
            params: params
        });

        return response.data;
    }

    async createDashboard(name, description, widgets) {
        const data = {
            name: name,
            description: description,
            is_public: false,
            layout: { columns: 12, rows: 8 },
            widgets: widgets
        };

        const response = await axios.post(`${this.baseUrl}/dashboards`, data, {
            headers: this.headers
        });

        return response.data;
    }
}

// Użycie
const client = new CloudWatchProClient(
    'https://api.cloudwatch-pro.example.com',
    'your_api_token_here'
);

// Pobieranie metryk
const endTime = new Date();
const startTime = new Date(endTime.getTime() - 60 * 60 * 1000); // 1 godzina temu

client.getMetrics('cpu_usage', startTime, endTime)
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

### cURL Examples

```bash
# Logowanie
curl -X POST https://api.cloudwatch-pro.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123!"
  }'

# Pobieranie metryk
curl -X GET "https://api.cloudwatch-pro.example.com/metrics?metric_type=cpu_usage&start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Tworzenie alertu
curl -X POST https://api.cloudwatch-pro.example.com/alerts/rules \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High CPU Usage",
    "metric_name": "cpu_usage",
    "condition": "greater_than",
    "threshold": 80,
    "duration": "5m",
    "severity": "warning",
    "enabled": true
  }'
```

## SDK i Biblioteki

### Oficjalne SDK

- **Python**: `pip install cloudwatch-pro-sdk`
- **JavaScript/Node.js**: `npm install cloudwatch-pro-sdk`
- **Go**: `go get github.com/cloudwatch-pro/go-sdk`
- **Java**: Maven/Gradle dependency

### Community Libraries

- **PHP**: `composer require cloudwatch-pro/php-client`
- **Ruby**: `gem install cloudwatch_pro`
- **C#**: NuGet package `CloudWatchPro.Client`

### Postman Collection

Dostępna jest kolekcja Postman z wszystkimi endpointami API:

```bash
# Import kolekcji
curl -o cloudwatch-pro.postman_collection.json \
  https://api.cloudwatch-pro.example.com/docs/postman
```

### OpenAPI Specification

Pełna specyfikacja OpenAPI 3.0 dostępna pod adresem:
- **JSON**: `https://api.cloudwatch-pro.example.com/openapi.json`
- **YAML**: `https://api.cloudwatch-pro.example.com/openapi.yaml`
- **Interactive Docs**: `https://api.cloudwatch-pro.example.com/docs`

---

Ta dokumentacja API zapewnia kompletny przewodnik po wszystkich dostępnych endpointach CloudWatch Pro. Dla najnowszych informacji i interaktywnej dokumentacji, odwiedź `https://api.cloudwatch-pro.example.com/docs`.

