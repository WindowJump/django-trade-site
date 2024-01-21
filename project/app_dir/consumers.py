import json

from _decimal import Decimal
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .tasks import delete_offer_from_account, fetch_coin_data
from .models import Offer, CoinType
from .custom_exceptions import InsufficientCoinsError, InsufficientUSDTError


class AsyncBaseConsumer(AsyncWebsocketConsumer):
    """
    Base consumer that contains methods used in ClientConsumer and Account Consumers.
    """
    async def display_transaction(self, event):
        """
        Sends transaction data to the frontend.
        """
        await self.send(text_data=json.dumps({
            'type': 'display_transaction',
            'crypto_name': event['crypto_name'],
            'operation': event['operation'],
            'amount': event['amount'],
            'exchange_rate': event['exchange_rate'],
            'total': event['total'],
        }))

    async def send_error(self, event):
        """
        Sends an error if it occurred.
        """
        error_message = event['error_message']
        await self.send(text_data=json.dumps({
            'type': 'send_error',
            'error_message': error_message,
        }))

    async def send_id_to_delete(self, event):
        """
        Sends the unique ID of the offer that needs to be deleted.
        """
        # Retrieve the ID to delete on the page.
        id_to_delete = event['id_to_delete']
        # Each offer has a unique ID that depends on the operation type.
        id_string = 'offer-' + id_to_delete
        await self.send(text_data=json.dumps({
            'type': 'delete_offer',
            'id_to_delete': id_string
        }))


@database_sync_to_async
def get_wallets_and_coin_type(user, coin_name):
    """
    Retrieves the user's wallets and coin_type
    """
    coin_type = CoinType.get_coin_type_from_verbose_name(coin_name)
    user_coin_wallet, user_usdt_wallet = user.wallets.filter(coin_type__type__in=[coin_type, 'USDT'])

    return user_coin_wallet, user_usdt_wallet, coin_type


@database_sync_to_async
def create_and_retrieve_id_offer(coin_wallet, usdt_wallet, operation, exchange_rate, amount, total, coin_type):
    """
    Creates an offer record in the database and returns its ID.
    """
    # Check the operation type.
    if operation.lower() == 'buy':
        # Convert the string total to Decimal.
        total = Decimal(total)
        # Check if the user has enough balance to create an offer.
        if usdt_wallet.balance < total:
            raise InsufficientUSDTError
        # Update data in the database.
        usdt_wallet.balance -= total
        usdt_wallet.reserved_in_offer += total
        usdt_wallet.save()

    elif operation.lower() == 'sell':
        amount = Decimal(amount)

        if coin_wallet.balance < amount:
            raise InsufficientCoinsError

        coin_wallet.balance -= amount
        coin_wallet.reserved_in_offer += amount
        coin_wallet.save()

    offer = Offer.objects.create(
        offer_coin_wallet=coin_wallet,
        offer_usdt_wallet=usdt_wallet,
        operation_type=operation.upper(),
        exchange_rate=exchange_rate,
        amount=amount,
        total=total,
        coin_type=CoinType.objects.get(type=coin_type)
    )
    return offer.id


class ClientConsumer(AsyncBaseConsumer):
    """
    Class that handles WebSocket connection between client and server
    """
    async def connect(self):
        """
        Method that called on WebSocket connection
        """
        # create group and channel to it
        self.coin_name = self.scope['url_route']['kwargs']['coin_name']
        self.coin_group_name = f'{self.coin_name}_group'
        await self.channel_layer.group_add(self.coin_group_name, self.channel_name)
        # accept connection
        await self.accept()
        fetch_coin_data.apply_async(args=[], kwargs={})

    async def disconnect(self, code):
        # discard channel from the group after disconnection
        await self.channel_layer.group_discard(self.coin_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Method that called when client sends message
        """
        text_data_json = json.loads(text_data)

        if 'type' and 'data' in text_data_json.keys():
            if text_data_json['type'] == 'create_offer' and await self.verify_sent_data(text_data_json['data']):
                data = text_data_json['data']
                # view func() has login_required, so we can be sure that we will retrieve active user
                user = self.scope['user']
                user_coin_wallet, user_usdt_wallet, coin_type = await get_wallets_and_coin_type(user, self.coin_name)
                # try to create the offer
                try:
                    object_id = await create_and_retrieve_id_offer(user_coin_wallet, user_usdt_wallet,
                                                                   data['operation_type'].upper(),
                                                                   data['exchange_rate'],
                                                                   data['amount'], data['total'], coin_type)
                    data['object_id'] = str(object_id)
                    data['coin_type'] = coin_type
                    # send data to method send_offer
                    await self.channel_layer.group_send(
                        self.coin_group_name, {'type': 'send_offer', 'data': data}
                    )

                except Exception as e:
                    await self.channel_layer.group_send(
                        self.coin_group_name, {'type': 'send_error', 'error_message': f'{str(e)}'}
                    )

            elif text_data_json['type'] == 'create_offer':
                await self.channel_layer.group_send(
                    self.coin_group_name, {'type': 'send_error', 'error_message': 'please, send all data needed'}
                )

            else:
                await self.channel_layer.group_send(
                    self.coin_group_name, {'type': 'send_error', 'error_message': 'unsupported type'}
                )

    @classmethod
    async def verify_sent_data(cls, data):
        """
        Method that verifies if user sent all necessary fields
        """
        # get all needed fields
        required_fields = [field.name for field in Offer._meta.get_fields()]
        # there are 4 fields that we get from other sources
        fields_sent = ['id', 'offer_coin_wallet', 'offer_usdt_wallet', 'coin_type'] + list(data.keys())

        for field_sent in fields_sent:
            if field_sent in required_fields:
                required_fields.remove(field_sent)
        # returns True if required_fields is empty
        return not bool(required_fields)

    async def send_offer(self, event):
        """
        Method that sends data back to client to show offer creation in real time
        """
        data = event['data']
        await self.send(text_data=json.dumps({
            'type': 'send_offer',
            'data': data
        }))

    async def fetch_coin_data(self, event):
        """
        Method that helps to update chart and coin data
        """
        await self.send(text_data=json.dumps({
            'type': 'fetch_coin_data',
            'dates': event['dates'],
            'prices': event['prices'],
            'max_val': event['max_val'],
            'min_val': event['min_val'],
        }))


class AccountConsumer(AsyncBaseConsumer):
    """
    Class that handles WebSocket connection between client and server
    """
    async def connect(self):
        """
        Method that called on WebSocket connection
        """
        # create group and channel to it
        self.username = self.scope['user'].username
        self.group_name = f'{self.username}_account_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        # accept connection
        await self.accept()

    async def disconnect(self, code):
        # discard channel from the group after disconnection
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Method that called when client sends message
        """
        # receive and check sent data
        text_data_json = json.loads(text_data)

        if 'type' in text_data_json.keys() and text_data_json['type'] == 'delete_offer':
            # delete offer
            self.offer_id = int(text_data_json['offerID_to_delete'])
            delete_offer_from_account.apply_async(args=[], kwargs={'username': self.username,
                                                  'offer_id': self.offer_id})
        else:
            await self.channel_layer.group_send(
                self.group_name, {'type': 'send_error', 'error_message': 'unsupported type'}
            )

    async def update_balance(self, event):
        """
        Updates the user's balance.
        """
        if self.scope['user'].username == event['username']:
            await self.send(text_data=json.dumps({
                'type': 'update_balance',
                'new_balance': event['user_balance'],
                'new_reserved': event['user_reserve_balance'],
                'id_prefix': event['coin_type'],
            }))
