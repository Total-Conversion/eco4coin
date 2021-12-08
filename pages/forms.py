from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ModelForm, Form
from django import forms
from accounts.models import CustomUser
from backend.models import Trade
from django.utils.translation import ugettext_lazy as _


class TradeForm(Form):
    pmt_recipient = forms.EmailField(
        error_messages={'cant': _('You cant Send $$ for yourself'),
                        'invalid': _('There is no such user')}
    )
    trade_value = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
        error_messages={
            'invalid': _('“%(value)s” value must be an integer.'),
            'not_enough': _('you do not have enough cash_balance')}
    )

    class Meta:
        model = Trade
        fields = ('trade_value', 'pmt_recipient',)

    def __init__(self, *args, **kwargs):
        self.user = (kwargs.pop('user', None))
        super(TradeForm, self).__init__(*args, **kwargs)

    def save(self, commit=True,):
        pmt_recipient = CustomUser.objects.get(email=self.cleaned_data['pmt_recipient'])
        trade = Trade(
            pmt_sender=self.user,
            trade_value=self.cleaned_data['trade_value'],
            pmt_recipient=pmt_recipient,
        )

        trade.save(commit)
        return trade

    def clean_trade_value(self):
        user = CustomUser.objects.get(id=self.user.id)
        if (user.cash_balance - self.cleaned_data['trade_value']) < 0:
            raise forms.ValidationError("you do not have enough balance")
        trade_value = self.cleaned_data['trade_value']
        return trade_value

    def clean_pmt_recipient(self):
        user = CustomUser.objects.get(id=self.user.id)
        try:
            pmt_recipient = CustomUser.objects.get(email=self.cleaned_data['pmt_recipient'])
            if user == pmt_recipient:
                raise ValidationError(self.fields['pmt_recipient'].error_messages['cant'])
            pmt_recipient = self.cleaned_data['pmt_recipient']
            return pmt_recipient

        except CustomUser.DoesNotExist:
            raise ValidationError(self.fields['pmt_recipient'].error_messages['invalid'])


