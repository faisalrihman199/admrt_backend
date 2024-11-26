# Action words
SEND = 'SEND'
FETCH = 'FETCH'
MESSAGE = 'MESSAGE'
CONVERSATION = 'CONVERSATION'
NEW = 'NEW'
UNREAD = 'UNREAD'
LIST = 'LIST'
ERROR = 'ERROR'

# Composit Action Words
class AllowedActions:
    SEND_MESSAGE = f"{SEND}-{MESSAGE}" # client requests for sending a message
    FETCH_CONVERSATION = f"{FETCH}-{CONVERSATION}" # client requests for a conversation
    # for server only
    NEW_MESSAGE = f"{NEW}-{MESSAGE}" # action to be taken after processing 'SEND-MESSAGE'
    CONVERSATION = CONVERSATION # action to be taken after processing 'FETCH-CONVERSATION'
    UNREAD_CONVERSATION = f"{CONVERSATION}-{LIST}" # when a client is connected, server automatically does this action
    ERROR = ERROR

    def __init__(self):
        self.all_actions = [action for action in AllowedActions.__dict__.values() if isinstance(action, str)]


ALLOWED_ACTIONS = AllowedActions()
# {
#     "action": "CONVERSATION",
#     "body": {
#         "partner_id": "5",
#         "conversation": [
#             {
#                 "sender_id": "5",
#                 "receiver_id": "7",
#                 "text": "alskdfjakdj",
#                 "created_at": 1379823749813,
#             },
#             {
#                 "sender_id": "7",
#                 "receiver_id": "5",
#                 "text": "alskdfjakdj",
#                 "created_at": 1379823749813,
#             }
#         ]
#     }
# }