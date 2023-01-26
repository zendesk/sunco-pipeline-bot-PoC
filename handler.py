from boto3 import resource
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from smooch.rest import ApiException
from datetime import datetime, timedelta
from time import sleep
from uuid import uuid4
import smooch, json, os, requests, re
import inspect

# TODO: pass context to Bus.Sys.

# IMPROVEMENT: Upload attachments/html/css to app on signup?

smooch_root = "https://api.smooch.io"
notificationEndpoints = {
    "procUrl": smooch_root + "/v1/middleware/processors",
    "piplUrl": smooch_root + "/v1/middleware/pipelines",
    "updatePiplUrl": smooch_root + "/v1/middleware/pipelines/appuser",
    "continueUrl": smooch_root + "/v1/middleware/continue",
}
human_WPM = 80
minSleep = 1

respones_file = "responses.json"

# (datetime.utcnow()+timedelta(days=2)).strftime("%d-%b")

# TODO: conversation:start handling + webSDK's startConversation()
# TODO: onboarding flow
# TODO: pipeline configuration flow
# def newSignup(event, context):
#     # sort by method
#     # GET: serve signup page
#     # POST: signup flow
#         # generate botURL from context + os.environ['botEndpoint']
#         # generateJWT
#         # linkBot2App(JWT, appId, awsSubdomain=os.environ['requestContext']['domainPrefix'])
#     raise NotImplementedError

# def linkBot2App(JWT, appId, botTarget=None, awsSubdomain=None, triggerList=None):
#     # TODO: Test JWT
#     smoochHdr = {"Authorization": "Bearer %s" % JWT, "Content-type": "application/json"}
#     if triggers is None:
#         triggers = [ "message:appUser", "postback" ]
#     if botTarget is None:
#  and awsSubdomain is not None:
#         botTarget = "https://%s.execute-api.us-east-1.amazonaws.com/%s/%s" % (awsSubdomain, os.environ['botStage'], os.environ['botEndpoint'])
#     elif botTarget is not None:
#         #TODO: validate URL?
#         pass   # botTarget = botTarget
#     else:
#         raise UnhandledException()
#
#     # Create Processor
#     newProc = { "target": botTarget, "triggers": triggers }
#     createResp = requests.post(procUrl, headers=smoochHdr, json=newProc)
#     if createResp.ok:
#         print("Processor created: %s\n%s" % (createResp, createResp.content))
#         createResp = json.loads(createResp.content)
#         processorId = createResp['processor']['_id']
#         processorSecret = createResp['processor']['secret']
#         #TODO: update DDB to store secret?
#         if not createResp['processor']['includeFullAppUser']:
#             raise NotImplementedError("`includeFullAppUser` is required")
#     else:
#         #TODO: handle gracefully
#         print(newProc)
#         raise Exception("Error %s creating Processor: %s" % (createResp, createResp.content))
#
#     # Get Pipelines
#     getPipResp = requests.get(piplUrl, headers=smoochHdr)
#     if getPipResp.ok:
#         print("Got pipeline contents: %s\n%s" % (getPipResp, getPipResp.content))
#         listResp = json.loads(getPipResp.content)
#         pipelines = listResp['pipelines']
#           # TODO: refactor - pipeline name is /appuser
#         for pipe, contents in pipelines.items():
#             print("Processing pipeline: %s" % pipe)
#             if pipe == "appUser" or pipe == "appuser":
#                 addProcessor = { pipe: processorId not in contents }
#             else:
#                 raise Exception("Unexpected pipeline type: %s" % pipe)
#             print("")
#     else:
#         #TODO: handle gracefully
#         raise Exception("Error %s listing Pipelines: %s" % (getPipResp, getPipResp.content))
#     # TODO: OK up to here ^^^ (processor not added to pipeline ?!?)
#
#     # Update Pipeline `/appuser`
#     for pipe, update in addProcessor.items():
#         if update:
#             #TODO Option to append or prepend?
#             pipelines[pipe].append(processorId)
#             print("Sending reuqest: %s" % )
#             updateResp = requests.put(updatePiplUrl.format(trigger=pipe), headers=smoochHdr, json=pipelines[pipe])
#             if updateResp.ok:
#                 print("Updated pipeline: %s\n%s" % (updateResp, updateResp.content))
#                 newPipelines = json.loads(updateResp.content)
#                 if processorId not in newPipelines['pipeline']:
#                     raise Exception("Error adding processor %s to pipeline.\n Current contents: %s" % (processorId, newPipelines['pipeline']))
#
#     # Log supported app in table
#     dynamodb = resource("dynamodb")
#     appsTable = dynamodb.Table(os.environ['appTableName'])
#     try:
#         putResp = appsTable.put_item( Item={
#             'appId': appId,
#             'processorId': processorId,
#             'processorSecret': processorSecret,
#             'owner': "TBD",
#             'JWT': JWT
#             } )
#     except ClientError as e:
#         print(e.response['Error']['Message'])
#         raise e
#     else:
#         print("PutItem succeeded:")
#         #print(json.dumps(putResp, indent=4, cls=DecimalEncoder))
#         print(putResp)
#         # if 'Item' in putResp.keys():
#         #     appCreds = putResp['Item']
#         #     #print("GetItem succeeded: %s" % appCreds)
#         # else:
#         #     print(" > ERROR: No 'Item' in db response: %s" % putResp)
#         #     return { "statusCode": 403, "body": " > Forbidden: appId not registered!" }
#         raise NotImplementedError


