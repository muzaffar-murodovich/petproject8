import datetime

from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .serializers import SignUpSerializer
from .models import User, DONE, CODE_VERIFIED, NEW

class CreateUserView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer

class VerifyAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = request.data.get("code")
        
        self.check_verify(user, code)

        return Response(
            data=
                {"success": True,
                    "auth_status": user.auth_status, 
                    "access": user.token()['access'],
                    "refresh": user.token()['refresh'],
                } 
            )

    @staticmethod
    def check_verify(user, code):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.datetime.now(), code=code, is_confirmed=False)
        if not verifies.exists():
            data = {
                "message": "Invalid or expired verification code."
            }
            raise ValidationError(data)
        else:
            verifies.update(is_confirmed=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True