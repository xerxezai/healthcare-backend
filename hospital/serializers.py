from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import secrets
from django.conf import settings

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirmPassword = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    recaptchaToken = serializers.CharField(write_only=True, required=True)
    licenseNumber = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certification = serializers.CharField(write_only=True, required=False, allow_blank=True)
    specialization = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phoneNumber = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'password', 'confirmPassword', 
            'role', 'recaptchaToken', 'licenseNumber', 'certification', 
            'specialization', 'phoneNumber'
        ]
        extra_kwargs = {
            'full_name': {'required': True},
            'username': {'required': False, 'allow_blank': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_recaptchaToken(self, value):
        """Verify reCAPTCHA token with Google"""
        # Skip verification in development
        if settings.DEBUG:
            return value or "test-token"
            
        if not value:
            raise serializers.ValidationError("reCAPTCHA verification is required.")
            
        secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', None)
        if not secret_key:
            # In production, this should be set properly
            if not settings.DEBUG:
                raise serializers.ValidationError("reCAPTCHA is not properly configured.")
            return value
        
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            'secret': secret_key,
            'response': value
        }
        
        try:
            response = requests.post(verify_url, data=data, timeout=10)
            result = response.json()
            
            if not result.get('success', False):
                error_codes = result.get('error-codes', [])
                raise serializers.ValidationError("reCAPTCHA verification failed. Please try again.")
            
            return value
            
        except requests.RequestException as e:
            # Don't fail registration for network issues in production
            if settings.DEBUG:
                raise serializers.ValidationError("reCAPTCHA verification failed due to network error.")
            return value
        except Exception as e:
            raise serializers.ValidationError("reCAPTCHA verification failed. Please try again.")

    def validate(self, data):
        """Cross-field validation"""
        # Password confirmation
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Role-specific validation
        role = data.get('role')
        if role == 'doctor':
            if not data.get('licenseNumber'):
                raise serializers.ValidationError("Medical license number is required for doctors.")
        elif role == 'nurse':
            if not data.get('certification'):
                raise serializers.ValidationError("Certification is required for nurses.")
        
        return data

    def create(self, validated_data):
        # Remove non-model fields
        validated_data.pop('confirmPassword', None)
        validated_data.pop('recaptchaToken', None)
        
        # Extract role-specific fields
        license_number = validated_data.pop('licenseNumber', '')
        certification = validated_data.pop('certification', '')
        specialization = validated_data.pop('specialization', '')
        phone_number = validated_data.pop('phoneNumber', '')
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username'),
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            role=validated_data.get('role'),
            license_number=license_number,
            certification=certification,
            specialization=specialization,
            phone_number=phone_number,
            verification_token=verification_token,
            is_verified=False
        )
        
        # TODO: Send verification email
        # send_verification_email(user)
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    recaptcha_token = serializers.CharField(label=_("reCAPTCHA Token"), write_only=True, required=False)
    token = serializers.CharField(label=_("Token"), read_only=True)
    refresh_token = serializers.CharField(label=_("Refresh Token"), read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    user_email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    user_role = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        recaptcha_token = attrs.get('recaptcha_token', '')
        
        print(f"Login attempt for {email}")

        # Validate reCAPTCHA (skip in development mode)
        if not settings.DEBUG and not self.verify_recaptcha(recaptcha_token):
            raise serializers.ValidationError(_('reCAPTCHA verification failed. Please try again.'), code='recaptcha_failed')

        if email and password:
            try:
                # Try to find the user directly first
                from hospital.models import CustomUser
                user_exists = CustomUser.objects.filter(email=email).exists()
                if not user_exists:
                    print(f"No user found with email: {email}")
                    raise serializers.ValidationError(_('User with this email does not exist.'), code='authorization')

                # Now try to authenticate
                user = authenticate(request=self.context.get('request'), email=email, password=password)
                if not user:
                    print(f"Authentication failed for {email}")
                    raise serializers.ValidationError(_('Unable to log in with provided credentials.'), code='authorization')
                
                print(f"Login successful for {email}")
            except Exception as e:
                print(f"Login error: {str(e)}")
                raise serializers.ValidationError(_('Login failed: {0}').format(str(e)), code='authorization')
        else:
            raise serializers.ValidationError(_('Must include "email" and "password".'), code='authorization')

        refresh = RefreshToken.for_user(user)
        attrs['token'] = str(refresh.access_token)
        attrs['refresh_token'] = str(refresh)
        attrs['user_id'] = user.id
        attrs['user_email'] = user.email
        attrs['full_name'] = user.full_name or user.email
        attrs['user_role'] = user.role
        attrs['created_at'] = user.date_joined
        return attrs
    
    def verify_recaptcha(self, token):
        """
        Verify reCAPTCHA token with Google
        """
        from django.conf import settings
        import requests
        
        # Always bypass in development mode
        if settings.DEBUG:
            print(f"DEBUG mode: Bypassing reCAPTCHA verification")
            return True
            
        # Skip verification if no secret key is configured
        if not settings.RECAPTCHA_SECRET_KEY:
            print(f"WARNING: No reCAPTCHA secret key configured, bypassing verification")
            return True
            
        url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': token,
            'remoteip': self.context.get('request').META.get('REMOTE_ADDR', '')
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            success = result.get('success', False)
            if not success:
                print(f"reCAPTCHA verification failed: {result}")
            return success
        except Exception as e:
            # Log the error but don't fail authentication for reCAPTCHA service issues
            print(f"reCAPTCHA verification error: {e}")
            # In development, we'll let it pass even with errors
            return settings.DEBUG