class mySmooch:
    def __init__(self, appId, appJwt, appUserId):
        self.appId = appId
        self.appUserId = appUserId

        with open(respones_file, "r") as f:
            self.responses = json.load(f)

        # Configure API key authorization (alternative): jwt
        smooch.configuration.api_key["Authorization"] = appJwt
        smooch.configuration.api_key_prefix["Authorization"] = "Bearer"

        # create an instance of the API class
        self.convoApi = smooch.ConversationApi()
        self.appUserApi = smooch.AppUserApi()

    def getAppUserInfo(self):
        # print(" > getAppUserInfo()")
        # create an instance of the API class
        appUserApi = smooch.AppUserApi()

        try:
            apiResp = appUserApi.get_app_user(self.appId, self.appUserId)
            # pprint(apiResp)
        except ApiException as e:
            print("Exception when calling AppUserApi->get_app_user: %s\n" % e)
            result = {"statusCode": 500, "body": e}
            # print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
            print(" >> Result: %s" % (result))
            return None
        # result = { "statusCode": 200, "body": "OK!"}
        # print(" >> Request:\n%s\n >> Response: %s\n >> Result: %s" % (bodyData, apiResp, result))
        return apiResp.app_user.properties, self._findLastSeen(apiResp.app_user.clients)

    def updateAppUser(self, properties):
        app_user_update_body = smooch.AppUserUpdate(
            properties=properties
        )  # AppUserUpdate | Body for an updateAppUser request.

        try:
            userUpdateResp = self.appUserApi.update_app_user(
                self.appId, self.appUserId, app_user_update_body
            )
            # pprint(userUpdateResp)
        except ApiException as e:
            print("Exception when calling AppUserApi->update_app_user: %s\n" % e)
            # result = { "statusCode": 500, "body": e }
            # print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
            # print(" >> Result: %s" % (result))
            return
        print(
            "appUser properties updated: %s" % str(userUpdateResp.app_user.properties)
        )
        return

    def sendTypingIndicator(self, sleepWords=None):
        # app_id = 'app_id_example' # str | Identifies the app.
        # user_id = 'user_id_example' # str | Identifies the user. Can be either the smoochId or the userId.
        conversation_activity_body = smooch.ConversationActivity(
            role="appMaker", type="typing:start"
        )  # ConversationActivity | Body for a triggerConversationActivity request.

        try:
            api_response = self.convoApi.conversation_activity(
                self.appId, self.appUserId, conversation_activity_body
            )
            # pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling ConversationApi->conversation_activity: %s\n"
                % e
            )
        else:
            print("Typing indicator resp: %s" % api_response)

        if sleepWords is not None and type(sleepWords) is int:
            duration = sleepWords / (human_WPM * 1.5)
            if duration < minSleep:
                duration = minSleep
            sleep(duration)

    def sendMessage(self, messageObj):
        print(" >> sendMessage() got: %s" % messageObj)

        if type(messageObj) is dict:
            pass
        elif type(messageObj) is str:
            messageObj = {"text": messageObj}
        else:
            raise TypeError("Unsupported type %s" % type(messageObj))

        if "text" in messageObj.keys():
            self.sendTypingIndicator(len(messageObj["text"].split()))
        messageToSend = {
            # smooch-python key format
            "type": "text",
            "role": "appMaker",
        }
        if "role" in messageObj.keys() and messageObj["role"] == "appMaker":
            messageToSend.update(self.responses["botPersona"])
            # print(" > DEV: Updated base msg: %s" % messageToSend)

        # TODO: check for key collisions?
        # x.update(y) will overwrite x with conflicting values from y
        messageToSend.update(messageObj)

        message_post_body = smooch.MessagePost(
            **messageToSend
        )  # MessagePost | Body for a postMessage request. Additional arguments are necessary based on message type ([text](https://docs.smooch.io/rest/#text), [image](https://docs.smooch.io/rest/#image), [carousel](https://docs.smooch.io/rest/#carousel), [list](https://docs.smooch.io/rest/#list), [form](https://docs.smooch.io/rest/#form))

        print(" >> Trying to send: %s" % messageToSend)
        try:
            msgPostResp = self.convoApi.post_message(
                self.appId, self.appUserId, message_post_body
            )
            # pprint(msgPostResp)
        except ApiException as e:
            print("Exception when calling ConversationApi->post_message: %s\n" % e)
            result = {"statusCode": 500, "body": e}
            # print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
            print(" >> Result: %s" % (result))
            return result
        result = {"statusCode": 200, "body": str(msgPostResp)}
        # print(" >> Response: %s\n >> Result: %s" % (msgPostResp, result))
        return result

    def escalate(self, nonce):
        passthroughResult = self.passthroughEscalated(nonce)
        # self.sendMessage({"text": "Please stand by while I get one of Humans to help you ⏳"})
        self.updateAppUser({"escalated": True})
        # self.sendResponses(">>msg>>escalate", nonce) # << gets caught in `start` fallback instead of trying to process the >>msg>> command

        # TODO: return something else if escalation flag update breaks?
        print(
            "Excecution complete (escalation set) - returning: %s" % passthroughResult
        )
        return passthroughResult

    def deescalate(self):
        # TODO: send message?
        # self.sendMessage({"text": "Please stand by while I get one of Humans to help you ⏳"})
        self.updateAppUser({"escalated": False})
        # TODO: return something else if escalation flag update breaks?
        print("Excecution complete (escalation unset)")
        return True

    def passthroughEscalated(self, nonce):
        continueHdr = {"Authorization": "Bearer %s" % nonce}
        # TODO: use urllib3 instead (Lambda-native lib)
        passthruResp = requests.post(
            notificationEndpoints["continueUrl"], headers=continueHdr
        )
        if not passthruResp.ok:
            raise Exception(
                "ERROR: %s signalling `/continue` to smooch: %s"
                % (passthruResp, passthruResp.content)
            )
        else:
            result = {"statusCode": 200, "body": "message escalated"}
            print(
                "Excecution complete (message passed through) - returning: %s" % result
            )
            return result

    def resetConvo(self, response=None, nonce=None):
        self.updateAppUser({"escalated": False, "flow": False})
        # self.sendMessage(self.responses['reusables'][response])
        if response is not None:
            self.sendResponses(None, response)  # TODO: needed?
        # TODO: re-send welcome message ?
        result = {"statusCode": 200, "body": "escalation/flow flags cleared"}
        print("Escalation unset - returning: %s" % result)
        return result

    def resetFlags(self):
        self.updateAppUser({"escalated": False, "flow": False})
        result = {"statusCode": 200, "body": "escalation/flow flags cleared"}
        print("Escalation unset by resetFlags(); returning: %s" % result)
        return result

    # def sendResponses(self, flow, userText, nonce, data=None, msgType=None):
    def sendResponses(self, userText, nonce=None, data=None, msgType=None):
        print("Starting sendResponses(): '%s'" % (userText))

        results = []
        hitType = None

        if msgType == "formResponse":
            hit = "FORM_RESPOSNE"
            hitType = "responses"
        elif userText in self.responses["responses"].keys():
            # Response keyword in userText
            hit = userText
            hitType = "responses"
        else:
            # No direct response - check for keywords
            for pattern in self.responses["text-matches"].keys():
                if self.responses["text-matches"][pattern][
                    "type"
                ] == "regex" and re.search(pattern, userText, re.IGNORECASE):
                    hit = pattern
                    hitType = "text-matches"
                    break

        if hitType is None:
            # No keyword hit either - use default
            print(
                " > WARNING: Unsupported input %s - using 'default' instead." % userText
            )
            hit = "default"
            hitType = "responses"

        if hitType == "responses":
            resp_list = self.responses[hitType][hit]
        elif hitType == "text-matches":
            resp_list = self.responses[hitType][hit]["responses"]

        for msg in resp_list:  # Iterate responses
            # Process '>>' commands
            cmdArr = msg.split(">>") if type(msg) is str else None
            if cmdArr is not None and len(cmdArr) >= 3 and msg.startswith(">>"):
                print("Processing command: %s" % msg)
                if cmdArr[1] == "do":  # special command
                    if cmdArr[2] == "echo":  # echo user message
                        results.append(self.sendMessage("%s" % userText))
                    elif cmdArr[2] == "reset":  # reset escalation flags
                        results.append(self.resetConvo())
                    elif cmdArr[2] == "escalate":  # escalate to bus.sys.
                        # TODO: check nonce != None; can only handoff from pipeline bot mode
                        results.append(self.escalate(nonce))
                    elif cmdArr[2] == "deescalate":  # deescalate from bus.sys.
                        results.append(self.deescalate())
                    elif cmdArr[2].startswith("sleep"):  # literally, sleep
                        sleep(int(cmdArr[2][5:]))
                        results.append("Slept %ss" % int(cmdArr[2][5:]))
                    elif cmdArr[2].startswith("typing"):  # send typing indicator
                        results.append(
                            self.sendTypingIndicator(0)
                        )  # 0=skip sleep in typing-indicator loop
                    else:  # backend behaviour
                        raise NotImplementedError(
                            "No handling for this 'do' action (yet) in '%s'"
                            % ">>".join(cmdArr)
                        )
                elif cmdArr[1] == "react":  # simulate user input
                    # self.sendResponses(flow, '>>'.join(cmdArr[2:]))
                    results.append(
                        self.sendResponses(
                            ">>".join(cmdArr[2:]).upper(), ">>".join(cmdArr[2:]), nonce
                        )
                    )
                    # TODO: And this was for...?
                elif cmdArr[1] == "msg":  # send reusable message
                    if cmdArr[2] in self.responses["reusables"].keys():
                        # self.sendMessage({"text": "%s" % self.responses['reusables'][cmdArr[2]]})
                        results.append(
                            self.sendMessage(self.responses["reusables"][cmdArr[2]])
                        )
                    else:
                        raise KeyError(
                            "command error: reusable message '%s' not found" % cmdArr[2]
                        )
                else:
                    raise NotImplementedError(
                        "Trying to run unknown command '%s': %s" % (cmdArr[1], msg)
                    )
            else:  # Send scripted response(s)
                # results.append( self.sendMessage( {"text": "%s" % msg} ) )
                results.append(self.sendMessage(msg))

        # TODO: check individual messages succeeded
        result = {"statusCode": 200, "body": str(results)}
        # print(" >> Request:\n%s\n >> Response: %s\n >> Result: %s" % (bodyData, msgPostResp, result))
        return result

    @staticmethod
    def _findLastSeen(clientList):
        # print(" > findLastSeen()...")
        epoch = datetime.utcfromtimestamp(0)  # start at epoch
        lastSeen = epoch
        for client in clientList:
            dt = datetime.strptime(client.last_seen, "%Y-%m-%dT%H:%M:%S.%fZ")
            if dt > lastSeen:
                lastSeen = dt

        if lastSeen == epoch:
            raise Exception(
                "no client with lastSeen > epoch on appUser...(!?)\n%s" % clientList
            )

        return lastSeen

    @staticmethod
    def getUserText(data):
        if "message" in data.keys():
            # postback = None
            if "payload" in data["message"].keys():  # postbacks(?)
                userText = data["message"]["payload"].upper().strip()
            elif "textFallback" in data["message"].keys():
                userText = data["message"]["textFallback"].upper().strip()
            elif "text" in data["message"].keys():
                userText = data["message"]["text"].upper().strip()
            elif "altText" in data["message"].keys():
                userText = data["message"]["altText"].upper().strip()
            return userText
        elif "postback" in data.keys():
            # userText = None
            postback = data["postback"]["action"]["payload"].upper().strip()
            return postback
        else:
            raise Exception("Expecting `message` or `postback` in response")

        # return userText

    @staticmethod
    def getEventTypeOrigin(data):
        # TODO: needed? (reply on presence or not of Nonce?)
        if "nonce" in data.keys():
            evtOrigin = "pipeline"
            # nonce = data['nonce']
        else:
            evtOrigin = "webhook"
            # nonce = None

        evtTrigger = data["trigger"]

        if evtTrigger == "message:appUser":
            evtType = data["message"]["type"]
        elif evtTrigger == "postback":
            evtType = "postback"
        elif evtTrigger == "passthrough:apple:interactive":
            evtType = "applePassthrough"
        else:
            raise ValueError("Unsupported trigger: %s" % evtTrigger)

        return evtType, evtOrigin


