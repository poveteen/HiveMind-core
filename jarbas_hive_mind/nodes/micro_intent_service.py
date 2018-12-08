from adapt.engine import IntentDeterminationEngine
from adapt.intent import Intent

from jarbas_hive_mind.utils.log import LOG


def open_intent_envelope(message):
    """ Convert dictionary received over messagebus to Intent. """
    intent_dict = message.data
    return Intent(intent_dict.get('name'),
                  intent_dict.get('requires'),
                  intent_dict.get('at_least_one'),
                  intent_dict.get('optional'))


def normalize(text, remove_articles=True, lang="en-us"):
    """ English string normalization """

    words = text.split()  # this also removed extra spaces
    normalized = ""
    for word in words:
        if remove_articles and word in ["the", "a", "an"]:
            continue

        # Expand common contractions, e.g. "isn't" -> "is not"
        contraction = ["ain't", "aren't", "can't", "could've", "couldn't",
                       "didn't", "doesn't", "don't", "gonna", "gotta",
                       "hadn't", "hasn't", "haven't", "he'd", "he'll",
                       "he's",
                       "how'd", "how'll", "how's", "I'd", "I'll", "I'm",
                       "I've", "isn't", "it'd", "it'll", "it's",
                       "mightn't",
                       "might've", "mustn't", "must've", "needn't",
                       "oughtn't",
                       "shan't", "she'd", "she'll", "she's", "shouldn't",
                       "should've", "somebody's", "someone'd",
                       "someone'll",
                       "someone's", "that'll", "that's", "that'd",
                       "there'd",
                       "there're", "there's", "they'd", "they'll",
                       "they're",
                       "they've", "wasn't", "we'd", "we'll", "we're",
                       "we've",
                       "weren't", "what'd", "what'll", "what're", "what's",
                       "whats",
                       # technically incorrect but some STT outputs
                       "what've", "when's", "when'd", "where'd", "where's",
                       "where've", "who'd", "who'd've", "who'll", "who're",
                       "who's", "who've", "why'd", "why're", "why's",
                       "won't",
                       "won't've", "would've", "wouldn't", "wouldn't've",
                       "y'all", "ya'll", "you'd", "you'd've", "you'll",
                       "y'aint", "y'ain't", "you're", "you've"]
        if word in contraction:
            expansion = ["is not", "are not", "can not", "could have",
                         "could not", "did not", "does not", "do not",
                         "going to", "got to", "had not", "has not",
                         "have not", "he would", "he will", "he is",
                         "how did",
                         "how will", "how is", "I would", "I will", "I am",
                         "I have", "is not", "it would", "it will",
                         "it is",
                         "might not", "might have", "must not",
                         "must have",
                         "need not", "ought not", "shall not", "she would",
                         "she will", "she is", "should not", "should have",
                         "somebody is", "someone would", "someone will",
                         "someone is", "that will", "that is",
                         "that would",
                         "there would", "there are", "there is",
                         "they would",
                         "they will", "they are", "they have", "was not",
                         "we would", "we will", "we are", "we have",
                         "were not", "what did", "what will", "what are",
                         "what is",
                         "what is", "what have", "when is", "when did",
                         "where did", "where is", "where have",
                         "who would",
                         "who would have", "who will", "who are", "who is",
                         "who have", "why did", "why are", "why is",
                         "will not", "will not have", "would have",
                         "would not", "would not have", "you all",
                         "you all",
                         "you would", "you would have", "you will",
                         "you are not", "you are not", "you are",
                         "you have"]
            word = expansion[contraction.index(word)]

        normalized += " " + word

    return normalized[1:]  # strip the initial space


class MicroIntentService(object):

    def __init__(self, ws):
        self.intent_map = {}
        self.skills_map = {}
        self.vocab_map = {}
        self.engine = IntentDeterminationEngine()
        self.bus = ws
        self.bus.on('register_vocab', self.handle_register_vocab)
        self.bus.on('register_intent', self.handle_register_intent)
        self.bus.on('recognizer_loop:utterance', self.handle_utterance)
        self.bus.on('detach_intent', self.handle_detach_intent)
        self.bus.on('detach_skill', self.handle_detach_skill)
        self.bus.on("mycroft.skills.loaded", self.handle_skill_load)
        self.bus.on("mycroft.skills.shutdown", self.handle_skill_shutdown)

    def handle_utterance(self, message):
        pass

    def handle_register_vocab(self, message):
        start_concept = message.data.get('start')
        end_concept = message.data.get('end')
        regex_str = message.data.get('regex')
        alias_of = message.data.get('alias_of')
        if regex_str:
            self.engine.register_regex_entity(regex_str)
        else:
            if start_concept:
                self.vocab_map[start_concept] = end_concept
            self.engine.register_entity(
                start_concept, end_concept, alias_of=alias_of)

    def handle_register_intent(self, message):
        intent = open_intent_envelope(message)
        self.engine.register_intent_parser(intent)
        skill_id, intent = message.data.get("name", "None:None").split(":")
        LOG.info("Registered: " + intent)
        if skill_id not in self.intent_map.keys():
            self.intent_map[skill_id] = []
        self.intent_map[skill_id].append(intent)

    def handle_detach_intent(self, message):
        intent_name = message.data.get('intent_name')
        new_parsers = [
            p for p in self.engine.intent_parsers if p.name != intent_name]
        self.engine.intent_parsers = new_parsers
        skill_id, intent = intent_name.split(":")
        self.intent_map[skill_id].pop(intent)

    def handle_detach_skill(self, message):
        skill_id = message.data.get('skill_id')
        new_parsers = [
            p for p in self.engine.intent_parsers if
            not p.name.startswith(skill_id)]
        self.engine.intent_parsers = new_parsers
        self.intent_map.pop(skill_id)

    def handle_skill_shutdown(self, message):
        name = message.data.get("name")
        id = message.data.get("id")
        self.skills_map[id] = name

    def handle_skill_load(self, message):
        id = message.data.get("id")
        self.skills_map.pop(id)

    def get_skills_map(self, lang="en-us"):
        return self.skills_map

    def get_intent_map(self, lang="en-us"):
        return self.intent_map

    def get_vocab_map(self, lang="en-us"):
        return self.vocab_map

    def get_intent(self, utterance, lang="en-us"):
        best_intent = None
        try:
            # normalize() changes "it's a boy" to "it is boy", etc.
            best_intent = next(self.engine.determine_intent(
                normalize(utterance, lang), 100, include_tags=True))
            best_intent['utterance'] = utterance
        except Exception as e:
            LOG.exception(e)

        if best_intent and best_intent.get('confidence', 0.0) > 0.0:
            return best_intent
        else:
            return None

    def shutdown(self):
        self.bus.remove("mycroft.skills.loaded", self.handle_skill_load)
        self.bus.remove("mycroft.skills.shutdown", self.handle_skill_shutdown)
