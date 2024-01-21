# Generated by Django 4.2.5 on 2024-01-21 10:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BTCModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priceUsd', models.DecimalField(decimal_places=3, max_digits=11)),
                ('time', models.PositiveBigIntegerField()),
                ('date', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CoinType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('BTC', 'bitcoin'), ('ETH', 'ethereum'), ('LTC', 'litecoin'), ('USDT', 'USDT')], max_length=4, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ETHModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priceUsd', models.DecimalField(decimal_places=3, max_digits=11)),
                ('time', models.PositiveBigIntegerField()),
                ('date', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LTCModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priceUsd', models.DecimalField(decimal_places=3, max_digits=11)),
                ('time', models.PositiveBigIntegerField()),
                ('date', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallet_address', models.CharField(max_length=128)),
                ('balance', models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ('reserved_in_offer', models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ('coin_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_dir.cointype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange_rate', models.DecimalField(decimal_places=2, max_digits=12)),
                ('amount', models.DecimalField(decimal_places=6, max_digits=12)),
                ('total', models.DecimalField(decimal_places=4, max_digits=12)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('operation', models.CharField(choices=[('SELL', 'Sell'), ('BUY', 'Buy')], max_length=4)),
                ('coin_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_dir.cointype')),
                ('receiver_coin_wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions_received', to='app_dir.wallet')),
                ('sender_coin_wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions_sent', to='app_dir.wallet')),
            ],
        ),
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation_type', models.CharField(choices=[('SELL', 'Sell'), ('BUY', 'Buy')], max_length=4)),
                ('exchange_rate', models.DecimalField(decimal_places=2, max_digits=12)),
                ('amount', models.DecimalField(decimal_places=6, max_digits=12)),
                ('total', models.DecimalField(decimal_places=4, max_digits=12)),
                ('coin_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_dir.cointype')),
                ('offer_coin_wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offer_coin', to='app_dir.wallet')),
                ('offer_usdt_wallet', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='offer_usdt', to='app_dir.wallet')),
            ],
        ),
    ]