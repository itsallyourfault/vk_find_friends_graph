import json
import os
import ydb as ydb
import random

# create driver in global space.
driver = ydb.Driver(endpoint=os.getenv('YDB_ENDPOINT'), database=os.getenv('YDB_DATABASE'))
# Wait for the driver to become active for requests.
driver.wait(fail_fast=True, timeout=5)
# Create the session pool instance to manage YDB sessions.
session = driver.table_client.session().create()

def get_user_token(session, user_id):
    # create the transaction and execute query.
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "SELECT `access_token` FROM `user_info` WHERE `user_id` = {user_id};".format(user_id=str(user_id)),
        commit_tx=True,
    )
    if data[0].rows[0].access_token == None:
        return "This user doesnt have token yet"

    return data[0].rows[0].access_token.decode('utf-8')

def get_token_from_db(session):
    # Get all tokens
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "SELECT * FROM `tokensData`",
        commit_tx=True,
        )
    
    # Choose token
    data = random.choice(data[0].rows)
    token = data.token.decode('utf-8')

    print(data)

    # Update usage count
    usageCount = data.usageCount
    usageCount += 1
    print(str(type(usageCount)))
    print(usageCount)
    req = session.transaction(ydb.SerializableReadWrite()).execute(
        "UPDATE tokensData SET usageCount = {usageCount} WHERE token == '{token}'".format(usageCount = usageCount, token = token),
        commit_tx=True,
    )

    return token

def user_exists(session, user_id):
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "SELECT `user_id` FROM `user_info` WHERE `user_id` = {user_id};".format(user_id=str(user_id)),
        commit_tx=True,
    )
    if data[0].rows == []:
        return False
    else:
        return True
    

def get_user_balance(session, user_id):
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "SELECT * FROM `user_info` WHERE `user_id` = {user_id};".format(user_id=str(user_id)),
        commit_tx=True,
    )
    balance = data[0].rows[0].balance
    if balance == None:
        return "0"
    return balance

def update_user_balance(session, user_id, new_balance):
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "UPDATE user_info SET balance = {new_balance} WHERE user_id = {user_id}".format(new_balance=new_balance, user_id = user_id),
        commit_tx=True,
    )
    return "Done"

def update_query_status(session, user_id, new_status):
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "UPDATE user_info SET active_query = {new_status} WHERE user_id = {user_id}".format(new_status=new_status, user_id = user_id),
        commit_tx=True,
    )
    return "Done"

def get_query_status(session, user_id):
    data = session.transaction(ydb.SerializableReadWrite()).execute(
        "SELECT active_query FROM `user_info` WHERE `user_id` = {user_id};".format(user_id=str(user_id)),
        commit_tx=True,
    )
    return data[0].rows[0].active_query

def new_user(session, user_id):
    token = get_token_from_db(session)
    session.transaction(ydb.SerializableReadWrite()).execute(
        "INSERT INTO `user_info` (`user_id`, `access_token`, `balance`, `active_query`) VALUES ({user_id}, '{token}', {balance}, {status_to_set});".format(user_id = int(user_id), balance = 0, token = token, status_to_set = False),
        commit_tx=True,
    )


def handler(event, context):
    
    try:
        r_type = event['queryStringParameters']['r_type']
        user_id = event['queryStringParameters']['user_id']

        if not user_id.isdecimal():
            return {'statusCode': 200,
                    'body': json.dumps("id must be int")}

        if not user_exists(session = session, user_id = user_id):
            new_user(session=session, user_id=user_id)
            return {'statusCode': 200,
                    'body': json.dumps("User not found")}

        if r_type == "get_user_token":
            response = get_user_token(session=session, user_id=user_id)
        elif r_type == "get_user_balance":
            response = get_user_balance(session=session, user_id=user_id)
        elif r_type == "update_user_balance":
            new_balance = event['queryStringParameters']["new_balance"]
            response = update_user_balance(session = session, user_id = user_id, new_balance = new_balance)
        elif r_type == "get_query_status":
            response = get_query_status(session = session, user_id = user_id)
        elif r_type == "update_query_status":
            new_status = event['queryStringParameters']["new_status"]
            response = update_query_status(session = session, user_id = user_id, new_status = new_status)
        elif r_type == "if_user":
            response = str(user_exists(session = session, user_id = user_id))
    
    except Exception as e:
        response = str(e)
        
    return {
        'statusCode': 200,
        'body': str(response)
    }