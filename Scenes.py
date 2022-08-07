import pygame as pyg
from abc import ABC, abstractmethod
from TextInputBox import TextInputBox
from Button import Button
import queue

pyg.init()

# == Scene globals ==

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
beige = (235, 222, 207)
dark_beige = (219, 195, 167)
darker_beige = (184, 157, 127)
check_green = (64, 255, 115)

# Screen variables
screenWidth: int = 0
screenHeight: int = 0

# General scene variables
screen: pyg.Surface = pyg.Surface((0, 0))
clock = pyg.time.Clock()   # Pygame clock
to_send_q = queue.Queue()  # Queue of messages to send, shared with main client program
server_ip = ""             # IP of server for display purposes


def init_scenes(server_ip_par, screen_res):
    """
    Initializes all the scene variables
    :param server_ip_par: Server ip for displaying purposes
    :param screen_res: Tuple of screen resolution
    """
    pyg.display.set_caption("Fakin' It")
    # Loading icon for window
    icon = pyg.image.load('img\\Icon.png')
    pyg.display.set_icon(icon)

    # Getting parameters from main program and synchronizing with it
    global screenWidth, screenHeight
    global screen
    global server_ip
    screenWidth, screenHeight = screen_res
    screen = pyg.display.set_mode((screenWidth, screenHeight))
    server_ip = server_ip_par


# === Fonts ===
def_font = pyg.font.SysFont(None, 45)           # Default font
input_font = pyg.font.SysFont(None, 100)        # Font for input box
lobby_title_font = pyg.font.SysFont(None, 85)   # Font for lobby title
lobby_title_font.set_underline(True)
task_font = pyg.font.SysFont(None, 55)          # Font for tasks
small_task_font = pyg.font.SysFont(None, 40)    # Secondary smaller font for tasks
send_button_font = pyg.font.SysFont(None, 75)   # Font for the send button text
player_name_font = pyg.font.SysFont(None, 65)   # Font for player names
final_titles_font = pyg.font.SysFont(None, 65)  # Font for titles in final results
final_titles_font.set_underline(True)
overall_winner_font = pyg.font.SysFont(None, 125)  # Font for the overall winner title in the final results
overall_winner_font.set_underline(True)
result_font = pyg.font.SysFont(None, 80)        # Font for results
drumroll_font = pyg.font.SysFont(None, 115)     # Font for "drumroll" dots
winner_font = pyg.font.SysFont(None, 165)       # Font for winner name
icon_font = pyg.font.SysFont("segoe-ui-symbol", 65)  # Font for icons


active_players = []  # A list of the active player, get updated when a player joins or leaves

# == Utility methods ==


def update_players(p_list):
    """
    Method that receives a player list from server and updates the local player list
    :param p_list: List of players from server
    """
    p_list = p_list.split("&")
    for player in p_list:
        if player not in active_players:
            active_players.append(player)
    for player in active_players:
        if player not in p_list:
            active_players.remove(player)


def center_text_x(text):
    """
    Returns x position of text so it'll be on the center of the screen
    :param text: Text to calculate center of
    :return: X position on screen to start drawing text
    """
    return (screenWidth - text.get_width()) / 2


class Scene(ABC):
    """
    Abstract class that represents the scene template
    """
    def process_input(self, events):
        """
        Method that gets pygame events and processes the input, gets called once per frame
        :param events: pygame event list
        """
        # == Default process_input ==
        # Iterating through events
        for event in events:
            if event.type == pyg.QUIT:
                pyg.quit()
                exit()

    @abstractmethod
    def update(self):
        """
        Method for updating scene variables, gets called once per frame (use clock.tick() in this)
        """
        pass

    @abstractmethod
    def draw(self):
        """
        Method for drawing graphics onto screen, gets called once per frame right before pyg.display.flip()
        """
        pass


class LoadingScene(Scene):
    """
    Loading scene, the initial scene of the game. gets shown until client is fully connected to server
    """
    def __init__(self):
        Scene.__init__(self)
        self.dot = 0  # Variable for showing loading dots
        # Loading text and it's permanent position
        self.loading_text = def_font.render(f"Connecting to {server_ip} . . .", True, dark_beige)
        self.loading_text_pos = (center_text_x(self.loading_text), (screenHeight - self.loading_text.get_height()) / 2)

    def update(self):
        pyg.time.wait(450)  # Waiting for the loading "animation"
        self.dot += 1  # Incrementing the dot count
        # Updating the text
        self.loading_text = def_font.render(f"Connecting to {server_ip}" + (" ." * (self.dot % 4)), True, dark_beige)
        clock.tick(60)  # Limiting frame rate

    def draw(self):
        screen.fill(beige)
        # Drawing text onto screen
        screen.blit(self.loading_text, self.loading_text_pos)


