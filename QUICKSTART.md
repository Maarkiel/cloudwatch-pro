# CloudWatch Pro - Szybki Start

## 🚀 Witaj w CloudWatch Pro!

Gratulacje! Masz teraz dostęp do zaawansowanej platformy monitoringu infrastruktury CloudWatch Pro. Ten przewodnik pomoże Ci szybko uruchomić projekt i zacząć korzystać z jego możliwości.

## 📋 Co otrzymałeś?

Kompletny projekt DevOps zawierający:

✅ **Mikrousługi Python** - 8 serwisów zbudowanych w FastAPI  
✅ **React Dashboard** - Nowoczesny interfejs użytkownika  
✅ **Docker & Kubernetes** - Pełna konteneryzacja i orkiestracja  
✅ **Terraform** - Infrastructure as Code dla AWS/Azure/GCP  
✅ **Monitoring Stack** - Prometheus, Grafana, ELK  
✅ **CI/CD Pipeline** - Automatyzacja wdrożeń  
✅ **Dokumentacja** - Kompletne przewodniki i API docs  

## ⚡ Szybki Start (5 minut)

### 1. Sprawdź wymagania

```bash
# Sprawdź czy masz zainstalowane:
docker --version          # >= 20.10
docker-compose --version  # >= 2.0
make --version            # (opcjonalnie)
```

### 2. Uruchom lokalnie

```bash
# Przejdź do katalogu projektu
cd cloudwatch-pro

# Uruchom wszystkie serwisy
make dev

# Lub bez Make:
docker-compose up -d
```

### 3. Otwórz aplikację

Po 2-3 minutach otwórz w przeglądarce:

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin123)

### 4. Przetestuj API

```bash
# Sprawdź status serwisów
curl http://localhost:8000/health

# Zarejestruj użytkownika testowego
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

## 🏗️ Wdrożenie Produkcyjne

### AWS (Zalecane)

```bash
# 1. Skonfiguruj AWS CLI
aws configure

# 2. Przejdź do katalogu Terraform
cd infrastructure/aws

# 3. Skopiuj i edytuj konfigurację
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# 4. Wdróż infrastrukturę
../scripts/deploy.sh production aws apply
```

### Azure

```bash
# 1. Zaloguj się do Azure
az login

# 2. Przejdź do katalogu Terraform
cd infrastructure/azure

# 3. Skonfiguruj i wdróż
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
../scripts/deploy.sh production azure apply
```

## 🎯 Kluczowe Funkcjonalności

### 1. Monitoring w Czasie Rzeczywistym
- Zbieranie metryk CPU, pamięci, dysku, sieci
- Dashboardy Grafana z wizualizacjami
- Alertowanie przy przekroczeniu progów

### 2. Skalowanie Automatyczne
- Horizontal Pod Autoscaler (HPA)
- Cluster Autoscaler
- Skalowanie na podstawie metryk biznesowych

### 3. Bezpieczeństwo
- JWT authentication
- RBAC (Role-Based Access Control)
- Network policies
- Szyfrowanie danych

### 4. Multi-Cloud Support
- AWS (EKS, RDS, ElastiCache)
- Azure (AKS, Azure Database)
- Google Cloud (GKE, Cloud SQL)

## 📊 Przykładowe Scenariusze Użycia

### Scenario 1: Monitoring Aplikacji Web

```bash
# 1. Dodaj metryki aplikacji
curl -X POST http://localhost:8000/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [{
      "metric_name": "http_requests_total",
      "value": 1500,
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "tags": {"service": "web-app", "status": "200"}
    }]
  }'

# 2. Utwórz alert dla wysokiego ruchu
curl -X POST http://localhost:8000/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Traffic Alert",
    "metric_name": "http_requests_total", 
    "threshold": 1000,
    "condition": "greater_than",
    "severity": "warning"
  }'
```

### Scenario 2: Analiza Kosztów

```bash
# Pobierz analizę kosztów z ostatniego tygodnia
curl "http://localhost:8000/costs/analysis?period=7d&group_by=service"
```

### Scenario 3: Predykcyjna Analityka

```bash
# Uzyskaj predykcję wykorzystania zasobów
curl "http://localhost:8000/ml/predict?metric=cpu_usage&horizon=24h"
```

## 🛠️ Przydatne Komendy

### Docker & Compose

```bash
# Sprawdź status serwisów
make health

# Zobacz logi wszystkich serwisów
make logs

# Restart konkretnego serwisu
docker-compose restart user-service

# Zatrzymaj wszystko
make down
```

### Kubernetes

```bash
# Sprawdź status podów
kubectl get pods -n cloudwatch-pro

# Skaluj serwis
kubectl scale deployment api-gateway --replicas=3 -n cloudwatch-pro

# Zobacz logi
kubectl logs -f deployment/user-service -n cloudwatch-pro

# Port forward do lokalnego dostępu
kubectl port-forward svc/grafana-service 3000:3000 -n cloudwatch-pro-monitoring
```

### Terraform

```bash
# Sprawdź plan zmian
terraform plan

# Zastosuj zmiany
terraform apply

# Zobacz outputy
terraform output

