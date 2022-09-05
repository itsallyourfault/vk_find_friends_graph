import random
import vk
import json
import os
import time
import requests
import boto3
import hashlib
from urllib import parse
from urllib.parse import urlparse
from requests.auth import HTTPBasicAuth



def generate_link(pay_amount, user_id):
    user = "admin"
    password = "***"

    server_paykeeper = "***"

    uri_token = "/info/settings/token/"
    uri_invoice = "/change/invoice/preview/"

    payment_data = {
        "pay_amount": pay_amount,
        "clientid": str(user_id)
    }

    auth = HTTPBasicAuth(user, password)

    response = requests.get(server_paykeeper + uri_token, auth=auth, data=payment_data)

    response_json = response.json()

    if "token" in response_json:
        token = response_json["token"]
    else:
        return

    print(token)

    payment_data["token"] = token

    response = requests.post(server_paykeeper + uri_invoice, data = payment_data, auth=auth)

    response_json = response.json()

    if "invoice_id" in response_json:
        invoice_id = response_json["invoice_id"]
    else:
        return

    link = f"{server_paykeeper}/bill/{invoice_id}/"

    return link



def links_to_id(text):
    res = ''
    res = text.replace('https://', '')
    res = res.replace('http://', '')
    res = res.replace('www.vk.com/', '')
    res = res.replace('vk.com/', '')
    res = ' '.join(res.split())
    check_str = res.split(' ')

    if len(check_str) == 2:
        return check_str
    if len(check_str) == 1:
        return check_str

    return 'WRONG_SEARCH_FUNC'


