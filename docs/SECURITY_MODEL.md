# HypeNova AI — Security & Authentication Architecture Model

## 1. Executive Summary & Core Security Directives

HypeNova AI is designed as a multi-user, multi-tenant short-form content automation SaaS platform. Because our software operates on creator assets, connects directly to platform publishing endpoints, and operates in both local development environments and multi-tenant cloud deployments, security is architected from first principles.

### The Zero-Password Mandate
> [!CAUTION]
> **Zero Personal Password Policy**: HypeNova AI never asks for, accepts, processes, logs, or stores user Google or YouTube passwords. Any credential prompt asking for a plaintext password is an immediate security violation. All third-party access is conducted exclusively through authorized, scoped OAuth 2.0 consent tokens issued directly by Google's OAuth servers.

---

## 2. Two-Tiered Segregated Authentication Model

A critical flaw in naive creator automation platforms is conflating application user authentication with external channel publishing permissions. HypeNova AI strictly separates these two domains:

```
+-----------------------------------------------------------------------------------+
|                                 APPLICATION LAYER                                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                     Tier 1: Firebase Auth & Workspace RBAC                  |  |
|  |  * User Identity (Google Sign-In, Email/Password via Firebase)             |  |
|  |  * Workspace Membership & Isolation (Tenant segregation)                   |  |
|  |  * Role-Based Access Control (OWNER, EDITOR, VIEWER)                        |  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  |                Tier 2: Google YouTube OAuth 2.0 Delegated Auth              |  |
|  |  * Channel-specific delegated publishing tokens                             |  |
|  |  * Scopes: youtube.upload, youtube.readonly, yt-analytics.readonly          |  |
|  |  * Workspace-isolated AES-256 encrypted token vaults                         |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Tier 1: User Identity (Firebase Auth)
- **Role**: Verifies who the user is and what workspaces they have permission to access.
- **Provider**: Firebase Authentication (supporting Google Identity Services, SAML, and Email Link).
- **Session Mechanism**: JWT ID Tokens verified cryptographically using Google's public JSON Web Key Sets (JWKS).
- **Workspace Association**: A single user may belong to multiple independent workspaces (e.g., their personal agency workspace and a client's gaming studio) with different roles in each.

### Tier 2: Channel Authorization (Google OAuth 2.0)
- **Role**: Authorizes HypeNova AI background workers to upload videos and fetch analytics on behalf of a specific YouTube channel.
- **Grant Type**: Authorization Code Grant with Proof Key for Code Exchange (PKCE).
- **Scopes Requested**:
  - `https://www.googleapis.com/auth/youtube.upload` (Upload videos as private/unlisted/public)
  - `https://www.googleapis.com/auth/youtube.readonly` (Verify channel ID, verify upload status)
  - `https://www.googleapis.com/auth/yt-analytics.readonly` (Retrieve authenticated retention & viewer demographics)

---

## 3. Multi-Tenant Isolation & Zero IDOR Guarantee

HypeNova AI prevents Insecure Direct Object References (IDOR) and cross-tenant data leaks at both the API dependency layer and the database query layer.

### A. Route-Level Workspace Verification Dependency
Every protected endpoint in the FastAPI backend injects the `get_current_workspace` dependency:

```python
def get_current_workspace(
    x_workspace_id: Optional[str] = Header(None),
    user: Dict = Depends(get_current_user)
) -> Dict:
    target_ws = x_workspace_id or "ws-default"
    # Strict validation: user MUST have an active row in workspace_members
    cur.execute("""
        SELECT w.*, m.role
        FROM workspaces w
        JOIN workspace_members m ON w.id = m.workspace_id
        WHERE w.id = ? AND m.user_id = ?;
    """, (target_ws, user["id"]))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Access denied: Cross-tenant access forbidden.")
    return dict(row)
```

