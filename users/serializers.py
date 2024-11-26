from rest_framework import serializers
from .models import (
    SpaceHost,
    Advertiser,
    AdvertiserProduct,
    Topic,
    SocialMedia,
    Portfolio,
    AdSpaceForSpaceHost,
)
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from core.models import User
from .models import SpaceHost
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from .models import SpaceHost,Topic,PlatformBaseUser
from core.models import User, Notification
def get_space_hosts_with_topics():
    # Get all users with 'space_host' role
    space_hosts = User.objects.filter(user_role='space_host')

    # Prepare a list to store the results
    result_data = []

    for user in space_hosts:
        # Fetch associated topics where Topic's user_id matches the current user.id
        topics = Topic.objects.filter(user_id=user.id)

        # Create a list of topics with their IDs and titles
        topics_list = [topic.title for topic in topics]

        # Append user and topics data to the result
        result_data.append({
            "user_id": user.id,
            "topics": topics_list
        })

    return result_data# from django.utils.deconstruct import deconstructible

# Profile Serializers
class AdSpaceForSpaceHostSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdSpaceForSpaceHost
        fields = ['id', 'space_type', 'file', 'url']


class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = ['id', 'social_media', 'url']


# class ProductImageUploadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductImageUploadFragment
#         fields = ['id', 'file']


from rest_framework import serializers
from .models import AdvertiserProduct

from rest_framework import serializers
from .models import AdvertiserProduct
import json
from ai_model.topic_similarity import TopicSimilarityModel

