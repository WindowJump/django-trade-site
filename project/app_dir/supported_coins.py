from django.contrib.auth.models import User

from app_dir.models import BTCModel, ETHModel, LTCModel, CoinType


supported_coins = {
    'bitcoin': BTCModel,
    'ethereum': ETHModel,
    'litecoin': LTCModel,
}


def db_init():
    """
    Call this function after you build this project and command sh -c "py manage.py migrate"
    You should type command sh -c "py manage.py shell", then from app_dir.supported_coins import db_init
    and finally call db_init()
    """
    for coin_type, _ in CoinType.COIN_CHOICES:
        CoinType.objects.get_or_create(type=coin_type)

    user1 = User.objects.create_user(
        username='user1',
        email='user1@gmail.com',
        password='4vH6v^Z,2c_',
    )
    user1_btc, user1_usdt = user1.wallets.filter(coin_type__type__in=['BTC', 'USDT'])
    user1_btc.balance = 100
    user1_usdt.balance = 100000
    user1_btc.save(), user1_usdt.save()

    user2 = User.objects.create_user(
        username='user2',
        email='user2@gmail.com',
        password='4vH6v^Z,2c_',
    )
    user2_btc, user2_usdt = user2.wallets.filter(coin_type__type__in=['BTC', 'USDT'])
    user2_btc.balance = 100
    user2_usdt.balance = 100000
    user2_btc.save(), user2_usdt.save()


if __name__ == '__main__':
    db_init()
