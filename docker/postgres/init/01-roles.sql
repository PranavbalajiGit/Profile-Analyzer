-- Development-only database bootstrap.
--
-- profile_owner  : schema owner, used by Alembic (POSTGRES_USER).
-- profile_app    : restricted runtime role for the API and workers.
--                  It is NOT the table owner and does not bypass RLS.
--
-- These passwords are for local development only and are rejected by the
-- application configuration when ENVIRONMENT=production.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'profile_app') THEN
        CREATE ROLE profile_app LOGIN PASSWORD 'profile_app';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE profile_analyzer TO profile_app;
GRANT USAGE ON SCHEMA public TO profile_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO profile_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO profile_app;

ALTER DEFAULT PRIVILEGES FOR ROLE profile_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO profile_app;

ALTER DEFAULT PRIVILEGES FOR ROLE profile_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO profile_app;
