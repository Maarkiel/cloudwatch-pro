# CloudWatch Pro - Real-time Infrastructure Monitoring Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue.svg)](https://kubernetes.io/)
[![Terraform](https://img.shields.io/badge/Terraform-Ready-purple.svg)](https://www.terraform.io/)
[![Python](https://img.shields.io/badge/Python-3.11-green.svg)](https://www.python.org/)

> **Uwaga**: Ten projekt został stworzony jako demonstracja umiejętności DevOps Engineer w ramach portfolio zawodowego. Przedstawia zaawansowane techniki orkiestracji kontenerów, automatyzacji infrastruktury oraz monitoringu w czasie rzeczywistym.

## 🚀 Przegląd Projektu

CloudWatch Pro to zaawansowana platforma monitoringu infrastruktury w czasie rzeczywistym, zbudowana z wykorzystaniem nowoczesnych technologii DevOps. System oferuje kompleksowe rozwiązanie do monitorowania, alertowania i analizy wydajności infrastruktury chmurowej z wykorzystaniem architektury mikrousług.

### ✨ Kluczowe Funkcjonalności

- **Monitoring w Czasie Rzeczywistym**: Zbieranie i analiza metryk z infrastruktury chmurowej

- **Inteligentne Alertowanie**: Zaawansowany system powiadomień z uczeniem maszynowym

- **Analiza Kosztów**: Optymalizacja wydatków na infrastrukturę chmurową

- **Predykcyjna Analityka**: Przewidywanie problemów przed ich wystąpieniem

- **Multi-Cloud Support**: Wsparcie dla AWS, Azure i Google Cloud Platform

- **Skalowalna Architektura**: Mikrousługi z automatycznym skalowaniem

- **Bezpieczeństwo**: Kompleksowe zabezpieczenia i szyfrowanie danych

### 🏗️ Architektura Systemu

System wykorzystuje architekturę mikrousług z następującymi komponentami:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │   API Gateway   │    │  User Service   │
│   (Frontend)    │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Metrics Service │    │ Alert Manager   │    │ Cost Analyzer   │
│   (FastAPI)     │    │   (FastAPI)     │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    InfluxDB     │    │      Redis      │
│   (Users DB)    │    │   (Metrics)     │    │     (Cache)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Stack Technologiczny

### Backend & APIs

- **Python 3.11** - Język programowania

- **FastAPI** - Framework do budowy API

- **SQLAlchemy** - ORM dla baz danych

- **Pydantic** - Walidacja danych

- **Celery** - Asynchroniczne przetwarzanie zadań

### Frontend

- **React 18** - Framework frontend

- **TypeScript** - Typowany JavaScript

- **Tailwind CSS** - Framework CSS

- **Recharts** - Biblioteka wykresów

- **React Query** - Zarządzanie stanem serwera

### Bazy Danych

- **PostgreSQL** - Główna baza danych

- **InfluxDB** - Baza danych czasowych dla metryk

- **Redis** - Cache i session store

- **Elasticsearch** - Wyszukiwanie i analityka

### DevOps & Infrastructure

- **Docker** - Konteneryzacja

- **Kubernetes** - Orkiestracja kontenerów

- **Terraform** - Infrastructure as Code

- **Helm** - Zarządzanie pakietami Kubernetes

- **NGINX** - Reverse proxy i load balancer

### Monitoring & Observability

- **Prometheus** - Zbieranie metryk

- **Grafana** - Wizualizacja danych

- **Jaeger** - Distributed tracing

- **ELK Stack** - Centralne logowanie

### Cloud Providers

- **AWS** - Amazon Web Services

- **Azure** - Microsoft Azure

- **GCP** - Google Cloud Platform

## 📋 Wymagania Systemowe

### Lokalne Środowisko Deweloperskie

- **Docker** >= 20.10

- **Docker Compose** >= 2.0

- **Python** >= 3.11

- **Node.js** >= 18.0

- **Make** (opcjonalnie, dla ułatwienia)

### Środowisko Produkcyjne

- **Kubernetes** >= 1.25

- **Terraform** >= 1.0

- **Helm** >= 3.0

- **kubectl** - klient Kubernetes

- Dostęp do providera chmurowego (AWS/Azure/GCP)

## 🚀 Szybki Start

### 1. Klonowanie Repozytorium

```bash
git clone https://github.com/your-username/cloudwatch-pro.git
cd cloudwatch-pro
```

### 2. Lokalne Środowisko Deweloperskie

```bash
# Kopiowanie plików konfiguracyjnych
cp services/user-service/.env.example services/user-service/.env
cp services/metrics-collector/.env.example services/metrics-collector/.env
cp services/api-gateway/.env.example services/api-gateway/.env

# Uruchomienie wszystkich serwisów
make dev

# Alternatywnie bez Make
docker-compose up -d
```

### 3. Dostęp do Aplikacji

Po uruchomieniu aplikacja będzie dostępna pod adresami:

- **Dashboard**: [http://localhost:3000](http://localhost:3000)

- **API Gateway**: [http://localhost:8000](http://localhost:8000)

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

- **Grafana**: [http://localhost:3001](http://localhost:3001) (admin/admin123)

- **Prometheus**: [http://localhost:9090](http://localhost:9090)

## 🔧 Konfiguracja Środowiska

### Zmienne Środowiskowe

Każdy serwis wymaga odpowiedniej konfiguracji zmiennych środowiskowych. Przykładowe pliki `.env.example` znajdują się w katalogach poszczególnych serwisów.

#### User Service (.env)

```bash
DATABASE_URL=postgresql://cloudwatch:cloudwatch123@postgres:5432/cloudwatch_users
REDIS_HOST=redis
REDIS_PORT=6379
SECRET_KEY=your-super-secret-key-for-development-only
LOG_LEVEL=INFO
```

#### Metrics Collector (.env)

```bash
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=cloudwatch-super-secret-token
INFLUXDB_ORG=cloudwatch-pro
INFLUXDB_BUCKET=metrics
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Konfiguracja Bazy Danych

System automatycznie inicjalizuje bazy danych przy pierwszym uruchomieniu. Skrypt inicjalizacyjny znajduje się w `scripts/init-db.sql`.

## 🏗️ Wdrożenie Produkcyjne

### AWS Deployment

```bash
# Przejście do katalogu infrastruktury
cd infrastructure/aws

# Kopiowanie i edycja pliku konfiguracyjnego
cp terraform.tfvars.example terraform.tfvars
# Edytuj terraform.tfvars zgodnie z Twoimi wymaganiami

# Wdrożenie infrastruktury
../scripts/deploy.sh production aws apply
```

### Azure Deployment

```bash
cd infrastructure/azure
cp terraform.tfvars.example terraform.tfvars
# Edytuj terraform.tfvars

../scripts/deploy.sh production azure apply
```

### Google Cloud Deployment

```bash
cd infrastructure/gcp
cp terraform.tfvars.example terraform.tfvars
# Edytuj terraform.tfvars

../scripts/deploy.sh production gcp apply
```

## 📊 Monitoring i Observability

### Metryki Systemu

System zbiera następujące metryki:

- **Infrastruktura**: CPU, pamięć, dysk, sieć

- **Aplikacja**: Czas odpowiedzi, throughput, błędy

- **Biznesowe**: Liczba użytkowników, transakcje, koszty

- **Bezpieczeństwo**: Próby logowania, anomalie, zagrożenia

### Dashboardy Grafana

Predefiniowane dashboardy obejmują:

1. **System Overview** - Ogólny przegląd systemu

1. **Application Performance** - Wydajność aplikacji

1. **Infrastructure Monitoring** - Monitoring infrastruktury

1. **Cost Analysis** - Analiza kosztów

1. **Security Dashboard** - Dashboard bezpieczeństwa

### Alertowanie

System alertów obejmuje:

- **Krytyczne**: Awarie serwisów, brak dostępności

- **Ostrzeżenia**: Wysokie wykorzystanie zasobów

- **Informacyjne**: Zmiany konfiguracji, aktualizacje

## 🔒 Bezpieczeństwo

### Implementowane Zabezpieczenia

- **Szyfrowanie**: TLS/SSL dla wszystkich połączeń

- **Uwierzytelnianie**: JWT tokens z refresh mechanism

- **Autoryzacja**: Role-based access control (RBAC)

- **Network Security**: Network policies, security groups

- **Secrets Management**: Kubernetes secrets, HashiCorp Vault

- **Vulnerability Scanning**: Regularne skanowanie kontenerów

### Best Practices

- Regularne aktualizacje zależności

- Minimalne uprawnienia (principle of least privilege)

- Audit logging wszystkich operacji

- Backup i disaster recovery procedures

- Security monitoring i incident response

## 🧪 Testowanie

### Uruchomienie Testów

```bash
# Testy jednostkowe
make test

# Testy integracyjne
make test-integration

# Testy wydajnościowe
make test-performance

# Wszystkie testy
make test-all
```

### Pokrycie Testów

Projekt utrzymuje wysokie pokrycie testów:

- **Unit Tests**: >90%

- **Integration Tests**: >80%

- **End-to-End Tests**: >70%

## 📈 Skalowanie

### Horizontal Pod Autoscaler

System automatycznie skaluje się na podstawie:

- Wykorzystania CPU (>70%)

- Wykorzystania pamięci (>80%)

- Liczby żądań na sekundę

- Niestandardowych metryk biznesowych

### Cluster Autoscaler

Kubernetes cluster automatycznie dodaje/usuwa węzły na podstawie zapotrzebowania.

### Database Scaling

- **Read Replicas**: Automatyczne tworzenie replik do odczytu

- **Connection Pooling**: Optymalizacja połączeń do bazy danych

- **Caching**: Wielopoziomowe cache'owanie danych

## 💰 Optymalizacja Kosztów

### Implementowane Strategie

- **Spot Instances**: Wykorzystanie tańszych instancji spot

- **Scheduled Scaling**: Skalowanie zgodnie z harmonogramem

- **Resource Optimization**: Optymalizacja zasobów na podstawie metryk

- **Cost Monitoring**: Ciągły monitoring kosztów z alertami

### Szacowane Koszty Miesięczne

| Środowisko | AWS | Azure | GCP |
| --- | --- | --- | --- |
| Development | $50-100 | $45-90 | $40-85 |
| Staging | $150-300 | $140-280 | $130-260 |
| Production | $500-1500 | $450-1350 | $400-1200 |

*Koszty mogą się różnić w zależności od wykorzystania i konfiguracji.

## 🤝 Współpraca

### Struktura Projektu

```
cloudwatch-pro/
├── services/                 # Mikrousługi
│   ├── api-gateway/         # API Gateway
│   ├── user-service/        # Serwis użytkowników
│   ├── metrics-collector/   # Kolektor metryk
│   └── ...
├── dashboard/               # Frontend React
├── k8s/                    # Manifesty Kubernetes
├── infrastructure/         # Terraform modules
├── monitoring/             # Konfiguracja monitoringu
├── scripts/               # Skrypty pomocnicze
└── docs/                  # Dokumentacja
```

### Workflow Rozwoju

1. **Feature Branch**: Tworzenie brancha dla nowej funkcjonalności

1. **Development**: Rozwój z testami lokalnymi

1. **Pull Request**: Code review i testy automatyczne

1. **Staging**: Wdrożenie na środowisko testowe

1. **Production**: Wdrożenie produkcyjne po zatwierdzeniu

### Standardy Kodowania

- **Python**: PEP 8, Black formatter, mypy type checking

- **JavaScript/TypeScript**: ESLint, Prettier

- **Docker**: Multi-stage builds, security best practices

- **Kubernetes**: Resource limits, security contexts

- **Terraform**: Consistent naming, modular structure

## 📚 Dokumentacja

### Dostępne Dokumenty

- [API Documentation](docs/api.md) - Szczegółowa dokumentacja API

- [Deployment Guide](docs/deployment.md) - Przewodnik wdrożenia

- [Architecture Guide](docs/architecture.md) - Architektura systemu

- [Security Guide](docs/security.md) - Przewodnik bezpieczeństwa

- [Troubleshooting](docs/troubleshooting.md) - Rozwiązywanie problemów

### Generowanie Dokumentacji

```bash
# Dokumentacja API
make docs-api

# Dokumentacja architektury
make docs-architecture

# Wszystkie dokumenty
make docs-all
```

## 🐛 Rozwiązywanie Problemów

### Częste Problemy

#### Problem: Serwisy nie mogą się połączyć z bazą danych

```bash
# Sprawdzenie statusu bazy danych
kubectl get pods -n cloudwatch-pro | grep postgres

# Sprawdzenie logów
kubectl logs -n cloudwatch-pro deployment/postgres
```

#### Problem: Wysokie wykorzystanie pamięci

```bash
# Sprawdzenie wykorzystania zasobów
kubectl top pods -n cloudwatch-pro

# Skalowanie serwisu
kubectl scale deployment user-service --replicas=3 -n cloudwatch-pro
```

### Logi i Debugging

```bash
# Sprawdzenie logów wszystkich serwisów
make logs

# Sprawdzenie logów konkretnego serwisu
make logs-user

# Monitoring w czasie rzeczywistym
make logs-f
```

## 🔄 CI/CD Pipeline

### GitHub Actions

Projekt wykorzystuje GitHub Actions dla:

- **Continuous Integration**: Automatyczne testy przy każdym commit

- **Security Scanning**: Skanowanie bezpieczeństwa kodu i kontenerów

- **Build & Push**: Budowanie i publikowanie obrazów Docker

- **Deployment**: Automatyczne wdrożenie na środowiska

### Pipeline Stages

1. **Lint & Test**: Sprawdzenie jakości kodu i uruchomienie testów

1. **Security Scan**: Skanowanie bezpieczeństwa

1. **Build**: Budowanie obrazów Docker

1. **Deploy to Staging**: Wdrożenie na środowisko testowe

1. **Integration Tests**: Testy integracyjne

1. **Deploy to Production**: Wdrożenie produkcyjne (manual approval)

## 📄 Licencja

Ten projekt jest udostępniony na licencji MIT. Zobacz plik [LICENSE](LICENSE) dla szczegółów.

## 👥 Autorzy

- **Mateusz Błaziak **- *Initial work* - [GitHub](https://github.com/Maarkiel)

---

**Uwaga**: Ten projekt został stworzony w celach demonstracyjnych jako część portfolio DevOps Engineer. Przedstawia zaawansowane techniki i best practices w zakresie orkiestracji kontenerów, automatyzacji infrastruktury oraz monitoringu systemów rozproszonych.

