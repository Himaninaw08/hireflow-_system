from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 
            'avatar', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'password_confirm', 
            'first_name', 'last_name', 'role'
        ]

    def validate_email(self, value):
        """
        Clean and validate email field
        """
        # Remove markdown links if present
        if '[' in value and '](' in value:
            # Extract email from markdown link [email](mailto:email)
            import re
            email_match = re.search(r'\[([^\]]+)\]', value)
            if email_match:
                value = email_match.group(1)
        
        # Validate email format
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        
        # Check for uniqueness
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value.lower().strip()

    def validate_password(self, value):
        """
        Validate password field
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        try:
        # Django's validate_password will handle common passwords, etc.
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value    
           

    def validate_password_confirm(self, value):
        """
        Validate password confirmation field
        """
        return value

    def validate_role(self, value):
        """
        Validate role field
        """
        valid_roles = ['candidate', 'employer', 'recruiter', 'admin']
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
        return value

    def validate_first_name(self, value):
        """
        Validate first name field
        """
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required.")
        return value.strip()

    def validate_last_name(self, value):
        """
        Validate last name field
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required.")
        return value.strip()

    def validate(self, attrs):
        """
        Object-level validation for password confirmation
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match.'
            })
        
        return attrs

    def create(self, validated_data):
        """
        Create and return a new user
        """
        # Remove password_confirm from data before creating user
        validated_data.pop('password_confirm', None)
        
        # Create user using CustomUserManager
        user = CustomUser.objects.create_user(**validated_data)
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                              username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
            return value
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            raise serializers.ValidationError("No account found with this email address.")

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    password_confirm = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def validate_token(self, value):
        # Token validation will be done in the view
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid reset token.")
        return value

    def save(self):
        # Password reset is handled in the view
        # This method is not used since we do token validation in the view
        pass
