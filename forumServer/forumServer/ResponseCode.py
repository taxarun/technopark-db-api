def alright(obj):
    data = {"code": 0, "response": obj}
    return data


def notFound():
    data = {"code": 1, "response": "Object wasn't found"}
    return data


def notValidQuery(err_str="The query isn't valid"):
    data = {"code": 2, "response": err_str}
    print (err_str)
    return data


def wrongQuery(sqlError="The query isn't correct"):
    data = {"code": 3, "response": sqlError}
    # print (sqlError)
    return data


def unknownError():
    data = {"code": 4, "response": "Error is unknown"}
    return data


def theUserAlreadyExists():
    data = {"code": 5, "response": "The user you trying to add is already in Data Base"}
    return data