def vk_callback(lambda_event, token):

    #start_text = "Привет! 👋🏻 Рады видеть тебя у нас в сообществе!\n\n❗Пожалуйста, внимательно прочитай информацию!\n\n💥 Наш бот поможет тебе найти цепочку знакомств между двумя людьми во вконтакте. Первый поиск бесплатно!\n\n❓Может быть ты слышал что-то о теории 6 рукопожатий? Да-да именно это мы здесь и проверяем!\n\n❗Для начала тебе нужно авторизоваться нажав на соответственную кнопку в меню бота, далее ты сможешь пополнить баланс и найти цепочку знакомств между двумя пользователями.\nПоиск идет до 15 минут, если за это время не получится найти цепочку, деньги вернутся на баланс бота! ✅\n\n🔔 Подробнее о команде поиска можно прочитать в инструкции!\n\n✌🏻 Приятного пользования!"
    start_text = "Привет! 👋🏻 Рады видеть тебя у нас в сообществе!\n\n💥 Просто отправь мне ссылку на человека с кем хочешь найти общих друзей! \n\nЕсли у вас закрытая страница, то нужно авторизоваться!"

    #insrt_text = "🔎 Команда для поиска цепочки знакомств между двумя пользователями\n💬Отправьте сообщение:\nПоиск (Ссылка или ID первого пользователя) (Ссылка или ID второго пользователя)\n\n❗Вместо одного из пользователей можно указать 'я', так обозначается ваш ID\n\nПример запроса:\n💬 Поиск id11111 id22222\n💬 Поиск vk.com/firstuser vk.com/seconduser\n💬 Поиск я durov\n\n❗Вконтакте есть свои ограничения, которые мы нарушать не хотим и не можем, если вы столкнулись с ограничением на количество запросов, пожалуйста, подождите сутки и попробуйте еще раз\n\n❗Со всеми вопросами вы можете написать администратору сообщества"
    insrt_text = "🔎 Для поиска просто отправь ссылку на страничку человека с кем хочешь найти общих друзей!\n Например: vk.com/a4\n Если у вас закрытая страница, то нужно авторизоваться!"

    keyboard_new = {
        "one_time": False,
        "buttons": [
            [
                #{
                #    "action": {
                #        "type": "text",
                #        "payload": "{\"button\": \"1\"}",
                #        "label": "Инструкция"
                #    },
                #    "color": "negative"
                #},
                {
                    "action": {
                        "type": "text",
                        "payload": "{\"button\": \"2\"}",
                        "label": "Поиск"
                    },
                    "color": "positive"
                }

            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "{\"button\": \"2\"}",
                        "label": "Пополнить баланс"
                    },
                    "color": "primary"
                },
                {
                    "action": {
                        "type": "text",
                        "payload": "{\"button\": \"3\"}",
                        "label": "Баланс"
                    },
                    "color": "primary"
                },

            ],
            [
                
                {
                    "action": {
                        "type": "text",
                        "payload": "{\"button\": \"1\"}",
                        "label": "Авторизация"
                    },
                    "color": "negative"
                },
            ]
        ]}
    keyboard_auth = {
        "one_time": False,
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "open_link",
                        "payload": "{\"button\": \"2\"}",
                        "link": "https://oauth.vk.com/authorize?client_id=8049680&redirect_uri=https://functions.yandexcloud.net/d4epbm3dn86eprcb1k1n&scope=friends,offline&response_type=code",
                        "label": "Авторизоваться"
                    },

                },
            ]
        ]}
    instructionKeyboardButton = {
        "one_time": False,
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": "{\"button\": \"2\"}",
                        "label": "Инструкция"
                    },

                },
            ]
        ]
    }

    keyboard_pay_not_inline = {
                "one_time": False,
                "inline": False,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "payload": "{\"type\": \"pay\", \"amount\": \"59\"}",
                                "label": "5 Поисков - 59 руб."
                            },
                            "color": "positive"

                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "payload": "{\"type\": \"pay\", \"amount\": \"99\"}",
                                "label": "10 Поисков - 99 руб."
                            },
                            "color": "positive"

                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "payload": "{\"type\": \"pay\", \"amount\": \"159\"}",
                                "label": "20 Поисков - 159 руб."
                            },
                            "color": "positive"

                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "payload": "{\"button\": \"3\"}",
                                "label": "Назад"
                            },
                            "color": "primary"

                        }
                    ]
                ]}

        
    
    

    session = vk.Session()
    api = vk.API(session, v=5.131)
    event = json.loads(lambda_event)

    

    if "type" not in event:
        return
    if event['type'] == 'message_new':
        msg_text = event['object']['message']['text']
        user_id = event['object']['message']['from_id']
        if (msg_text == 'Начать') or (msg_text == 'начать')or (msg_text == 'Start')or (msg_text == 'start'):
            api.messages.send(access_token=token, user_id=str(user_id), message=start_text, random_id=int(
                time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
            time.sleep(1)
            #api.messages.send(access_token=token, user_id=str(user_id),
            #                      message="Авторизация:", random_id=int(
            #            time.time()) * 10000000, keyboard=json.dumps(keyboard_auth))
        elif ((os.getenv('service_status') == "timeout") and (str(user_id) != "admin_id")):
            api.messages.send(access_token=token, user_id=str(user_id), message="Ведутся технические работы, сервис временно недоступен.", random_id=int(
                time.time()) * 10000000)
        elif (msg_text == 'Баланс') or (msg_text == 'баланс'):
            params = {
                "r_type": "get_user_balance",
                "user_id": user_id
            }
            balance = requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                   params=params)
            if (json.loads(balance.text) == "User not found"):
                 balance = requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                   params=params)

            api.messages.send(access_token=token, user_id=str(user_id),
                              message="Ваш баланс: " + balance.text + " запросов. 🔎", random_id=int(
                    time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
        elif (msg_text == 'Пополнить баланс') or (msg_text == 'пополнить баланс'):
            keyboard_new_pay = {
                "one_time": False,
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "payload": "{\"type\": \"pay\", \"amount\": \"59\"}",
                                "label": "5 - 59 руб."
                            },

                        },
                        {
                            "action": {
                                "type": "callback",
                                "payload": "{\"type\": \"pay\", \"amount\": \"99\"}",
                                "label": "10 - 99 руб."
                            },

                        },
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "payload": "{\"type\": \"pay\", \"amount\": \"159\"}",
                                "label": "20 - 159 руб."
                            },

                        }
                        #{
                        #    "action": {
                        #        "type": "callback",
                        #        "payload": "{\"type\": \"pay\", \"amount\": \"449\"}",
                        #        "label": "20 - 449 руб."
                        #    },
                        #},
                    ]
                ]}
            params = {
                "r_type": "get_user_balance",
                "user_id": user_id
            }
            balance = requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                   params=params)
            if (json.loads(balance.text) == "User not found"):
                 balance = requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                   params=params)
            api.messages.send(access_token=token, user_id=str(user_id),
                              message="Выберите сколько запросов вы хотите купить:\n❗ Не забывайте выключить VPN!", random_id=int(
                    time.time()) * 10000000, keyboard=json.dumps(keyboard_pay_not_inline))
        elif (msg_text == 'god_give_me_money'):

            params = {
                "r_type": "get_user_balance",
                "user_id": user_id
            }
            balance = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                    params=params))
            if (balance.text == "User not found"):
                api.messages.send(access_token=token, user_id=str(user_id),
                                  message="💬 Сначала вам нужно авторизоваться!", random_id=int(
                        time.time()) * 10000000, keyboard=json.dumps(keyboard_auth))
                return
            new_balance = int(balance.text) + 10
            params = {
                "r_type": "update_user_balance",
                "user_id": user_id,
                "new_balance": new_balance
            }
            requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og", params=params)
            api.messages.send(access_token=token, user_id=str(user_id), message="Бог вас услышал!", random_id=int(
                time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
            time.sleep(2)
            api.messages.send(access_token=token, user_id=str("335328970"), message="Год гиви ми мони от - vk.com/id" + str(user_id), random_id=int(
                time.time()) * 10000000)
        elif (msg_text == 'Инструкция') or (msg_text == 'инструкция'):
            api.messages.send(access_token=token, user_id=str(user_id), message=insrt_text, random_id=int(
                time.time()) * 10000000, keyboard=json.dumps(keyboard_pay_not_inline)
                #, attachment="doc-210111570_642257694"
                )
        elif (msg_text == 'Назад'):
            api.messages.send(access_token=token, user_id=str(user_id), message="Меню", random_id=int(
                time.time()) * 10000000, keyboard=json.dumps(keyboard_new)
                #, attachment="doc-210111570_642257694"
                )
            
        elif (msg_text == 'Авторизация') or (msg_text == 'авторизация'):

            api.messages.send(access_token=token, user_id=str(user_id), message="Для авторизации пройдите по ссылке\nАвторизация нужна если у вас закрытая страница и для повышения точности поиска",
                              random_id=int(
                                  time.time()) * 10000000, keyboard=json.dumps(keyboard_auth))
        elif (msg_text == '1rub'):
            link = generate_link(str(1), str(user_id))
            api.messages.send(access_token=token, user_id=str(user_id),
                              message=str(link),
                              random_id=int(time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
            return
        elif (msg_text == 'Поиск'):
            api.messages.send(access_token=token, user_id=str(user_id), message=insrt_text,
                              random_id=int(
                                  time.time()) * 10000000, keyboard=json.dumps(keyboard_new)
                                  #, attachment="doc-210111570_642257694"
                                  )

        elif (msg_text[:5] == 'Поиск') or (msg_text[:5] == 'поиск') or ('vk.com' in msg_text):

            request_type = "full_access"
            

            params = {
                "r_type": "get_user_balance",
                "user_id": user_id
            }
            balance = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                    params=params))
            if (json.loads(balance.text) == "User not found"):
                balance = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                    params=params))
                
            params = {
                    "r_type": "get_query_status",
                    "user_id": user_id
                    }
            queryStatus = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                params=params))
            if queryStatus.text == 'True':
                api.messages.send(access_token=token, user_id=str(user_id),
                                  message="❗ У вас уже запущен запрос, подождите его результата и попробуйте снова!", random_id=int(
                        time.time()) * 10000000)
                return


            balance = int(balance.text)
            if (balance < 1):

                request_type = "demo_access"

                #api.messages.send(access_token=token, user_id=str(user_id),
                #                  message=f"Недостаточно средств на балансе! Ваш баланс: {balance} запросов 💸",
                #                  random_id=int(
                #                      time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
                #return

            
            
                        
            if (msg_text[:5] == 'Поиск') or (msg_text[:5] == 'поиск'):
                ids = links_to_id(msg_text[6:])
            else:
                ids = links_to_id(msg_text)
            if ids != 'WRONG_SEARCH_FUNC':
                if len(ids) == 2:
                    if (ids[0] == 'я') or (ids[0] == 'Я'):
                        ids[0] = user_id
                    elif (ids[1] == 'я') or (ids[1] == 'Я'):
                        ids[1] = user_id
                elif len(ids) == 1:
                    ids = [str(user_id), ids[0]]

                if request_type == "full_access":
                    new_balance = balance - 1
                    params = {
                        "r_type": "update_user_balance",
                        "user_id": user_id,
                        "new_balance": new_balance
                    }
                    requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                                params=params)

                api.messages.send(access_token=token, user_id=str(user_id),
                                  message=f'🔥 Запрос на поиск между Вами и {ids[1]}', random_id=int(
                        time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
                        
                datatosend = {
                    "user_id": int(user_id),
                    "entrance_id": ids[0],
                    "target_id": ids[1],
                    "request_type": request_type
                }
                try:
                    client = boto3.client(
                    service_name='sqs',
                    endpoint_url='https://message-queue.api.cloud.yandex.net',
                    region_name='ru-central1'
                    )

                    params = {
                    "r_type": "update_query_status",
                    "user_id": user_id,
                    "new_status": True
                    }
                    queryStatus = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
                        params=params))

                    # Send message to queue
                    client.send_message(
                        QueueUrl="https://message-queue.api.cloud.yandex.net/b1g96b95lu5trfs7poul/dj6000000005ifbb05g9/vkbot-power",
                        MessageBody=json.dumps(datatosend)
                    )

                    

                    
                except Exception as e:
                    api.messages.send(access_token=token, user_id=str(user_id),
                                  message='Не получилось', random_id=int(
                                    time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
            
            

            else:
                api.messages.send(access_token=token, user_id=str(user_id),
                                  message="⚠ Неверный формат запроса! Пожалуйста, проверьте Ваш запрос.",
                                  random_id=int(
                                      time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
        else:
            api.messages.send(access_token=token, user_id=str(user_id),
                              message="⚠ Я не могу понять ваш запрос :(",
                              random_id=int(time.time()) * 10000000, keyboard=json.dumps(keyboard_new))
    if event['type'] == 'message_event':
        
        clb_type = event['object']['payload']['type']
        user_id = event['object']['user_id']

        if clb_type == "pay":
            clb_amount = event['object']['payload']['amount']
            link = generate_link(str(clb_amount), str(user_id))
            data = {
                "type": "open_link",
                "link": link
            }
            api.messages.sendMessageEventAnswer(
                                access_token=token,
                                event_id=event['object']['event_id'],
                                user_id=event['object']['user_id'],
                                peer_id=event['object']['peer_id'],
                                event_data=json.dumps(data)
                                )
            return



def handler(event, context):
    try:
        if json.loads(event["body"])["type"] == "auth":
            session = vk.Session()
            api = vk.API(session, v=5.131)
            api.messages.send(access_token=str(os.getenv('token')), user_id=json.loads(event["body"])["user_id"],
                              message="✅ Успешная авторизация!", random_id=int(
                    time.time()) * 10000000)
            return {
                'statusCode': 200,
                'body': "OK"

            }
        
    except Exception as e:
        pass

    try:
        if json.loads(event["body"])["type"] == "confirmation" and json.loads(event["body"])["group_id"] == "your_group_id_as_int":
            data = "b98cc701"
            return {
                'statusCode': 200,
                'body': data
            }

        if json.loads(event["body"])["secret"] == "secter_key_here_as_str":
            vk_callback(event["body"], os.getenv('token'))

        return {
            'statusCode': 200,
            'body': "OK"
        }

    except Exception as e:
        
        rep = str(e)
        return {
            'statusCode': 200,
            'body': "OK"
        }
