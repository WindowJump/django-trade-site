import json

from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, post_init

from .models import CoinType

from hdwallet import HDWallet
from hdwallet.utils import generate_entropy
from hdwallet.symbols import BTC, ETH, LTC, FIX

from .models import Wallet, Offer, Transaction


@receiver(post_delete, sender=Offer)
def delete_offer_on_frontend(sender, instance, *args, **kwargs):
    """
    Send id and operation type to delete from html table
    """
    # send data to {coin_name}_group
    coin_name = instance.coin_type.get_type_display()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'{coin_name}_group',
        {
            'type': 'send_id_to_delete',
            'id_to_delete': str(instance.id),
        }
    )


@receiver(post_save, sender=Transaction)
def send_transaction_to_frontend(sender, instance, *args, **kwargs):
    """
    Send transaction instance data to display on frontend
    """
    # necessary data to send
    base_info_dict = {
        'type': 'display_transaction',
        'crypto_name': instance.coin_type.type,
        'exchange_rate': str(instance.exchange_rate),
        'amount': str(instance.amount),
        'total': str(instance.total),
        'operation': instance.operation,
    }

    # retrieve coin_name and channel layer
    coin_name = instance.coin_type.get_type_display()
    channel_layer = get_channel_layer()
    # send data to {coin_name}_group
    async_to_sync(channel_layer.group_send)(
        f'{coin_name}_group',
        base_info_dict,
    )
    # retrieve sender and provider wallets
    sender_wallet = instance.sender_coin_wallet
    provider_wallet = instance.receiver_coin_wallet

    # send data to user accounts to display in live
    usernames = (sender_wallet.user.username,
                 provider_wallet.user.username)

    # change operation type to display for users from their perspective side
    if instance.operation == 'BUY':
        operations = 'SELL', 'BUY'
    else:
        operations = 'BUY', 'SELL'
    # send transaction to account page
    for username, operation in zip(usernames, operations):
        base_info_dict['operation'] = operation
        async_to_sync(channel_layer.group_send)(
            f'{username}_account_group',
            base_info_dict,
        )


@receiver(post_save, sender=Wallet)
def send_new_balance_data(sender, instance, *args, **kwargs):
    """
    func() to send new user's balance data to frontend
    """
    coin_type = instance.coin_type
    username = instance.user.username
    # retrieve channel layer and coin_type
    coin_name = coin_type.get_type_display()
    channel_layer = get_channel_layer()
    # send message to {coin_name}_group
    async_to_sync(channel_layer.group_send)(
        f'{username}_account_group',
        {
           'type': 'update_balance',
           'username': instance.user.username,
           'user_balance': str(instance.balance),
           'user_reserve_balance': str(instance.reserved_in_offer),
           'coin_type': coin_name,
        }
    )


@receiver(post_save, sender=User)
def create_wallets_for_user(sender, instance, *args, **kwargs):
    """
    Generate addresses wallets for new or existing users, to call this func use user.save()
    Also this func call itself after user registration or authentication
    """
    all_coin_types = CoinType.objects.all()
    wallets_to_create = {coin.get_type_display(): coin.type for coin in all_coin_types}

    if instance.wallets:
        for wallet in instance.wallets.all():
            if str(wallet.coin_type) in wallets_to_create.keys():
                wallets_to_create.pop(str(wallet.coin_type))

    for SYMBOL in wallets_to_create.values():
        if SYMBOL == 'USDT':
            SYMBOL = 'FIX'
            # Choose strength 128, 160, 192, 224 or 256
        STRENGTH = 160
        # Choose language english
        LANGUAGE = "english"
        # Generate new entropy hex string
        ENTROPY = generate_entropy(strength=STRENGTH)
        # Secret passphrase for mnemonic
        PASSPHRASE = None

        # Initialize Coin mainnet HDWallet
        hdwallet: HDWallet = HDWallet(symbol=SYMBOL, use_default_path=False)
        # Get Bitcoin HDWallet from entropy
        hdwallet.from_entropy(
            entropy=ENTROPY, language=LANGUAGE, passphrase=PASSPHRASE
        )
        Wallet.objects.create(
            user=instance,
            wallet_address=json.dumps(hdwallet.dumps()['addresses']['p2pkh']),
            coin_type_id=CoinType.objects.get(type=SYMBOL if SYMBOL != 'FIX' else 'USDT').id
            # HDWallet does not
            # support USDT, so I decided to simulate it with FIX
        )

