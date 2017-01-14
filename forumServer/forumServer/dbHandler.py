import json
from django.http import JsonResponse
from django.http import HttpRequest
import mysql.connector
import mysql.connector.pooling
import ResponseCode
from datetime import datetime

# database = "technoForum"
database = "technoTest"

cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool",
                                                      pool_size=32,
                                                      user='root', password='',
                                                      host='127.0.0.1',
                                                      database=database)


# General usage methods
def clear(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    try:
        connector = cnxpool.get_connection()
        query = ("TRUNCATE TABLE Users; "
                 "TRUNCATE TABLE Threads; "
                 "TRUNCATE TABLE Subscriptions; "
                 "TRUNCATE TABLE Posts; "
                 "TRUNCATE TABLE Forums; "
                 "TRUNCATE TABLE Followers; ")
        cursor = connector.cursor()
        for _ in cursor.execute(query, multi=True): pass
        connector.commit()
        resp = ResponseCode.alright("OK")
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
    return JsonResponse(resp)


def status(request):
    resp = {}
    data = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT TABLE_NAME, table_rows "
                 "FROM INFORMATION_SCHEMA.TABLES "
                 "WHERE TABLE_SCHEMA = '" + database + "';")
        cursor.execute(query)
        for row in cursor:
            tableName = row['TABLE_NAME']
            if tableName == 'Forums':
                data['forum'] = row['table_rows']
            elif tableName == 'Posts':
                data['post'] = row['table_rows']
            elif tableName == 'Threads':
                data['thread'] = row['table_rows']
            elif tableName == 'Users':
                data['user'] = row['table_rows']
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return JsonResponse(resp)


def createObject(data, query):
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(dictionary=True)
        cursor.execute(query, data)
        connector.commit()
        data["id"] = cursor.lastrowid
        resp = ResponseCode.alright(data)
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        # if err.errno == 1062:
        #     resp = ResponseCode.theUserAlreadyExists()
        # else:
        resp = ResponseCode.wrongQuery(str(err))
        print (str(err))
    finally:
        cursor.close()
        connector.close()
    return resp


# Users methods


def userCreate(request):
    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse(ResponseCode.notValidQuery())
    try:
        if "isAnonymous" not in data:
            data["isAnonymous"] = 0
        add_user = ("INSERT INTO Users "
                    "(username, about, name, email, isAnonymous) "
                    "VALUES (%(username)s, %(about)s, %(name)s, %(email)s, %(isAnonymous)s)")
        connector = cnxpool.get_connection()
        cursor = connector.cursor(dictionary=True)
        cursor.execute(add_user, data)
        connector.commit()
        data["id"] = cursor.lastrowid
        resp = ResponseCode.alright(data)
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        if err.errno == 1062:
            resp = ResponseCode.theUserAlreadyExists()
        else:
            resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
    return JsonResponse(resp)


