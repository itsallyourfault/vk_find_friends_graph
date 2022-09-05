import vk
import os
import time
import json
import hashlib
import requests
import base64
from urllib import parse


def add_balance(amn_to_add, user_id):
    params = {
                "r_type": "get_user_balance",
                "user_id": user_id
            }
    balance = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og", params=params))
    new_balance = int(balance.text) + amn_to_add
    params = {
        "r_type": "update_user_balance",
        "user_id": user_id,
        "new_balance": new_balance
    }
    requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og", params=params)


def echo(user_id, response):
    session = vk.Session()
    api = vk.API(session, v=5.131)
    api.messages.send(
        access_token=os.getenv('token'),
        user_id=user_id, message=response,
        random_id=int(time.time()) * 10000000)


def handler(event, context):

    #echo(335328970, base64.b64decode(event["body"]).decode("utf-8"))

    decoded_body =  base64.b64decode(event["body"]).decode("utf-8")
    body_dict = dict(parse.parse_qsl(decoded_body))

    secret_seed = os.getenv('pass');
    payment_id = body_dict['id'];
    order_sum = body_dict['sum'];
    clientid = body_dict['clientid'];
    key = body_dict['key'];
    check_id = body_dict['fop_receipt_key'];
    check_link = "***" + payment_id + "/" + check_id

    sig_val = hashlib.md5((payment_id + order_sum + clientid + secret_seed).encode("utf-8")).hexdigest()


    if key != sig_val:
        return {
        'statusCode': 200,
        'body': 'No hash match'
        }
    
    key_to_return = hashlib.md5((payment_id + secret_seed).encode("utf-8")).hexdigest()

    

    sum_as_int = int(float(order_sum))

    try:
        intclientid = int(clientid)
    except Exception as e:
        echo("admin_id_as_int", str(e) + " " + str(payment_id))
        return {
        'statusCode': 200,
        'body': 'OK {key}'.format(key=key_to_return)
        }


    if sum_as_int == 59:
        add_balance(5, clientid)
    elif sum_as_int == 99:
        add_balance(10, clientid)
    elif sum_as_int == 159:
        add_balance(20, clientid)
    elif sum_as_int == 449:
        add_balance(20, clientid)
    else:
        echo(clientid, "Неверная сумма пополнения, обратитесь к администратору сообщества!\nПо этой ссылке будет доступен чек (обычно появляется через 15-30 мин.)\n" + check_link)
        return {
        'statusCode': 200,
        'body': 'OK {key}'.format(key=key_to_return)
        }

    


    echo(clientid, "✅ Баланс успешно пополнен!\nПо этой ссылке будет доступен чек (обычно появляется через 15-30 мин.)\n" + check_link)

    return {
        'statusCode': 200,
        'body': 'OK {key}'.format(key=key_to_return)
    }