def lookupAppInDb(appId):
    # Lookup supported app in table
    dynamodb = resource("dynamodb")
    appsTable = dynamodb.Table(os.environ["appTableName"])
    try:
        response = appsTable.get_item(Key={"appId": appId})
    except ClientError as e:
        print("Table lookup error: %s" % e.response["Error"]["Message"])
        raise e
    else:
        if "Item" in response.keys():
            appCreds = response["Item"]
            # print("GetItem succeeded %s (App %s is subscribed)" % (appCreds, appId))
        else:
            print(" > ERROR: No 'Item' in db response: %s" % response)
            raise ValueError(
                json.dumps(
                    {"statusCode": 403, "body": " > Forbidden: appId not registered!"}
                )
            )

    return appCreds


def pipelineEvent(event, context):
    # global bodyData
    # print("New request: %s" % event)
    bodyData = json.loads(event["body"])
    print("Starting %s with %s" % (inspect.stack()[0][3], bodyData))  # DEV

    # TODO: test required values in payload: {
    #   "": ['trigger', 'app', 'appUser', 'message', 'nonce'],
    #   "app": ['_id'],
    #   "appUser": ['_id'],
    #   "message": ['text']
    # if not test_contents(bodyData, structures['message:appUser']):

    appId = bodyData["app"]["_id"]
    appUserId = bodyData["appUser"]["_id"]
    nonce = bodyData["nonce"] if "nonce" in bodyData.keys() else None

    # get parse event info
    eventType, eventOrigin = mySmooch.getEventTypeOrigin(bodyData)

    # Lookup supported app in table
    appCreds = lookupAppInDb(appId)

    # Verify webhook signature
    if (
        "X-API-Key" not in event["headers"].keys()
        or event["headers"]["X-API-Key"] != appCreds["processorSecret"]
    ):
        print(
            " %s == %s" % (event["headers"]["X-API-Key"], appCreds["processorSecret"])
        )
        print(
            "Types: %s, %s"
            % (type(event["headers"]["X-API-Key"]), type(appCreds["processorSecret"]))
        )
        result = {"statusCode": 400, "body": " > Bad Request"}
        print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
        return result

    # Configure API key authorization (alternative): jwt
    smoochApi = mySmooch(appId, appCreds["JWT"], appUserId)

    # TODO: check escalation flag + timestamp
    properties, lastSeen = smoochApi.getAppUserInfo()
    print("appUser properties: %s" % properties)  # DEV
    # if 'flow' not in properties.keys():
    #     properties['flow'] = ""

    # Check/clear escalation state
    userText = smoochApi.getUserText(bodyData)
    if "escalated" in properties.keys() and properties["escalated"]:
        if lastSeen < (
            datetime.utcnow() - timedelta(hours=1)
        ):  # >1h inactive, reset escalation state
            print(smoochApi.resetFlags())
        elif userText in smoochApi.responses["deescalationKeywords"]:
            # Process master keywords
            return smoochApi.sendResponses(userText, nonce, msgType=eventType)
        else:  # Continue escalation
            return smoochApi.passthroughEscalated(nonce)

    return smoochApi.sendResponses(userText, nonce, msgType=eventType)


