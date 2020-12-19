import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)


class Player():

    def __init__(self):
        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def is_alone(position):
        characters = self.game_state["characters"]
        population = 0
        for character in characters:
            if position == character["position"]:
                population += 1
        return (0 if population >= 2 else 1)

    def split_characters(self):
        # will get the manifestable character and the other in two array in order to define our inspector and fantom strategy
        manifestable = []
        not_manifestable = []
        characters = self.game_state["characters"]
        shadow_room = self.game_state["shadow"]
        for character in characters:
            if character["position"] in shadow_room or self.is_alone(character["position"]) == 1:
                manifestable.append(character)
            else:
                not_manifestable.append(character)
        print(manifestable)
        print(not_manifestable)
        print(game_state["characters"])
        return 0

    def select_character(self):
        return random.randint(0, len(data)-1)

    def move(self):

        return 0
    
    def answer(self, question):
        # work
        self.data = question["data"]
        self.game_state = question["game state"]
        self.question_type = question["question type"]

        if question_type == "select character":
            splited_characters = self.split_characters()
            response_index = self.select_character()
        elif question_type == "select position":
            response_index = self.move()
        elif "activate" in question_type == True:
            response_index = 0
        else:
            response_index = random.randint(0, len(data)-1)

        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {self.question_type}")
        fantom_logger.debug(f"data -------------- {self.data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {self.data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()

p.run()
