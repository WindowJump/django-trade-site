import requests

from asgiref.sync import async_to_sync

from celery import shared_task
from channels.layers import get_channel_layer
from django.db.models import Min, Max

from app_dir.models import Offer
from app_dir.supported_coins import supported_coins


def check_last_record(data_json, model):
    """
    func() that helps to update db BTCModel, ETHModel, LTCModel records
    and sorts api data what we are need to store
    """
    # retrieve last btc object from db 
    last_model_object = model.objects.last()
    # sort api data
    if last_model_object:
        # checking whether the last record in the database matches the current time to get the next minute's data and
        # deletes record that is not actual anymore and not used in this app
        if last_model_object.time + 60000 == data_json[-1]['time']:
            model.objects.first().delete()
            return [data_json[-1]]
        # if your server was shout down for a while, it checks your last db record and looks for the right interval to
        # fill in the missing data. Also deletes not actual data
        else:
            target_time = data_json[0]['time']
            model.objects.filter(time__lt=target_time).delete()
            last_object_index = next((index for index, item in enumerate(data_json)
                                      if item['time'] == last_model_object.time), None)
            if last_object_index:
                return data_json[last_object_index + 1:]
            else:
                # if you haven't received data for more than 24 hours
                return data_json
    else:
        # fills the database with all information if the data is missing
        return data_json


@shared_task()
def populate_db():
    """
    Celery task that responsible for db updates, it calls every 65 seconds using celery beat settings
    """
    for coin_name, model in supported_coins.items():
        # get data for coin via coin cap api
        response = requests.get(f'https://api.coincap.io/v2/assets/{coin_name}/history?interval=m1')
        if response.status_code == 200:
            # parse response data
            data_json = response.json()['data']
            data_sorted = check_last_record(data_json, model)
            # write sorted data to db
            coin_data_objects = [
                model(
                    priceUsd=item['priceUsd'],
                    time=item['time'],
                    date=item['date'],
                )
                for item in data_sorted
            ]
            model.objects.bulk_create(coin_data_objects)
        else:
            pass


@shared_task
def fetch_coin_data():
    """
    Celery task that sends necessary data coin data to show on 'main-page/<coin_name>' page,
    it calls on first user connection and also every 70 seconds to update coin data for all users in <coin_name>_group
    """
    for coin_name, model in supported_coins.items():
        qs = model.objects.all()
        # Find max and min price for 24h
        max_val = qs.aggregate(max_price=Max('priceUsd'))['max_price']
        min_val = qs.aggregate(min_price=Min('priceUsd'))['min_price']
        # Data for chart, we need to use str and float format to serialize them for sending to consumer
        dates = [obj.date.strftime('%Y-%m-%dT%H:%M:%S') for obj in qs]
        prices = [float(obj.priceUsd) for obj in qs]

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'{coin_name}_group',
            {
                'type': 'fetch_coin_data',
                'dates': dates,
                'prices': prices,
                'max_val': float(max_val),
                'min_val': float(min_val),
            }
        )


@shared_task
def delete_offer_from_account(username, offer_id):
    """
    Celery task that responsible for handling deletion of an offer that has been deleted by user on his account page
    """
    # find offer
    offer_qs = Offer.objects.filter(id=offer_id)
    # check if offer still exist (user can spam on delete button or somebody already have accepted an offer)
    if offer_qs:
        offer = offer_qs.get()
        # return balance to user
        operation_type = offer.operation_type.lower()
        if operation_type == 'sell':
            user_coin_wallet = offer.offer_coin_wallet
            user_coin_wallet.reserved_in_offer -= offer.amount
            user_coin_wallet.balance += offer.amount
            user_coin_wallet.save()
        elif operation_type == 'buy':
            user_usdt_wallet = offer.offer_usdt_wallet
            user_usdt_wallet.reserved_in_offer -= offer.total
            user_usdt_wallet.balance += offer.total
            user_usdt_wallet.save()
        # finally delete an offer
        offer.delete()
        # send id to delete from account page
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'{username}_account_group',
        {
            'type': 'send_id_to_delete',
            'id_to_delete': str(offer_id),
        }
    )
