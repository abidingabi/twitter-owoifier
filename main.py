import json
import logging
import random
import re

import tweepy

CONFIG_PATH = "config.json"
LOG_LEVEL = logging.ERROR


def read_config(config_path):
    with open(config_path) as config_file:
        return json.load(config_file)


logging.basicConfig(level=LOG_LEVEL)

# see https://docs.tweepy.org/en/stable/authentication.html#legged-oauth
# for generating access token; can be done in a repl
config = read_config(CONFIG_PATH)


def owoify(text):
    substitutions = [
        ("nixos", "nixowos"),
        ("NixOS", "NixOwOs"),
        ("rust", "ruwust"),
        ("Rust", "rUwUst"),
        ("r|l", "w"),
        ("R|L", "W"),
        ("n(?=[aeiouAEIOU])(?![xX])", "ny"),
        ("N(?=[aeiouAEIOU])(?![xX])", "Ny"),
        ("ove", "uv"),
    ]

    faces = ["(・`ω´・)", ";;w;;", "owo", "UwU", ">w<", "^w^"]

    for substitution in substitutions:
        text = re.sub(substitution[0], substitution[1], text)

    text = re.sub("!+", random.choice(faces), text)

    return text


class OwOifierClient(tweepy.StreamingClient):
    def save_tweeting_clients(self, tweeting_clients):
        self.tweeting_clients = tweeting_clients

    def on_response(self, response):
        tweet = response.data

        if tweet.referenced_tweets:  # retweet or quote retweet
            return

        clients = [self.tweeting_clients[rule.id] for rule in response.matching_rules]

        owofied_text = owoify(tweet.text)

        for client in clients:
            client.create_tweet(quote_tweet_id=tweet.id, text=owofied_text)

    def on_errors(self, errors):
        pass

    def on_connection_error(self):
        pass


client = OwOifierClient(config["bearer_token"])

rules_correct = len(client.get_rules().data) == len(config["owo_targets"])

if not rules_correct:
    client.delete_rules([rule.id for rule in client.get_rules().data])

tweeting_clients = {}

for target in config["owo_targets"]:
    tweeting_clients[target["id"]] = tweepy.Client(
        consumer_key=config["api_key"],
        consumer_secret=config["api_key_secret"],
        access_token=target["access_token"],
        access_token_secret=target["access_token_secret"],
    )

    if not rules_correct:
        client.add_rules(
            tweepy.StreamRule(
                f"({target['stream_rule']}) -is:retweet -is:reply -is:quote"
            )
        )

print("Rules: ")
print(client.get_rules())

client.save_tweeting_clients(tweeting_clients)
client.filter(threaded=True)
