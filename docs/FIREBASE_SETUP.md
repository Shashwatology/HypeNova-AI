# HypeNova AI — Firebase Authentication Setup Guide

## 1. Overview

HypeNova AI uses **Firebase Authentication** for identity management, user onboarding, and workspace membership verification. This provides a secure, battle-tested authentication flow supporting Google Sign-In, multi-factor authentication (MFA), and token-based session management without ever handling user passwords directly.

---

## 2. Step-by-Step Firebase Project Setup

### Step 1: Create Firebase Project
1. Navigate to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add Project** and name it `hypenova-ai-production` (or `hypenova-ai-dev`).
3. Google Analytics can be toggled on or off based on privacy preferences.
4. Click **Create Project**.

### Step 2: Enable Google Sign-In Provider
1. In the Firebase Console left navigation, select **Build > Authentication**.
2. Click **Get Started**.
3. Under the **Sign-in method** tab, choose **Google** from the Additional Providers list.
4. Toggle **Enable**.
5. Set the public project support email (e.g., `support@hypenova.ai` or your admin email).
6. Click **Save**.

### Step 3: Register Authorized Domains
Under **Authentication > Settings > Authorized domains**, ensure the following domains are whitelisted:
- `localhost`
- `127.0.0.1`
- Your production SaaS domain (e.g., `app.hypenova.ai`)

---

## 3. Backend Admin SDK Configuration

To verify incoming Firebase ID Tokens in the FastAPI backend:

### Step 1: Generate Service Account Key
1. In Firebase Console, click the Gear icon (Project Settings) > **Service accounts**.
2. Select **Python** as the snippet language.
3. Click **Generate new private key** and confirm.
4. A JSON file (`hypenova-ai-firebase-adminsdk-*.json`) will download to your machine.

### Step 2: Secure Environment Configuration
> [!CAUTION]
> **Never commit your Firebase service account JSON to version control.** Store it securely on the server and reference its path via the environment variable.

In your `.env` file (copied from `.env.example`):
```bash
# Path to downloaded Firebase service account key
FIREBASE_SERVICE_ACCOUNT_KEY="C:\\Users\\shash\\Downloads\\secrets\\firebase-service-account.json"
```

### Step 3: Backend Verification Logic
The backend (`hypenova/auth.py`) automatically detects this file and activates cryptographically verified token inspection:
```python
import firebase_admin
from firebase_admin import auth as fb_auth, credentials

if cred_path and os.path.isfile(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    FIREBASE_INITIALIZED = True
```

When an HTTP request arrives with `Authorization: Bearer <FIREBASE_ID_TOKEN>`, the backend verifies signature validity, expiry timestamp, and extracts the `uid` and `email` to associate with the tenant's workspace.

---

## 4. Local Development Offline Mode

When running on a college PC or offline development environment without internet access or Firebase service account keys:
- The system gracefully defaults to **Local Development Auth Mode**.
- Passing `Authorization: Bearer dev-token-usr-admin` or simulating login via `POST /api/auth/login?email=creator@example.com` produces a persistent local test token that fully exercises tenant isolation without external network calls.