class FailedConnectionScene(Scene):
    """
    Scene to load when server is down or the connection failed
    """
    def __init__(self):
        Scene.__init__(self)
        self.failed_text = None

    def update(self):
        clock.tick(20)

    def draw(self):
        # This draw is only called once since the scene is static
        screen.fill(beige)
        self.failed_text = def_font.render(f"Couldn't reach server,  please close the game and try again later", True, dark_beige)
        screen.blit(self.failed_text, ((screenWidth-self.failed_text.get_width())/2, (screenHeight-self.failed_text.get_height())/2))


class ConnectionScreen(Scene):
    """
    Main menu and connection screen with username input
    """
    def __init__(self):
        Scene.__init__(self)
        self.logo_img = pyg.image.load("img\\Fakin It.png")  # Loading title image
        self.server_ip_text = def_font.render("Connected to " + server_ip, True, dark_beige)  # "Connected to" text
        # In case the server sends an invalid username msg
        self.invalid_username = def_font.render("", True, dark_beige)
        self.invalid_pos = (0, 0)
        text_width = 600
        # Text input box for username
        self.text_input_box = TextInputBox(black, (screenWidth - text_width)/2, screenHeight*(4/6), text_width,
                                           input_font, backcolor=dark_beige, max_letters=10, default_text="Enter Username")
        self.text_input_box.active = True  # Setting the initial state of the text box to be active
        self.group = pyg.sprite.Group(self.text_input_box)

    def invalidate_username(self, invalid_msg):
        """
        Method to call when server disapproves username.
        Displays the invalid username message onto screen
        """
        self.invalid_username = def_font.render(invalid_msg, True, dark_beige)
        # Calculating text position on screen
        self.invalid_pos = (center_text_x(self.invalid_username), screenHeight * (5/6))
        self.text_input_box.clear()

    def process_input(self, events):
        # Iterating through all events
        for event in events:
            if event.type == pyg.QUIT:
                pyg.quit()
                exit()
            # Key press event
            elif event.type == pyg.KEYUP:
                if event.key == pyg.K_RETURN:  # If the user pressed enter
                    username = self.text_input_box.get_text()  # Getting the username from the text box
                    self.text_input_box.clear()  # Clearing the text box
                    if not username == "":  # If the textbox is not empty
                        to_send_q.put("U" + username)  # Sending the chosen username to the server for approval
        self.group.update(events)  # Updating the text box with input

    def update(self):
        clock.tick(60)

    def draw(self):
        screen.fill(beige)
        # Drawing logo and text onto screen
        screen.blit(self.logo_img, ((screenWidth - self.logo_img.get_width()) / 2, 0))
        screen.blit(self.server_ip_text, (10, screenHeight * 0.96))
        screen.blit(self.invalid_username, self.invalid_pos)
        self.group.draw(screen)  # Drawing text box onto screen


class LobbyScene(Scene):
    """
    Scene for lobby before game starts, displays all player's name and a ready button
    """
    def __init__(self):
        Scene.__init__(self)

        # Lobby tittle text
        self.lobby_title = lobby_title_font.render("Lobby", True, black)
        self.lobby_title_pos = (center_text_x(self.lobby_title), screenHeight * 0.03)

        # Ready button
        button_width = 175
        self.ready_button = Button(dark_beige, darker_beige, (screenWidth-button_width) / 2, screenHeight*0.9,
                                   button_width, 70, font=def_font, text="Ready", text_color=black)
        self.group = pyg.sprite.Group(self.ready_button)
        self.is_ready = False  # Is ready boolean

        # Checkmark text
        self.check_text = icon_font.render("✔", True, dark_beige)
        self.check_pos = ((screenWidth+self.check_text.get_width() + self.ready_button.width)/2, screenHeight*0.9 - self.check_text.get_height()*0.15)

    def process_input(self, events):
        # Iterating through events
        for event in events:
            if event.type == pyg.QUIT:
                pyg.quit()
                exit()
        self.group.update(events)  # Updating the ready button with the events

    def update(self):
        clock.tick(60)
        if self.ready_button.pressed:  # If the ready button was pressed
            self.is_ready = not self.is_ready  # Flipping the is ready boolean
            if self.is_ready:  # If we are now ready
                # Updating the checkmark text to be green and updating server on our state
                self.check_text = icon_font.render("✔", True, check_green)
                to_send_q.put("RY")  # Sending new state to server
            else:
                # Updating the checkmark text to be greyed out and updating server on our state
                self.check_text = icon_font.render("✔", True, dark_beige)
                to_send_q.put("RN")  # Sending new state to server
            # Clearing the button's state
            self.ready_button.clear_active()

    def draw(self):
        screen.fill(beige)
        screen.blit(self.lobby_title, self.lobby_title_pos)
        # Variables for dynamically drawing each players name
        draw_count = 0  # How many player have we drawn
        rect_width = screenWidth / 3  # Width of each rect
        width_space = (screenWidth - rect_width * 2) / 3  # Space between the screen border and each rect horizontally
        height_space = screenHeight / 14  # Space between each rect vertically
        cur_width = width_space  # Starting width
        cur_height = height_space * 2  # Starting drawing height
        # Iterating over all active players and dynamically drawing each one
        for player in active_players:
            # Drawing rect for current player at the current position
            pyg.draw.rect(screen, dark_beige, pyg.Rect(cur_width, cur_height, rect_width, height_space*2))
            # Drawing the text onto the rect
            p_name = player_name_font.render(f"{player}", True, black)
            screen.blit(p_name, (cur_width + rect_width/2 - p_name.get_width() / 2, cur_height + height_space/2 +
                        (p_name.get_height() / 4)))
            # Updating the position for the next draw
            draw_count += 1
            if draw_count % 2 == 0:  # If we need to go down a line
                cur_height += height_space * 2.5
                if draw_count == len(active_players) - 1:
                    # If there's only one more we draw it centered
                    cur_width = (screenWidth - rect_width) / 2
                else:
                    # Resetting the width
                    cur_width -= width_space + rect_width
            else:
                # Need to draw on the same line
                cur_width += width_space + rect_width

        self.group.draw(screen)  # Drawing the button onto the screen
        screen.blit(self.check_text, self.check_pos)  # Drawing the checkmark

    def reset_scene(self):
        self.ready_button.pressed = True  # Simulating button press to update visuals and ready variable


