"""HypeNova AI - Authentication & Multi-Tenant Workspace Authorization Layer"""
import json
import os
import secrets
import time
from typing import Dict, List, Optional
from fastapi import Depends, Header, HTTPException, status
from hypenova.database import get_connection, log_event

# Environment detection
def is_production_mode() -> bool:
    env = os.getenv("HYPENOVA_ENV", os.getenv("ENV", "development")).lower()
    return env in ("production", "prod")

# In-memory OAuth CSRF State Nonce Store (with TTL)
_OAUTH_STATE_STORE: Dict[str, Dict] = {}

def generate_oauth_state(workspace_id: str) -> str:
    """Generates a cryptographically secure CSRF state nonce for OAuth consent flows."""
    state_nonce = secrets.token_urlsafe(32)
    _OAUTH_STATE_STORE[state_nonce] = {
        "workspace_id": workspace_id,
        "created_at": time.time()
    }
    return state_nonce

def validate_oauth_state(state_nonce: str, expected_workspace_id: str) -> bool:
    """Validates an incoming OAuth CSRF state nonce, ensuring no forgery or replay."""
    if not state_nonce or state_nonce not in _OAUTH_STATE_STORE:
        return False
    entry = _OAUTH_STATE_STORE.pop(state_nonce)
    # Check 15-minute expiration window (900 seconds)
    if time.time() - entry["created_at"] > 900:
        return False
    return entry["workspace_id"] == expected_workspace_id

# Optional Firebase Admin SDK initialization
FIREBASE_INITIALIZED = False
try:
    import firebase_admin
    from firebase_admin import auth as fb_auth, credentials
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if cred_path and os.path.isfile(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        FIREBASE_INITIALIZED = True
        log_event("Auth", "Firebase Admin SDK initialized with service account.")
except Exception as e:
    log_event("Auth", f"Firebase Admin SDK not loaded (running in local development auth mode): {str(e)}", "INFO")

def verify_token(token: str) -> Dict:
    """Verifies a bearer token via Firebase or local development token handler."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")

    # PRODUCTION MODE ENFORCEMENT
    if is_production_mode():
        if token.startswith("dev-") or not FIREBASE_INITIALIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development tokens ('dev-token-*') are strictly prohibited when production mode is enabled. Valid Firebase credentials required."
            )
        try:
            decoded = fb_auth.verify_id_token(token, check_revoked=True)
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            if project_id and decoded.get("aud") != project_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token audience mismatch: expected {project_id}, got {decoded.get('aud')}"
                )
            return {
                "id": decoded.get("uid"),
                "email": decoded.get("email", ""),
                "display_name": decoded.get("name", "Creator"),
                "photo_url": decoded.get("picture", "")
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired Firebase ID token: {str(e)}")

    # LOCAL DEVELOPMENT AUTHENTICATION (Disabled in production)
    if FIREBASE_INITIALIZED and not token.startswith("dev-"):
        try:
            decoded = fb_auth.verify_id_token(token)
            return {
                "id": decoded.get("uid"),
                "email": decoded.get("email", ""),
                "display_name": decoded.get("name", "Creator"),
                "photo_url": decoded.get("picture", "")
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Firebase ID token: {str(e)}")

    # Local development & testing token handler
    # Accepts tokens like: "dev-token-usr-admin", "dev-token-creator-2", or plain "usr-admin"
    clean_token = token.replace("dev-token-", "").strip()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ? OR email = ?;", (clean_token, clean_token))
    row = cur.fetchone()

    if not row:
        # Create a new local user on demand for test isolation
        new_uid = f"usr-{clean_token[:12]}"
        email = f"{clean_token}@hypenova.ai" if "@" not in clean_token else clean_token
        cur.execute("INSERT OR REPLACE INTO users (id, email, display_name) VALUES (?, ?, ?);",
                    (new_uid, email, clean_token.replace("-", " ").title()))
        
        # Create personal workspace for new user
        ws_id = f"ws-{new_uid}"
        cur.execute("INSERT OR REPLACE INTO workspaces (id, name, slug, owner_user_id, tier) VALUES (?, ?, ?, ?, 'CREATOR');",
                    (ws_id, f"{clean_token.title()}'s Studio", f"ws-{clean_token.lower()}", new_uid))
        cur.execute("INSERT OR REPLACE INTO workspace_members (id, workspace_id, user_id, role) VALUES (?, ?, ?, 'OWNER');",
                    (f"mem-{ws_id}", ws_id, new_uid))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE id = ?;", (new_uid,))
        row = cur.fetchone()

    conn.close()
    return dict(row)

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """FastAPI dependency for authenticated user."""
    if not authorization:
        if is_production_mode():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Missing Authorization header in production mode."
            )
        # Default local dev fallback to primary admin user
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = 'usr-admin';")
        user = cur.fetchone()
        conn.close()
        if user:
            return dict(user)
        return {"id": "usr-admin", "email": "admin@hypenova.ai", "display_name": "Studio Lead"}

    token = authorization.replace("Bearer ", "").strip()
    return verify_token(token)

def get_current_workspace(
    x_workspace_id: Optional[str] = Header(None),
    user: Dict = Depends(get_current_user)
) -> Dict:
    """FastAPI dependency ensuring tenant isolation: user MUST be a member of the requested workspace."""
    conn = get_connection()
    cur = conn.cursor()

    if x_workspace_id:
        cur.execute("""
        SELECT w.*, m.role
        FROM workspaces w
        JOIN workspace_members m ON w.id = m.workspace_id
        WHERE w.id = ? AND m.user_id = ?;
        """, (x_workspace_id, user["id"]))
        row = cur.fetchone()
        conn.close()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User {user['email']} is not a member of workspace '{x_workspace_id}'."
            )
        return dict(row)

    # If no workspace header provided, resolve user's primary workspace
    cur.execute("""
    SELECT w.*, m.role
    FROM workspaces w
    JOIN workspace_members m ON w.id = m.workspace_id
    WHERE m.user_id = ? LIMIT 1;
    """, (user["id"],))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User {user['email']} has no active workspaces."
        )

    return dict(row)
