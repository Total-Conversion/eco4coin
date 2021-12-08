# from django.contrib.auth.models import User
# from django.contrib.auth.models import User
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .models import Trade, Sale, Purchase, ApplicationVersion
from accounts.models import CustomUser
from rest_framework import serializers
from django.db.models.query_utils import Q


class ApplicationVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApplicationVersion
        fields = ['version']


class CreateTradeSerializer(serializers.ModelSerializer):
    recipient = serializers.CharField(min_length=34, max_length=34)

    class Meta:
        model = Trade
        fields = ['trade_type', 'trade_value', 'recipient', 'notes']

    def __init__(self, instance=None, user=None, **kwargs):
        self.user = user
        super().__init__(instance, **kwargs)

    def validate_user(self, data):
        return data

    def validate_recipient(self, data):
        print(data)
        print(self.user.wallet_id)
        if self.user.wallet_id == data:
            raise serializers.ValidationError("You cant send Coins to Yourself ")
        return data

    def validate_trade_value(self, data):

        if self.user.coin_balance < data:
            raise serializers.ValidationError("You don't have enough coins")
        return data

    def create(self, validated_data):
        if CustomUser.objects.filter(wallet_id=validated_data['recipient']).exists():
            trade_instance = Trade.objects.create(
                trade_type=validated_data['trade_type'],
                trade_value=validated_data['trade_value'],
                sender=validated_data['sender'],
                notes=validated_data['notes'],
                recipient=CustomUser.objects.get(wallet_id=validated_data['recipient']),
                recipient_wallet_id=validated_data['recipient']
            )
            return trade_instance
        else:
            trade_instance = Trade.objects.create(
                trade_type=validated_data['trade_type'],
                trade_value=validated_data['trade_value'],
                sender=validated_data['sender'],
                notes=validated_data['notes'],
                recipient_wallet_id=validated_data['recipient']
            )
            return trade_instance


class TradeSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.wallet_id')

    class Meta:
        model = Trade
        fields = ['sender', 'trade_type', 'trade_price', 'sale_order', 'purchase_order', 'trade_value', 'recipient_wallet_id', 'created_at', 'notes']


class NestedTradeSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.wallet_id')

    class Meta:
        model = Trade
        fields = ['wallet_id', 'sender', 'trade_type', 'trade_value', 'recipient_wallet_id', 'created_at', 'notes']


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['device']
        extra_kwargs = {"device": {"required": True}}

    def create(self, validated_data):
        if CustomUser.objects.filter(device=validated_data['device']).exists():
            user = CustomUser.objects.create(
                username=validated_data['username'],
                device=validated_data['device'],
                cash_balance=0,
                coin_balance=0,
            )
        else:
            user = CustomUser.objects.create(
                username=validated_data['username'],
                device=validated_data['device'],
            )
        return user


class StandardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'device', 'email', 'cash_balance', 'coin_balance', 'id', 'wallet_id', 'cash_locked', 'coin_locked']


class UserSerializer(serializers.ModelSerializer):
    trades = serializers.SerializerMethodField(
        source='trade', read_only=True)

    def get_trades(self):
        return NestedTradeSerializer(
            Trade.objects.filter(
                Q(sender=self.context.get("request").user) |
                Q(recipient=self.context.get("request").user)
            ).order_by("-created_at"),
            many=True, read_only=True).data

    class Meta:
        model = CustomUser
        # queryset = Trade.objects.all()
        fields = ['cash_balance', 'coin_balance', 'trades', 'wallet_id', 'cash_locked', 'coin_locked']


class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['wallet_id', 'cash_balance', 'coin_balance', 'cash_locked', 'coin_locked']

# ================


class SaleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sale
        fields = ['id', 'sale_price', 'init_amount', 'amount', 'sale_status', 'created_at']


class RevokeSaleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sale
        fields = []


class CreateSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ['sale_price', 'amount']

    def __init__(self, instance=None, user=None, **kwargs):
        self.user = user
        super().__init__(instance, **kwargs)

    def validate_user(self, data):
        return data

    def validate_amount(self, data):
        if self.user.coin_balance < data:
            raise serializers.ValidationError("not enough coin")  # todo z error_messages
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = CustomUser.objects.select_for_update().get(id=self.user.id)
        user.coin_balance -= validated_data['amount']
        user.coin_locked += validated_data['amount']
        user.save()
        sale_instance = Sale.objects.create(
            amount=validated_data['amount'],
            init_amount=validated_data['amount'],
            sale_price=validated_data['sale_price'],
            sale_user=validated_data['sale_user']
        )
        return sale_instance


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['id', 'purchase_price', 'init_amount', 'amount', 'purchase_status', 'created_at']


class RevokePurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = []


class CreatePurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['purchase_price', 'amount']

    def __init__(self, instance=None, user=None, **kwargs):
        self.user = user
        super().__init__(instance, **kwargs)

    def validate(self, data):
        if self.user.cash_balance < data['amount'] * data['purchase_price']:
            raise serializers.ValidationError("not enough cash")  # todo z error_messages
        return data

    # def validate_amount(self, data):
    #     if self.user.cash_balance < data:
    #         raise serializers.ValidationError("not enough cash")
    #     return data

    @transaction.atomic
    def create(self, validated_data):
        # self.user.cash_balance -= validated_data['amount']
        # self.user.save()
        user = CustomUser.objects.select_for_update().get(id=self.user.id)
        user.cash_balance -= validated_data['amount'] * validated_data['purchase_price']  # max price
        user.cash_locked += validated_data['amount'] * validated_data['purchase_price']  # max price
        user.save()
        purchase_instance = Purchase.objects.create(
            amount=validated_data['amount'],
            init_amount=validated_data['amount'],
            purchase_price=validated_data['purchase_price'],
            purchase_user=validated_data['purchase_user']
        )
        return purchase_instance