def applePassthroughEvent(event, context):
    bodyData = json.loads(event["body"])
    print("Starting %s with %s" % (inspect.stack()[0][3], bodyData))  # DEV

    # TODO: test required values in payload: {
    #   "": ['trigger', 'app', 'appUser', 'message', 'nonce'],
    #   "app": ['_id'],
    #   "appUser": ['_id'],
    #   "message": ['text']
    # if not test_contents(bodyData, structures['message:appUser']):

    appId = bodyData["app"]["_id"]
    appUserId = bodyData["appUser"]["_id"]

    # get parse event info
    eventType, eventOrigin = mySmooch.getEventTypeOrigin(bodyData)

    # Lookup supported app in table
    appCreds = lookupAppInDb(appId)

    # Verify webhook signature
    if (
        "X-API-Key" not in event["headers"].keys()
        or event["headers"]["X-API-Key"] != appCreds["webhookSecret"]
    ):
        print(
            " Error: %s != %s"
            % (event["headers"]["X-API-Key"], appCreds["webhookSecret"])
        )
        print(
            "Types: %s, %s"
            % (type(event["headers"]["X-API-Key"]), type(appCreds["webhookSecret"]))
        )
        result = {"statusCode": 400, "body": " > Bad Request"}
        print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
        return result

    if eventType != "applePassthrough":
        result = {"statusCode": 400, "body": " > Bad Request: %s" % eventType}
        print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
        return result

    # Configure API key authorization (alternative): jwt
    smoochApi = mySmooch(appId, appCreds["JWT"], appUserId)

    payload_apple = bodyData["payload"]["apple"]
    if "interactiveDataRef" in payload_apple.keys():
        # getRefPayload(payload_apple['interactiveDataRef'], payload_apple['id'])
        raise NotImplementedError("interactiveDataRef")
    elif "interactiveData" in payload_apple.keys():
        requestIdent = payload_apple["interactiveData"]["data"]["requestIdentifier"]
        if requestIdent == "list-picker":
            # if len(payload_apple["interactiveData"]["data"]["listPicker"][
            #     "sections"
            # ])>1:
            #     raise NotImplementedError
            selectedOption = payload_apple["interactiveData"]["data"]["listPicker"][
                "sections"
            ][0]["items"][0]["identifier"]
            print("543: %s" % selectedOption)
        elif requestIdent == "time-picker":
            eventId = payload_apple["interactiveData"]["data"]["event"]["identifier"]
            if len(payload_apple["interactiveData"]["data"]["event"]["timeslots"]) > 1:
                raise ValueError(
                    "Expecting a single event, got: ",
                    payload_apple["interactiveData"]["data"]["event"]["timeslots"],
                )
            selectedOption = payload_apple["interactiveData"]["data"]["event"][
                "timeslots"
            ][0]["identifier"]
            # << identifiers stripped for simplicity>>
            # { "type": "interactive",
            #     "locale": "en_CA",
            #     "interactiveData": {
            #         "data": {
            #             "requestIdentifier": "appointment-selector",
            #             "replyMessage": {
            #                 "title": "Feb 24, 2023 at 05:00",
            #                 "style": "icon",
            #                 "alternateTitle": "Feb 24, 2023 at 05:00",
            #             },
            #             "event": {
            #                 "timeslots": [ {
            #                         "identifier": "7am UTC",
            #                         "duration": 3600,
            #                         "startTime": "2023-02-24T10:00+0000",
            #                 } ],
            #                 "identifier": "reservation-id",
            #                 "title": "Available Reservations",
            #                 "timezoneOffset": -300,
            #             },
            #             "receivedMessage": {
            #                 "title": "Book an agent (options are 10, and 14 UTC)",
            #                 "style": "icon",
            #             },
            #         },
            #     },
            # }
        elif requestIdent == "quick-replies":
            selectedIndex = payload_apple["data"]["quick-reply"]["selectedIndex"]
            selectedOption = payload_apple["data"]["quick-reply"]["items"][
                selectedIndex
            ]["identifier"]
            print("547: %s" % selectedOption)
            # << identifiers stripped >>
            # { "quick-reply":
            #     {   "items": [
            #             {"identifier": "1", "title": "Watch our video"},
            #             {"identifier": "2", "title": "Ask for office hours"},
            #             {"identifier": "3", "title": "Find more about pet adoption"},
            #             {"title": "Talk to an agent", "identifier": "4"}, ],
            #         "selectedIndex": 3,
            #         "selectedIdentifier": "4", },
            #     "requestIdentifier": "quick-replies",
            # }
        else:
            raise NotImplementedError("unexpected payload\n", payload_apple)

        return smoochApi.sendResponses(selectedOption.upper())
    else:
        result = {"statusCode": 400, "body": " > Bad Request: 539"}
        print(" >> Request:\n%s\n >> Result: %s" % (bodyData, result))
        return result


def linter_smoketest():
    purposely_unused_variable = None
