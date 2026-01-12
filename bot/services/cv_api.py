"""Common Voice API client."""

import httpx
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class TokenInfo:
    """Stores token and its expiry."""
    token: str
    expires_at: datetime


class CVAPIError(Exception):
    """Common Voice API error."""
    def __init__(self, message: str, status_code: Optional[int] = None, detail: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class CVAPIClient:
    """Async client for the Common Voice API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        token_expiry_buffer_seconds: int = 300,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.token_expiry_buffer_seconds = token_expiry_buffer_seconds
        self._token_info: Optional[TokenInfo] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        if not self._token_info:
            return False
        # Token valid if more than buffer time remaining
        return datetime.utcnow() < self._token_info.expires_at - timedelta(seconds=self.token_expiry_buffer_seconds)

    async def _ensure_token(self) -> str:
        """Ensure we have a valid token, refreshing if needed."""
        if not self._is_token_valid():
            await self._refresh_token()
        return self._token_info.token

    async def _refresh_token(self) -> None:
        """Get a new bearer token from the API."""
        client = await self._get_http_client()
        
        response = await client.post(
            "/auth/token",
            json={
                "clientId": self.client_id,
                "clientSecret": self.client_secret,
            },
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code != 200:
            error_detail = None
            try:
                error_data = response.json()
                error_detail = error_data.get("detail") or error_data.get("message")
            except Exception:
                pass
            raise CVAPIError(
                f"Failed to authenticate: {response.status_code}",
                status_code=response.status_code,
                detail=error_detail,
            )
        
        data = response.json()
        token = data.get("token")
        if not token:
            raise CVAPIError("No token in response")
        
        # Token is valid for 1 hour
        self._token_info = TokenInfo(
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

    async def validate_credentials(self) -> bool:
        """Validate that the credentials work by getting a token."""
        try:
            await self._refresh_token()
            return True
        except CVAPIError:
            return False

    async def create_user(self, email: str, username: str) -> dict:
        """Create or get a user in Common Voice.
        
        Returns user info including userId.
        If user exists, returns existing user info from the 409 response.
        """
        token = await self._ensure_token()
        client = await self._get_http_client()
        
        response = await client.post(
            "/auth/users",
            json={"email": email, "username": username},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        
        if response.status_code == 201:
            # New user created
            return response.json().get("data", {})
        elif response.status_code == 409:
            # User already exists - extract userId from response
            data = response.json()
            user_info = data.get("user", {})
            return {
                "userId": user_info.get("userId"),
                "email": email,
                "username": username,
            }
        else:
            error_detail = None
            try:
                error_data = response.json()
                error_detail = error_data.get("detail") or error_data.get("message")
            except Exception:
                pass
            raise CVAPIError(
                f"Failed to create user: {response.status_code}",
                status_code=response.status_code,
                detail=error_detail,
            )

    async def get_sentences(
        self, 
        dataset_code: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> list[dict]:
        """Fetch sentences for a language.
        
        Returns list of sentences with textId, text, hash.
        """
        token = await self._ensure_token()
        client = await self._get_http_client()
        
        response = await client.get(
            "/text/sentences",
            params={
                "datasetCode": dataset_code,
                "limit": limit,
                "offset": offset,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code != 200:
            error_detail = None
            try:
                error_data = response.json()
                error_detail = error_data.get("detail") or error_data.get("message")
            except Exception:
                pass
            raise CVAPIError(
                f"Failed to fetch sentences: {response.status_code}",
                status_code=response.status_code,
                detail=error_detail,
            )
        
        data = response.json()
        return data.get("data", [])

    async def upload_audio(
        self,
        audio_data: bytes,
        user_id: str,
        dataset_code: str,
        text_id: str,
        text: str,
        text_hash: str,
        age: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> dict:
        """Upload an audio recording to Common Voice.
        
        Returns the response including audio id and status.
        """
        token = await self._ensure_token()
        client = await self._get_http_client()
        
        # Build multipart form data
        files = {
            "file": ("recording.ogg", audio_data, "audio/ogg"),
        }
        data = {
            "resource": "scripted",
            "datasetCode": dataset_code,
            "textId": text_id,
            "text": text,
            "hash": text_hash,
            "userId": user_id,
        }
        
        # Add optional demographic info
        if age:
            data["age"] = age
        if gender:
            data["gender"] = gender
        
        response = await client.post(
            "/audio",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code not in (200, 201, 202):
            error_detail = None
            try:
                error_data = response.json()
                error_detail = error_data.get("detail") or str(error_data.get("errors", ""))
            except Exception:
                pass
            raise CVAPIError(
                f"Failed to upload audio: {response.status_code}",
                status_code=response.status_code,
                detail=error_detail,
            )
        
        return response.json()

    async def get_audio_status(self, audio_id: str) -> dict:
        """Get the status of an uploaded audio."""
        token = await self._ensure_token()
        client = await self._get_http_client()
        
        response = await client.get(
            f"/audio/{audio_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code != 200:
            raise CVAPIError(
                f"Failed to get audio status: {response.status_code}",
                status_code=response.status_code,
            )
        
        return response.json()

    async def get_supported_languages(self) -> list[dict]:
        """Get list of supported languages for audio upload."""
        token = await self._ensure_token()
        client = await self._get_http_client()
        
        response = await client.get(
            "/audio/datasets/codes",
            params={"service": "audio", "resource": "scripted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        if response.status_code != 200:
            raise CVAPIError(
                f"Failed to get languages: {response.status_code}",
                status_code=response.status_code,
            )
        
        return response.json()
