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

passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
# ways for the pink character
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]
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
        self.selected_room = 0
        self.data = []
        self.game_state = []
        self.question_type = []

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def is_alone(self, position):
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
        innocent_manifestable = []
        innocent_not_manifestable = []
        characters = self.game_state["characters"]
        shadow_room = self.game_state["shadow"]
        for character in characters:
            if (character["position"] == shadow_room or self.is_alone(character["position"]) == 1):
                if character["suspect"] == True: 
                    manifestable.append(character)
                else:
                    innocent_manifestable.append(character)
            else:
                if character["suspect"] == True: 
                    not_manifestable.append(character)
                else:
                    innocent_manifestable.append(character)
        splited_characters = {
            "manifestable" : manifestable,
            "not_manifestable" : not_manifestable,
            "innocent_manifestable": innocent_manifestable
        }
        return splited_characters

    # the aim for the fantom player is to put the fantom character in the biggest pool of manifestable or not_manifestable (suspect)
    # in order to get the maximum amount of suspect in all time
    def get_character_possible_movement(self, character):
        if charact["color"] == "pink":
            active_passages = pink_passages
        else:
            active_passages = passages
        return [room for room in active_passages[character["position"]] if set([room, character["position"]]) != set(self.game_state["blocked"])]

    def is_room_manifestable(self, room):
        # room are manifestable and not_manifestable
        # a manifestable room is a room with the shadow or with only one person in it
        if self.game_state["shadow"] == room:
            return True
        characters = self.game_state["characters"]
        for character in characters:
            if room == character["position"]:
                return False
        return True

    def select_character(self):
        # in the fantom case, we want to avoid the fifty fifty situation
        splited_characters = self.split_characters()
        chooseable_character = self.data
        biggest_pool = []
        smallest_pool = []
        if (len(splited_characters["manifestable"]) < len(splited_characters["not_manifestable"])):
            biggest_pool = "not_manifestable"
            smallest_pool = "manifestable"
        else:
            biggest_pool = "manifestable"
            smallest_pool = "not_manifestable"

        for character in chooseable_character:
            if character in splited_characters[smallest_pool]:
                possible_movement = self.get_character_possible_movement(character)
                for room in possible_movement:
                    if (self.is_room_manifestable(room) and biggest_pool == "manifestable") or
                        (self.is_room_manifestable(room) == False and biggest_pool == "not_manifestable"):
                        self.selected_room = room
                        return character
        # faire en sorte de bouger les innocent pour desiquilibrer les pool
        return chooseable_character[0]

    def move(self):

        return 0
    
    def answer(self, question):
        # work
        self.data = question["data"]
        self.game_state = question["game state"]
        self.question_type = question["question type"]
        if self.question_type == "select character":
            selected_character = self.select_character()
            i = 0
            for character in self.data:
                if selected_character == character:
                    response_index = i
                    break
                i += 1
        elif self.question_type == "select position":
            i = 0
            for room in self.data:
                if self.selected_room == room:
                    response_index = i
                    break
                i += 1
            self.selected_room = 0
        elif "activate" in self.question_type:
            response_index = 0
        else:
            response_index = random.randint(0, len(self.data)-1)

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