### B. Query-Level Tenant Scoping
All database queries (`SELECT`, `UPDATE`, `DELETE`) incorporate `WHERE workspace_id = ?` with parameter binding:
- Clips created in Workspace A are invisible to Workspace B.
- YouTube OAuth tokens connected in Workspace A can never be triggered to publish content from Workspace B.
- Timeline edits and custom preset modifications are hard-scoped to the owning workspace.

---

## 4. Shared / Managed Workstation Threat Model

Our current development environment is a college-managed Dell workstation with multiple shared local users. In such environments, several unique threats exist and are mitigated:

| Threat | Risk Description | HypeNova Mitigation |
| :--- | :--- | :--- |
| **Local File Snooping** | Another local user inspects temporary directories or `.env` files. | Production `.env` files are excluded via `.gitignore`. Development mode uses isolated `dev-token-*` sessions without persisting live Google tokens to disk. |
| **Shared Browser Sessions** | Unattended browser leaving live Google credentials logged in. | Fast session timeout, manual logout control in topbar, and no browser persistence of master credentials. |
| **Process Inspection** | Non-privileged users running `Get-Process` or inspecting command line arguments. | API secrets, tokens, and credentials are never passed as command-line arguments to `run.py` or FFmpeg; they are passed via in-memory environment variables or stdin pipes. |
| **Credential Git Leaks** | Accidental commit of API keys or service account keys to public repositories. | Root `.gitignore` enforces exclusion of `*.env`, `service-account*.json`, `*.pem`, `*.db`, and token caches. |

---

## 5. Token Encryption at Rest

In production deployments, Google OAuth refresh tokens stored in the `connected_accounts` table are encrypted before persistence:

- **Algorithm**: AES-256-GCM (Authenticated Encryption with Associated Data).
- **Key Derivation**: HKDF (HMAC-based Key Derivation Function) with SHA-256.
- **Key Management**: The master encryption key `HYPENOVA_ENCRYPTION_KEY` is loaded strictly from environment variables or KMS (AWS KMS, Google Cloud KMS, or HashiCorp Vault), never stored alongside the database.
- **Database Row Structure**:
  ```json
  {
    "ciphertext": "v1:GCM:a7b8c9d0...",
    "nonce": "e4f5a6...",
    "tag": "c1d2e3..."
  }
  ```

---

## 6. Role-Based Access Control (RBAC) Matrix

Within any individual workspace, users are assigned one of three granular roles:

| Action / Capability | OWNER | EDITOR | VIEWER |
| :--- | :---: | :---: | :---: |
| View Overview & Metrics | ✅ | ✅ | ✅ |
| View Discovered Opportunities | ✅ | ✅ | ✅ |
| Clear / Update Rights Status | ✅ | ✅ | ❌ |
| Run Scout Radar Scan | ✅ | ✅ | ❌ |
| Open & Edit Clips in Timeline | ✅ | ✅ | ❌ |
| Save Timeline Drafts & Presets | ✅ | ✅ | ❌ |
| Trigger Re-render & Export | ✅ | ✅ | ❌ |
| Schedule Posts in Calendar | ✅ | ✅ | ❌ |
| Connect / Disconnect YouTube Channels | ✅ | ❌ | ❌ |
| Toggle Automated Background Workers | ✅ | ❌ | ❌ |
| Manage Workspace Members & Billing | ✅ | ❌ | ❌ |

---

## 7. Incident Response & Token Revocation

If a connected creator channel or workspace credential is suspected of compromise:
1. **Immediate Revocation**: Click "Disconnect" in the YouTube Accounts tab. This purges all encrypted tokens from `connected_accounts` and issues a revocation call to `https://oauth2.googleapis.com/revoke?token={token}`.
2. **Channel-Side Invalidation**: The creator can navigate to `myaccount.google.com/permissions` and revoke HypeNova AI's access in one click, immediately invalidating all outstanding tokens.
3. **Audit Log Verification**: Inspect `GET /api/health` logs for any unauthorized upload or timeline tamper attempts.
