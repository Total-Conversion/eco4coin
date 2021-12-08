import uuid

from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from backend.serializers import TradeSerializer, UserSerializer, CreateTradeSerializer, \
    CreateUserSerializer, StandardUserSerializer, UserWalletSerializer, CreateSaleSerializer, SaleSerializer, \
    CreatePurchaseSerializer, PurchaseSerializer, RevokeSaleSerializer, RevokePurchaseSerializer, \
    ApplicationVersionSerializer
from backend.models import Trade, Sale, Purchase, ApplicationVersion
from accounts.models import CustomUser


from django.db.models.query_utils import Q
import random
import string


class TradeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_permissions(self):
        if self.action == 'user_trades_list':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(TradeViewSet, self).get_permissions()
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(TradeViewSet, self).get_permissions()
        else:
            self.permission_classes = [permissions.IsAuthenticated]
            return super(TradeViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTradeSerializer
        return TradeSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=False)
    def user_trades_list(self, request):
        queryset = Trade.objects.order_by('-created_at').filter(
            Q(sender=self.request.user) |
            Q(recipient=self.request.user)
        )
        self.serializer = TradeSerializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            user=request.user
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        sender = CustomUser.objects.get(id=self.request.user.id)
        if (serializer.data['trade_type'] == 'SEND_COIN') \
                and ((sender.coin_balance - serializer.data['trade_value']) >= 0):
            sender.coin_balance -= serializer.data['trade_value']
            sender.save()
            if CustomUser.objects.filter(wallet_id=serializer.data['recipient']).exists():
                recipient = CustomUser.objects.get(wallet_id=serializer.data['recipient'])
                recipient.coin_balance += serializer.data['trade_value']
                recipient.save()

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


def random_char(y):
    return ''.join(random.choice(string.ascii_letters) for x in range(y))


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(username=uuid.uuid4())

    def get_serializer_class(self):

        if self.action == 'create':
            return CreateUserSerializer
        if self.action == 'wallet_info':
            return UserSerializer
        return StandardUserSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.AllowAny]
            return super(UserViewSet, self).get_permissions()
        if self.action == 'wallet_info':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(UserViewSet, self).get_permissions()
        else:
            self.permission_classes = [permissions.IsAuthenticated]
            return super(UserViewSet, self).get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        token, created = Token.objects.get_or_create(user=serializer.instance)
        user = serializer.instance
        return Response(
            {'token': token.key,
             'coin_balance': user.coin_balance,
             'cash_balance': user.cash_balance,
             'wallet_id': user.wallet_id
             },
            status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False)
    def wallet_info(self, request):
        queryset = CustomUser.objects.get(id=self.request.user.id)
        serializer = UserWalletSerializer(queryset, many=False, context={"request": request})

        return Response(serializer.data)

# =========================================


class SaleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateSaleSerializer
        if self.action == 'revoke':
            return RevokeSaleSerializer
        return SaleSerializer

    def get_permissions(self):
        if self.name == 'User sale list':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(SaleViewSet, self).get_permissions()
        if self.name == 'Revoke':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(SaleViewSet, self).get_permissions()
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(SaleViewSet, self).get_permissions()
        if self.action == 'list':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(SaleViewSet, self).get_permissions()
        else:
            self.permission_classes = [permissions.IsAuthenticated]
            return super(SaleViewSet, self).get_permissions()

    def perform_create(self, serializer):
        serializer.save(sale_user=self.request.user)

    @action(detail=False)
    def user_sell_list(self, request):
        queryset = Sale.objects.order_by('-created_at').filter(sale_user=self.request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = Sale.objects.filter(Q(sale_status='AVAILABLE') and Q(amount__gt=0))
        # Q(sender=self.request.user) |
        # Q(recipient=self.request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            user=request.user
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['PUT'])
    def revoke(self, request, *args, **kwargs):
        sale_instance = Sale.objects.get(id=kwargs['pk'])

        if self.request.user == sale_instance.sale_user:
            sell_owner = CustomUser.objects.get(id=self.request.user.id)
            sell_owner.coin_balance += sale_instance.amount
            sell_owner.coin_locked -= sale_instance.amount
            sell_owner.save()
            sale_instance.sale_status = "CANCELLED"
            sale_instance.amount = 0
            sale_instance.save()

            return Response(status=status.HTTP_200_OK)

        headers = {"error": "only creator can update his sale"}
        return Response(status=status.HTTP_400_BAD_REQUEST, headers=headers)


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_permissions(self):

        if self.name == 'User purchase list':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(PurchaseViewSet, self).get_permissions()
        if self.name == 'Revoke':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(PurchaseViewSet, self).get_permissions()
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(PurchaseViewSet, self).get_permissions()
        if self.action == 'list':
            self.permission_classes = [permissions.IsAuthenticated]
            return super(PurchaseViewSet, self).get_permissions()
        else:
            self.permission_classes = [permissions.IsAuthenticated]
            return super(PurchaseViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePurchaseSerializer
        if self.action == 'revoke':
            return RevokePurchaseSerializer
        return PurchaseSerializer

    def perform_create(self, serializer):
        serializer.save(purchase_user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            user=request.user
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = Purchase.objects.filter(Q(sale_status='AVAILABLE') and Q(amount__gt=0))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['PUT'])
    def revoke(self, request, *args, **kwargs):
        purchase_instance = Purchase.objects.get(id=kwargs['pk'])

        if self.request.user == purchase_instance.purchase_user:
            purchase_owner = CustomUser.objects.get(id=self.request.user.id)
            purchase_owner.cash_balance += purchase_instance.amount * purchase_instance.purchase_price
            purchase_owner.cash_locked -= purchase_instance.amount * purchase_instance.purchase_price
            purchase_owner.save()
            purchase_instance.purchase_status = "CANCELLED"  # todo: zwracać kase userowi
            purchase_instance.amount = 0
            purchase_instance.save()

            return Response(status=status.HTTP_200_OK)

        headers = {"error": "only creator can update his purchase"}
        return Response(status=status.HTTP_400_BAD_REQUEST, headers=headers)

    @action(detail=False)
    def user_buy_list(self, request):
        queryset = Purchase.objects.order_by('-created_at').filter(purchase_user=self.request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def application_version_view(request):
    if ApplicationVersion.objects.filter(id=1).exists():
        queryset = ApplicationVersion.objects.get(id=1)
        serializer = ApplicationVersionSerializer(queryset)
        return Response(serializer.data)
    else:
        return Response({"exists": "put app version id=1 to your db!"})