class ChooseCategory(Scene):
    """
    Scene for the category choosing screen, can either be a waiting text or three buttons depending on if the
    current player is the chooser
    """
    def __init__(self):
        Scene.__init__(self)
        self.choosing = False  # Is the player the one choosing the category
        self.choosing_player = ""  # The choosing players name for the waiting text
        # Text to show when player is not choosing category
        self.waiting_text = def_font.render("Please wait while ... is choosing a category", True, dark_beige)
        self.waiting_text_pos = (center_text_x(self.waiting_text), screenHeight / 2)

        # Instruction text when player is choosing a category
        self.choose_text = def_font.render("Choose a category!", True, black)
        self.choose_text_pos = (center_text_x(self.choose_text),
                                screenHeight / 10 - self.choose_text.get_height() / 2)

        # Category buttons
        button_width = 265
        # Point category button
        self.point_category = Button(dark_beige, darker_beige, (screenWidth-button_width) / 2,
                                     screenHeight * 3/10 - 110, button_width, 110, font=def_font,
                                     text="You gotta point", text_color=black)

        # Number category button
        self.number_category = Button(dark_beige, darker_beige, (screenWidth - button_width) / 2,
                                      screenHeight * 6 / 10 - 110, button_width, 110, font=def_font,
                                      text="Number pressure", text_color=black)

        # Raise category button
        self.raise_category = Button(dark_beige, darker_beige, (screenWidth - button_width) / 2,
                                     screenHeight * 9 / 10 - 110, button_width, 110, font=def_font,
                                     text="Hands of truth", text_color=black)
        # Sprite group of all buttons
        self.button_group = pyg.sprite.Group(self.point_category, self.number_category, self.raise_category)

    def update_wait_text(self):
        """
        Updates the text when the player isn't choosing
        """
        self.waiting_text = def_font.render(f"Please wait while {self.choosing_player} is choosing a category",
                                            True, dark_beige)
        self.waiting_text_pos = (center_text_x(self.waiting_text), screenHeight / 2)
        self.choosing = False

    def process_input(self, events):
        # Iterating through events
        for event in events:
            if event.type == pyg.QUIT:
                pyg.quit()
                exit()
        if self.choosing:  # Updating the button list only if the player is choosing
            self.button_group.update(events)

    def update(self):
        clock.tick(60)
        # Updating the server if we choose a category
        if self.point_category.pressed:     # Point was chosen
            self.point_category.clear_active()
            to_send_q.put("CPOINT")
        elif self.number_category.pressed:  # Number was chosen
            self.number_category.clear_active()
            to_send_q.put("CNUMBER")
        elif self.raise_category.pressed:    # Raise was chosen
            self.raise_category.clear_active()
            to_send_q.put("CRAISE")

    def draw(self):
        screen.fill(beige)
        if not self.choosing:  # If we aren't choosing we only show the waiting text
            screen.blit(self.waiting_text, self.waiting_text_pos)
        else:  # If we are choosing we display the buttons and the instruction text
            self.button_group.draw(screen)
            screen.blit(self.choose_text, self.choose_text_pos)


