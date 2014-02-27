#Forum.details
Get forum details

## Supported request methods 
* GET

##Supported formats
* json

##Arguments
###Optional
* related
   ```array``` include related entities. Possible values: ```['user',]```. Default: []


###Requried
* forum
   ```str``` forum short_name


Requesting http://some.host.ru/db/api/s.stupnikov/forum/details/ with _{'related': ['user'], 'forum': 'forum3'}_:
```json
{u'code': 0,
 u'response': {u'id': 682,
               u'name': u'\u0424\u043e\u0440\u0443\u043c \u0422\u0440\u0438',
               u'short_name': u'forum3',
               u'user': {u'about': u'hello im user2',
                         u'email': u'example2@mail.ru',
                         u'followers': [],
                         u'following': [],
                         u'id': 820,
                         u'isAnonymous': False,
                         u'name': u'Jey',
                         u'subscriptions': [],
                         u'username': u'user2'}}}
```