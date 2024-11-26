from django.contrib import admin
from .models import SpaceHost, Topic, Portfolio, SocialMedia, Advertiser, AdvertiserProduct


admin.site.register([SpaceHost, Topic, Portfolio, SocialMedia, Advertiser, AdvertiserProduct])