class GameRound(Scene):
    def __init__(self):
        Scene.__init__(self)
        # Text for displaying task
        self.cur_task = ""
        self.task_text = task_font.render("TASK", True, black)
        self.task_text_bot = None  # In case the text is too long to show in one line
        self.task_text_pos = (0, 0)
        self.task_text_bot_pos = (0, 0)

        # Confirm text
        self.confirm_text = def_font.render("Answer successfully sent!", True, dark_beige)
        self.confirm_text_pos = (center_text_x(self.confirm_text), (screenHeight * 0.9))
        self.show_confirm = False

        # Choice functionality
        self.options = []  # Dynamic list of valid answers, changes for each category
        self.current_choice = 0  # Index of current choice in options
        # Choice text
        self.choice_text = task_font.render("", True, black)
        self.choice_text_pos = (0, 0)

        # Option box
        box_width = 375
        self.option_box = pyg.Rect((screenWidth - box_width) / 2, screenHeight / 2, box_width, 110)

        # Left and right buttons
        self.left_button = Button(dark_beige, darker_beige, self.option_box.left - 75,
                                  self.option_box.top, 75, 110, font=icon_font,
                                  text="⮜", text_color=black)
        self.right_button = Button(dark_beige, darker_beige, self.option_box.left + box_width,
                                   self.option_box.top, 75, 110, font=icon_font,
                                   text="⮞", text_color=black)

        # Send button
        send_button_width = 225
        self.send_button = Button(dark_beige, darker_beige, (screenWidth - send_button_width) / 2,
                                  screenHeight * 0.7, send_button_width, 70, font=send_button_font,
                                  text="Send", text_color=black)

        # Button group
        self.button_group = pyg.sprite.Group(self.left_button, self.right_button, self.send_button)

    def set_task(self, task):
        """
        Sets task and updates all text objects accordingly
        :param task: task to display
        """
        self.show_confirm = False  # Resetting the confirmation message boolean
        # == Task text ==
        self.task_text = task_font.render(task, True, black)
        if self.task_text.get_width() > screenWidth - 80:
            # === Text is too long to fit on the screen ===
            # Splitting text in to
            split_text = task.split(" ")
            half = int(len(split_text) / 2)
            first_text = " ".join(split_text[0:half])
            sec_text = " ".join(split_text[half:])

            # Updating text objects accordingly
            self.task_text = task_font.render(first_text, True, black)
            self.task_text_pos = (center_text_x(self.task_text), screenHeight * 0.2)
            self.task_text_bot = task_font.render(sec_text, True, black)
            self.task_text_bot_pos = (center_text_x(self.task_text_bot),
                                      self.task_text_pos[1] + self.task_text_bot.get_height())
        else:
            # No need to split text
            self.task_text_bot = None
            self.task_text_pos = (center_text_x(self.task_text), screenHeight * 0.2)

    # === Methods to update the options according to the category of the round ===
    def point_round(self):
        self.options = active_players.copy()
        self.current_choice = 0
        self._update_choice_text()

    def raise_round(self):
        self.options = ["Yes", "No"]
        self.current_choice = 0
        self._update_choice_text()

    def number_round(self):
        self.options = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.current_choice = 0
        self._update_choice_text()

    def _update_choice_text(self):
        """
        Updates the choice text object and position according to new text
        """
        self.choice_text = task_font.render(self.options[self.current_choice], True, black)
        self.choice_text_pos = (self.option_box.left + (self.option_box.width / 2) - (self.choice_text.get_width() / 2),
                                self.option_box.top + (self.option_box.height / 2) - (self.choice_text.get_height() / 2))

    def process_input(self, events):
        # Iterating through events
        for event in events:
            if event.type == pyg.QUIT:
                pyg.quit()
                exit()
        # Updating the button group with events
        self.button_group.update(events)

    def update(self):
        clock.tick(60)
        # Moving current choice index according to button presses
        if self.left_button.pressed:
            # == Left button logic ==
            self.current_choice -= 1
            # Loop around if we reached the limit
            if self.current_choice < 0:
                self.current_choice = len(self.options) - 1
            # Updating the text
            self._update_choice_text()
            self.left_button.clear_active()
        elif self.right_button.pressed:
            # == Right button logic ==
            self.current_choice += 1
            # Loop around if we reached the limit
            if self.current_choice == len(self.options):
                self.current_choice = 0
            # Updating the text
            self._update_choice_text()
            self.right_button.clear_active()
        elif self.send_button.pressed:
            # == Send button logic ==
            # Sending answer to server
            to_send_q.put("A" + self.options[self.current_choice])
            self.send_button.clear_active()
            # Showing confirm text
            self.show_confirm = True

    def draw(self):
        screen.fill(beige)
        # Showing task text
        screen.blit(self.task_text, self.task_text_pos)
        # Is there continuation text
        if self.task_text_bot is not None:
            # Showing continuation text
            screen.blit(self.task_text_bot, self.task_text_bot_pos)
        # Drawing option box
        pyg.draw.rect(screen, dark_beige, self.option_box)

        # Displaying current choice
        screen.blit(self.choice_text, self.choice_text_pos)

        # Showing confirm message if needed
        if self.show_confirm:
            screen.blit(self.confirm_text, self.confirm_text_pos)

        # Drawing buttons
        self.button_group.draw(screen)


