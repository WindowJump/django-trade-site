from django.db import models
from django.contrib.auth.models import User

from .custom_exceptions import WalletTypeError


class CoinBaseModel(models.Model):
    priceUsd = models.DecimalField(max_digits=11, decimal_places=3)
    time = models.PositiveBigIntegerField()
    date = models.DateTimeField()

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.__class__.__name__}: {self.date}: {self.priceUsd}'


class BTCModel(CoinBaseModel):
    pass


class ETHModel(CoinBaseModel):
    pass


class LTCModel(CoinBaseModel):
    pass


class CoinType(models.Model):
    COIN_CHOICES = [
        ('BTC', 'bitcoin'),
        ('ETH', 'ethereum'),
        ('LTC', 'litecoin'),
        ('USDT', 'USDT')
    ]

    type = models.CharField(
        max_length=4,
        choices=COIN_CHOICES,
        unique=True
    )

    def __str__(self):
        return self.get_type_display()

    @classmethod
    def get_coin_type_from_verbose_name(cls, verbose_name):
        for code, name in cls.COIN_CHOICES:
            if name == verbose_name:
                return code
        return None


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    coin_type = models.ForeignKey(CoinType, on_delete=models.PROTECT)
    wallet_address = models.CharField(max_length=128)
    balance = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    reserved_in_offer = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    def __str__(self):
        return f"{self.user}'s {self.coin_type} wallet, balance: {self.balance}"


OPERATION_CHOICES = [
    ('SELL', 'Sell'),
    ('BUY', 'Buy'),
]


class Offer(models.Model):
    offer_coin_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='offer_coin')
    offer_usdt_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, default=None, related_name='offer_usdt')
    operation_type = models.CharField(max_length=4, choices=OPERATION_CHOICES)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    total = models.DecimalField(max_digits=12, decimal_places=4)
    # successful = models.BooleanField(default=False)
    coin_type = models.ForeignKey(CoinType, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.offer_coin_wallet.user} offering: {self.amount} for {self.total}"

    def save(self, *args, **kwargs):
        # type of usdt_wallet can be only USDT
        if self.offer_usdt_wallet.coin_type.type != 'USDT':
            raise WalletTypeError
        super().save(*args, **kwargs)


class Transaction(models.Model):
    sender_coin_wallet = models.ForeignKey(Wallet, related_name='transactions_sent', on_delete=models.CASCADE)
    receiver_coin_wallet = models.ForeignKey(Wallet, related_name='transactions_received', on_delete=models.CASCADE)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    total = models.DecimalField(max_digits=12, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)
    coin_type = models.ForeignKey(CoinType, on_delete=models.PROTECT)
    operation = models.CharField(max_length=4, choices=OPERATION_CHOICES)

    def __str__(self):
        return f'{self.amount} for {self.total}'
