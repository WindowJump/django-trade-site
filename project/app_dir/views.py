from _decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import CreateView
from django.views.generic.detail import SingleObjectMixin

from .custom_exceptions import InsufficientCoinsError, InsufficientUSDTError
from .models import Offer, Transaction, Wallet, CoinType
from .forms import LoginUserForm, RegisterUserForm
from .supported_coins import supported_coins


def main_page(request):
    """
    func() that responsible for '/' url, shows actual user's and coins data
    """
    # initial context
    context = {
        'coin_data': {},
        'user_data': {'is_anonymous': True}
    }

    # fill context with user needed data
    user = request.user
    
    if not user.is_anonymous:
        user_usdt_wallet = user.wallets.get(coin_type__type='USDT')
        context['user_data']['is_anonymous'] = False
        context['user_data']['username'] = user.username
        context['user_data']['USDT_balance'] = Decimal(user_usdt_wallet.balance).normalize()

    # fill context with necessary data
    for coin_name, model in supported_coins.items():
        prices = model.objects.order_by('id')
        # check if db is populated
        if prices:
            first_price = prices.first().priceUsd
            last_price = prices.last().priceUsd
            # calculate 24h change in %
            percentage_change = ((last_price - first_price) / first_price) * 100
            # create dict with necessary data
            coin_data = {
                'first_price_' + coin_name: first_price,
                'last_price_' + coin_name: last_price,
                '24h_change_' + coin_name: percentage_change
            }

            context['coin_data'][coin_name] = coin_data

        else:
            return HttpResponse(f'<h1>{coin_name} data is missing</h1>')

    return render(request, 'btcTest/main-page.html', context)


@login_required(login_url='/login/')
def index(request, coin_name):
    """
    func() that responsible for handling 'main-page/<coin_name>' url, actual coin data,
    active offers and last transactions
    """
    # check if coin is supported
    if coin_name not in supported_coins:
        raise Http404
    # retrieve coin symbol of verbose name
    coin_type = CoinType.get_coin_type_from_verbose_name(coin_name)

    # retrieve user's necessary data
    user = request.user

    wallets_qs = user.wallets.filter(Q(coin_type__type=coin_type) | Q(coin_type__type='USDT'))
    user_coin_wallet, user_usdt_wallet = wallets_qs
    # normalize values
    user_coin_balance = Decimal(user_coin_wallet.balance).normalize()
    user_usdt_balance = Decimal(user_usdt_wallet.balance).normalize()

    # retrieve transactions and offers of this coin type
    transactions = Transaction.objects.filter(coin_type__type=coin_type).order_by('-timestamp')[:4]

    qs_offer = Offer.objects.filter(coin_type__type=coin_type)
    buy_offers = qs_offer.filter(operation_type='BUY')
    sell_offers = qs_offer.filter(operation_type='SELL')

    context = {
        'coin_name': coin_name,
        'user': user.username,
        'user_coin_balance': user_coin_balance,
        'user_usdt_balance': user_usdt_balance,
        'buy_offers': sell_offers,  # we are changing operational type because we want to show people offer operation
        'sell_offers': buy_offers,  # from their perspective side
        'transactions': transactions,
    }

    return render(request, 'btcTest/index.html', context)


@login_required(login_url='/login/')
def account_page(request):
    """
    func() that responsible for handling 'account/' url, shows all user's data
    including his balance, active offers, last transactions
    """
    # we can be sure that we will retrieve active user
    user = request.user

    # retrieve user wallets
    *user_coin_wallets, user_usdt_wallet = user.wallets.all()

    # retrieve all active user offers
    user_offers = Offer.objects.filter(offer_usdt_wallet=user_usdt_wallet)
    offers = {}
    for offer in user_offers:
        crypto_type = offer.coin_type
        if crypto_type not in offers.keys():
            offers[crypto_type] = {}
        offers[crypto_type][offer.id] = offer

    # retrieve all user's transactions and wallet data
    transactions = {}
    user_wallets_data = {}
    for wallet in user_coin_wallets:
        crypto_type = wallet.coin_type
        # needed data from wallet
        user_wallets_data[crypto_type] = {}
        user_wallets_data[crypto_type]['address'] = wallet.wallet_address
        user_wallets_data[crypto_type]['balance'] = Decimal(wallet.balance).normalize()
        user_wallets_data[crypto_type]['reserved_in_offer'] = Decimal(wallet.reserved_in_offer).normalize()
        # finding transactions
        sell_transactions_qs = Transaction.objects.filter(sender_coin_wallet=wallet).order_by('-timestamp')
        buy_transactions_qs = Transaction.objects.filter(receiver_coin_wallet=wallet).order_by('-timestamp')
        if sell_transactions_qs or buy_transactions_qs:
            if crypto_type not in transactions.keys():
                transactions[crypto_type] = {}
            transactions[crypto_type]['sell'] = sell_transactions_qs
            transactions[crypto_type]['buy'] = buy_transactions_qs

    # fill the data in context
    context = {
        'user': user,
        'user_usdt_data': {
            'usdt_balance': Decimal(user_usdt_wallet.balance).normalize(),
            'usdt_reserved': Decimal(user_usdt_wallet.reserved_in_offer).normalize(),
            'usdt_address': user_usdt_wallet.wallet_address
        },
        'user_wallets_data': user_wallets_data,
        'user_offers': offers,
        'user_transactions': transactions,
    }
    return render(request, 'btcTest/account-page.html', context)


