from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Any, Dict
from django.conf import settings
# from django.contrib.auth import get_user_model
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
# from django.utils.crypto import get_random_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
# from djoser.serializers import PasswordResetSerializer as DjoserPasswordResetSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer
from django.core.exceptions import ImproperlyConfigured
from core.models import User
from core.utils import get_profile_image_url
from users.models import SpaceHost, Advertiser
from .models import AffiliateLink


class UserCreateSerializer(BaseUserCreateSerializer):
    username = serializers.CharField(read_only=True)

    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'email', 'password', 'full_name', 'phone', 'country', 'birthday', 'user_role']

    def create(self, validated_data):
        user = super().create(validated_data)
        user_role = validated_data.get('user_role')
        
        profile_class = None
        if user_role == settings.K_SPACE_HOST_ID:
            profile_class = SpaceHost
        elif user_role == settings.K_ADVERTISER_ID:
            profile_class = Advertiser
        if profile_class is not None:
            profile_class.objects.create(user=user)
        
        # Send the welcome email
        self.send_welcome_email(user, user_role)
        
        return user

    def send_welcome_email(self, user, user_role):
    
        try:
            # Debug: Print the settings values
            print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
            print("EMAIL_HOST_PASSWORD:", settings.EMAIL_HOST_PASSWORD)
            print("EMAIL_HOST:", settings.EMAIL_HOST)
        
            # Set up email details
            sender_email = settings.EMAIL_HOST_USER
            receiver_email = user.email
            password = settings.EMAIL_HOST_PASSWORD
            smtp_server = settings.EMAIL_HOST
            smtp_port = 587

            # Prepare the email message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Welcome to Admrt! Claim Your Free Media Kit Today 🎉"
            message["From"] = "Intro Email to Claim Free Media Kit"
            message["To"] = receiver_email

            # Create the HTML content using the template
            html_content = f"""
            <html>
                <body>
                    <p>Hi {user.full_name},</p>
                    <p>Welcome to Admrt.com – the platform designed to connect you with brands and businesses eager to collaborate. We're thrilled to have you on board!</p>
                    <p>To get you started, we’re offering you a <strong>FREE professional media kit</strong>. Your media kit is your personalized pitch tool that highlights your audience, pricing, and value to potential advertisers.</p>
                    <h3>Claiming your media kit is easy:</h3>
                    <ol>
                        <li><strong>Click the link below</strong> to fill out a quick form with your details.</li>
                        <li><strong>We’ll create your media kit</strong> based on the information you provide.</li>
                        <li><strong>Receive your polished media kit</strong>, ready to share with brands!</li>
                    </ol>
                    <p><strong>👉 <a href="https://docs.google.com/forms/d/e/1FAIpQLSfCfdcKRt6aSefpyzt1RT6_FNF6T7HtR6_lkog2tpkLkuxnLQ/viewform">Claim Your Free Media Kit Here</a></strong></p>
                    <p>Need help or have questions? Reply to this email, and we’ll be happy to assist.</p>
                    <p>Best Regards,<br>Admr Team</p>
                </body>
            </html>
            """
            part = MIMEText(html_content, "html")
            message.attach(part)

            # Send the email using SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())

        except ImproperlyConfigured:
            print("SMTP configuration is missing or incorrect.")
        except Exception as e:
            print(f"An error occurred while sending email: {e}")


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'country', 'birthday', 'user_role']
        
        
class UserDetailSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id",'full_name', 'email', 'phone', 'country', 'birthday', 'user_role', 'last_seen', 'profile_image']
        read_only_fields = ['email', 'user_role']

    def get_profile_image(self, obj):
        if hasattr(obj, 'profile') and obj.profile.profile_image:
            return obj.profile.profile_image.url  # Return the URL of the profile image
        return None  # Return None if no profile image is available

        
        
class UserPartialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'country', 'birthday']
        

class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        image_url = None
        is_admin = None
        if hasattr(user, 'profile'):
            image_url = get_profile_image_url(user.profile.profile_image)
            is_admin = user.profile.is_admin
        token['id'] = user.id
        token['email'] = user.email
        token['username'] = user.username
        token['full_name'] = user.full_name
        token['profile_image'] = image_url
        token['is_admin'] = is_admin
        token['user_role'] = user.user_role
        return token
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        data = super().validate(attrs)
        image_url = None
        is_admin = None
        if hasattr(self.user, 'profile'):
            image_url = get_profile_image_url(self.user.profile.profile_image)
            is_admin = self.user.profile.is_admin
        data['user'] = {
            "id": self.user.id,
            "email": self.user.email,
            "username": self.user.username,
            "full_name": self.user.full_name,
            "profile_image": image_url,
            "is_admin": is_admin,
            "phone": self.user.phone,
            "country": self.user.country,
            "user_role": self.user.user_role
        }
        return data
    
    
# class PasswordResetSerializer(serializers.Serializer):
#     email = serializers.EmailField()

#     def validate_email(self, value):
#         user = User.objects.filter(email=value).first()
#         if not user:
#             raise serializers.ValidationError(_("No user is associated with this email address."))
#         return value

#     def save(self):
#         user = User.objects.get(email=self.validated_data['email'])
#         user.set_reset_code()

#         # Send the code via email
#         send_mail(
#             'Password reset code',
#             f'Your password reset code is: {user.reset_code}',
#             settings.DEFAULT_FROM_EMAIL,
#             [user.email],
#             fail_silently=False,
#         )


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("No user is associated with this email address.")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_reset_code()

        # Prepare email context
        context = {
            'reset_code': user.reset_code,
            'site_name': 'AdMrt',
            'full_name': user.full_name,
        }

        # Render the HTML template
        html_content = render_to_string('emails/password_reset.html', context)
        text_content = strip_tags(html_content)

        # Send email
        email = EmailMultiAlternatives(
            subject="Password Reset on AdMrt",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        
class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(email=data['email']).first()
        if not user or not user.validate_reset_code(data['reset_code']):
            raise serializers.ValidationError("Invalid reset code or email.")
        return data

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.clear_reset_code()
        user.save()

class UserCountSerializer(serializers.Serializer):
    period = serializers.CharField()
    data = serializers.DictField()  # Allowing any structure for the data


class AdvertiserProductCountSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'product_count']

class AffiliateLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateLink
        fields = ['url']

    def validate_url(self, value):
        # Check if the URL already exists
        if AffiliateLink.objects.filter(url=value).exists():
            raise serializers.ValidationError("URL already exists")
        return value