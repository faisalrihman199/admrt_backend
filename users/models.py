import datetime
import uuid
from django.conf import settings
from django.db import models
from ai_model.topic_similarity import TopicSimilarityModel


def change_filename(folder_path, original_filename, given_filename):
    file_parts = original_filename.split('.')
    if len(file_parts) > 1:
        updated_filename = f"{folder_path}/{given_filename}.{file_parts[-1]}"
    else:
        updated_filename = f"{folder_path}/{original_filename}"
    return updated_filename


def change_profile_image_filename(instance, filename):
    return change_filename(
        folder_path=f"profile/{instance.user.id}",
        original_filename=filename,
        given_filename='profile_image'
    )


def change_banner_image_filename(instance, filename):
    return change_filename(
        folder_path=f"profile/{instance.user.id}",
        original_filename=filename,
        given_filename='banner_image'
    )


def change_advertiser_product_image_filename(instance, filename):
    return change_filename(
        folder_path=f"profile/{instance.user.user.id}",
        original_filename=filename,
        given_filename='advertiser_product'
    )

# @deconstructible
# class UploadTo:
#     def __init__(self, folder_path, custom_file_name):
#         self.folder_path = folder_path
#         self.custom_file_name = custom_file_name

#     def __call__(self, instance, filename):
#         return self.change_filename(self.folder_path, filename, self.custom_file_name)

#     def change_filename(self, folder_path, original_filename, given_filename):
#         file_parts = original_filename.split('.')
#         if len(file_parts) > 1:
#             updated_filename = f"{folder_path}/{given_filename}.{file_parts[-1]}"
#         else:
#             updated_filename = f"{folder_path}/{original_filename}"
#         return updated_filename
    


def change_portfolio_image_filename(instance, filename):
    return change_filename(
        folder_path=f"profile/{instance.user.user.id}/portfolios/{instance.id}",
        original_filename=filename,
        given_filename=f'{uuid.uuid4()}'
    )


def change_product_image_filename(instance, filename):
    return change_filename(
        folder_path=f"profile/{instance.user.user.id}/products/{instance.id}",
        original_filename=filename,
        given_filename=f'{uuid.uuid4()}'
    )


def change_space_filename(instance, filename):
    return change_filename(
        folder_path=f"profile/{instance.user.user.id}/spaces/{instance.id}",
        original_filename=filename,
        given_filename=f'{uuid.uuid4()}'
    )


class PlatformBaseUser(models.Model):
    profile_image = models.ImageField(upload_to=change_profile_image_filename, null=True, blank=True)
    banner_image = models.ImageField(upload_to=change_banner_image_filename, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(max_length=255, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='profile')

    def __str__(self) -> str:
        return self.user.full_name


class SpaceHost(PlatformBaseUser):
    languages = models.CharField(max_length=255, null=True, blank=True)
    long_term_service_availability = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return self.user.full_name

    def save(self, *args, **kwargs):
        if not self.user.user_role == settings.K_SPACE_HOST_ID:
            print(f"user needs to have role of {settings.K_SPACE_HOST_ID} to be saved in SpaceHost model")
        else:
            return super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['user__full_name']


class Advertiser(PlatformBaseUser):
    def __str__(self) -> str:
        return self.user.full_name

    def save(self, *args, **kwargs):
        if not self.user.user_role == settings.K_ADVERTISER_ID:
            print(f"user needs to have role of {settings.K_ADVERTISER_ID} to be saved in Advertiser model")
        else:
            return super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['user__full_name']


class Topic(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(SpaceHost, on_delete=models.CASCADE, related_name='topics')

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['title']


class AdvertiserProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image1 = models.ImageField(
        upload_to=change_product_image_filename,
        null=True,
        blank=True
    )
    image2 = models.ImageField(
        upload_to=change_product_image_filename,
        null=True,
        blank=True
    )
    image3 = models.ImageField(
        upload_to=change_product_image_filename,
        null=True,
        blank=True
    )
    productType = models.CharField(max_length=255,default="public")
    topics = models.TextField(null=True, blank=True)
    user = models.ForeignKey(Advertiser, on_delete=models.CASCADE, related_name='products')

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        ordering = ['name']


# class ProductImageUploadFragment(models.Model):
#     file = models.ImageField(upload_to=change_product_image_filename)
#     product = models.ForeignKey(AdvertiserProduct, related_name='images', on_delete=models.CASCADE)


# class Language(models.Model):
#     language = models.CharField(max_length=100)
#     user = models.ForeignKey(SpaceHost, related_name='languages', on_delete=models.CASCADE)

#     def __str__(self) -> str:
#         return self.language
    
#     class Meta:
#         ordering = ['language']


class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image1 = models.ImageField(
        upload_to=change_portfolio_image_filename,
        null=True,
        blank=True
    )
    image2 = models.ImageField(
        upload_to=change_portfolio_image_filename,
        null=True,
        blank=True
    )
    image3 = models.ImageField(
        upload_to=change_portfolio_image_filename,
        null=True,
        blank=True
    )
    youtube_url = models.URLField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(SpaceHost, on_delete=models.CASCADE, related_name='portfolios')

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['title']


# class PortfolioImageUploadFragment(models.Model):
#     file = models.ImageField(upload_to=change_portfolio_image_filename)
#     portfolio = models.ForeignKey(Portfolio, related_name='images', on_delete=models.CASCADE)


class SocialMedia(models.Model):
    SM_CHOICES = [(key, value) for key, value in settings.K_SOCIAL_MEDIAS.items()]

    social_media = models.CharField(max_length=2, choices=SM_CHOICES)
    # username = models.CharField(max_length=100, null=True, blank=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(PlatformBaseUser, on_delete=models.CASCADE, related_name='socials')

    def __str__(self) -> str:
        if self.url is not None:
            return self.url
        elif self.username is not None:
            return self.username
        else:
            return None
        

def generate_random_uuid():
    return str(uuid.uuid4())
        

class AdSpaceForSpaceHost(models.Model):
    ST_CHOICES = [(key, value) for key, value in settings.K_AD_TYPES.items()]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space_type = models.CharField(max_length=30, choices=ST_CHOICES)
    url = models.CharField(max_length=256)
    file = models.FileField(upload_to=change_space_filename, null=True, blank=True)
    user = models.ForeignKey(SpaceHost, on_delete=models.CASCADE, related_name='ad_spaces')
