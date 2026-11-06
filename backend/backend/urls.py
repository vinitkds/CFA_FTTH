from django.contrib import admin
from django.urls import path, include
from api.views import CreateUserView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/register/' , CreateUserView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='get_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),

    path('api-auth/', include('rest_framework.urls')),
    # path('api/', include('api.urls')),
    path('api/OLT/', include('OLT.urls')),
]


# ⚠️ One Important Nginx Fix Required

# Because your base URLs now start with /OLT/ instead of /api/, your existing Nginx reverse proxy will not automatically route these requests to your Django backend.
# To prevent 404 Not Found errors when your React frontend tries to call these URLs, you must add an /OLT/ location block to your nginx.conf file:
# nginx
# # Add this block inside your server {} context in nginx.conf
# location /OLT/ {
#     proxy_pass http://backend:8000;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
#     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#     proxy_set_header X-Forwarded-Proto $scheme;
# }