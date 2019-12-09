import logging
from threading import Thread

from jarbas_hive_mind.nodes.flask.base import get_app, noindex, donation, requires_auth, request, nice_json, start
from jarbas_hive_mind.utils.messagebus.message import Message
from jarbas_hive_mind.utils.messagebus.ws import WebsocketClient

platform = "FlaskHiveNodev0.1"
LOG = logging.getLogger(platform)
LOG.setLevel("INFO")

app = get_app()
ws = None
answers = {}
users_on_hold = {}
timeout = 60


def connect():
    global ws
    ws.run_forever()


@app.route("/ask/<lang>/<utterance>", methods=['PUT', 'GET'])
@noindex
@donation
@requires_auth
def ask(utterance, lang="en-us"):
    global users_on_hold, answers
    ip = request.remote_addr
    user = request.headers["Authorization"]
    data = {"utterances": [utterance], "lang": lang}
    user_id = str(ip) + ":" + str(user)
    LOG.info("[IP] " + ip + " [UTTERANCE] " + utterance)
    context = {"source": user_id,
               "destination": "skills",
               "platform": platform}
    message = Message("recognizer_loop:utterance", data, context)
    # clean prev answer # TODO figure out how to answer both, timestamps?
    if user_id in answers:
        answers.pop(user_id)
    users_on_hold[user_id] = False
    answers[user_id] = None
    # emit message
    ws.emit(message)
    result = {"status": "processing"}
    return nice_json(result)


@app.route("/get_answer", methods=['GET', 'PUT'])
@noindex
@donation
@requires_auth
def get_answer():
    global users_on_hold, answers
    ip = request.remote_addr
    user = request.headers["Authorization"]
    user_id = str(ip) + ":" + str(user)
    if users_on_hold.get(user_id, False):
        # if answer is ready
        LOG.info("[ANSWER READY] " + ip)
        answer = Message("speak", answers[user_id]["data"], answers[
            user_id]["context"]).serialize()
        users_on_hold.pop(user_id)
        answers.pop(user_id)
        result = {"status": "done", "answer": answer}
    else:
        LOG.info("[PROCESSING ANSWER] " + ip)
        result = {"status": "processing"}
    return nice_json(result)


@app.route("/cancel", methods=['GET', 'PUT'])
@noindex
@donation
@requires_auth
def cancel_answer():
    global users_on_hold, answers
    ip = request.remote_addr
    user = request.headers["Authorization"]
    user_id = str(ip) + ":" + str(user)
    if user_id in list(users_on_hold.keys()):
        LOG.info("[CANCEL REQUEST] " + ip)
        users_on_hold.pop(user_id)
        answers.pop(user_id)
    result = {"status": "canceled"}
    return nice_json(result)


def listener(message):
    ''' listens for speak messages and checks if we are supposed to send it to some user '''
    global users_on_hold, answers
    message.context = message.context or {}
    user = message.context.get("destination", "")
    if user in list(
            users_on_hold.keys()):  # are we waiting to answer this user?

        if answers[user] is not None:
            # update data and context
            for k in list(message.context.keys()):
                answers[user]["context"][k] = message.context[k]
            for k in list(message.data.keys()):
                # update utterance
                if k == "utterance":
                    answers[user]["data"]["utterance"] = \
                        answers[user]["data"]["utterance"] + ". " + \
                        message.data["utterance"]
                else:
                    answers[user]["data"][k] = message.data[k]
        else:
            # create answer
            answers[user] = {"data": message.data,
                             "context": message.context}


def end_wait(message):
    ''' stop capturing answers for this user '''
    global users_on_hold, answers
    user = message.context.get("destination", "")
    if user in list(users_on_hold.keys()):
        LOG.info("[REQUEST COMPLETE] " + user.split(":")[0])
        # mark as answered
        users_on_hold[user] = True
        # process possible failure scenarios
        context = {}
        if message.type == "complete_intent_failure":

            answers[user] = {"data": {"utterance": "does not compute"},
                             "context": context}
        # no answer but end of handler
        elif answers[user] is None:
            answers[user] = {"data": {"utterance": "something went wrong, "
                                                   "ask me later"},
                             "context": context}


def launch(config=None):
    global app, ws, timeout
    config = config or {}
    # connect to internal mycroft
    ws = WebsocketClient()
    ws.on("mycroft.skill.handler.complete", end_wait)
    ws.on("complete_intent_failure", end_wait)
    ws.on("speak", listener)
    event_thread = Thread(target=connect)
    event_thread.setDaemon(True)
    event_thread.start()
    port = config.get("port", 6712)
    timeout = config.get("timeout", timeout)
    start(app, port)


if __name__ == "__main__":
    launch()
