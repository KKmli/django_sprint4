from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.conf import settings
from blog.views import simple_logout


handler403 = 'pages.views.csrf_failure'
handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'

urlpatterns = [
    path('', include('blog.urls')),
    path('pages/', include('pages.urls')),
    path('admin/', admin.site.urls),

    path('auth/login/', LoginView.as_view(), name='login'),
    # Используем кастомный logout, который принимает GET-запрос
    path('auth/logout/', simple_logout, name='logout'),
    path('auth/password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('auth/password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('auth/password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('auth/password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
