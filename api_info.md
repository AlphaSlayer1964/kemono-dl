## USERS
```python
# api call: /api/{service}/user/{user_id}?o={chunk}
# chunk starts at 0 and incriments by 25
# returns a list of post data (see POSTS)
```
## POSTS
```python
# api call: /api/{service}/user/{user_id}/post/{post_id}
# returns a dictionary of the post data

post                    # dict      
    ['title']           # str 
    ['added']           # str, datetime object
    ['edited']          # str, datetime object
    ['id']              # str
    ['user']            # str
    ['published']       # str, datetime object
    ['attachments']     # list of dict
        ['name']        # str
        ['path']        # str
    ['file']            # dict
        ['name']        # str
        ['path']        # str 
    ['content']         # str, html
    ['shared_file']     # bool 
    ['embed']:          # dict
        ['description'] # str
        ['subject']     # str
        ['url']         # str
```
## DISCORD CHANNELS
```python
# api call: /api/discord/channels/lookup?q={sercer_id}
# returns a list of dictionaris contaning channel names and ids

channel                     # dict
    ['id']                  # str
    ['name']                # str
```
## DISCORD CHANNEL POSTS
```python
# api call: /api/discord/channel/{channel_id}?skip={skip}
# skip starts at 0 and incriments by 10
# returns a list of dictionaries contaning each posts data

post                        # dict
    ['added']               # str, datetime object
    ['attachments']         # list of dict
        ['isImage']         # str
        ['name']            # str
        ['path']            # str
    ['author']              # dict   
        ['avatar']          # str
        ['discriminator']   # str
        ['id']              # str
        ['public_flags']    # int
        ['username']        # str
    ['channel']             # str
    ['content']             # str, html
    ['edited']              # ???
    ['embeds']              # list of dict
        ['description']     # str
        ['thumbnail']       # dict
            ['height']      # int
            ['proxy_url']   # str
            ['url']         # str
            ['width']       # int
        ['title']           # str
        ['type']            # str
        ['url']             # str
    ['id']                  # str
    ['mentions']            # list of dict
        ['avatar']          # str
        ['discriminator']   # str
        ['id']              # str
        ['public_flags']    # int
        ['username']        # str    
    ['published']           # str, datetime object
    ['server']              # str
```
## CREATORS
```python
# api call: /api/creators
# returns a list of dictionaries of user data

creator            # dict
    ['id']         # str
    ['indexed']    # str 
    ['name']       # str
    ['service']    # str
    ['updated']    # str
```
## FAVORITES
```python
# api all: /api/favorites?type={type}
# type can be post or artist
# (artist) returns a list of dictionaries with user data

favorite_user       # dict
    ['faved_seq']   # int
    ['id']          # str
    ['indexed']     # str, datetime object
    ['name']        # str
    ['service']     # str
    ['updated']     # str, datetime object
   
# (post) returns a list of dictionaries with post data

favorite_post       # dict, same as post
    ['faved_seq']   # int
```
