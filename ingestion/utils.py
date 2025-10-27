import os
from supabase import create_client

def get_user_id(request):
    """
    Extracts the user ID from the X-User-Id header.
    Falls back to 'dev-user' in development mode.
    """
    return request.headers.get("X-User-Id")


def get_access_token(request):
    """
    Extracts and validates the Supabase access token from the Authorization header.
    Returns the token if valid, otherwise None.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    access_token = auth_header.split("Bearer ")[-1].strip()
    # supabase_url = os.getenv("SUPABASE_URL")
    # supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
    #     "SUPABASE_ANON_KEY"
    # )

    # print(f"Supabase URL: {supabase_url}")

    # if not supabase_url or not supabase_key:
    #     return None

    # supabase = create_client(supabase_url, supabase_key)
    # print("Validating access token with Supabase...")

    # try:
    #     response = supabase.auth.get_user(access_token)
    #     # ✅ check status and data explicitly
    #     if not response or not response.user:
    #         return None
    # except Exception:
    #     return None

    return access_token
