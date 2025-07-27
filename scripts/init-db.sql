-- CloudWatch Pro - Database Initialization Script

-- Tworzenie rozszerzeń PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tworzenie dodatkowych baz danych dla różnych serwisów
CREATE DATABASE cloudwatch_dashboards;
CREATE DATABASE cloudwatch_alerts;
CREATE DATABASE cloudwatch_reports;

-- Tworzenie użytkowników dla różnych serwisów
CREATE USER dashboard_user WITH PASSWORD 'dashboard123';
CREATE USER alert_user WITH PASSWORD 'alert123';
CREATE USER report_user WITH PASSWORD 'report123';

-- Nadanie uprawnień
GRANT ALL PRIVILEGES ON DATABASE cloudwatch_dashboards TO dashboard_user;
GRANT ALL PRIVILEGES ON DATABASE cloudwatch_alerts TO alert_user;
GRANT ALL PRIVILEGES ON DATABASE cloudwatch_reports TO report_user;

-- Przełączenie na bazę główną
\c cloudwatch_users;

-- Tworzenie indeksów dla lepszej wydajności
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);

-- Wstawienie przykładowych danych (tylko dla developmentu)
INSERT INTO users (id, username, email, password_hash, first_name, last_name, role, is_active) 
VALUES 
    (uuid_generate_v4(), 'admin', 'admin@cloudwatch-pro.com', crypt('admin123', gen_salt('bf')), 'Admin', 'User', 'super_admin', true),
    (uuid_generate_v4(), 'demo', 'demo@cloudwatch-pro.com', crypt('demo123', gen_salt('bf')), 'Demo', 'User', 'user', true)
ON CONFLICT (email) DO NOTHING;

-- Tworzenie organizacji przykładowej
INSERT INTO organizations (id, name, description) 
VALUES 
    (uuid_generate_v4(), 'CloudWatch Pro Demo', 'Organizacja demonstracyjna dla CloudWatch Pro')
ON CONFLICT DO NOTHING;

-- Funkcja do czyszczenia starych sesji
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM user_sessions WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Tworzenie zadania cron do czyszczenia sesji (wymaga pg_cron extension)
-- SELECT cron.schedule('cleanup-sessions', '0 2 * * *', 'SELECT cleanup_expired_sessions();');

