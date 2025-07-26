import jwt
import requests
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import json
from functools import lru_cache
import time


class ClerkAuth:
    def __init__(self):
        self.secret_key = os.getenv("CLERK_SECRET_KEY")
        self.publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY")

        if not self.secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable is required")

        if not self.publishable_key:
            raise ValueError("CLERK_PUBLISHABLE_KEY environment variable is required")

        # For debugging
        print(
            f"Initializing Clerk with publishable key: {self.publishable_key[:20]}..."
        )

    def get_jwks_url_from_token(self, token: str) -> str:
        """Extract JWKS URL from token issuer"""
        try:
            # Decode without verification to get the issuer
            payload = jwt.decode(
                token, verify=False, options={"verify_signature": False}
            )
            issuer = payload.get("iss")

            if issuer:
                # The issuer should be something like https://clerk.example.com
                # JWKS URL would be {issuer}/.well-known/jwks.json
                if issuer.endswith("/"):
                    issuer = issuer[:-1]  # Remove trailing slash
                jwks_url = f"{issuer}/.well-known/jwks.json"
                print(f"Extracted JWKS URL from token: {jwks_url}")
                return jwks_url
            else:
                raise ValueError("No issuer found in token")

        except Exception as e:
            print(f"Error extracting JWKS URL from token: {e}")
            # Fallback to trying to construct from publishable key
            return self.construct_jwks_url_from_key()

    def construct_jwks_url_from_key(self) -> str:
        """Fallback method to construct JWKS URL from publishable key"""
        try:
            # Try different patterns based on the publishable key format
            if self.publishable_key.startswith("pk_test_"):
                # Extract the identifier part
                key_part = self.publishable_key[8:]  # Remove 'pk_test_'
                instance_id = key_part.split("_")[0]

                # Try the standard format
                jwks_url = (
                    f"https://{instance_id}.clerk.accounts.dev/.well-known/jwks.json"
                )
                print(f"Constructed JWKS URL from key: {jwks_url}")
                return jwks_url

            elif self.publishable_key.startswith("pk_live_"):
                # Extract the identifier part
                key_part = self.publishable_key[8:]  # Remove 'pk_live_'
                instance_id = key_part.split("_")[0]

                # Try the standard format
                jwks_url = (
                    f"https://{instance_id}.clerk.accounts.dev/.well-known/jwks.json"
                )
                print(f"Constructed JWKS URL from key: {jwks_url}")
                return jwks_url

            else:
                raise ValueError("Unsupported publishable key format")

        except Exception as e:
            print(f"Error constructing JWKS URL from key: {e}")
            raise ValueError(f"Cannot determine JWKS URL: {e}")

    def get_jwks(self, token: str) -> Dict[str, Any]:
        """Fetch JWKS from Clerk"""
        try:
            # First try to get JWKS URL from token
            jwks_url = self.get_jwks_url_from_token(token)

            print(f"Fetching JWKS from: {jwks_url}")
            response = requests.get(jwks_url, timeout=10)

            if response.status_code != 200:
                print(
                    f"JWKS request failed with status {response.status_code}: {response.text}"
                )

            response.raise_for_status()
            jwks_data = response.json()
            print(
                f"Successfully fetched JWKS with {len(jwks_data.get('keys', []))} keys"
            )
            return jwks_data

        except Exception as e:
            print(f"Error fetching JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch authentication keys: {str(e)}",
            )

    def get_signing_key(self, token: str) -> str:
        """Get the signing key for JWT verification"""
        try:
            # Decode header without verification to get kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            print(f"Token kid: {kid}")

            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID",
                )

            # Get JWKS and find the matching key
            jwks = self.get_jwks(token)

            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    print(f"Found matching key for kid: {kid}")
                    # Convert JWK to PEM format for PyJWT
                    from cryptography.hazmat.primitives.asymmetric import rsa
                    from cryptography.hazmat.primitives import serialization

                    # Extract RSA components
                    n = self._base64url_decode(key["n"])
                    e = self._base64url_decode(key["e"])

                    # Create RSA public key
                    public_numbers = rsa.RSAPublicNumbers(
                        int.from_bytes(e, "big"), int.from_bytes(n, "big")
                    )
                    public_key = public_numbers.public_key()

                    # Convert to PEM format
                    pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )

                    return pem.decode("utf-8")

            available_kids = [k.get("kid") for k in jwks.get("keys", [])]
            print(f"Available key IDs: {available_kids}")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unable to find key for kid: {kid}. Available: {available_kids}",
            )

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Error getting signing key: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token format: {str(e)}",
            )

    def _base64url_decode(self, data: str) -> bytes:
        """Decode base64url string"""
        import base64

        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Clerk JWT token and return claims"""
        try:
            # Get signing key
            signing_key = self.get_signing_key(token)

            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"verify_aud": False, "verify_iss": False},
            )

            # Verify token is not expired
            current_time = int(time.time())
            if payload.get("exp", 0) < current_time:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
                )

            print(f"Token verified successfully for user: {payload.get('sub')}")
            return payload

        except jwt.InvalidTokenError as e:
            print(f"JWT validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            print(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
            )

    def get_user_id(self, token: str) -> str:
        """Extract user ID from token"""
        payload = self.verify_token(token)
        user_id = payload.get("sub")  # 'sub' claim contains the user ID

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user ID"
            )

        return user_id


# Global instance
clerk_auth = ClerkAuth()