class VotingRound(Scene):
    """
    Scene for the voting part of each round
    """
    def __init__(self):
        Scene.__init__(self)
        self.answers = {}  # Dictionary of each player's name and their answers to the task
        # Text objects for showing voting
        # Instruction text
        self.instruction_text = task_font.render("Vote for who you think the faker is", True, black)
        self.instruction_text_pos = (center_text_x(self.instruction_text), screenHeight * 0.2)

        # Showing player name and answer
        self.player_name = task_font.render("PLAYER's answer is:", True, black)
        self.player_answer = task_font.render("", True, black)
        self.player_name_pos = (0, 0)
        self.player_answer_pos = (0, 0)

        # Task text
        self.task = ""
        self.task_title = def_font.render("The task was:", True, black)
        self.task_title_pos = (center_text_x(self.task_title), screenHeight * 0.05)
        self.task_text = small_task_font.render("", True, black)
        self.task_text_pos = (0, 0)

        # Confirm text
        self.confirm_text = def_font.render("Vote successfully counted!", True, dark_beige)
        self.confirm_text_pos = (center_text_x(self.confirm_text), (screenHeight * 0.9))
        self.show_confirm = False

        # Keeping track and showing currently chosen player
        self.current_player = 0
        self.choice_text = task_font.render("", True, black)
        self.choice_text_pos = (0, 0)

        # Option box
        box_width = 375
        self.option_box = pyg.Rect((screenWidth - box_width) / 2, screenHeight / 2, box_width, 110)

        # Left and right buttons
        self.left_button = Button(dark_beige, darker_beige, self.option_box.left - 75,
                                  self.option_box.top, 75, 110, font=icon_font,
                                  text="⮜", text_color=black)
        self.right_button = Button(dark_beige, darker_beige, self.option_box.left + box_width,
                                   self.option_box.top, 75, 110, font=icon_font,
                                   text="⮞", text_color=black)

        # Vote button
        Vote_button_width = 225
        self.vote_button = Button(dark_beige, darker_beige, (screenWidth - Vote_button_width) / 2,
                                  screenHeight * 0.7, Vote_button_width, 70, font=send_button_font,
                                  text="Vote", text_color=black)

        # Button group
        self.button_group = pyg.sprite.Group(self.left_button, self.right_button, self.vote_button)

    def process_input(self, events):
        # Iterating through events
        for event in events:
            if event.type == pyg.QUIT:
                pyg.quit()
                exit()
        # Updating buttons with events
        self.button_group.update(events)

    def update(self):
        clock.tick(60)
        # Moving current player choice index according to button presses
        if self.left_button.pressed:
            # == Left button logic ==
            self.current_player -= 1
            # Loop around if we reached the limit
            if self.current_player < 0:
                self.current_player = len(self.answers) - 1
            # Updating the text
            self._update_text()
            self.left_button.clear_active()
        elif self.right_button.pressed:
            # == Right button logic ==
            self.current_player += 1
            # Loop around if we reached the limit
            if self.current_player == len(self.answers):
                self.current_player = 0
            # Updating the text
            self._update_text()
            self.right_button.clear_active()
        elif self.vote_button.pressed:
            # == Vote button logic ==
            # Sending vote to server
            to_send_q.put("V" + list(self.answers.keys())[self.current_player])
            self.vote_button.clear_active()
            # Showing confirm text
            self.show_confirm = True

    def draw(self):
        screen.fill(beige)
        # Showing instruction text
        screen.blit(self.instruction_text, self.instruction_text_pos)

        # Showing task text
        screen.blit(self.task_title, self.task_title_pos)
        screen.blit(self.task_text, self.task_text_pos)

        # Showing player name and their answer
        screen.blit(self.player_name, self.player_name_pos)
        screen.blit(self.player_answer, self.player_answer_pos)
        # Drawing option box
        pyg.draw.rect(screen, dark_beige, self.option_box)

        # Displaying current choice
        screen.blit(self.choice_text, self.choice_text_pos)

        # Showing confirm message if needed
        if self.show_confirm:
            screen.blit(self.confirm_text, self.confirm_text_pos)

        # Drawing buttons
        self.button_group.draw(screen)

    def _update_text(self):
        """
        Updates all the texts, called when a choice has changed
        """
        # Getting the player name from the dictionary
        cur_player_name = list(self.answers.keys())[self.current_player]
        # Updating the choice text
        self.choice_text = task_font.render(cur_player_name, True, black)
        self.choice_text_pos = (self.option_box.left + (self.option_box.width / 2) - (self.choice_text.get_width() / 2),
                                self.option_box.top + (self.option_box.height / 2) - (self.choice_text.get_height() / 2))

        # Updating task text
        self.task_text = small_task_font.render(f"{self.task}", True, black)
        self.task_text_pos = (center_text_x(self.task_text), screenHeight * 0.1)

        # Updating player name text
        self.player_name = task_font.render(f"{cur_player_name}'s answer is:", True, black)
        self.player_name_pos = (center_text_x(self.player_name), screenHeight * 0.3)

        # Updating player answer text
        self.player_answer = input_font.render(self.answers[cur_player_name], True, black)
        self.player_answer_pos = (center_text_x(self.player_answer),
                                  self.player_name_pos[1] + self.player_answer.get_height())

    def set_answers(self, answers):
        """
        Updates the local variable according to each players answer
        :param answers: answers sent by server
        """
        # Making answers into a dictionary with the username and player's answer
        self.current_player = 0  # Resetting the current player choice index
        self.show_confirm = False
        ans_list = answers.split("&")  # Splitting by &
        self.task = ans_list[-1]  # Getting task from answer list
        ans_list = ans_list[:-1]  # Removing the task from the answer list
        self.answers = dict(zip(active_players, ans_list))  # Converting to dictionary using stored active player list
        # Updating the text
        self._update_text()


