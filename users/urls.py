# from django.urls import include, path
from django.urls import include, path
from rest_framework.routers import SimpleRouter
from . import views
from .views import UserCountView


router = SimpleRouter()

router.register('products', views.AdvertiserProductViewSet, basename='product_view_set')
router.register('product', views.AllAdvertiserProductViewSet, basename='all_product_view_set')
router.register('accounts', views.AllAccounts, basename='all_account_view_set')
router.register('socials', views.SocialMediaViewSet, basename='social_view_set')
router.register('ad-space', views.AdSpaceForSpaceHostViewSet, basename='ad_space_view_set')
router.register('portfolios', views.PortfolioViewSet, basename='portfolio_view_set')
# router.register('languages', views.LanguageViewSet, basename='language_view_set')

router.register('topics', views.TopicViewSet, basename='topic_view_set')
router.register('', views.UserViewSet, basename='user_view_set')
# router.register('accounts',UserCountView,basename="accounts")

urlpatterns = router.urls

# Add a path for UserCountView separately


# product_router = SimpleRouter()
# product_router.register('', views.AdvertiserProductViewSet, basename='product_view_set')

# # product_images_router = SimpleRouter()
# # product_images_router.register('', views.ProductImageViewSet, basename='product_images_view_set')

# ad_space_router = SimpleRouter()
# ad_space_router.register('', views.AdSpaceForSpaceHostViewSet, basename='ad_space_view_set')

# social_router = SimpleRouter()
# social_router.register('', views.SocialMediaViewSet, basename='social_view_set')

# portfolio_router = SimpleRouter()
# portfolio_router.register('', views.PortfolioViewSet, basename='portfolio_view_set')

# # portfolio_images_router = SimpleRouter()
# # portfolio_images_router.register('', views.PortfolioImageViewSet, basename='portfolio_images_view_set')

# language_router = SimpleRouter()
# language_router.register('', views.LanguageViewSet, basename='language_view_set')

# topic_router = SimpleRouter()
# topic_router.register('', views.TopicViewSet, basename='topic_view_set')

# router = SimpleRouter()
# router.register('', views.UserViewSet, basename='user_view_set')

# urlpatterns = [
#     # path('products/<int:id>/images/', include(product_images_router.urls)),
#     path('products/', include(product_router.urls)),
#     path('socials/', include(social_router.urls)),
#     path('ad_space/', include(ad_space_router.urls)),
#     # path('portfolios/<int:id>/images/', include(portfolio_images_router.urls)),
#     path('portfolios/', include(portfolio_router.urls)),
#     path('languages/', include(language_router.urls)),
#     path('topics/', include(topic_router.urls)),
#     path('', include(router.urls)),
# ]