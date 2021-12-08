from django.contrib.admin.views.decorators import staff_member_required

from django.views.generic import TemplateView, ListView
import csv
from django.http import HttpResponse
from backend.models import CustomUser
from django.contrib.auth.mixins import LoginRequiredMixin


class HomePageView(TemplateView):
    template_name = 'pages/home.html'


class UsersListView(LoginRequiredMixin, ListView):
    model = CustomUser
    context_object_name = 'user'
    template_name = 'pages/users_list.html'
    paginate_by = 100

    def get_queryset(self):
        return CustomUser.objects.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super(UsersListView, self).get_context_data(**kwargs)
        context['user'] = CustomUser.objects.get(id=self.request.user.id)
        return context


@staff_member_required(login_url="/accounts/login/")
def users_to_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_list.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "id ", "cash_balance ", "cash_locked ", "coin_balance ", "coin_locked ", "wallet_id ", " date_joined"
         ]
    )
    users_list = CustomUser.objects.all().order_by("id")
    for user in users_list:
        writer.writerow(
            [
                user.id,
                user.cash_balance,
                user.cash_locked,
                user.coin_balance,
                user.coin_locked,
                user.wallet_id,
                user.date_joined
             ]
        )
    return response