class VoteResults(Scene):
    """
    Scene for showing results of a vote
    """
    def __init__(self):
        Scene.__init__(self)
        # === Text in case of no majority ===
        self.no_majorirty_text = result_font.render("There was no majority vote!", True, black)
        self.no_majorirty_text_pos = (center_text_x(self.no_majorirty_text), screenHeight * 0.4)
        self.hint_text = def_font.render("Next time try to work together to get more information!", True, black)
        self.hint_text_pos = (center_text_x(self.hint_text), screenHeight * 0.55)

        # === Text in case of a majority ===
        self.is_majority = True
        # Majority text
        self.majority_text = result_font.render("The majority voted for:", True, black)
        self.majority_text_pos = (center_text_x(self.majority_text), screenHeight * 0.15)
        # Drumroll variables
        self.drumroll = 0  # Drumroll dot counter
        self.last_tick = pyg.time.get_ticks()  # Last time a drumroll happened
        self.drumroll_finished = False  # Has the drumroll finished
        # Drumroll text
        self.drumroll_text = drumroll_font.render(".  .  .", True, black)
        self.drumroll_text_pos = (center_text_x(self.drumroll_text), screenHeight * 0.25)
        # Majority vote text (username of player that got the majority)
        self.majority_vote_text = drumroll_font.render("PLAYER", True, black)
        self.majority_vote_text_pos = (center_text_x(self.majority_vote_text), screenHeight * 0.45)
        # Final result of vote
        self.show_result = False
        # Final result text
        self.result_text = result_font.render("Was NOT the faker!", True, black)
        self.result_text_pos = (center_text_x(self.result_text), screenHeight * 0.65)

    def start_scene_majority(self, majority_player, was_faker):
        """
        Starts scene in a majority vote way (there was a majority vote)
        :param majority_player: the username of the majority voted player
        :param was_faker: A Boolean indicating if the voted to player is the faker (True - he was, False - was not)
        """

        # Resetting variables accordingly
        self.drumroll_text = drumroll_font.render("", True, black)
        self.is_majority = True
        self.drumroll = 0
        self.drumroll_finished = False

        # Resetting the text
        self.majority_vote_text = drumroll_font.render(f"{majority_player}", True, black)
        self.majority_vote_text_pos = (center_text_x(self.majority_vote_text), screenHeight * 0.45)

        # Resetting result text
        self.show_result = False
        if was_faker:
            self.result_text = result_font.render("Was the faker!", True, black)
            self.result_text_pos = (center_text_x(self.result_text), screenHeight * 0.65)

        else:
            self.result_text = result_font.render("Was NOT the faker!", True, black)
            self.result_text_pos = (center_text_x(self.result_text), screenHeight * 0.65)

        # Resetting the time to the current time
        self.last_tick = pyg.time.get_ticks()

    def start_scene_no_majority(self):
        """
        Starts the scene when there wasn't a majority vote
        """
        self.is_majority = False

    def update(self):
        clock.tick(60)
        if self.is_majority:  # If there was a majority vote we need to animate the drumroll
            if not self.drumroll_finished:  # If the drumroll isn't finished
                # Checking if enough time has passed by comparing the current time to the last drum roll time
                now = pyg.time.get_ticks()
                if now - self.last_tick >= 1000:  # Waiting until a second passes
                    self.last_tick = now  # Updating the last tick
                    self.drumroll += 1    # Incrementing drum roll
                    # Updating drumroll text
                    self.drumroll_text = drumroll_font.render(".  " * min(self.drumroll, 3), True, black)
                    # If we are done with the animation
                    if self.drumroll == 4:
                        self.drumroll_finished = True
            elif not self.show_result:
                # Checking if enough time has passes to show the result
                now = pyg.time.get_ticks()
                if now - self.last_tick >= 1250:
                    self.show_result = True

    def draw(self):
        screen.fill(beige)
        # If there was a majority
        if self.is_majority:
            # Drawing the majority text and drumroll
            screen.blit(self.majority_text, self.majority_text_pos)
            screen.blit(self.drumroll_text, self.drumroll_text_pos)
            if self.drumroll_finished:
                # If the drumroll is finished we draw the majority vote text
                screen.blit(self.majority_vote_text, self.majority_vote_text_pos)
                if self.show_result:
                    # Drawing the result
                    screen.blit(self.result_text, self.result_text_pos)
        else:
            # Else if there wasn't a majority we draw the no majority text
            screen.blit(self.no_majorirty_text, self.no_majorirty_text_pos)
            screen.blit(self.hint_text, self.hint_text_pos)