def getUserPosts(request):
    get_data = request.GET
    if 'user' in get_data.keys():
        param = "user"
        val = get_data["user"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    related = []
    return postList(param, val, get_data, related)


def getUserDetails(request):
    return JsonResponse(getUserInfo(request))


def getUserInfo(request):
    get_data = request.GET
    if 'user' in get_data.keys():
        email = get_data["user"]
    else:
        return ResponseCode.notValidQuery()
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        get_user = ("SELECT Users.*, GROUP_CONCAT(DISTINCT Followers.follower) as followers, "
                    "GROUP_CONCAT(DISTINCT thread) as subscriptions, "
                    "GROUP_CONCAT(DISTINCT Followees.followee) as following FROM Users "
                    "LEFT JOIN Followers ON email = followee "
                    "LEFT JOIN Followers as Followees ON email = Followees.follower "
                    "LEFT JOIN Subscriptions ON user = email "
                    "WHERE email like %s "
                    "GROUP BY Users.id, Users.username, Users.about, Users.name, Users.email, Users.isAnonymous")
        cursor.execute(get_user % ('"' + email + '"'))
        for row in cursor:
            data = row
            followers = row["followers"]
            following = row["following"]
            subscriptions = row["subscriptions"]
            if followers is None:
                data["followers"] = []
            else:
                data["followers"] = followers.split(',')
            if following is None:
                data["following"] = []
            else:
                data["following"] = following.split(',')
            if subscriptions is None:
                data["subscriptions"] = []
            else:
                data["subscriptions"] = map(int, subscriptions.split(','))
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return resp


def userUnfollow(request):
    unfollow = ("DELETE FROM Followers "
                "WHERE follower = %(follower)s AND followee = %(followee)s")
    return JsonResponse(userPost(request, unfollow, "follower"))


def userFollow(request):
    add_follow = ("INSERT INTO Followers "
                  "(follower, followee) "
                  "VALUES (%(follower)s, %(followee)s)")
    return JsonResponse(userPost(request, add_follow, "follower"))


def userUpdate(request):
    update = ("UPDATE Users SET about = %(about)s, name = %(name)s "
              "WHERE email = %(user)s")
    return JsonResponse(userPost(request, update, "user"))


def userPost(request, query, keyForUser):
    try:
        data = json.loads(request.body)
    except:
        return ResponseCode.notValidQuery()
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        cursor.execute(query, data)
        connector.commit()
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if not resp:
            fakeRequest = HttpRequest()
            fakeRequest.GET["user"] = data[keyForUser]
            return getUserInfo(fakeRequest)
    return resp


def getFollowers(request):
    get_followers = ("SELECT thatUsers.*, GROUP_CONCAT(DISTINCT theFollowers.follower) as followersFollowers, "
                     "GROUP_CONCAT(DISTINCT thatFollowers.followee) as followersFollowee, "
                     "GROUP_CONCAT(DISTINCT Subscriptions.thread) as subscriptions FROM Users "
                     "JOIN Followers ON Users.email = Followers.followee "
                     "JOIN Users as thatUsers ON thatUsers.email = Followers.follower "
                     "LEFT JOIN Followers as theFollowers ON theFollowers.followee = thatUsers.email "
                     "LEFT JOIN Followers as thatFollowers ON thatFollowers.follower = thatUsers.email "
                     "LEFT JOIN Subscriptions ON Subscriptions.user = thatUsers.email "
                     "WHERE Users.email like %s ")
    return JsonResponse(getFollowersOrFollowee(request, get_followers))


def getFollowee(request):
    get_followees = ("SELECT thatUsers.*, GROUP_CONCAT(DISTINCT theFollowers.follower) as followersFollowers, "
                     "GROUP_CONCAT(DISTINCT thatFollowers.followee) as followersFollowee, "
                     "GROUP_CONCAT(DISTINCT Subscriptions.thread) as subscriptions FROM Users "
                     "JOIN Followers ON Users.email = Followers.follower "
                     "JOIN Users as thatUsers ON thatUsers.email = Followers.followee "
                     "LEFT JOIN Followers as theFollowers ON theFollowers.followee = thatUsers.email "
                     "LEFT JOIN Followers as thatFollowers ON thatFollowers.follower = thatUsers.email "
                     "LEFT JOIN Subscriptions ON Subscriptions.user = thatUsers.email "
                     "WHERE Users.email like %s  ")
    return JsonResponse(getFollowersOrFollowee(request, get_followees))


def getFollowersOrFollowee(request, query):
    get_data = request.GET
    sortOrder = "desc"
    limit = None
    since_id = None
    if 'user' in get_data.keys():
        email = get_data["user"]
    else:
        return ResponseCode.notValidQuery()
    if 'order' in get_data.keys():
        sortOrder = get_data["order"]
    if 'limit' in get_data.keys():
        limit = get_data["limit"]
    if 'since_id' in get_data.keys():
        since_id = get_data["since_id"]
    resp = {}
    try:
        if since_id is not None:
            query += ("AND thatUsers.id >= " + since_id + " ")
        query += ("GROUP BY thatUsers.id, thatUsers.username, thatUsers.about, "
                  "thatUsers.name, thatUsers.email, thatUsers.isAnonymous "
                  "ORDER BY thatUsers.name " + sortOrder + " ")
        if limit is not None:
            query += ("LIMIT " + limit)
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        cursor.execute(query % ('"' + email + '"'))
        data = []
        newUser = {}
        for row in cursor:
            newUser["id"] = row["id"]
            newUser["username"] = row["username"]
            newUser["about"] = row["about"]
            newUser["name"] = row["name"]
            newUser["email"] = row["email"]
            newUser["isAnonymous"] = row["isAnonymous"]
            followers = row["followersFollowers"]
            following = row["followersFollowee"]
            subscriptions = row["subscriptions"]
            if followers is None:
                newUser["followers"] = []
            else:
                newUser["followers"] = followers.split(',')
            if following is None:
                newUser["following"] = []
            else:
                newUser["following"] = following.split(',')
            if subscriptions is None:
                newUser["subscriptions"] = []
            else:
                newUser["subscriptions"] = map(int, subscriptions.split(','))
            data.append(newUser)
            newUser = {}
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return resp


# Forum methods


def forumCreate(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    query = ("INSERT INTO Forums "
             "(name, short_name, user) "
             "VALUES (%(name)s, %(short_name)s, %(user)s)")

    resp = createObject(data, query)
    if resp['code'] == 5:
        fakeRequest = HttpRequest()
        fakeRequest.GET["forum"] = data["short_name"]
        resp = getForumObject(fakeRequest)

    return JsonResponse(resp)


def getForumDetails(request):
    return JsonResponse(getForumObject(request))


def getForumsPostList(request):
    get_data = request.GET
    if 'forum' in get_data.keys():
        param = "forum"
        val = get_data["forum"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    related = []
    if 'related' in get_data.keys():
        relVal = get_data.getlist("related")
        if 'user' in relVal:
            related.append("user")
        if 'forum' in relVal:
            related.append("forum")
        if 'thread' in relVal:
            related.append("thread")
        if len(relVal) != len(related):
            return JsonResponse(ResponseCode.wrongQuery())
    return postList(param, val, get_data, related)


def getForumObject(request):
    get_data = request.GET
    if 'forum' in get_data.keys():
        forum = get_data["forum"]
    else:
        return ResponseCode.notValidQuery()
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT * FROM Forums "
                 "WHERE short_name = %s")
        cursor.execute(query % ('"' + forum + '"'))
        data = None
        for row in cursor:
            data = row
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if 'related' in get_data.keys():
            related = get_data.getlist("related")
            if data is not None:
                if 'user' in related:
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["user"] = data["user"]
                    data["user"] = getUserInfo(fakeRequest)["response"]
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return resp


def forumUserList(request):
    get_data = request.GET
    sortOrder = "desc"
    limit = None
    since_id = None
    if 'forum' in get_data.keys():
        forum = get_data["forum"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'order' in get_data.keys():
        sortOrder = get_data["order"]
    if 'limit' in get_data.keys():
        limit = get_data["limit"]
    if 'since_id' in get_data.keys():
        since_id = get_data["since_id"]
    resp = {}
    try:
        query = ("SELECT Users.*, GROUP_CONCAT(distinct Subscriptions.thread) as subscriptions, "
                 "GROUP_CONCAT(distinct followers.follower) as followers, "
                 "GROUP_CONCAT(distinct followees.followee) as following "
                 "FROM Users JOIN Posts ON Users.email = Posts.user "
                 "JOIN Forums ON Posts.forum = Forums.short_name "
                 "LEFT JOIN Subscriptions ON Subscriptions.user = Users.email "
                 "LEFT JOIN Followers as followees ON followees.follower = Users.email "
                 "LEFT JOIN Followers as followers ON followers.followee = Users.email "
                 "WHERE Forums.short_name = %s ")
        if since_id is not None:
            query += ("AND Users.id >= " + since_id + " ")
        query += ("GROUP BY Users.id, Users.username, Users.about, Users.name, Users.email, Users.isAnonymous "
                  "ORDER BY Users.name " + sortOrder + " ")
        if limit is not None:
            query += ("LIMIT " + limit)
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        cursor.execute(query % ('"' + forum + '"'))
        data = []
        newUser = {}
        for row in cursor:
            newUser = row
            followers = row["followers"]
            following = row["following"]
            subscriptions = row["subscriptions"]
            if followers is None:
                newUser["followers"] = []
            else:
                newUser["followers"] = followers.split(',')
            if following is None:
                newUser["following"] = []
            else:
                newUser["following"] = following.split(',')
            if subscriptions is None:
                newUser["subscriptions"] = []
            else:
                newUser["subscriptions"] = map(int, subscriptions.split(','))
            data.append(newUser)
            newUser = {}
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return JsonResponse(resp)


def forumThreadList(request):
    get_data = request.GET
    sortOrder = "desc"
    limit = None
    since = None
    related = None
    if 'forum' in get_data.keys():
        forum = get_data["forum"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'order' in get_data.keys():
        sortOrder = get_data["order"]
    if 'limit' in get_data.keys():
        limit = get_data["limit"]
    if 'since' in get_data.keys():
        since = get_data["since"]
        try:
            datetime.strptime(since, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return JsonResponse(ResponseCode.notValidQuery())
    if 'related' in get_data.keys():
        related = get_data.getlist("related")
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT Threads.*, COUNT(CASE WHEN Posts.isDeleted = 0 "
                 "THEN 1 ELSE NULL END) as posts FROM Threads "
                 "LEFT JOIN Posts ON Posts.thread = Threads.id "
                 "WHERE Threads.forum like '" + forum + "' ")
        if since is not None:
            query += ("AND Threads.date >= '" + since + "' ")
        query += ("GROUP BY Threads.id, Threads.forum, Threads.title, Threads.user, Threads.date, "
                  "Threads.message, Threads.slug, Threads.isClosed, Threads.isDeleted, "
                  "Threads.likes, Threads.dislikes "
                  "ORDER BY Threads.date " + sortOrder + " ")
        if limit is not None:
            query += ("LIMIT " + limit)
        cursor.execute(query)
        data = []
        for row in cursor:
            thread = row
            thread["points"] = thread["likes"] - thread["dislikes"]
            if related is not None:
                if 'forum' in related:
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["forum"] = thread["forum"]
                    thread["forum"] = getForumObject(fakeRequest)["response"]
                if 'user' in related:
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["user"] = thread["user"]
                    thread["user"] = getUserInfo(fakeRequest)["response"]
            data.append(thread)
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return JsonResponse(resp)


# Post methods


def postCreate(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    PATH = None
    if 'parent' not in data.keys():
        data["parent"] = None
    elif data["parent"] is None:
        pass
    else:
        fakeRequest = HttpRequest()
        fakeRequest.GET["post"] = data["parent"]
        parentPost = postDetails(fakeRequest, showPATH=True)
        if parentPost["code"] == 0:
            parentPost = parentPost["response"]
            PATH = parentPost["PATH"]
        else:
            return JsonResponse(ResponseCode.notValidQuery())
    if 'isApproved' not in data.keys():
        data["isApproved"] = 1
    if 'isHighlighted' not in data.keys():
        data["isHighlighted"] = 0
    if 'isEdited' not in data.keys():
        data["isEdited"] = 0
    if 'isSpam' not in data.keys():
        data["isSpam"] = 0
    if 'isDeleted' not in data.keys():
        data["isDeleted"] = 0

    query = ("INSERT INTO Posts "
             "(date, forum, isApproved, isDeleted, isEdited, isHighlighted, isSpam, message, parent, thread, user) "
             "VALUES (%(date)s, %(forum)s, %(isApproved)s, %(isDeleted)s, %(isEdited)s, %(isHighlighted)s, "
             "%(isSpam)s, %(message)s, %(parent)s, %(thread)s, %(user)s)")
    resp = createObject(data, query)
    if resp["code"] == 0:
        createdID = resp["response"]["id"]
        newPart = pathEncoder(createdID)
        if PATH is None:
            PATH = newPart
        else:
            PATH += newPart
            # PATH += "." + newPart
        try:
            connector = cnxpool.get_connection()
            cursor = connector.cursor(buffered=True, dictionary=True)
            query = ("UPDATE Posts SET PATH = '" + PATH +
                     "' WHERE id = " + str(createdID))
            cursor.execute(query)
            connector.commit()
        except mysql.connector.Error as err:
            resp = ResponseCode.wrongQuery(str(err))
        finally:
            cursor.close()
            connector.close()
    return JsonResponse(resp)


def getPostDetails(request):
    resp = postDetails(request)
    return JsonResponse(resp)


def pathEncoder(number):
    prefix = ["!!!!", "!!!", "!!", "!", ""]
    BASE87 = "#$&()*+,-/0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~"
    charNum = ""
    i = 0
    while number >= 86:
        div, mod = divmod(number, 86)
        charNum = BASE87[mod] + charNum
        number = int(div)
        i += 1
    charNum = prefix[i] + BASE87[number] + charNum
    return charNum


def postDetails(request, showPATH=False):
    get_data = request.GET
    data = None
    if 'post' in get_data.keys():
        post_id = get_data["post"]
    else:
        return ResponseCode.notValidQuery()
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT * FROM Posts "
                 "WHERE id = %s")
        cursor.execute(query % ('"' + str(post_id) + '"'))
        for row in cursor:
            data = row
            data["points"] = data["likes"] - data["dislikes"]
            if not showPATH:
                del data["PATH"]
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if 'related' in get_data.keys():
            related = get_data.getlist("related")
            if data is not None:
                if 'user' in related:
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["user"] = data["user"]
                    data["user"] = getUserInfo(fakeRequest)["response"]
                if 'thread' in get_data.keys():
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["thread"] = data["thread"]
                    data["thread"] = threadDetails(fakeRequest)
                if 'forum' in get_data.keys():
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["forum"] = data["forum"]
                    data["forum"] = getForumDetails(fakeRequest)["response"]
        if resp == {}:
            if data is not None:
                resp = ResponseCode.alright(data)
            else:
                resp = ResponseCode.notFound()
    return resp


def getPostList(request):
    get_data = request.GET
    if 'forum' in get_data.keys():
        param = "forum"
        val = get_data["forum"]
    elif 'thread' in get_data.keys():
        param = "thread"
        val = get_data['thread']
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    related = []
    return postList(param, val, get_data, related)


def postList(param, val, get_data, related):
    sortOrder = "desc"
    limit = None
    since = None
    if 'order' in get_data.keys():
        sortOrder = get_data["order"]
    if 'limit' in get_data.keys():
        limit = get_data["limit"]
    if 'since' in get_data.keys():
        since = get_data["since"]
        try:
            datetime.strptime(since, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return JsonResponse(ResponseCode.notValidQuery())
    resp = {}
    forumRelated = None
    threadRelated = None
    userRelated = None
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT * from Posts "
                 "WHERE " + param + " = '" + val + "' ")
        if since is not None:
            query += ("AND date >= '" + since + "' ")
        query += ("ORDER BY date " + sortOrder + " ")
        if limit is not None:
            query += ("LIMIT " + limit)
        cursor.execute(query)
        data = []
        for row in cursor:
            post = row
            post["points"] = post["likes"] - post["dislikes"]
            del post["PATH"]
            # related for FORUM ONLY. This means we require data for forum
            if related:
                if 'forum' in related:
                    if forumRelated is None:
                        fakeRequest = HttpRequest()
                        fakeRequest.GET["forum"] = post["forum"]
                        forumRelated = getForumObject(fakeRequest)["response"]
                    post["forum"] = forumRelated
                if 'thread' in related:
                    # if threadRelated is None:
                    #     threadRelated = getRelatedThreads(val)
                    # post["thread"] = threadRelated[post["thread"]]
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["thread"] = post["thread"]
                    post["thread"] = threadDetails(fakeRequest)["response"]
                if 'user' in related:
                    # if userRelated is None:
                    #     userRelated = getRelatedUsers(val)
                    # post["user"] = userRelated[post["user"]]
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["user"] = post["user"]
                    post["user"] = getUserInfo(fakeRequest)
            data.append(post)
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return JsonResponse(resp)


def getRelatedThreads(forum):
    data = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        # query = ("SELECT Threads.*, COUNT(CASE WHEN Posts.isDeleted = 0 "
        #          "THEN 1 ELSE NULL END) as posts FROM Threads "
        #          "LEFT JOIN Posts ON Posts.thread = Threads.id "
        #          "WHERE Threads.forum = '" + forum + "' "
        #          "GROUP BY Threads.id ")
        query = ("SELECT Threads.*, COUNT(Posts.id) as posts "
                 "FROM Threads "
                 "LEFT JOIN Posts ON Posts.thread = Threads.id AND Posts.isDeleted = 0 "
                 "WHERE Threads.forum = '" + forum + "' "
                 "GROUP BY Threads.date")
        cursor.execute(query)
        for row in cursor:
            row["points"] = row["likes"] - row["dislikes"]
            data[row["id"]] = row
    finally:
        cursor.close()
        connector.close()
    return data


def getRelatedUsers(forum):
    data = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT Users.*, GROUP_CONCAT(DISTINCT Followers.follower) as followers, "
                 "GROUP_CONCAT(DISTINCT Subscriptions.thread) as subscriptions, "
                 "GROUP_CONCAT(DISTINCT Followees.followee) as following FROM Users "
                 "LEFT JOIN Followers ON email = followee "
                 "LEFT JOIN Followers as Followees ON email = Followees.follower "
                 "LEFT JOIN Subscriptions ON user = email "
                 "JOIN Posts ON Posts.user = Users.email "
                 "WHERE forum = '" + forum + "' "
                 "GROUP BY email")
        cursor.execute(query)
        for row in cursor:
            followers = row["followers"]
            following = row["following"]
            subscriptions = row["subscriptions"]
            if followers is None:
                row["followers"] = []
            else:
                row["followers"] = followers.split(',')
            if following is None:
                row["following"] = []
            else:
                row["following"] = following.split(',')
            if subscriptions is None:
                row["subscriptions"] = []
            else:
                row["subscriptions"] = map(int, subscriptions.split(','))
            data[row["email"]] = row
    finally:
        cursor.close()
        connector.close()
    return data


def postRemove(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'post' in data.keys():
        val = data["post"]
        return JsonResponse(postDeleteSet(val, 1))
    else:
        return JsonResponse(ResponseCode.notValidQuery())


def postRestore(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'post' in data.keys():
        val = data["post"]
        return JsonResponse(postDeleteSet(val, 0))
    else:
        return JsonResponse(ResponseCode.notValidQuery())


def postDeleteSet(id, val):
    resp = {}
    dat = {"post": id}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = "UPDATE Posts SET isDeleted = " + str(val) + " WHERE id = " + str(id)
        cursor.execute(query)
        connector.commit()
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            resp = ResponseCode.alright(dat)
    return resp


def postVote(request):
    return JsonResponse(Vote(request, "Posts", "post"))


def Vote(request, table, row):
    try:
        data = json.loads(request.body)
    except:
        return ResponseCode.notValidQuery()
    if row in data.keys() and 'vote' in data.keys():
        post = str(data[row])
        vote = data["vote"]
        if vote > 0:
            param = "likes"
            vote = "+" + str(vote)
        else:
            param = "dislikes"
            vote *= -1
            vote = "+" + str(vote)
    else:
        return ResponseCode.notValidQuery()
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("UPDATE " + table + " SET " + param + " = " + param + " " + vote +
                 " WHERE id = " + post)
        cursor.execute(query)
        connector.commit()
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            if row == "post":
                fakeRequest = HttpRequest()
                fakeRequest.GET["post"] = post
                resp = postDetails(fakeRequest)
            elif row == "thread":
                fakeRequest = HttpRequest()
                fakeRequest.GET["thread"] = post
                resp = threadDetails(fakeRequest)
    return resp


def postUpdate(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'post' in data.keys() and 'message' in data.keys():
        post = str(data["post"])
        message = data["message"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("UPDATE Posts SET message = '" + message +
                 "' WHERE id = " + post)
        cursor.execute(query)
        connector.commit()
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            fakeRequest = HttpRequest()
            fakeRequest.GET["post"] = post
            resp = postDetails(fakeRequest)
    return JsonResponse(resp)


# Thread methods

def updateThreadParam(param, value, ID):
    resp = {}
    try:
        ID = str(ID)
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("UPDATE Threads SET " + param + " = " + value +
                 " WHERE id = " + ID)
        cursor.execute(query)
        connector.commit()
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            resp["thread"] = ID
    return ResponseCode.alright(resp)


def threadCreate(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())

    if 'isDeleted' not in data.keys():
        data["isDeleted"] = 0

    query = ("INSERT INTO Threads "
             "(date, forum, title, isDeleted, isClosed, user, message, slug) "
             "VALUES (%(date)s, %(forum)s, %(title)s, %(isDeleted)s, %(isClosed)s, %(user)s, %(message)s, %(slug)s)")
    return JsonResponse(createObject(data, query))


def getThreadDetails(request):
    return JsonResponse(threadDetails(request))


def threadDetails(request):
    get_data = request.GET
    data = None
    related = []
    if 'thread' in get_data.keys():
        thread_id = get_data["thread"]
    else:
        return ResponseCode.notValidQuery()
    if 'related' in get_data.keys():
        relVal = get_data.getlist("related")
        if 'user' in relVal:
            related.append("user")
        if 'forum' in relVal:
            related.append("forum")
        if len(relVal) != len(related):
            return ResponseCode.wrongQuery()
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(dictionary=True)
        # query = ("SELECT Threads.*, COUNT(CASE WHEN Posts.isDeleted = 0 "
        #          "THEN 1 ELSE NULL END) as posts FROM Threads "
        #          "LEFT JOIN Posts ON Posts.thread = Threads.id "
        #          "WHERE Threads.id = %s "
        #          "GROUP BY Threads.id ")
        query = ("SELECT Threads.*, COUNT(Posts.id) as posts "
                 "FROM Threads "
                 "LEFT JOIN Posts ON Posts.thread = Threads.id AND Posts.isDeleted = 0 "
                 "WHERE Threads.id = %s "
                 "GROUP BY Threads.id, Threads.forum, Threads.title, Threads.user, Threads.date, "
                 "Threads.message, Threads.slug, Threads.isClosed, Threads.isDeleted, "
                 "Threads.likes, Threads.dislikes ")
        cursor.execute(query % (str(thread_id)))
        for row in cursor:
            data = row
            data["points"] = data["likes"] - data["dislikes"]
            if related:
                if 'user' in related:
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["user"] = data["user"]
                    info = getUserInfo(fakeRequest)
                    if info["code"] == 0:
                        data["user"] = info["response"]
                    else:
                        return ResponseCode.wrongQuery()
                if 'forum' in related:
                    fakeRequest = HttpRequest()
                    fakeRequest.GET["forum"] = data["forum"]
                    info = getForumObject(fakeRequest)
                    if info["code"] == 0:
                        data["forum"] = info["response"]
                    else:
                        return ResponseCode.wrongQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            if data is not None:
                resp = ResponseCode.alright(data)
            else:
                resp = ResponseCode.notFound()
    return resp


def threadClose(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'thread' in data.keys():
        thread = data["thread"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    return JsonResponse(updateThreadParam("isClosed", "1", thread))


def threadOpen(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'thread' in data.keys():
        thread = data["thread"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    return JsonResponse(updateThreadParam("isClosed", "0", thread))


def threadClose(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'thread' in data.keys():
        thread = data["thread"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    return JsonResponse(updateThreadParam("isClosed", "1", thread))


def threadRemove(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'thread' in data.keys():
        thread = data["thread"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    try:
        resp = updateThreadParam("isDeleted", "1", thread)
        if resp["code"] == 0:
            connector = cnxpool.get_connection()
            cursor = connector.cursor(dictionary=True)
            query = ("UPDATE Posts SET isDeleted = 1 "
                     " WHERE thread = " + str(thread))
            cursor.execute(query)
            connector.commit()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
    return JsonResponse(ResponseCode.alright(resp))


def threadRestore(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'thread' in data.keys():
        thread = data["thread"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    try:
        resp = updateThreadParam("isDeleted", "0", thread)
        if resp["code"] == 0:
            connector = cnxpool.get_connection()
            cursor = connector.cursor(dictionary=True)
            query = ("UPDATE Posts SET isDeleted = 0 "
                     " WHERE thread = " + str(thread))
            cursor.execute(query)
            connector.commit()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
    return JsonResponse(ResponseCode.alright(resp))


def threadSubscribe(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    query = ("INSERT INTO Subscriptions "
             "(thread, user) "
             " VALUES (%(thread)s, %(user)s)")
    resp = createObject(data, query)
    if resp["code"] == 0:
        if "id" in resp["response"].keys():
            del (resp["response"])["id"]
    return JsonResponse(resp)


def threadUnsubscribe(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    query = ("DELETE FROM Subscriptions "
             "WHERE thread = %(thread)s AND user = %(user)s")
    resp = createObject(data, query)
    if resp["code"] == 0:
        if "id" in resp["response"].keys():
            del (resp["response"])["id"]
    return JsonResponse(resp)


def threadUpdate(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'thread' in data.keys() and 'message' in data.keys() and 'slug' in data.keys():
        thread = str(data["thread"])
        message = data["message"]
        slug = data["slug"]
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("UPDATE Threads SET message = '" + message + "', slug = '" + slug +
                 "' WHERE id = " + thread)
        cursor.execute(query)
        connector.commit()
    except KeyError:
        resp = ResponseCode.notValidQuery()
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            fakeRequest = HttpRequest()
            fakeRequest.GET["thread"] = thread
            resp = threadDetails(fakeRequest)
    return JsonResponse(resp)


def threadVote(request):
    return JsonResponse(Vote(request, "Threads", "thread"))


def threadList(request):
    get_data = request.GET
    sortOrder = "desc"
    limit = None
    since = None
    if 'forum' in get_data.keys():
        param = get_data["forum"]
        paramName = "Threads.forum"
    elif 'user' in get_data.keys():
        param = get_data["user"]
        paramName = "Threads.user"
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    if 'order' in get_data.keys():
        sortOrder = get_data["order"]
    if 'limit' in get_data.keys():
        limit = get_data["limit"]
    if 'since' in get_data.keys():
        since = get_data["since"]
        try:
            datetime.strptime(since, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return JsonResponse(ResponseCode.notValidQuery())
    resp = {}
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        query = ("SELECT Threads.*, COUNT(CASE WHEN Posts.isDeleted = 0 "
                 "THEN 1 ELSE NULL END) as posts FROM Threads "
                 "LEFT JOIN Posts ON Posts.thread = Threads.id "
                 "WHERE " + paramName + " like '" + param + "' ")
        if since is not None:
            query += ("AND Threads.date >= '" + since + "' ")
        query += ("GROUP BY Threads.id, Threads.forum, Threads.title, Threads.user, Threads.date, "
                  "Threads.message, Threads.slug, Threads.isClosed, Threads.isDeleted, "
                  "Threads.likes, Threads.dislikes "
                  "ORDER BY Threads.date " + sortOrder + " ")
        if limit is not None:
            query += ("LIMIT " + limit)
        cursor.execute(query)
        data = []
        for row in cursor:
            thread = row
            thread["points"] = thread["likes"] - thread["dislikes"]
            data.append(thread)
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return JsonResponse(resp)


def getThreadPosts(request):
    get_data = request.GET
    if 'thread' in get_data.keys():
        param = "thread"
        val = get_data['thread']
    else:
        return JsonResponse(ResponseCode.notValidQuery())
    sortOrder = "desc"
    limit = None
    since = None
    sort = "flat"
    if 'sort' in get_data.keys():
        sort = get_data["sort"]
    if 'order' in get_data.keys():
        sortOrder = get_data["order"]
    if 'limit' in get_data.keys():
        limit = get_data["limit"]
    if 'since' in get_data.keys():
        since = get_data["since"]
        try:
            datetime.strptime(since, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return JsonResponse(ResponseCode.notValidQuery())
    resp = {}
    data = []
    try:
        connector = cnxpool.get_connection()
        cursor = connector.cursor(buffered=True, dictionary=True)
        if sort == "flat":
            query = ("SELECT * from Posts "
                     "WHERE " + param + " like '" + val + "' ")
            if since is not None:
                query += ("AND date >= '" + since + "' ")
            query += ("ORDER BY date " + sortOrder + " ")
            if limit is not None:
                query += ("LIMIT " + limit)
            cursor.execute(query)
            for row in cursor:
                post = row
                post["points"] = post["likes"] - post["dislikes"]
                del post["PATH"]
                data.append(post)
        elif sort == 'tree':
            parents = []
            query = ("SELECT * from Posts "
                     "WHERE " + param + " like '" + val + "' AND parent is null ")
            if since is not None:
                query += ("AND date >= '" + since + "' ")
            query += ("ORDER BY PATH " + sortOrder + " ")
            if limit is not None:
                query += ("LIMIT " + limit)
            cursor.execute(query)
            for row in cursor:
                post = row
                post["points"] = post["likes"] - post["dislikes"]
                parents.append(post)
            limit = int(limit)
            for parent in parents:
                print (limit)
                query = ("SELECT * from Posts "
                         "WHERE PATH like '" + str(parent["PATH"]) + "%' AND parent is not null "
                         "AND " + param + " = '" + val + "' ")
                del parent["PATH"]
                data.append(parent)
                limit -= 1
                if since is not None:
                    query += ("AND date >= '" + since + "' ")
                query += "ORDER BY PATH asc "
                if limit is not None:
                    query += ("LIMIT " + str(limit))
                cursor.execute(query)
                limit -= cursor.rowcount
                for row in cursor:
                    post = row
                    post["points"] = post["likes"] - post["dislikes"]
                    del post["PATH"]
                    data.append(post)
                if limit <= 0:
                    break
        elif sort == 'parent_tree':
            parents = []
            query = ("SELECT * from Posts "
                     "WHERE " + param + " = '" + val + "' AND parent is null ")
            if since is not None:
                query += ("AND date >= '" + since + "' ")
            query += ("ORDER BY PATH " + sortOrder + " ")
            if limit is not None:
                query += ("LIMIT " + limit)
            cursor.execute(query)
            for row in cursor:
                post = row
                post["points"] = post["likes"] - post["dislikes"]
                parents.append(post)
            for parent in parents:
                query = ("SELECT * from Posts "
                         "WHERE PATH like '" + str(parent["PATH"]) + "%' AND parent is not null "
                         "AND " + param + " = '" + val + "' ")
                if since is not None:
                    query += ("AND date >= '" + since + "' ")
                query += ("ORDER BY PATH " + sortOrder + " ")
                cursor.execute(query)
                # print (cursor.statement)
                del parent["PATH"]
                data.append(parent)
                for row in cursor:
                    post = row
                    post["points"] = post["likes"] - post["dislikes"]
                    del post["PATH"]
                    data.append(post)
    except mysql.connector.Error as err:
        resp = ResponseCode.wrongQuery(str(err))
    finally:
        cursor.close()
        connector.close()
        if resp == {}:
            try:
                resp = ResponseCode.alright(data)
            except:
                resp = ResponseCode.notFound()
    return JsonResponse(resp)