class OfferView(LoginRequiredMixin, SingleObjectMixin, View):
    """
    Class-based View for the detail view of the Offer record on a get request.
    For a post request, it creates a transaction record in the db and deletes the Offer record.
    """
    model = Offer
    context_object_name = 'offer'

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        # swap operation type to show from the user's perspective
        self.object.operation_type = 'BUY' if self.object.operation_type == 'SELL' else 'SELL'
        # normalize attributes
        attrs_to_normalize = ['amount', 'exchange_rate', 'total']
        for attr in attrs_to_normalize:
            normalized_value = Decimal.normalize(getattr(self.object, attr))
            setattr(self.object, attr, normalized_value)
        # get context
        context = self.get_context_data()
        return render(self.request, 'btcTest/offer-detail.html', context)

    @transaction.atomic
    def post(self, *args, **kwargs):
        self.object = self.get_object()
        try:
            # all changes to the db will convert into one singular atomic transaction, which will increase the safety
            # of the transaction
            with transaction.atomic():
                # retrieve seeker wallets and provider wallets
                seeker_wallets = Wallet.objects.filter(Q(coin_type=self.object.coin_type) | Q(coin_type__type='USDT'),
                                                       user__username=self.request.user)
                seeker_coin_wallet, seeker_usdt_wallet = seeker_wallets

                provider_coin_wallet, provider_usdt_wallet = self.object.offer_coin_wallet, self.object.offer_usdt_wallet

                # check operation_types and make db changes
                if self.object.operation_type == 'BUY':
                    # check if users have enough resources to make a transaction
                    if provider_usdt_wallet.reserved_in_offer >= self.object.total \
                            and seeker_coin_wallet.balance >= self.object.amount:

                        provider_usdt_wallet.reserved_in_offer -= self.object.total
                        provider_coin_wallet.balance += self.object.amount

                        seeker_usdt_wallet.balance += self.object.amount
                        seeker_coin_wallet.balance -= self.object.amount

                        # variables for Transaction record
                        receiver_coin_wallet, sender_coin_wallet = provider_coin_wallet, seeker_coin_wallet

                    # in case they don't have enough coins/usdt to make a transaction raise errors
                    else:
                        if provider_usdt_wallet.reserved_in_offer < self.object.total:
                            self.object.delete()
                            raise InsufficientUSDTError
                        elif seeker_coin_wallet.balance < self.object.amount:
                            raise InsufficientCoinsError

                # make the same operation but invert it for 'SELL' operation type
                elif self.object.operation_type == 'SELL':
                    if provider_coin_wallet.reserved_in_offer >= self.object.amount \
                            and seeker_usdt_wallet.balance >= self.object.total:

                        provider_coin_wallet.reserved_in_offer -= self.object.amount
                        provider_usdt_wallet.balance += self.object.total

                        seeker_coin_wallet.balance += self.object.amount
                        seeker_usdt_wallet.balance -= self.object.total

                        receiver_coin_wallet, sender_coin_wallet = seeker_coin_wallet, provider_coin_wallet
                    else:
                        if provider_coin_wallet.reserved_in_offer < self.object.amount:
                            self.object.delete()
                            raise InsufficientCoinsError
                        elif seeker_usdt_wallet.balance < self.object.total:
                            raise InsufficientUSDTError

                # if an error didn't occur we can create a Transaction record in the db and delete the offer instance
                Transaction.objects.create(
                    sender_coin_wallet=sender_coin_wallet,
                    receiver_coin_wallet=receiver_coin_wallet,
                    exchange_rate=self.object.exchange_rate,
                    amount=self.object.amount,
                    total=self.object.total,
                    coin_type=self.object.coin_type,
                    operation=self.object.operation_type,
                )
                self.object.delete()

                # save wallet changes
                for wallet in provider_coin_wallet, provider_usdt_wallet, seeker_coin_wallet, seeker_usdt_wallet:
                    wallet.save()

        except Exception as e:
            return HttpResponse(f'{e}')

        return redirect('account')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'btcTest/login.html'


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'btcTest/registration.html'
    success_url = '/'
