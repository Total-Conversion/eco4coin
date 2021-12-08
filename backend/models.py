from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from accounts.models import CustomUser
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from accounts.models import CustomUser
from django.db import transaction


class ApplicationVersion(models.Model):
    version = models.CharField(max_length=50, null=True, blank=True)


class Sale(models.Model):

    sale_user = models.ForeignKey(CustomUser, related_name="sale_user", on_delete=models.PROTECT)
    sale_price = models.DecimalField(max_digits=99, decimal_places=2)
    amount = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
        error_messages={'invalid': _('“%(value)s” value must be an integer.'),
                        'not_enough': _('you do not have enough coin balance')}
    )

    init_amount = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    SALE_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('FULFILLED', 'Fulfilled'),  # udało się sprzedać
        ('CANCELLED', 'Cancelled'),
    ]
    sale_status = models.CharField(
        max_length=32,
        choices=SALE_STATUS_CHOICES,
        default='AVAILABLE',
    )


class Purchase(models.Model):
    purchase_user = models.ForeignKey(CustomUser, related_name="purchase_user", on_delete=models.PROTECT)
    purchase_price = models.FloatField()
    amount = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
        error_messages={'invalid': _('“%(value)s” value must be an integer.'),
                        'not_enough': _('you do not have enough cash balance')
                        }
    )
    init_amount = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    PURCHASE_STATUS_CHOICES = [
        ('AVAILABLE', 'available'),
        ('FULFILLED', 'Fulfilled'),
        ('CANCELLED', 'Cancelled'),
    ]
    purchase_status = models.CharField(
        max_length=32,
        choices=PURCHASE_STATUS_CHOICES,
        default='AVAILABLE',
    )


class Trade(models.Model):
    """
    trade_view
    """
    TRADE_TYPES_CHOICES = [
        ('SEND_COIN', 'Send Coin'),
        ('SELL_COIN', 'Sell Coin')
    ]
    sale_order = models.ForeignKey(
        Sale,
        related_name="sale_order",
        on_delete=models.PROTECT,
        null=True,
        blank=True)
    purchase_order = models.ForeignKey(
        Purchase,
        related_name="purchase_order",
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    sender = models.ForeignKey(
        CustomUser, related_name="pmt_sender",
        on_delete=models.PROTECT,
        null=True, blank=True)

    recipient = models.ForeignKey(
        CustomUser,
        help_text="Entry wallet id",
        related_name="pmt_recipient",
        on_delete=models.PROTECT,
        error_messages={'cant': _('You cant Send $$ for yourself'),
                        'invalid': _('There is no such user')},
        null=True,
        blank=True
    )

    recipient_wallet_id = models.CharField(
        max_length=34,
        null=True,
        blank=True
    )

    trade_price = models.FloatField(blank=True, null=True,)

    trade_value = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
        error_messages={
            'invalid': _('“%(value)s” value must be an integer.'),
            'not_enough': _('you do not have enough cash_balance')
        },
        blank=True,
        null=True,
    )

    notes = models.TextField(max_length=255, blank=True, null=True, default="")

    trade_type = models.CharField(
        max_length=32,
        choices=TRADE_TYPES_CHOICES,
        default='SEND_COIN',
        null=True, blank=True
    )

    TRANSACTION_STATUS_CHOICES = [
                ('FULFILLED', 'Fulfilled'),
                ('CANCELLED', 'Cancelled'),
            ]
    transaction_status = models.CharField(
        max_length=32,
        choices=TRANSACTION_STATUS_CHOICES,
        default='FULFILLED',
        null=True, blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)


# todo czy ten zestaw nie powinien być ograniczony do x rekordów, a potem brac następny?
@transaction.atomic
def match():
    purchases = Purchase.objects.order_by("-created_at").filter(purchase_status="AVAILABLE")
    # przetwarzamy oferty kupna
    try:
        for p in purchases:
            try:
                print("Purchase id", p.id, p.amount)
                while p.amount > 0:
                    # szukamy pasujących ofert sprzedaż
                    # todo przy skalowaniu pojedyńcze selecty mogą być wolne

                    matching_sale = Sale.objects.order_by('-sale_price', '-created_at') \
                        .filter(sale_price__lte=p.purchase_price, sale_status='AVAILABLE') \
                        .select_for_update(skip_locked=True) \
                        .first()

                    if matching_sale is None:  # bez pasującej oferty sprzedaży nie da się jej przetowżyć więc tzreba przerwać pętlę
                        break

                    print("Matching sale", matching_sale.id, matching_sale.amount)

                    # kurs jest tego, kto pierwszy wystawił
                    if matching_sale.created_at > p.created_at:
                        trade_price = p.purchase_price
                    else:
                        trade_price = matching_sale.sale_price
                    # purchase: blokujemy: $ X * kurs_max # nie mamy zapisane ile zablokowaliśmy
                    # ale zablokowaliśmy MAX wartość
                    # zablokowane_srodki = matching_sale.amount * matching_sale.sale_price  # a nie purchase??

                    t = Trade.objects.create(
                        transaction_status="FULFILLED",
                        sender=matching_sale.sale_user,
                        recipient=p.purchase_user,
                        trade_price=trade_price,
                        trade_value=matching_sale.amount,
                        sale_order=matching_sale,
                        purchase_order=p,
                        recipient_wallet_id=p.purchase_user.wallet_id,
                        trade_type='TRANSACTION',
                    )
                    trade_coins = t.trade_value
                    trade_cash = float(trade_price * trade_coins)

                    if matching_sale.amount <= p.amount:
                        p.amount -= matching_sale.amount
                        if p.amount == 0:
                            p.purchase_status = "FULFILLED"

                        matching_sale.sale_status = "FULFILLED"
                        matching_sale.amount = 0  # to jest do zamknięcia sprzedaży
                    else:
                        p.purchase_status = "FULFILLED"
                        p.amount = 0

                        matching_sale.amount -= p.amount

                    matching_sale.save()
                    p.save()
                    # 3.

                    seller = CustomUser.objects.get(id=matching_sale.sale_user.id)
                    seller.cash_balance += trade_cash  # sprzedający dostaje wartość tranzakcji
                    seller.coin_locked -= trade_coins  # zdejmujemy zablokowane coiny
                    seller.save()

                    buyer = CustomUser.objects.get(id=p.purchase_user.id)
                    buyer.coin_balance += trade_coins
                    lock_adjustment = (float(p.purchase_price) - float(trade_price)) * trade_coins
                    buyer.cash_locked -= trade_cash
                    buyer.cash_locked -= lock_adjustment
                    buyer.cash_balance += lock_adjustment

                    buyer.save()
                    t.save()

            except Sale.DoesNotExist:
                print("sales not found")
                raise CommandError('Nie poszło')
    except Purchase.DoesNotExist:
        print("purchases does not exist")
        raise CommandError('Nie poszło')


@receiver(post_save, sender=Sale)
def sale_created_signal(sender, instance=None, created=False, **kwargs):
    if created:
        # django_rq.enqueue(find_transactions)
        match()


@receiver(post_save, sender=Purchase)
def purchase_created_signal(sender, instance=None, created=False, **kwargs):
    if created:
        # django_rq.enqueue(find_transactions)
        match()

