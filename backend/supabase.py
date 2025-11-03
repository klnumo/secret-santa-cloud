from supabase import create_client, Client
import os

url: str = os.environ.get("SUPABASE_URL")
anon_key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, anon_key)
supabase_admin: Client = create_client(url, service_key)  # для RLS-байпаса при запуске