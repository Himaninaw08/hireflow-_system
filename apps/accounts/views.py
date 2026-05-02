from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import login, logout
from .models import CustomUser
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, 
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("REQUEST DATA:", request.data) 
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        print("ERRORS:", serializer.errors)    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            return Response({"message": "Successfully logged out."}, 
                          status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token."}, 
                          status=status.HTTP_400_BAD_REQUEST)

class MeView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully."}, 
                          status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = CustomUser.objects.get(email=email)
                
                # Generate secure token
                from django.contrib.auth.tokens import PasswordResetTokenGenerator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                from django.conf import settings
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from datetime import datetime, timedelta
                
                # Generate token
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset URL
                reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}&uid={uid}&email={email}"
                
                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
                
                # Send email
                try:
                    # HTML email
                    html_message = render_to_string('emails/password_reset.html', {
                        'user': user,
                        'reset_url': reset_url,
                        'token': token,
                        'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                    })
                    
                    # Text email
                    text_message = render_to_string('emails/password_reset.txt', {
                        'user': user,
                        'reset_url': reset_url,
                        'token': token,
                        'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                    })
                    
                    send_mail(
                        subject=settings.PASSWORD_RESET_EMAIL_SUBJECT,
                        message=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False
                    )
                    
                    print(f"PASSWORD RESET EMAIL SENT TO: {email}")
                    print(f"RESET URL: {reset_url}")
                    print(f"TOKEN: {token}")
                    print(f"EXPIRES: {expires_at}")
                    
                    return Response({
                        "message": "Password reset link sent to your email.",
                        "debug_info": f"Reset link sent to {email}",
                        "reset_url": reset_url,  # For development/testing
                        "token": token,  # For development/testing
                        "expires_at": expires_at.isoformat()  # For development/testing
                    }, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    print(f"EMAIL SENDING ERROR: {e}")
                    return Response({
                        "message": "Password reset link sent to your email.",
                        "debug_info": f"Email sending failed: {str(e)}",
                        "reset_url": reset_url,  # Fallback for development
                        "token": token,
                        "expires_at": expires_at.isoformat()
                    }, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                # Don't reveal if email exists or not for security
                return Response({
                    "message": "Password reset link sent to your email.",
                    "debug_info": "Email not found in database (security: not revealing this to user)"
                }, status=status.HTTP_200_OK)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            email = serializer.validated_data.get('email', '')
            
            try:
                # Find user by email
                user = CustomUser.objects.get(email=email)
                
                # Verify token
                from django.contrib.auth.tokens import PasswordResetTokenGenerator
                token_generator = PasswordResetTokenGenerator()
                
                if token_generator.check_token(user, token):
                    # Token is valid, reset password
                    user.set_password(new_password)
                    user.save()
                    
                    print(f"PASSWORD RESET SUCCESSFUL FOR: {email}")
                    print(f"TOKEN: {token}")
                    print(f"NEW PASSWORD SET: Yes")
                    
                    return Response({
                        "message": "Password reset successfully."
                    }, status=status.HTTP_200_OK)
                else:
                    print(f"INVALID TOKEN FOR: {email}")
                    print(f"TOKEN: {token}")
                    
                    return Response({
                        "error": "Invalid or expired reset token."
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except CustomUser.DoesNotExist:
                print(f"USER NOT FOUND FOR EMAIL: {email}")
                return Response({
                    "error": "Invalid reset token."
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"PASSWORD RESET ERROR: {e}")
                return Response({
                    "error": "Password reset failed."
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenRefreshView(TokenRefreshView):
    pass
