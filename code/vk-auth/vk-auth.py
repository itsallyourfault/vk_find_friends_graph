import json
import requests
import os
import ydb as ydb

# create driver in global space.
driver = ydb.Driver(endpoint=os.getenv('YDB_ENDPOINT'), database=os.getenv('YDB_DATABASE'))
# Wait for the driver to become active for requests.
driver.wait(fail_fast=True, timeout=5)
# Create the session pool instance to manage YDB sessions.
session = driver.table_client.session().create()

def user_exists(session, user_id):
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "SELECT `user_id` FROM `user_info` WHERE `user_id` = {user_id};".format(user_id=str(user_id)),
        commit_tx=True,
    )
    if data[0].rows == []:
        return False
    else:
        return True

def if_user_exists(user_id):
    params = {
        "r_type": "if_user",
        "user_id": user_id
    }
    r = requests.get('https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og')
    return r.content 
def new_user(session, user_info):
    
    session.transaction(ydb.SerializableReadWrite()).execute(
        "INSERT INTO `user_info` (`user_id`, `access_token`, `balance`, `active_query`) VALUES ({user_id}, '{access_token}', {balance}, {status_to_set});".format(user_id = int(user_info["id"]), access_token = str(user_info["access_token"]), balance = 0, status_to_set = False),
        commit_tx=True,
    )
    tobotdata = {
        "type": "auth",
        "user_id": str(user_info["id"])
    }
    requests.post("https://functions.yandexcloud.net/d4euu8qh1474bajii21a", json = {"type": "auth", "user_id": str(user_info["id"])})

def update_user(session, user_info):
    
    session.transaction(ydb.SerializableReadWrite()).execute(
        "UPSERT INTO `user_info` (`user_id`, `access_token`) VALUES ({user_id}, '{access_token}');".format(user_id = int(user_info["id"]), access_token = str(user_info["access_token"])),
        commit_tx=True,
    )
    tobotdata = {
        "type": "auth",
        "user_id": str(user_info["id"])
    }
    requests.post("https://functions.yandexcloud.net/d4euu8qh1474bajii21a", json = {"type": "auth", "user_id": str(user_info["id"])})

def create_access_token(code):
    params = {
        "client_id": "8049680",
        "client_secret": "M4CGpSCFkorIOzeymTNk",
        "redirect_uri": "https://functions.yandexcloud.net/d4epbm3dn86eprcb1k1n",
        "code": code
    }
    r = requests.get("https://oauth.vk.com/access_token", params=params)
    response_data = r.json()
    user_info = {
        "id": response_data["user_id"],
        "access_token": response_data["access_token"]
    }
    return user_info


def handler(event, context):
    try:
        code = event["queryStringParameters"]['code']
        response = create_access_token(code=code)
        if not user_exists(session = session, user_id = response["id"]):
            new_user(session = session, user_info = response)
        else:
            response = update_user(session = session, user_info = response)
        
        response = {}
        response["statusCode"]=302
        response["headers"]={'Location': 'https://vk.com/im?sel=-210111570'}
        data = {}
        response["body"]=json.dumps(data)
    except Exception as e:
        response = str(e)
    
    return response
