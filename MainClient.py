import pygame as pyg
import queue
from Clientcom import ClientComm
import Scenes

server_ip = input("Please enter the server ip to connect to:\n")  # Ip of server to connect to and display onscreen
msg_q = queue.Queue()  # Queue of message sent by server
client = ClientComm(server_ip, 7878, msg_q)  # Creating client communication object

# Display settings
screenWidth, screenHeight = (1200, 800)

# Initializing scenes
Scenes.init_scenes(server_ip, (screenWidth, screenHeight))
to_send = Scenes.to_send_q

# ==== SCENES ====
cur_scene = Scenes.LoadingScene()  # Current scene will point on the current active scene, start on the loading scene
FailedConnection = Scenes.FailedConnectionScene()   # Failed connection screen
ConnectionScreen = Scenes.ConnectionScreen()        # Connection screen, gets username
LobbyScreen = Scenes.LobbyScene()                   # Lobby screen
ChooseScreen = Scenes.ChooseCategory()              # Choose category screen, get function when choosing and waiting for another to choose
RoundScreen = Scenes.GameRound()                    # Task display and functionality to answer it
VoteScreen = Scenes.VotingRound()                   # Voting and showing each other player's answer
VoteResultsScreen = Scenes.VoteResults()            # Vote results screen
RoundResultsScreen = Scenes.RoundResults()          # Point results for each round
FinalResultsScreen = Scenes.FinalResults()          # Final results of entire game


def failed_screen():
    """
    Method to call when switching to failed connection screen, loops infinitely until game closes
    """
    cur_scene.draw()
    pyg.display.flip()
    while True:
        cur_scene.process_input(pyg.event.get())
        cur_scene.update()


# While we are waiting for the client comm to connect fully to the server
while not client.connected:

    # Staying on the connection screen scene until we connect or get an error
    cur_scene.process_input(pyg.event.get())

    cur_scene.draw()
    pyg.display.flip()
    cur_scene.update()

    # If failed to connect to server
    if client.connected is None:
        cur_scene = FailedConnection
        failed_screen()

Running = True

cur_scene = ConnectionScreen  # When connected to server switching to main menu scene
# == Main game loop ==
while Running:
    # Getting the event list
    event_list = pyg.event.get()

    # Processing input
    cur_scene.process_input(event_list)

    # Reading waiting messages and processing them
    while not msg_q.empty():
        msg = msg_q.get()
        command_code = msg[0]  # Getting the message's command code
        if not len(msg) == 1:  # If the message is not only a command code
            msg = msg[1:]      # Setting the message to be equal to itself not including the command code

        if command_code == "Y":  # Server approved username
            cur_scene = LobbyScreen  # Moving on to lobby scene

        elif command_code == "N":  # Server disapproved username
            if type(cur_scene) == Scenes.ConnectionScreen:
                cur_scene.invalidate_username(msg)  # Showing invalid username text

        elif command_code == "L":  # Updated player list
            Scenes.update_players(msg)  # Updating the scenes' active player list

        elif command_code == "Q":  # Quit back to lobby command
            cur_scene = LobbyScreen  # Changing scene to lobby
            cur_scene.reset_scene()  # Resetting lobby scene

        elif command_code == "C":  # Choose category command
            cur_scene = ChooseScreen  # Updating the scene to be the category choose scene
            if msg[0] == "&":  # If we aren't the current category chooser
                # Updating the text on the scene
                cur_scene.choosing_player = msg[1:]
                cur_scene.update_wait_text()
            elif msg == "Y":  # If we are the chooser
                cur_scene.choosing = True

        elif command_code == "T":  # Task command
            cur_scene = RoundScreen  # Updating the scene to be the game round scene
            if msg[0] == "P":  # Point task
                cur_scene.point_round()
            elif msg[0] == "N":  # Number task
                cur_scene.number_round()
            else:  # Raise task
                cur_scene.raise_round()
            cur_scene.set_task(msg[1:])  # Removing second command code and setting the task

        elif command_code == "V":  # Vote command
            cur_scene = VoteScreen  # Moving to vote screen
            cur_scene.set_answers(msg)  # Setting the scenes answers to be the answers got from server

        elif command_code == "G":  # Vote results command
            cur_scene = VoteResultsScreen  # Switching to result scene
            if msg[0] == "T":  # T means it was a majority vote, F means it wasn't:
                majority_vote_name = msg[1:-1]  # Getting the name of the majority vote player
                was_faker = msg[-1] == "T"  # If the final character is T that means the player was the faker else the final character is F
                # Updating result screen with parameters got from server
                cur_scene.start_scene_majority(majority_vote_name, was_faker)
            else:
                # There was no majority vote
                cur_scene.start_scene_no_majority()

        elif command_code == "P":  # Points for round results command
            cur_scene = RoundResultsScreen    # Updating current scene to be the point results scene
            cur_scene.set_player_points(msg)  # Updating saved points in scene

        elif command_code == "W":  # Points for final results screen
            cur_scene = FinalResultsScreen    # Changing to final results scene
            cur_scene.set_winners(msg)        # Updating winners

        else:
            # Else it's an invalid message
            print(command_code, msg)

    # Sending waiting messages to servers
    while not to_send.empty():
        client.send(to_send.get())

    # If we disconnected from the server we switch to the failed connection scene
    if client.connected is None:
        cur_scene = FailedConnection
        failed_screen()

    # Updating scene values and drawing the scene onto the screen
    cur_scene.update()
    cur_scene.draw()
    # Updating display
    pyg.display.flip()
