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
set up inspector logging
"""
inspector_logger = logging.getLogger()
inspector_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/inspector.log"):
    os.remove("./logs/inspector.log")
file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
inspector_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
inspector_logger.addHandler(stream_handler)


class Player():

    def __init__(self):

        self.end = False
        # self.old_question = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.selected_room = 10
        self.data = []
        self.game_state = []
        self.question_type = []

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()
    def is_alone(self, position, characters):
        population = 0
        for character in characters:
            if position == character["position"]:
                population += 1
        return (True if population == 1 else False)

    def split_characters(self, characters):
        # will get the manifestable character and the other in two array in order to define our inspector and fantom strategy
        manifestable = []
        not_manifestable = []
        innocent = []
        shadow_room = self.game_state["shadow"]

        for character in characters:
            if (character["suspect"] == True and (character["position"] == shadow_room or self.is_alone(character["position"], characters) == True)):
                manifestable.append(character)
            elif (character["suspect"] == True and (character["position"] != shadow_room and self.is_alone(character["position"], characters) != True)):
                not_manifestable.append(character)
            else:
                innocent.append(character)
        splited_characters = {
            "manifestable" : manifestable,
            "not_manifestable" : not_manifestable,
            "innocent": innocent
            }
        return splited_characters

    # the aim for the fantom player is to put the fantom character in the biggest pool of manifestable or not_manifestable (suspect)
    # in order to get the maximum amount of suspect in all time
    def get_character_possible_movement(self, character):
        if character["color"] == "pink":
            active_passages = pink_passages
        else:
            active_passages = passages
        return [room for room in active_passages[character["position"]] if set([room, character["position"]]) != set(self.game_state["blocked"])]

    def get_adjacent_positions_from_position(self, position, charact):
        if charact["color"] == "pink":
            active_passages = pink_passages
        else:
            active_passages = passages
        return [room for room in active_passages[position] if set([room, position]) != set(self.game_state["blocked"])]

    def get_character_movement(self, character):
        # stolen from the server
        characters_in_room = [q for q in self.game_state["characters"] if q["position"] == character["position"]]
        number_of_characters_in_room = len(characters_in_room)

        available_rooms = list()
        available_rooms.append(self.get_character_possible_movement(character))
        for step in range(1, number_of_characters_in_room):
            next_rooms = list()
            for room in available_rooms[step-1]:
                next_rooms += self.get_adjacent_positions_from_position(room, character)
            available_rooms.append(next_rooms)

        temp = list()
        for sublist in available_rooms:
            for room in sublist:
                temp.append(room)

        temp = set(temp)
        available_positions = list(temp)

        return available_positions

    def select_character(self):
        splited_characters = self.split_characters(self.game_state["characters"])

        chooseable_character = self.data
        suspects = []
        biggest_pool = []
        smallest_pool = []
        if (len(splited_characters["manifestable"]) < len(splited_characters["not_manifestable"])):
            biggest_pool = "not_manifestable"
            smallest_pool = "manifestable"
        else:
            biggest_pool = "manifestable"
            smallest_pool = "not_manifestable"
        char_index = 0
        for character in chooseable_character:
            possible_movement = self.get_character_movement(character)
            move_index = 0
            for room in possible_movement:
                temp = []
                for charact in self.game_state["characters"]:
                    temp.append(dict(charact))
                for charact in temp:
                    if charact["color"] == character["color"]:
                        charact.update({"position": room})
                length = 0
                splited_characters = self.split_characters(temp)
               
                length = len(splited_characters["manifestable"]) - len(splited_characters["not_manifestable"])
                suspects.append({"char_color": character["color"],"char_index": char_index, "move_index": move_index, "nb_suspects": abs(length)})
                move_index += 1
            char_index += 1   
        best_choice = min(suspects, key=lambda x:x["nb_suspects"])
        self.selected_room = best_choice["move_index"]
        return best_choice["char_index"]
    def answer(self, question):
        # work
        self.data = question["data"]
        self.game_state = question["game state"]
        self.question_type = question["question type"]
        if self.question_type == "select character":
            response_index = self.select_character()
        elif self.question_type == "select position":
            response_index = self.selected_room
        elif "activate" in self.question_type:
            response_index = 0
        else:
            response_index = random.randint(0, len(self.data)-1)
        inspector_logger.debug("|\n|")
        inspector_logger.debug("inspector answers")
        inspector_logger.debug(f"question type ----- {question['question type']}")
        inspector_logger.debug(f"data -------------- {self.data}")
        inspector_logger.debug(f"response index ---- {response_index}")
        inspector_logger.debug(f"response ---------- {self.data[response_index]}")
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
