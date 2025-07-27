# CloudWatch Pro - Przewodnik Wdrożenia

## Spis Treści

1. [Przygotowanie Środowiska](#przygotowanie-środowiska)
2. [Lokalne Środowisko Deweloperskie](#lokalne-środowisko-deweloperskie)
3. [Wdrożenie na AWS](#wdrożenie-na-aws)
4. [Wdrożenie na Azure](#wdrożenie-na-azure)
5. [Wdrożenie na Google Cloud](#wdrożenie-na-google-cloud)
6. [Konfiguracja DNS i SSL](#konfiguracja-dns-i-ssl)
7. [Monitoring i Alertowanie](#monitoring-i-alertowanie)
8. [Backup i Disaster Recovery](#backup-i-disaster-recovery)
9. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)

## Przygotowanie Środowiska

### Wymagania Systemowe

Przed rozpoczęciem wdrożenia upewnij się, że masz zainstalowane następujące narzędzia:

#### Podstawowe Narzędzia
```bash
# Docker (>= 20.10)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose (>= 2.0)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Terraform (>= 1.0)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm (>= 3.0)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### Cloud CLI Tools

**AWS CLI**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Konfiguracja
aws configure
```

**Azure CLI**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Logowanie
az login
```

**Google Cloud CLI**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Inicjalizacja
gcloud init
```

### Klonowanie Repozytorium

```bash
git clone https://github.com/your-username/cloudwatch-pro.git
cd cloudwatch-pro
```

## Lokalne Środowisko Deweloperskie

### 1. Konfiguracja Zmiennych Środowiskowych

```bash
# Kopiowanie przykładowych plików konfiguracyjnych
cp services/user-service/.env.example services/user-service/.env
cp services/metrics-collector/.env.example services/metrics-collector/.env
cp services/api-gateway/.env.example services/api-gateway/.env

# Edycja plików .env zgodnie z potrzebami
nano services/user-service/.env
```

### 2. Uruchomienie Środowiska Lokalnego

```bash
# Opcja 1: Używając Make (zalecane)
make dev

# Opcja 2: Bezpośrednio Docker Compose
docker-compose up -d

# Sprawdzenie statusu serwisów
make health
```

### 3. Weryfikacja Instalacji

```bash
# Sprawdzenie dostępności serwisów
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # User Service
curl http://localhost:8002/health  # Metrics Collector

# Dostęp do interfejsów web
# Dashboard: http://localhost:3000
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
```

### 4. Inicjalizacja Danych Testowych

```bash
# Uruchomienie skryptu inicjalizacji
docker-compose exec user-service python scripts/init_test_data.py

# Lub ręczne dodanie użytkownika testowego
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

## Wdrożenie na AWS

### 1. Przygotowanie Konta AWS

```bash
# Konfiguracja AWS CLI
aws configure set aws_access_key_id YOUR_ACCESS_KEY
aws configure set aws_secret_access_key YOUR_SECRET_KEY
aws configure set default.region us-west-2

# Weryfikacja dostępu
aws sts get-caller-identity
```

### 2. Konfiguracja Terraform

```bash
cd infrastructure/aws

# Kopiowanie i edycja pliku konfiguracyjnego
cp terraform.tfvars.example terraform.tfvars

# Edycja terraform.tfvars
nano terraform.tfvars
```

**Przykładowa konfiguracja terraform.tfvars:**
```hcl
# Podstawowa konfiguracja
project_name = "cloudwatch-pro"
environment  = "production"
aws_region   = "us-west-2"

# VPC
vpc_cidr = "10.0.0.0/16"

# EKS
kubernetes_version = "1.28"
node_groups = {
  general = {
    instance_types = ["t3.medium"]
    scaling_config = {
      desired_size = 3
      max_size     = 10
      min_size     = 1
    }
    disk_size     = 20
    capacity_type = "ON_DEMAND"
  }
}

# Database
database_password = "your-secure-password-here"
domain_name      = "cloudwatch-pro.yourdomain.com"
```

### 3. Wdrożenie Infrastruktury

```bash
# Inicjalizacja Terraform backend
../scripts/deploy.sh production aws plan

# Przegląd planu wdrożenia
terraform plan -var="environment=production"

# Wdrożenie infrastruktury
../scripts/deploy.sh production aws apply
```

### 4. Konfiguracja kubectl

```bash
# Automatyczna konfiguracja (wykonywana przez skrypt deploy.sh)
aws eks update-kubeconfig --region us-west-2 --name cloudwatch-pro-production

# Weryfikacja połączenia
kubectl get nodes
kubectl get namespaces
```

### 5. Wdrożenie Aplikacji

```bash
# Aplikacja zostanie automatycznie wdrożona przez skrypt deploy.sh
# Lub ręczne wdrożenie:

cd ../../k8s

# Wdrożenie w kolejności
kubectl apply -f namespaces/
kubectl apply -f storage/
kubectl apply -f configmaps/
kubectl apply -f secrets/
kubectl apply -f deployments/
kubectl apply -f services/
kubectl apply -f ingress/
kubectl apply -f monitoring/
```

### 6. Weryfikacja Wdrożenia

```bash
# Sprawdzenie statusu podów
kubectl get pods -n cloudwatch-pro

# Sprawdzenie serwisów
kubectl get services -n cloudwatch-pro

# Sprawdzenie ingress
kubectl get ingress -n cloudwatch-pro

# Sprawdzenie logów
kubectl logs -n cloudwatch-pro deployment/api-gateway
```

## Wdrożenie na Azure

### 1. Przygotowanie Subskrypcji Azure

```bash
# Logowanie do Azure
az login

# Ustawienie subskrypcji
az account set --subscription "Your Subscription Name"

# Weryfikacja
az account show
```

### 2. Konfiguracja Service Principal

```bash
# Tworzenie Service Principal dla Terraform
az ad sp create-for-rbac --role="Contributor" --scopes="/subscriptions/YOUR_SUBSCRIPTION_ID"

# Zapisz output - będzie potrzebny w terraform.tfvars
```

### 3. Konfiguracja Terraform

```bash
cd infrastructure/azure

cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Przykładowa konfiguracja terraform.tfvars:**
```hcl
# Azure Configuration
subscription_id = "your-subscription-id"
client_id       = "your-client-id"
client_secret   = "your-client-secret"
tenant_id       = "your-tenant-id"

# Project Configuration
project_name = "cloudwatch-pro"
environment  = "production"
location     = "West Europe"

# AKS Configuration
kubernetes_version = "1.28"
node_count        = 3
vm_size          = "Standard_D2s_v3"

# Database
database_password = "your-secure-password-here"
domain_name      = "cloudwatch-pro.yourdomain.com"
```

### 4. Wdrożenie

```bash
# Wdrożenie infrastruktury
../scripts/deploy.sh production azure apply

# Konfiguracja kubectl
az aks get-credentials --resource-group cloudwatch-pro-production --name cloudwatch-pro-production

# Wdrożenie aplikacji (automatyczne przez skrypt)
```

## Wdrożenie na Google Cloud

### 1. Przygotowanie Projektu GCP

```bash
# Logowanie
gcloud auth login

# Tworzenie projektu
gcloud projects create cloudwatch-pro-project --name="CloudWatch Pro"

# Ustawienie projektu
gcloud config set project cloudwatch-pro-project

# Włączenie wymaganych API
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sql-component.googleapis.com
```

### 2. Konfiguracja Service Account

```bash
# Tworzenie Service Account
gcloud iam service-accounts create terraform-sa --display-name="Terraform Service Account"

# Nadanie uprawnień
gcloud projects add-iam-policy-binding cloudwatch-pro-project \
  --member="serviceAccount:terraform-sa@cloudwatch-pro-project.iam.gserviceaccount.com" \
  --role="roles/editor"

# Tworzenie klucza
gcloud iam service-accounts keys create terraform-key.json \
  --iam-account=terraform-sa@cloudwatch-pro-project.iam.gserviceaccount.com
```

### 3. Konfiguracja Terraform

```bash
cd infrastructure/gcp

cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

### 4. Wdrożenie

```bash
# Ustawienie zmiennej środowiskowej
export GOOGLE_APPLICATION_CREDENTIALS="./terraform-key.json"

# Wdrożenie
../scripts/deploy.sh production gcp apply

# Konfiguracja kubectl
gcloud container clusters get-credentials cloudwatch-pro-production --zone us-central1-a
```

## Konfiguracja DNS i SSL

### 1. Konfiguracja DNS

**AWS Route53:**
```bash
# DNS zostanie automatycznie skonfigurowany przez Terraform
# Sprawdzenie rekordów DNS
aws route53 list-resource-record-sets --hosted-zone-id YOUR_ZONE_ID
```

**Cloudflare (alternatywa):**
```bash
# Dodanie rekordów CNAME wskazujących na Load Balancer
# cloudwatch-pro.yourdomain.com -> your-alb-dns-name.region.elb.amazonaws.com
# api.cloudwatch-pro.yourdomain.com -> your-alb-dns-name.region.elb.amazonaws.com
```

### 2. Konfiguracja SSL/TLS

**AWS Certificate Manager:**
```bash
# Certyfikat zostanie automatycznie utworzony przez Terraform
# Weryfikacja certyfikatu
aws acm list-certificates --region us-west-2
```

**Let's Encrypt (cert-manager):**
```bash
# cert-manager zostanie automatycznie zainstalowany
# Sprawdzenie statusu certyfikatów
kubectl get certificates -n cloudwatch-pro
kubectl describe certificate cloudwatch-pro-tls -n cloudwatch-pro
```

## Monitoring i Alertowanie

### 1. Konfiguracja Prometheus

```bash
# Prometheus zostanie automatycznie wdrożony
# Sprawdzenie konfiguracji
kubectl get configmap prometheus-config -n cloudwatch-pro-monitoring -o yaml

# Dostęp do Prometheus UI
kubectl port-forward -n cloudwatch-pro-monitoring svc/prometheus-service 9090:9090
# Otwórz http://localhost:9090
```

### 2. Konfiguracja Grafana

```bash
# Grafana zostanie automatycznie wdrożona z predefiniowanymi dashboardami
# Dostęp do Grafana
kubectl port-forward -n cloudwatch-pro-monitoring svc/grafana-service 3000:3000
# Otwórz http://localhost:3000 (admin/admin123)

# Import dodatkowych dashboardów
# Dashboard ID: 1860 (Node Exporter Full)
# Dashboard ID: 6417 (Kubernetes Cluster Monitoring)
```

### 3. Konfiguracja Alertów

```bash
# Sprawdzenie reguł alertów
kubectl get prometheusrules -n cloudwatch-pro-monitoring

# Konfiguracja Slack/Email notifications
kubectl edit configmap alertmanager-config -n cloudwatch-pro-monitoring
```

## Backup i Disaster Recovery

### 1. Backup Baz Danych

**PostgreSQL:**
```bash
# Automatyczny backup (skonfigurowany w Terraform)
# Ręczny backup
kubectl exec -n cloudwatch-pro deployment/postgres -- pg_dump -U cloudwatch cloudwatch_users > backup.sql

# Restore
kubectl exec -i -n cloudwatch-pro deployment/postgres -- psql -U cloudwatch cloudwatch_users < backup.sql
```

**InfluxDB:**
```bash
# Backup InfluxDB
kubectl exec -n cloudwatch-pro deployment/influxdb -- influx backup /tmp/backup
kubectl cp cloudwatch-pro/influxdb-pod:/tmp/backup ./influxdb-backup

# Restore
kubectl cp ./influxdb-backup cloudwatch-pro/influxdb-pod:/tmp/restore
kubectl exec -n cloudwatch-pro deployment/influxdb -- influx restore /tmp/restore
```

### 2. Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 godziny
2. **RPO (Recovery Point Objective)**: 1 godzina
3. **Backup Frequency**: Codziennie o 2:00 AM UTC
4. **Cross-Region Replication**: Włączona dla krytycznych danych

**Procedura DR:**
```bash
# 1. Weryfikacja dostępności backup
aws s3 ls s3://cloudwatch-pro-backups/

# 2. Wdrożenie w regionie DR
cd infrastructure/aws
terraform workspace select dr
terraform apply -var="environment=dr" -var="aws_region=us-east-1"

# 3. Restore danych
./scripts/restore-from-backup.sh latest

# 4. Aktualizacja DNS
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://failover-dns.json
```

## Rozwiązywanie Problemów

### Częste Problemy i Rozwiązania

#### 1. Pod nie może się uruchomić

```bash
# Sprawdzenie statusu
kubectl describe pod POD_NAME -n cloudwatch-pro

# Sprawdzenie logów
kubectl logs POD_NAME -n cloudwatch-pro

# Sprawdzenie eventów
kubectl get events -n cloudwatch-pro --sort-by='.lastTimestamp'

# Typowe przyczyny:
# - Brak zasobów (CPU/Memory)
# - Błędna konfiguracja secrets/configmaps
# - Problemy z image pull
```

#### 2. Serwis nie odpowiada

```bash
# Sprawdzenie endpoints
kubectl get endpoints -n cloudwatch-pro

# Test połączenia wewnętrznego
kubectl run test-pod --image=busybox -it --rm -- wget -qO- http://api-gateway-service:8000/health

# Sprawdzenie ingress
kubectl describe ingress cloudwatch-pro-ingress -n cloudwatch-pro
```

#### 3. Problemy z bazą danych

```bash
# Sprawdzenie statusu PostgreSQL
kubectl exec -it -n cloudwatch-pro deployment/postgres -- psql -U cloudwatch -c "SELECT version();"

# Sprawdzenie połączeń
kubectl exec -it -n cloudwatch-pro deployment/postgres -- psql -U cloudwatch -c "SELECT * FROM pg_stat_activity;"

# Restart bazy danych
kubectl rollout restart deployment/postgres -n cloudwatch-pro
```

#### 4. Wysokie wykorzystanie zasobów

```bash
# Sprawdzenie wykorzystania
kubectl top pods -n cloudwatch-pro
kubectl top nodes

# Skalowanie serwisu
kubectl scale deployment api-gateway --replicas=5 -n cloudwatch-pro

# Sprawdzenie HPA
kubectl get hpa -n cloudwatch-pro
```

#### 5. Problemy z SSL/TLS

```bash
# Sprawdzenie certyfikatów
kubectl get certificates -n cloudwatch-pro
kubectl describe certificate cloudwatch-pro-tls -n cloudwatch-pro

# Sprawdzenie cert-manager
kubectl logs -n cert-manager deployment/cert-manager

# Ręczne odnowienie certyfikatu
kubectl delete certificate cloudwatch-pro-tls -n cloudwatch-pro
kubectl apply -f k8s/ingress/ingress.yaml
```

### Logi i Debugging

```bash
# Centralne logowanie (ELK Stack)
kubectl port-forward -n cloudwatch-pro-monitoring svc/kibana 5601:5601

# Sprawdzenie logów aplikacji
kubectl logs -f deployment/api-gateway -n cloudwatch-pro

# Sprawdzenie logów systemowych
kubectl logs -f daemonset/fluentd -n kube-system

# Debug networking
kubectl exec -it test-pod -- nslookup api-gateway-service.cloudwatch-pro.svc.cluster.local
```

### Kontakt z Supportem

W przypadku problemów, które nie zostały rozwiązane przez powyższe kroki:

1. Zbierz logi: `kubectl logs deployment/DEPLOYMENT_NAME -n cloudwatch-pro`
2. Sprawdź status: `kubectl describe deployment/DEPLOYMENT_NAME -n cloudwatch-pro`
3. Sprawdź eventy: `kubectl get events -n cloudwatch-pro`
4. Utwórz issue na GitHub z pełnymi logami i opisem problemu

### Przydatne Komendy

```bash
# Sprawdzenie wszystkich zasobów
kubectl get all -n cloudwatch-pro

# Sprawdzenie wykorzystania zasobów
kubectl top pods -n cloudwatch-pro --sort-by=memory
kubectl top nodes --sort-by=cpu

# Backup konfiguracji
kubectl get all -n cloudwatch-pro -o yaml > cloudwatch-pro-backup.yaml

# Restart wszystkich deploymentów
kubectl rollout restart deployment -n cloudwatch-pro

# Sprawdzenie wersji
kubectl version
helm version
terraform version
```

---

Ten przewodnik wdrożenia zapewnia kompleksowe instrukcje dla wszystkich etapów wdrożenia CloudWatch Pro. W przypadku pytań lub problemów, skonsultuj się z dokumentacją poszczególnych narzędzi lub utwórz issue w repozytorium projektu.