# Zniszcz infrastrukturę
terraform destroy
```

## 🔧 Konfiguracja

### Zmienne Środowiskowe

Główne pliki konfiguracyjne:

- `services/user-service/.env` - Konfiguracja serwisu użytkowników
- `services/metrics-collector/.env` - Konfiguracja kolektora metryk  
- `services/api-gateway/.env` - Konfiguracja API Gateway
- `infrastructure/aws/terraform.tfvars` - Konfiguracja infrastruktury AWS

### Dostosowanie Dashboardów

1. Otwórz Grafana: http://localhost:3001
2. Zaloguj się: admin/admin123
3. Przejdź do "Dashboards" → "Manage"
4. Edytuj istniejące lub utwórz nowe dashboardy

### Konfiguracja Alertów

```bash
# Lista dostępnych reguł alertów
curl http://localhost:8000/alerts/rules

# Utwórz nową regułę
curl -X POST http://localhost:8000/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database Connection Alert",
    "metric_name": "database_connections",
    "threshold": 80,
    "condition": "greater_than",
    "severity": "critical",
    "notification_channels": ["email", "slack"]
  }'
```

## 📈 Monitoring i Metryki

### Kluczowe Metryki do Śledzenia

1. **System Metrics**
   - CPU Usage (%)
   - Memory Usage (%)
   - Disk I/O (ops/sec)
   - Network Traffic (bytes/sec)

2. **Application Metrics**
   - Request Rate (req/sec)
   - Response Time (ms)
   - Error Rate (%)
   - Active Users

3. **Business Metrics**
   - Cost per Service ($)
   - Resource Utilization (%)
   - SLA Compliance (%)

### Dashboardy Grafana

Predefiniowane dashboardy:

1. **System Overview** - Ogólny przegląd infrastruktury
2. **Application Performance** - Wydajność aplikacji
3. **Cost Analysis** - Analiza kosztów
4. **Security Dashboard** - Monitoring bezpieczeństwa
5. **Custom Dashboards** - Twoje własne dashboardy

## 🔒 Bezpieczeństwo

### Najlepsze Praktyki

1. **Zmień domyślne hasła**
   ```bash
   # Grafana admin password
   kubectl exec -it deployment/grafana -n cloudwatch-pro-monitoring -- \
     grafana-cli admin reset-admin-password NewSecurePassword123
   ```

2. **Skonfiguruj HTTPS**
   - Certyfikaty SSL są automatycznie zarządzane przez cert-manager
   - Sprawdź status: `kubectl get certificates -n cloudwatch-pro`

3. **Włącz Network Policies**
   ```bash
   kubectl apply -f k8s/security/network-policies.yaml
   ```

4. **Regularne aktualizacje**
   ```bash
   # Aktualizuj obrazy Docker
   docker-compose pull
   docker-compose up -d
   ```

## 🚨 Rozwiązywanie Problemów

### Częste Problemy

**Problem**: Serwisy nie mogą się uruchomić
```bash
# Sprawdź logi
docker-compose logs user-service

# Sprawdź zasoby
docker stats

# Restart serwisu
docker-compose restart user-service
```

**Problem**: Brak dostępu do dashboardu
```bash
# Sprawdź status nginx
docker-compose logs dashboard

# Sprawdź porty
netstat -tulpn | grep :3000
```

**Problem**: Błędy połączenia z bazą danych
```bash
# Sprawdź status PostgreSQL
docker-compose exec postgres pg_isready -U cloudwatch

# Sprawdź logi bazy
docker-compose logs postgres
```

### Przydatne Linki

- 📖 [Pełna Dokumentacja](docs/README.md)
- 🔧 [Przewodnik Wdrożenia](docs/deployment.md)
- 🔌 [Dokumentacja API](docs/api.md)
- 🏗️ [Architektura Systemu](docs/architecture.md)
- 🔒 [Przewodnik Bezpieczeństwa](docs/security.md)

## 💡 Wskazówki Pro

### 1. Optymalizacja Wydajności

```bash
# Włącz cache Redis dla lepszej wydajności
docker-compose exec redis redis-cli CONFIG SET maxmemory 256mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 2. Backup Automatyczny

```bash
# Skonfiguruj automatyczny backup
crontab -e
# Dodaj: 0 2 * * * /path/to/cloudwatch-pro/scripts/backup.sh
```

### 3. Monitoring Kosztów

```bash
# Sprawdź szacowane koszty AWS
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY --metrics BlendedCost
```

### 4. Skalowanie Zaawansowane

```bash
# Skonfiguruj custom metrics dla HPA
kubectl apply -f k8s/monitoring/custom-metrics.yaml

# Utwórz HPA z custom metrics
kubectl apply -f k8s/autoscaling/advanced-hpa.yaml
```

## 🎉 Gratulacje!

Masz teraz w pełni funkcjonalną platformę CloudWatch Pro! 

**Następne kroki:**
1. Eksploruj dashboardy Grafana
2. Przetestuj API endpoints
3. Skonfiguruj własne alerty
4. Wdróż na środowisko produkcyjne
5. Dostosuj do swoich potrzeb

**Potrzebujesz pomocy?**
- Sprawdź dokumentację w katalogu `docs/`
- Utwórz issue na GitHub
- Skontaktuj się z zespołem DevOps

---

**Powodzenia z CloudWatch Pro!** 🚀

*Ten projekt został stworzony jako demonstracja umiejętności DevOps Engineer. Pokazuje zaawansowane techniki orkiestracji kontenerów, automatyzacji infrastruktury oraz monitoringu systemów rozproszonych.*

