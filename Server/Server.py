from Servercom import ServerComm
from TaskDatabase import TaskDatabase
import queue
import Phases


msg_q = queue.Queue()  # Message queue of message sent from client. Format: Tuple - (socket sent from, msg)
server_comm = ServerComm(7878, msg_q)  # Server communication object

instruct_q = queue.Queue()  # Queue of instruction sent by phases to main server program

# Connecting to the task database
task_db = TaskDatabase("task_database")

max_rounds = 5  # Max amount of round in each game

# Creating phases
ConnectingAndLobby = Phases.ConnectingAndLobby(server_comm, instruct_q)  # Connecting and lobby phase
ChooseCategory = Phases.ChooseCategory(server_comm, instruct_q)          # Choosing category phase
GameRound = Phases.Round(server_comm, instruct_q, task_db)               # Main phase - Tasks, Voting, and round results
FinalScreen = Phases.FinalScreen(server_comm, instruct_q)                # Final phase, final game results

# cur_phase will point at the current active phase
# Setting the initial phase to the connecting and lobby phase
cur_phase = ConnectingAndLobby

# Main server loop
running = True
while running:
    cur_phase.process_queue()  # Processing the waiting messages queue

    # If a socket has disconnected
    if server_comm.has_disconnect:
        server_comm.has_disconnect = False
        # Calling the current phases' on disconnect method
        cur_phase.on_disconnect()

    # Looping through instructions sent by phases
    while not instruct_q.empty():
        instruction = instruct_q.get()

        if instruction == "BACK TO LOBBY":  # Back to lobby instruction
            server_comm.send_all("Q")           # Telling all player to quit to lobby
            server_comm.is_in_progress = False  # Updating the server comm to allow new player for approval
            cur_phase = ConnectingAndLobby      # Changing phase to lobby phase
            GameRound.reset_chosen_ids()        # Resetting chosen ids of tasks
            Phases.num_game_rounds = 0
            # Resetting each player parameters
            for player in server_comm.open_clients.values():
                player.ready = False
                player.chose_category = False
                player.detective_points = 0
                player.faker_points = 0

        elif instruction == "START NEW ROUND":  # Start new game round instruction --> means choose category
            server_comm.is_in_progress = True  # Blocking new players from joining
            # Checking if game has ended (max rounds for a game is 5)
            if Phases.num_game_rounds == min(len(server_comm.open_clients), max_rounds):
                # Game ended
                cur_phase = FinalScreen  # Setting the phase to be the final results
                cur_phase.broadcast_final_results()  # Broadcasting final results to all players

            else:
                # Setting up choose category phase
                cur_phase = ChooseCategory
                cur_phase.start_phase()
                Phases.num_game_rounds += 1  # Incrementing game rounds counter

        elif instruction.startswith("ROUND"):  # Category was chosen, start a game round
            round_type = instruction[-1]  # Type of round
            cur_phase = GameRound
            cur_phase.choose_faker()    # Choosing random player to be the faker
            cur_phase.task_counter = 0  # Counts the number of tasks that were played
            # Category type is first letter of round Type
            # P --> Point round, R --> Raise round, N --> Number round
            cur_phase.cur_category = round_type
            cur_phase.reset_round_points()  # Resetting round points

            if round_type == "P":
                cur_phase.start_round_point()   # Starting the round
            elif round_type == "R":
                cur_phase.start_round_raise()   # Starting the round
            elif round_type == "N":
                cur_phase.start_round_number()  # Starting the round
