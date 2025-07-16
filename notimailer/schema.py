from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="📧 Notimailer API Docs",
      default_version='v1',
      description="Welcome to the Swagger UI!",
      terms_of_service="https://your-site.com/terms/",
      contact=openapi.Contact(email="support@notimailer.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