class RoundResults(Scene):
    """
    Shows results for a game round
    """
    def __init__(self):
        self.player_points = {}  # Dictionary of each player and their points
        # Point title text
        self.points_text = result_font.render("Points each player earned this round:", True, black)
        self.points_text_pos = (center_text_x(self.points_text), screenHeight * 0.1)

    def update(self):
        clock.tick(20)

    def draw(self):
        screen.fill(beige)
        # Variables for dynamically drawing each players name
        draw_count = 0  # How many player have we drawn
        rect_width = screenWidth / 3  # Width of each rect
        width_space = (screenWidth - rect_width * 2) / 3  # Space between the screen border and each rect horizontally
        height_space = screenHeight / 14  # Space between each rect vertically
        cur_width = width_space  # Starting width
        cur_height = height_space * 3  # Starting drawing height
        # Iterating over all active players and dynamically drawing each one
        for player in self.player_points:
            # Drawing rect for current player at the current position
            pyg.draw.rect(screen, dark_beige, pyg.Rect(cur_width, cur_height, rect_width, height_space*2))
            # Drawing the text onto the rect
            p_name = player_name_font.render(f"{player} - {self.player_points[player]}", True, black)
            screen.blit(p_name, (cur_width + rect_width/2 - p_name.get_width() / 2, cur_height + height_space/2 +
                                 (p_name.get_height() / 4)))
            # Updating the position for the next draw
            draw_count += 1
            if draw_count % 2 == 0:  # If we need to go down a line
                cur_height += height_space * 2.5
                if draw_count == len(self.player_points) - 1:
                    # If there's only one more we draw it centered
                    cur_width = (screenWidth - rect_width) / 2
                else:
                    # Resetting the width
                    cur_width -= width_space + rect_width
            else:
                # Need to draw on the same line
                cur_width += width_space + rect_width

        # Drawing point title text
        screen.blit(self.points_text, self.points_text_pos)

    def set_player_points(self, point_list):
        """
        Updates the local variable according to each players points
        :param point_list: points sent by server
        """
        # Making answers into a dictionary with the username and player's answer
        ans_list = point_list.split("&")  # Splitting by &
        # Converting to dictionary using stored active player list
        self.player_points = dict(zip(active_players, ans_list))


