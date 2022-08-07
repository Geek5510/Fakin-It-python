import time
from abc import ABC, abstractmethod
import random

"""
=== Server phases ===
"""

num_game_rounds = 0  # Game rounds that have passed
min_players = 4  # Minimum amount of players for a game


class Phase(ABC):
    """
        Abstract class to represent server phases
    """
    def __init__(self, server_comm, instruct_q):
        self.server_comm = server_comm  # Access to the server communication
        self.instruct_q = instruct_q  # Instruction queue for main server program

    @abstractmethod
    def process_queue(self):
        """
        Processes waiting messages in server comm queue
        """
        pass

    def on_disconnect(self):
        """
        Gets called when approved client disconnects
        :return:
        """
        pass

    def _enough_to_continue(self):
        """
        Returns True if there are enough players to continue if not returns False brings back players to lobby
        Gets called in specific phases when player disconnects
        """
        flag = True
        if len(self.server_comm.open_clients) < min_players:  # Are there enough to continue
            flag = False
            self.instruct_q.put("BACK TO LOBBY")  # Sending the server and all clients back to lobby
            global num_game_rounds
            num_game_rounds = 0  # Resetting the game rounds
        return flag

    def _get_next_msg(self):
        """
            returns a tuple of info about the current received message
            tuple is built this way: (sender sock, message code, message body -(can be None if the message is empty) )
        """
        msg = self.server_comm.msg_q.get()
        sender_sock = msg[0]
        # Getting the message code
        msg = msg[1]
        msg_code = msg[0]
        if len(msg) > 1:
            msg = msg[1:]
        else:
            msg = None
        rtr = (sender_sock, msg_code, msg)
        return rtr


class ConnectingAndLobby(Phase):
    """
    Connecting and lobby phase, default starting phase
    """
    def __init__(self, server_comm, instruct_q):
        Phase.__init__(self, server_comm, instruct_q)

    def process_queue(self):
        # Iterating through all messages sent from clients
        while not self.server_comm.msg_q.empty():
            (sender_sock, msg_code, msg) = self._get_next_msg()
            # Updating ready status of players
            if msg_code == "R":  # A client changed his ready status
                if msg == "Y":  # To True
                    self.server_comm.open_clients[sender_sock].ready = True
                if msg == "N":  # To False
                    self.server_comm.open_clients[sender_sock].ready = False
                # Calling the update ready method only if the status of one of the players changed
                self.update_ready()

    def update_ready(self):
        """
        Updates the ready status of the game, only gets called when ready status of a player changes
        :return:
        """
        p_list = self.server_comm.open_clients.values()  # Getting a list of all players
        cur_ready = True
        if len(p_list) >= min_players:  # Making sure there are enough connected players
            for player in p_list:
                # Checking if all players are ready
                cur_ready = cur_ready and player.ready
                if not cur_ready:
                    break
        else:
            cur_ready = False

        if cur_ready:
            # If all are ready we start the first round
            self.instruct_q.put("START NEW ROUND")


