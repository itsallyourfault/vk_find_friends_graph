from os import access
from time import process_time, perf_counter
import vk
import vk_api
import requests
import time
import logging as lg
import json
import os
import neo4j as n4


import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

request_type = "full_access"

keyboard_new_pay = {
                "one_time": False,
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "text",
                                "payload": "{\"button\": \"1\"}",
                                "label": "Пополнить баланс"
                            },

                        }
                    ]
                ]}

def return_balance(user_id):
    params = {
        "r_type": "get_user_balance",
        "user_id": user_id
    }
    balance = int((requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og", params=params)).text)
    new_balance = balance + 1
    params = {
        "r_type": "update_user_balance",
        "user_id": user_id,
        "new_balance": new_balance
    }
    requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og", params=params)


def get_user_token(user_id):
    params = {
        "r_type": "get_user_token",
        "user_id": user_id
    }
    access_token = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og", params=params)).text
    logging.info(access_token)
    return access_token


def errors_catch(error):
    string_error = str(error)
    if ('5' in string_error) and ('15' not in string_error):
        logging.critical("Error while auth mb something wrong with the access token --- " + string_error)
        return "❗ Возникла ошибка авторизации, пожалуйста, попробуйте авторизоваться заново!"
    elif ('18' in string_error) or ('30' in string_error):
        logging.error("18 or 30 error--- " + string_error)
        return "❗ Не удается получить данные одного из пользователей.\nЕсли у вас закрытая страничка, то нужно авторизоваться!"
    elif ('29' in string_error):
        logging.error("DAY LIMIT REACHED !!! TRY TOMORROW!--- " + string_error)
        return "❗ Вы достигли лимита запросов, это ограничение от VK, к сожалению, избежать его нельзя. Обычно лимит сбарсывается через час - день."
    else:
        logging.error("UNKNOWN ApiError--- " + string_error)
        return "❗ Возникла неизвестная ошибка, если эта ошибка повторяется у Вас, пожалуйста, напишите администратору группы." + string_error


def get_user_id(user_name):
    flist = vk_session.method("users.get", {"user_ids": user_name})
    return flist[0]["id"]


def get_user_name(user_id):
    flist = vk_session.method("users.get", {"user_ids": user_id})
    full_name = flist[0]["first_name"] + ' ' + flist[0]["last_name"]
    return full_name


def get_friend(user_id):
    flist = vk_session.method(
        "friends.get", {"user_id": user_id, "order": 'hints', "count": 10000})
    return flist["items"]

def add_lots_nodes(tx, root_friend, nodes):

    query1 = f'MERGE (a:Person {{ id: "{root_friend}" }})'
    query = """
        MATCH (b:Person {{id: $root_friend}})
        UNWIND $nodes as row
        MERGE (a:Person {{id: row.id}})
        MERGE (a)-[:FRIENDS]-(b)
        """.format(nodes=nodes, root_friend=root_friend)
    tx.run(query1)
    tx.run(query, nodes=nodes, root_friend=root_friend)


def convert(lst):
    res = []
    if isinstance(lst, int):
        res.append({'id': f'{str(lst)}'})
        return res

    for x in lst:
        res.append({'id': f'{str(x)}'})
    return res

def graph_maker(new_users, root_friend):

    nodes = convert(new_users)


    with driver.session() as session:
        session.write_transaction(add_lots_nodes, str(root_friend), nodes)





def search_for_friend(first_user_id, second_user_id):
    try:
        if first_user_id in get_friend(second_user_id):
            return True
        else:
            return False
    except Exception as e:
        logging.warn(str(e) + " -- search_for_friend")
        return False

def shortest_path_query(tx, first_id, second_id):
    res = tx.run(
        f'MATCH p = ShortestPath((:Person {{ id: "{first_id}" }} )-[*..{max_path_len-1}]-(:Person {{ id:  "{second_id}" }} )) RETURN p')
    rec = res.single()
    if rec == None:
        raise ValueError("No Path")
    nodes = rec[0].nodes
    list_to_return = []
    for node in nodes:
        list_to_return.append(node["id"])
    return list_to_return

def delete_relation_query(tx, first_id, second_id):
    tx.run(f'MATCH (:Person {{ id: "{first_id}" }})-[a:FRIENDS]-(:Person {{ id: "{second_id}" }}) DELETE a')

def graph_path(first_id, second_id):
    

    with driver.session() as session:
        path_test = session.write_transaction(shortest_path_query, first_id, second_id)

    for i in range(len(path_test) - 1):
        if not search_for_friend(int(path_test[i]), int(path_test[i + 1])):
            with driver.session() as session:
                session.write_transaction(delete_relation_query, path_test[i], path_test[i + 1])
            #ComG.remove_edge(str(path_test[i]), str(path_test[i + 1]))
            with driver.session() as session:
                path_test = session.write_transaction(all_paths_query, first_id, second_id)
            try:
                path_test = path_test[0]
                i = len(path_test)
                break
            except:
                raise ValueError("Not actual info and no other ways")
            

    path = path_test
    if len(path) <= max_path_len:
        return path
    else:
        raise ValueError("Longer than needed")


def all_paths_query(tx, first_us, second_us):
    res = tx.run(
        f'MATCH p = allShortestPaths((:Person {{id: "{first_us}"}})-[*..5]-(:Person {{id: "{second_us}"}})) RETURN p LIMIT 4')
    rec = res.values()
    if rec[0] == None:
        return "NoPath"
    paths_to_return = []
    for path in rec:
        nodes = path[0].nodes
        list_to_add = []
        for node in nodes:
            list_to_add.append(node["id"])
        paths_to_return.append(list_to_add)

    for path in paths_to_return:
        for i in range(len(path) - 1):
            if not search_for_friend(int(path[i]), int(path[i + 1])):
                paths_to_return.remove(path)
                break

    return paths_to_return


def add_second_user_lvl2(friends_list):
    for user in friends_list:
        try:
            new_list = get_friend(user)
            graph_maker(new_list[:100], user)
        except:
            pass


def search_f(friends_list,
             context
             ):

    global path
    lvl_friends = []
    count = 0
    alreadyTriedToFindPath = False

    for i in range(10):
        try:

            # TimoutHandler
            if float(context.get_remaining_time_in_millis() / 1000) < 120:
                return False

            graph_path(first_id, second_id)
            return True
        except Exception as e:

            alreadyTriedToFindPath = True

            logging.warn(str(e) + " -- Error while finding path in the main cycle")

            if (count == 0) and (i == 0):
                print("добавляю друзей второго уровня второго пользователя")
                add_second_user_lvl2(second_friends[:100])
                print("Готово")

            for user in friends_list:
                if count >= friends_max:
                    break

                if ((count % 90) == 0) and (alreadyTriedToFindPath == False):
                    try:
                        graph_path(first_id, second_id)
                        return True
                    except Exception as e1:
                        logging.warn(str(e1) + " -- Error while finding path in the submain cycle")

                #if (count % 90) == 0:
                #    print(f"Count = {count}, i = {i}")
                alreadyTriedToFindPath = False

                try:



                    # TimoutHandler
                    if float(context.get_remaining_time_in_millis() / 1000) < 120:
                        return False

                    new_list = get_friend(user)

                    if (second_id in new_list):
                        graph_maker(new_list, user)
                        graph_path(first_id, second_id)
                        return True

                    if any(item in new_list for item in second_friends):
                        new_list = list(
                            set(new_list).intersection(second_friends))
                        graph_maker(user, new_list[0])
                        graph_maker(new_list[0], second_id)
                        #ComG.add_edge(str(user), str(new_list[0]))
                        #ComG.add_edge(str(new_list[0]), str(second_id))
                        graph_path(first_id, second_id)
                        return True

                    new_list = new_list[:friends_max]
                    graph_maker(new_list, user)
                    count = count + 1
                    lvl_friends.extend(new_list)
                except vk_api.AuthError as e2:
                    logging.warning(str(e2) + "AuthError")
                    continue
                except vk_api.ApiError as e2:
                    if ('18' in str(e2)) or ('30' in str(e2)):
                        continue
                    elif '29' in str(e2):

                        logging.error(str(e2) + "DAY LIMIT REACHED !!! TRY TOMORROW! in fun")

                        return 'day limit'
                        continue
                    elif ('5' in str(e2)) and ('15' not in str(e2)):

                        logging.error(str(e2) + "ACCESS TOKEN DENIED OR EXPIRED! in fun")

                        return 'token error'
                        continue

                    else:
                        logging.error(str(e2) + "UNKNOWN ApiError")
                        continue
                except vk_api.VkApiError as e2:
                    logging.warn(str(e2) + "VkApiError")
                    continue
                except vk_api.ApiHttpError as e2:
                    logging.warn(str(e2) + "ApiHttp")
                    continue
                except Exception as e2:
                    logging.warn(str(e2) + "OTHER ERROR")
                    continue

            friends_list = lvl_friends
            lvl_friends = []
            count = 0


def main(user_id, entrance_id, target_id,
         context
         ):
    global graph_file_pth
    try:

        logging.info("Session has started")

        global path, friends_max, all_friends, found, ifstop, max_path_len, vk_session, first_id, second_id, second_friends

        path = []
        friends_max = 10000
        all_friends = []
        found = False
        ifstop = False
        max_path_len = 6

        access_token = get_user_token(user_id=user_id)

        # токен принимается из бд
        vk_session = vk_api.VkApi(
            token=access_token)
        vk_session.get_api()

        logging.info("access token has been obtained -- " + access_token)
        time.sleep(2)
        echo(user_id,
             "✅Ваш запрос принят!")

        logging.info("Подключение к Neo4j")

        global driver

        driver = n4.GraphDatabase.driver("bolt link to neo4j server", auth=('login', 'password'))


        first_guy = entrance_id
        second_guy = target_id

        logging.info("Getting ids of selected users!")

        try:
            first_id = get_user_id(first_guy)
            second_id = get_user_id(second_guy)

            if first_id == second_id:
                return "Вы отправили ссылку на самого себя!"
                
        except Exception as e:
            if 'list' in str(e):
                return "❗ Не удается получить информацию об одном из указанных пользователей! Проверьте корректность запроса или авторизуйтесь!"
            else:
                raise e

        logging.info("Getting friends of both ids")

        first_friends = get_friend(first_id)
        first_friends = first_friends[:friends_max]
        second_friends = get_friend(second_id)
        second_friends = second_friends[:friends_max]

        logging.info("Got it")

        if (second_friends == []) or (first_friends == []):
            return "У одного из указанных людей невозможно получить список друзей, возможно скрыт профиль или список друзей! Если у вас закрытая страница, то авторизуйтесь!"

        graph_maker(first_friends, first_id)
        graph_maker(second_friends, second_id)

        logging.info("Added to graph")



        search_res = search_f(first_friends,
                              context
                              )

        if (search_res == True) or ((len(path) > 0) and (len(path) <= max_path_len)):
            logging.info("I know the WAY!!!!!!!")

            res = "🔎 Удалось найти цепочку знакомств!"

            if request_type == "full_access":
                res = res + "\nЧерез этих людей Вы с ним знакомы ✅\n"
           

            with driver.session() as session:
                paths = session.write_transaction(all_paths_query, first_id, second_id)

            count = 1

            if len(paths) == 0:
                return ""

            if len(paths) == 1:
                if request_type == "full_access":
                    for user in paths[0]:
                        name = get_user_name(user)
                        res = res + f'[id{user}|{name}]' + '\n'
                    res = res + "\n"

            else:
                if request_type == "full_access":
                    for path_now in paths:
                        res = res + f"Вариант №{count}: \n"
                        count = count + 1
                        for user in path_now:
                            name = get_user_name(user)
                            res = res + f'[id{user}|{name}]' + '\n'
                        res = res + "\n"
                elif request_type == "demo_access":
                    res = res + f"\nНайдено {len(paths)} различных варианта знакомства ✅\n"
                    res = res + f'[id{paths[0][0]}|{get_user_name(paths[0][0])}]' + '\n'
                    res = res + f'***** *****' + '\n'
                    res = res + f'[id{paths[0][-1]}|{get_user_name(paths[0][-1])}]' + '\n'
                    #for user in paths[0]:
                    #    name = get_user_name(user)
                    #    res = res + f'[id{user}|{name}]' + '\n'
                    res = res + "\n"


            if request_type == "demo_access":    
                res = res + "Для просмотра всех цепочек знакомств нужно пополнить баланс!"



            return res


        else:

            logging.info("Nothing has been found!")

            if search_res == False:
                return "😫 Путь не найден, попробуйте других людей"
            elif search_res == 'day limit':
                return "❗ Вы достигли лимита запросов, это ограничение от VK, к сожалению, избежать его нельзя. Обычно лимит сбарсывается через час - день."
            elif search_res == 'token error':
                return "❗ Возникла ошибка авторизации, пожалуйста, попробуйте авторизоваться заново!"
            else:
                return "❗ Возникла неизвестная ошибка, если эта ошибка повторяется у Вас, пожалуйста, напишите администратору группы."


    except Exception as e:

        return errors_catch(e)
        # Должен возвращать ошибку что неизвестная ошибка
        # print('ЗАВЕРШЕНИЕ С ОШИБКОЙ! Читайте логи!')
        # #.info(f"CRITICAL ERROR RAISED!")


def echo(user_id, response):
    session = vk.Session()
    api = vk.API(session, v=5.131)
    logging.info("отправил")
    time.sleep(1)
    if ((request_type == "demo_access") and ("Удалось найти" in response)):
        api.messages.send(
            access_token=os.getenv('token'),
            user_id=user_id, message=response,
            random_id=int(time.time()) * 10000000,
            keyboard=json.dumps(keyboard_new_pay))

    else: 
        api.messages.send(
            access_token=os.getenv('token'),
            user_id=user_id, message=response,
            random_id=int(time.time()) * 10000000)


def handler(event, context):

    global request_type


    try:
        if json.loads(event["body"])["type"] == "confirmation" and json.loads(event["body"])['group_id'] == "vk_admin_id_as_int":
            confirmation_code = "code_here"
            return {
                'statusCode': 200,
                'body': confirmation_code
            }
    except:
        pass
    try:
        
        message = json.loads(event['messages'][0]['details']['message']['body'])
        user_id = message["user_id"]
        entrance_id = message["entrance_id"]
        target_id = message["target_id"]
        request_type = message["request_type"]
        logging.info("Input data: " + str(user_id) + " " + str(entrance_id) + " " + str(target_id))
        response = main(user_id, entrance_id, target_id, context)
        params = {
                    "r_type": "update_query_status",
                    "user_id": user_id,
                    "new_status": False
                }
        queryStatus = (requests.get("https://functions.yandexcloud.net/d4e15rdqtnakc2noq0og",
            params=params))
        if "Удалось найти" in response:
            echo(user_id, response)
        else:
            if request_type == "full_access":
                return_balance(user_id)
            echo(user_id, response)
        return {
            'statusCode': 200,
            'body': "OK"
        }
    except Exception as e:
        response = str(e)
        echo(335328970, response)

        return {
            'statusCode': 200,
            'body': 'OK'
        }

