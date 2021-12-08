from django.urls import path

from .views import HomePageView, UsersListView, users_to_csv
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('accounts_customuser/', UsersListView.as_view(), name='UsersListView'),
    path('export/users-to-csv/', users_to_csv, name='csv_simple_write'),

]