class ChooseCategory(Phase):
    """
    Choosing category phase, chooses a random player that hasn't chosen a category and receives category from them
    """
    def __init__(self, server_comm, instruct_q):
        Phase.__init__(self, server_comm, instruct_q)
        self.chosen_sock = None  # Socket chosen to pick category

    def process_queue(self):
        # Iterating through all messages sent from clients
        while not self.server_comm.msg_q.empty():
            (sender_sock, msg_code, msg) = self._get_next_msg()
            if msg_code == "C" and sender_sock is self.chosen_sock:  # If the chosen user picked a category
                if msg == "POINT" or msg == "NUMBER" or msg == "RAISE":  # If the chosen category is valid
                    # Instructing the main program to switch to according game round
                    self.instruct_q.put("ROUND " + msg[0])

    def on_disconnect(self):
        # Checking if there are enough players to continue
        if self._enough_to_continue():
            # Checking if disconnected player was the category chooser
            if self.chosen_sock not in self.server_comm.open_clients.keys():
                # If it was we pick a different one
                self.start_phase()
            # Else we continue as normal

    def _choose_player_for_category(self):
        """
        Internal method, chooses a random player that hasn't picked yet to pick category
        :return:
        """
        # Creating a list of all available players to pick a category
        available = []
        for player in self.server_comm.open_clients.keys():
            if not self.server_comm.open_clients[player].chose_category:
                # If player has not picked a category yet we add it to the list
                available.append(self.server_comm.open_clients[player])

        if not len(available) == 0:  # Making sure there are available players in the case of a disconnect

            # Choosing a random player to pick category
            chosen = random.choice(available)
        else:
            # Just picking a random socket to be the faker
            chosen = random.choice(list(self.server_comm.open_clients.keys()))

        # Updating the chosen player's variables
        chosen.chose_category = True
        # Getting the socket from the chosen user
        reverse = {v: k for k, v in self.server_comm.open_clients.items()}
        self.chosen_sock = reverse[chosen]

    def start_phase(self):
        """
        Method to call when starting the category phase, initializes the phase variables
        """
        self._choose_player_for_category()
        chosen_username = self.server_comm.open_clients[self.chosen_sock].username
        # Sending a message to all players telling them who is the chosen player
        self.server_comm.send_all_exl("C&" + chosen_username, self.chosen_sock)
        # Telling the chosen socket he is the category chooser
        self.server_comm.send_one("CY", self.chosen_sock)