class ProductSerializer(serializers.ModelSerializer):
    topics = serializers.CharField(write_only=True, required=False, allow_blank=True)  # Optional field
    full_name = serializers.CharField(read_only=True)  # Include full_name as a read-only field
    class Meta:
        model = AdvertiserProduct
        fields = ['id', 'name', 'description', 'image1', 'image2', 'image3', 'productType', 'topics',"full_name"]

    def create(self, validated_data):
        topics_data = validated_data.pop('topics', '')  # Get the comma-separated string, or empty string if not provided
        if topics_data:
            # Convert the comma-separated string into a list
            topics_list = [topic.strip() for topic in topics_data.split(',')]
        else:
            topics_list = []  # If no topics provided, set it as an empty list
        
          
        similarity_model = TopicSimilarityModel()
        
        
        data = get_space_hosts_with_topics()
        print("data is",data)
        similarity_scores_for_users = []
        maillist = []  # List to store users whose similarity score is greater than 0.8
        product = AdvertiserProduct.objects.create(**validated_data)
        for space_host in data:
            user_id = space_host['user_id']
            space_host_topics = space_host['topics']  # Get the topics list for this user

            # Calculate similarity between the input topics and the user's topics
            user_similarity = similarity_model.find_similar_topics(topics_list, space_host_topics)
            
            similarity_scores_for_users.append({
                "user_id": user_id,
                "similarity_scores": user_similarity
            })

        print("similarity_scores_for_users",similarity_scores_for_users)
            # Apply condition for maillist based on similarity scores
        for user_similarity in similarity_scores_for_users:
            user_id = user_similarity['user_id']
            for similarity in user_similarity['similarity_scores']:
                if similarity['score'] > 0.5:
                    maillist.append(user_id)
                    break  # No need to check further once the user is added to the maillist
         # Print out the maillist
        for i in maillist:
            try:
                # Ensure the user exists in the database
                user = User.objects.get(id=i)
                
                # Create the notification for the user
                Notification.objects.create(
                    user_id=i,
                    message=f"related product from user {product.user_id}",
                    notificationType="related product",
                    status="sent"
                )
            except User.DoesNotExist:
                print(f"User with ID {i} does not exist. Skipping notification.")
            except Exception as e:
                print(f"Error while creating notification for user {i}: {e}")
        emails = list(User.objects.filter(id__in=maillist).values_list('email', flat=True))
        print("Emails to Notify:", emails)
        product_name = validated_data.get("name", "a new product")
        self.send_product_alert_emails(emails, product_name)
        # Store topics as a stringified list (JSON format)
        product.topics = json.dumps(topics_list)
        product.save()
        return product
    
    def update(self, instance, validated_data):
        topics_data = validated_data.pop('topics', '')  # Get the comma-separated string, or empty string if not provided
        if topics_data:
            # Convert the comma-separated string into a list
            topics_list = [topic.strip() for topic in topics_data.split(',')]
        else:
            topics_list = []  # If no topics provided, set it as an empty list
        instance = super().update(instance, validated_data)
        # Update the topics as a stringified list
        instance.topics = json.dumps(topics_list)
        instance.save()
        return instance
    
    def send_product_alert_emails(self, emails, product_name):
            
        try:


            # Debug: Print the settings values
            print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
            print("EMAIL_HOST_PASSWORD:", settings.EMAIL_HOST_PASSWORD)
            print("EMAIL_HOST:", settings.EMAIL_HOST)

            # Set up email details
            sender_email = settings.EMAIL_HOST_USER
            password = settings.EMAIL_HOST_PASSWORD
            smtp_server = settings.EMAIL_HOST
            smtp_port = 587

            # Prepare the email message template
            for receiver_email in emails:
                
                # Create the email message
                message = MIMEMultipart("alternative")
                message["Subject"] = "New Product Alert: Your Favorite Interests!"
                message["From"] = sender_email
                message["To"] = receiver_email

                # Create the HTML content
                html_content = f"""
                <html>
                <body>
                    <h2>Hello!</h2>
                    <p>A new product, <strong>{product_name}</strong>, has been added that matches your favorite interests!</p>
                    <p>We thought you might be interested in checking it out.</p>
                    <p>Visit our platform to learn more.</p>
                    <p>Best Regards,<br>Our Team</p>
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
                    print(f"Email sent successfully to {receiver_email}")

        except ImproperlyConfigured:
            print("SMTP configuration is missing or incorrect.")
        except Exception as e:
            print(f"An error occurred while sending email: {e}")


    def to_representation(self, instance):
        # When returning data, convert the stringified list back to a Python list
        representation = super().to_representation(instance)
        representation['topics'] = json.loads(instance.topics) if instance.topics else []  # Convert stringified list back to list
        return representation



class AdvertiserSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    socials = SocialMediaSerializer(many=True, read_only=True)
    joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    id = serializers.IntegerField(source='user.id', read_only=True)
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    user_role = serializers.CharField(source='user.user_role', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Advertiser
        fields = ['id', 'full_name', 'profile_image', 'banner_image', 'description', 'location', 'website', 'is_admin', 'joined', 'products', 'socials', 'user_role', 'user']


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'title']


# class PortfolioImageUploadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PortfolioImageUploadFragment
#         fields = ['id', 'file']
        

class PortfolioSerializer(serializers.ModelSerializer):
    # images = PortfolioImageUploadSerializer(many=True, read_only=True)
    class Meta:
        model = Portfolio
        fields = ['id', 'title', 'description', 'image1', 'image2', 'image3', 'youtube_url']


# class LanguageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Language
#         fields = ['id', 'language']


class SpaceHostSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    # languages = LanguageSerializer(many=True, read_only=True)
    portfolios = PortfolioSerializer(many=True, read_only=True)
    socials = SocialMediaSerializer(many=True, read_only=True)
    ad_spaces = AdSpaceForSpaceHostSerializer(many=True, read_only=True)
    joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    id = serializers.IntegerField(source='user.id', read_only=True)
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    user_role = serializers.CharField(source='user.user_role', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = SpaceHost
        fields = ['id', 'full_name', 'profile_image', 'banner_image', 'description', 'location', 'website', 'is_admin', 'joined', 'long_term_service_availability', 'topics', 'languages', 'portfolios', 'socials', 'ad_spaces', 'user_role', 'user']


class AdvertiserProductCountSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'product_count']