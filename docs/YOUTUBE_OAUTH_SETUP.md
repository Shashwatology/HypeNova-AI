# HypeNova AI — Official YouTube OAuth 2.0 Setup Guide

## 1. Overview & Security Foundation

HypeNova AI publishes videos and fetches performance analytics through Google's official **YouTube Data API v3** and **YouTube Analytics API**. 

> [!CAUTION]
> **Zero Password Directive**: Creators never share their Google account passwords with HypeNova AI. Instead, they complete Google's standard OAuth consent flow in a secure popup or browser tab, granting our application restricted, revocable permissions.

---

## 2. Google Cloud Console Configuration

### Step 1: Create a Google Cloud Project
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown in the top navigation bar and select **New Project**.
3. Name the project `hypenova-publishing-engine` and click **Create**.

### Step 2: Enable Required APIs
In the Google Cloud Console search bar, enable the following two APIs:
1. **YouTube Data API v3**: Enables video uploading (`videos.insert`), metadata retrieval, and playlist inspection.
2. **YouTube Analytics API**: Enables programmatic retrieval of watch time, retention percentages, and subscriber acquisition metrics.

### Step 3: Configure OAuth Consent Screen
1. Navigate to **APIs & Services > OAuth consent screen**.
2. Select **External** user type and click **Create**.
3. Fill in the App Information:
   - **App name**: `HypeNova AI`
   - **User support email**: Your admin/support email.
   - **Developer contact information**: Your developer email.
4. Click **Save and Continue**.

### Step 4: Add OAuth Scopes
Click **Add or Remove Scopes** and select:
- `.../auth/youtube.upload`: Upload YouTube videos and manage video status.
- `.../auth/youtube.readonly`: View your YouTube account and channel metadata.
- `.../auth/yt-analytics.readonly`: View YouTube Analytics monetary and non-monetary reports for your YouTube content.
Click **Update** and **Save and Continue**.

### Step 5: Test Users (Crucial for Unverified Apps)
While your Google Cloud app is in "Testing" status, Google restricts authorization to registered test users:
1. In the **Test users** section, click **Add Users**.
2. Enter the Google account email addresses of the channels you intend to connect (e.g., `creator@clutchrush.in`, your personal channel email).
3. Click **Add** and **Save and Continue**.

---

## 3. Creating OAuth 2.0 Credentials

1. Navigate to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Select **Web application** as the application type.
4. Name: `HypeNova Web Client`.
5. **Authorized JavaScript origins**:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
   - Production URL (e.g., `https://app.hypenova.ai`)
6. **Authorized redirect URIs**:
   - `http://127.0.0.1:8000/api/accounts/oauth/callback`
   - `http://localhost:8000/api/accounts/oauth/callback`
   - Production callback URL
7. Click **Create**.
8. Note down the **Client ID** and **Client Secret**.

---

## 4. Environment Variables Configuration

Copy your credentials into your `.env` file (based on `.env.example`):

```bash
# Google Cloud YouTube OAuth Credentials
YOUTUBE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
YOUTUBE_CLIENT_SECRET="GOCSPX-your-client-secret"
YOUTUBE_REDIRECT_URI="http://127.0.0.1:8000/api/accounts/oauth/callback"

# Secret Key used to encrypt refresh tokens at rest in database
HYPENOVA_ENCRYPTION_KEY="generate-a-random-32-byte-hex-string"
```

---

## 5. Token Exchange & Refresh Flow

1. **Authorization URL Generation**:
   The user clicks "+ Connect Channel" in the HypeNova dashboard. The app redirects to Google's consent screen with:
   - `access_type=offline` (demands a refresh token for unattended publishing)
   - `prompt=consent` (ensures refresh token is returned even on re-authorization)
2. **Callback Handling**:
   Google redirects back to `/api/accounts/oauth/callback?code=...`. The backend exchanges the code for:
   - Short-lived Access Token (valid for 3600 seconds)
   - Long-lived Refresh Token
3. **Encrypted Storage**:
   The refresh token is encrypted with AES-256-GCM using `HYPENOVA_ENCRYPTION_KEY` and saved to the `connected_accounts` table tied strictly to the user's active workspace.
4. **Automated Publishing**:
   When the background worker schedules an upload, it decrypts the refresh token in memory, obtains a fresh access token, and streams the MP4 using resumable chunking.