class Round(Phase):
    """
    Class for game rounds - task setting and voting
    """
    def __init__(self, server_comm, instruct_q, task_db):
        Phase.__init__(self, server_comm, instruct_q)
        # === Task variables ===
        self.task_db = task_db  # Access to the task database
        # Ids of tasks that were already chosen
        self.picked_id_point = []
        self.picked_id_number = []
        self.picked_id_raise = []

        self.faker = (None, None)  # Socket and username of faker
        self.task_counter = 0      # Task counter
        self.is_in_voting = False  # is in voting
        self.cur_category = ""     # Keeps track of current category
        self.cur_task = ""         # Current task

    # === Methods to start round by category ====
    def start_round_point(self):
        # Choosing random task until getting one we haven't picket yet
        self.is_in_voting = False
        task = self.task_db.task_point()  # Getting random task from database
        while task[0] in self.picked_id_point:  # Until we get a task we haven't picked yet
            task = self.task_db.task_point()
        self.picked_id_point.append(task[0])  # Adding the chosen id to the picked id list
        self.cur_task = task[1]
        # Sending the first task
        self._send_task("P")  # "P" Prefix for point rounds
        self.task_counter += 1  # Incrementing task counter

    def start_round_number(self):
        # Choosing random task until getting one we haven't picket yet
        self.is_in_voting = False
        task = self.task_db.task_number()  # Getting random task from database
        while task[0] in self.picked_id_number:  # Until we get a task we haven't picked yet
            task = self.task_db.task_number()
        self.picked_id_number.append(task[0])  # Adding the chosen id to the picked id list
        self.cur_task = task[1]
        # Sending the first task
        self._send_task("N")  # "N" Prefix for number rounds
        self.task_counter += 1  # Incrementing task counter

    def start_round_raise(self):
        # Choosing random task until getting one we haven't picket yet
        self.is_in_voting = False
        task = self.task_db.task_raise()  # Getting random task from database
        while task[0] in self.picked_id_raise:  # Until we get a task we haven't picked yet
            task = self.task_db.task_raise()
        self.picked_id_raise.append(task[0])  # Adding the chosen id to the picked id list
        self.cur_task = task[1]
        # Sending the first task
        self._send_task("R")  # "R" Prefix for raise rounds
        self.task_counter += 1  # Incrementing task counter

    def choose_faker(self):
        """
        Chooses random socket to be the faker
        """
        # Choosing a random socket to be the faker
        faker_sock = random.choice(list(self.server_comm.open_clients.keys()))
        # Getting the socket's associated username for voting purposes
        faker_user = self.server_comm.open_clients[faker_sock].username
        self.faker = (faker_sock, faker_user)

    def _send_task(self, prefix):
        """
        Sends task to all players except faker (Sending tasks uses encryption to prevent cheating)
        :param prefix: prefix of specific round
        """
        # Sending a message to all players but the faker
        self.server_comm.send_all_exl_encrypted("T" + prefix + self.cur_task, self.faker[0])
        # Sending a message to the faker
        self.server_comm.send_one_encrypted("T" + prefix + "You are the faker!  try to blend in...", self.faker[0])

    def process_queue(self):
        # Iterating through all messages sent from clients
        while not self.server_comm.msg_q.empty():
            (sender_sock, msg_code, msg) = self._get_next_msg()
            if msg_code == "A" and not self.is_in_voting:  # Answer to a task
                self.server_comm.open_clients[sender_sock].current_ans = msg  # Updating answer stored for player

                # Checking if all players have answered
                all_ans = True
                for player in self.server_comm.open_clients.values():
                    if player.current_ans == "":
                        all_ans = False
                        break
                if all_ans:
                    # If everybody answered we continue to the voting round
                    self._goto_voting()
                    self._reset_player_answers()

            elif msg_code == "V" and self.is_in_voting:  # Vote from voting round:
                self.server_comm.open_clients[sender_sock].current_ans = msg  # Updating vote stored for player
                # Checking if all players have voted
                all_vote = True
                for player in self.server_comm.open_clients.values():
                    if player.current_ans == "":
                        all_vote = False
                        break
                if all_vote:
                    # If everybody answered we continue to the result of the vote
                    self._goto_results()

    def on_disconnect(self):
        # Checking if there are enough players to continue
        if self._enough_to_continue():
            # Checking if disconnected player was the faker
            if self.faker[0] not in self.server_comm.open_clients.keys():
                self.choose_faker()
                # If it was we just pick a different one and continue
                if not self.is_in_voting:  # If we aren't voting we need to redo the current task
                    self.task_counter -= 1  # Decrementing the current task
                    self._next_task()
            # Else we continue as normal

    def _goto_voting(self):
        """
        Broadcasts all the players answers to all the players
        """
        self.is_in_voting = True
        # Formatting broadcast message
        answer_broadcast = "V"
        # Adding each players answer to the broadcast
        for player in self.server_comm.open_clients.values():
            answer_broadcast += player.current_ans + "&"
        answer_broadcast += self.cur_task  # Adding the task as the final part for displaying on each player screen
        # Broadcasting the message
        self.server_comm.send_all(answer_broadcast)

    def _next_task(self):
        """
        Calls the next flag according to the current category
        """
        if self.cur_category == "P":
            self.start_round_point()
        elif self.cur_category == "N":
            self.start_round_number()
        else:  # Cur category is Raise
            self.start_round_raise()

    def _goto_results(self):
        """
        Calculates result of round and broadcasts it to the players
        """
        majority_sock = None  # The socket with the current majority vote
        # Iterating through each player's vote
        for player in self.server_comm.open_clients.values():
            cur_vote = player.current_ans
            # If the player voted for the faker and is not the faker himself
            if not player.username == self.faker[1] and cur_vote == self.faker[1]:
                # Adding detective points according to which round it is
                awarded_points = 200 - (self.task_counter * 50)
                player.detective_points += awarded_points
                player.cur_round_points += awarded_points
            # Adding vote to player
            voted_sock = self.server_comm.username_to_socket(cur_vote)
            self.server_comm.open_clients[voted_sock].vote_counter += 1
            # Checking if the voted socket is now the majority voted socket
            if majority_sock is None or self.server_comm.open_clients[voted_sock].vote_counter > self.server_comm.open_clients[majority_sock].vote_counter:
                majority_sock = voted_sock
        caught = False  # If the faker was caught
        # Checking if the socket that got the majority vote actually got a majority
        if self.server_comm.open_clients[majority_sock].vote_counter > round(len(self.server_comm.open_clients) / 2):
            # Checking if the majority voted for the faker
            if majority_sock is self.faker[0]:
                caught = True
                # G - Game round result, 1st T - Majority vote, 2nd T - Was the faker.
                self.server_comm.send_all(f"GT{self.faker[1]}T")
                time.sleep(7.5)  # Waiting for clientside animation
            else:
                # G - Game round result, 1st T - Majority vote, 2nd T - Was not the faker.
                self.server_comm.send_all(f"GT{self.server_comm.open_clients[majority_sock].username}F")
                time.sleep(7.5)  # Waiting for clientside animation
        else:
            # No majority vote
            self.server_comm.send_all(f"GF")
            time.sleep(5.5)  # Waiting for clientside reading time
            pass

        self._reset_player_answers()
        if not caught:
            # Giving the faker points for not being caught
            awarded_points = 125 + (self.task_counter * 50)
            self.server_comm.open_clients[self.faker[0]].faker_points += awarded_points
            self.server_comm.open_clients[self.faker[0]].cur_round_points += awarded_points
            if self.task_counter == 3:
                # Rounds run out, faker won
                self._broadcast_player_points()  # Broadcasting points earned this round to all players
                self.instruct_q.put("START NEW ROUND")
            else:
                # Continue to next task
                self._next_task()
        else:  # The faker was caught
            self._broadcast_player_points()  # Broadcasting points earned this round to all players
            self.instruct_q.put("START NEW ROUND")

    def _broadcast_player_points(self):
        """
        Broadcasts the point of each player to all players and waits for reading time, get called at the end of each round
        """
        # Formatting the point list msg
        formatted_point_list = "P"
        for player in self.server_comm.open_clients.values():
            formatted_point_list += str(player.cur_round_points) + "&"
        formatted_point_list = formatted_point_list[:-1]  # Removing the last &
        self.server_comm.send_all(formatted_point_list)   # Sending to all clients
        time.sleep(6.5)  # Waiting for clientside reading time

    def _reset_player_answers(self):
        """
        Resets each player's answer and vote counts for the next part of the phase
        :return:
        """
        for player in self.server_comm.open_clients.values():
            player.current_ans = ""
            player.vote_counter = 0

    def reset_chosen_ids(self):
        """
        Resets ids chosen for game
        """
        self.picked_id_point = []
        self.picked_id_number = []
        self.picked_id_raise = []

    def reset_round_points(self):
        """
        Resets each player's round points
        :return:
        """
        for player in self.server_comm.open_clients.values():
            player.cur_round_points = 0


