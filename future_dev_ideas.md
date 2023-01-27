# Future dev ideas

- send welcome on `conversation:start`

- allow users to `register` their own app via a landing page (+responses.json)
  - per app response customisation
- eliminate responses.json by using templates (?)
  - landing page can also configure templates

- serve static resources as attachments
- pre-upload external resources to media.smooch.io
- apply custom app Icon
- command: notify(channel, msg) (?)
- `postback` passthough doesn't open a new ticket (another user message required)
  - inject as role:appUser

## Bugs

- Messages with `type: 'file'` do not contain any `text` parameter:

``` python
[ERROR] UnboundLocalError: local variable 'userText' referenced before assignment
Traceback (most recent call last):
  File "/var/task/handler.py", line 537, in pipelineEvent
    userText = smoochApi.getUserText(bodyData)
  File "/var/task/handler.py", line 430, in getUserText
    return userText
[ERROR] UnboundLocalError: local variable 'userText' referenced before assignment Traceback (most recent call last):   File "/var/task/handler.py", line 537, in pipelineEvent     userText = smoochApi.getUserText(bodyData)   File "/var/task/handler.py", line 430, in getUserText     return userText
```
