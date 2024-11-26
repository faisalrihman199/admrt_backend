from django.urls import include, path
from rest_framework.routers import SimpleRouter

from ad_space import views


router = SimpleRouter()
router.register('search', views.AdSpaceViewSet, basename='search_space')

urlpatterns = router.urls