class FinalScreen(Phase):
    """
    Final phase of the game, send final point results and goes back to lobby at the end
    """
    def __init__(self, server_comm, instruct_q):
        Phase.__init__(self, server_comm, instruct_q)

    def process_queue(self):
        pass

    def broadcast_final_results(self):
        """
        Broadcasts the final results of the game
        :return:
        """
        max_faker = (None, 0)       # Tuple of socket with current max faker points and it's points
        max_detective = (None, 0)   # Tuple of socket with current max detective points and it's points
        max_winner = (None, 0)      # Tuple of socket with current max points and it's points

        # Iterating through all player's points
        for sock in self.server_comm.open_clients.keys():
            player = self.server_comm.open_clients[sock]
            # Setting the max if a new maximum is found
            # Faker
            if player.faker_points > max_faker[1]:
                max_faker = (sock, player.faker_points)
            # Detective
            if player.detective_points > max_detective[1]:
                max_detective = (sock, player.detective_points)
            # Overall
            if player.get_points() > max_winner[1]:
                max_winner = (sock, player.get_points())

            # In the rare case that no one got detective or faker point we randomly pick a socket to prevent errors
        if max_faker[0] is None:
            max_faker = (random.choice(list(self.server_comm.open_clients.keys())), 0)

        if max_detective[0] is None:
            max_detective = (random.choice(list(self.server_comm.open_clients.keys())), 0)

        # Formatting winner message to send to players
        formatted_winners_msg = "W"
        # Adding faker
        formatted_winners_msg += f"{str(max_faker[1]).zfill(4) + self.server_comm.open_clients[max_faker[0]].username}&"
        # Adding detective
        formatted_winners_msg += f"{str(max_detective[1]).zfill(4) + self.server_comm.open_clients[max_detective[0]].username}&"
        # Adding overall winner
        if max_winner[0] in self.server_comm.open_clients:
            formatted_winners_msg += f"{str(max_winner[1]).zfill(4) + self.server_comm.open_clients[max_winner[0]].username}"
        else:
            formatted_winners_msg += f"0000NOONE"

        # Broadcasting the formatted message
        self.server_comm.send_all(formatted_winners_msg)

        # Waiting for clientside animation
        time.sleep(14)
        self.instruct_q.put("BACK TO LOBBY")