class FinalResults(Scene):
    """
    Scene of final game results
    """
    def __init__(self):
        # Variables of minor winner and the winner
        self.best_faker = ""
        self.best_detective = ""
        self.overall_winner_name = ""
        self.overall_winner_points = "0000"

        # Parameters for animation
        self.last_tick = pyg.time.get_ticks()  # Last tick of animation
        self.minor_winners_anim_counter = 0    # Minor winners animation counter
        self.displayed_minor_winners = False   # Displayed minor winner
        self.winner_anim_counter = 0           # Winner animation counter
        self.displayed_winner_name = False     # Displayed winner

        # Faker text
        self.faker_title_text = final_titles_font.render("Best Faker:", True, black)
        self.faker_title_pos = (center_text_x(self.faker_title_text), screenHeight * 0.07)
        # Faker name
        self.faker_name = player_name_font.render(".  .  .", True, black)
        self.faker_name_pos = (center_text_x(self.faker_name),
                               self.faker_title_pos[1] + self.faker_name.get_height() + 30)
        self.cached_faker_name_pos = self.faker_name_pos  # Caching position for later

        # Detective text
        self.detective_title_text = final_titles_font.render("Best Detective:", True, black)
        self.detective_title_pos = (center_text_x(self.detective_title_text), screenHeight * 0.27)

        # Detective name
        self.detective_name = player_name_font.render(".  .  .", True, black)
        self.detective_name_pos = (center_text_x(self.detective_name),
                                   self.detective_title_pos[1] + self.detective_name.get_height() + 30)
        self.cached_detective_name_pos = self.detective_name_pos  # Caching position for later

        # Overall winner text
        self.winner_title_text = overall_winner_font.render("Overall Winner:", True, black)
        self.winner_title_pos = ((screenWidth - self.winner_title_text.get_width()) / 2,
                                 screenHeight * 0.57 - self.winner_title_text.get_height() / 2)
        # Overall winner name
        self.winner_name = winner_font.render(".  .  .", True, black)
        self.winner_name_pos = (center_text_x(self.winner_name), screenHeight * 0.63)
        # Overall winner points text
        self.winner_points_text = winner_font.render("0000", True, black)
        self.winner_points_pos = (0, 0)

    def set_winners(self, winners):
        """
        Resets the scenes parameters and sets the winner variables according to the winner list the server sent
        :param winners: Winner list the server sent
        """
        # The winners are formatted this way: 4 digit number representing the point followed by the name and separated by &
        # Example: 0950Player1&1125Player2&1125Player2
        winners = winners.split("&")  # Splitting into list by &
        self.best_faker = winners[0][4:] + " - " + winners[0][:4]      # Getting faker name and points from win list
        self.best_detective = winners[1][4:] + " - " + winners[1][:4]  # Getting detective name and points from win list
        self.overall_winner_name = winners[2][4:]  # Getting winner name
        # Updating the winner point text
        self.winner_points_text = winner_font.render(f"{winners[2][:4]}", True, black)
        self.winner_points_pos = (center_text_x(self.winner_points_text),
                                  screenHeight * 0.67 + self.winner_name.get_height())

        # === Resetting scene parameters ===
        self.minor_winners_anim_counter = 0
        self.displayed_minor_winners = False
        self.winner_anim_counter = 0
        self.displayed_winner_name = False
        # Faker text
        self.faker_name = final_titles_font.render("", True, black)
        self.faker_name_pos = self.cached_faker_name_pos

        # Detective text
        self.detective_name = final_titles_font.render("", True, black)
        self.detective_name_pos = self.cached_detective_name_pos

        # Overall winner text
        self.winner_name = winner_font.render("", True, black)
        self.winner_title_text = overall_winner_font.render("", True, black)

        # Resetting the time to the current time
        self.last_tick = pyg.time.get_ticks()

    def update(self):
        clock.tick(60)
        if not self.displayed_minor_winners:  # If we haven't finished the minor winner animation
            # Checking if enough time has passed by comparing the current time to the animation
            now = pyg.time.get_ticks()
            if now - self.last_tick >= 1000:  # Until a second passes
                self.last_tick = now  # Updating the last tic
                self.minor_winners_anim_counter += 1  # Incrementing the animation
                # Updating the faker and detective text for the animation
                self.faker_name = player_name_font.render(".  " * min(self.minor_winners_anim_counter, 3), True, black)
                self.detective_name = player_name_font.render(".  " * min(self.minor_winners_anim_counter, 3), True, black)
                # If the animation is done
                if self.minor_winners_anim_counter == 4:
                    self.displayed_minor_winners = True
                    # Updating faker name text
                    self.faker_name = player_name_font.render(self.best_faker, True, black)
                    self.faker_name_pos = (center_text_x(self.faker_name),
                                           self.faker_title_pos[1] + self.faker_name.get_height() + 30)
                    # Updating detective name text
                    self.detective_name = player_name_font.render(self.best_detective, True, black)
                    self.detective_name_pos = (center_text_x(self.detective_name),
                                               self.detective_title_pos[1] + self.detective_name.get_height() + 30)

        elif not self.displayed_winner_name:  # We have finished the minor title animation
            now = pyg.time.get_ticks()
            if now - self.last_tick >= 1275:  # Until a second and a bit passes (for drama!)

                self.last_tick = now
                self.winner_anim_counter += 1
                # Updating winner name for the animation
                self.winner_name = winner_font.render(".  " * min(self.winner_anim_counter, 3), True, black)
                self.winner_title_text = overall_winner_font.render("Overall Winner:", True, black)

                # If the animation is done we display the winner's name
                if self.winner_anim_counter == 4:
                    self.displayed_winner_name = True
                    # Updating the winner's name
                    self.winner_name = winner_font.render(self.overall_winner_name, True, black)
                    self.winner_name_pos = (center_text_x(self.winner_name), screenHeight * 0.63)

    def draw(self):
        screen.fill(beige)
        # Drawing minor titles and name
        screen.blit(self.faker_title_text, self.faker_title_pos)
        screen.blit(self.faker_name, self.faker_name_pos)
        screen.blit(self.detective_title_text, self.detective_title_pos)
        screen.blit(self.detective_name, self.detective_name_pos)
        # If the minor winner animation is done
        if self.displayed_minor_winners:
            # Drawing the overall winner text
            screen.blit(self.winner_title_text, self.winner_title_pos)
            screen.blit(self.winner_name, self.winner_name_pos)
        if self.displayed_winner_name:
            # Drawing the point text
            screen.blit(self.winner_points_text, self.winner_points_pos)
