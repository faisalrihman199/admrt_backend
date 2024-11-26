from jwt import decode as jwt_decode, ExpiredSignatureError, InvalidTokenError
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken
from core.models import User  # Assuming you're using the custom User model from core
from dotenv import load_dotenv
import os
load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')
print("inside middleware")
@database_sync_to_async
def get_user_from_jwt(token):
    try:
        decoded_data = jwt_decode(token, SECRET_KEY, algorithms=["HS256"])
        print(decoded_data)
        return User.objects.get(id=decoded_data["user_id"])
    except (User.DoesNotExist, InvalidTokenError, ExpiredSignatureError):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])

        # Ensure that the 'authorization' header is present in the headers
        if b"authorization" in headers:
            try:
                token_name, token = headers[b"authorization"].decode().split()

                # Ensure token_name matches the one defined in SIMPLE_JWT
                if token_name == "JWT":
                    # Get the user from the JWT token
                    scope["user"] = await get_user_from_jwt(token)
                else:
                    scope["user"] = AnonymousUser()
            except ValueError:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
