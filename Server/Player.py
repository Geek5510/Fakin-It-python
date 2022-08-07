class Player:
    def __init__(self, ip, key, username):
        """
        Data storing class for server
        :param ip: IP of player
        :param key: AES encryption and decryption key
        :param username: Username of player
        """
        self.ip = ip                 # Associated ip of player
        self.key = key               # AES key for encrypted communication
        self.username = username     # Username of player
        self.detective_points = 0    # Points earned from voting to the faker
        self.faker_points = 0        # Points earned from being a faker
        self.cur_round_point = 0     # Points earned from current round (For round results)
        self.vote_counter = 0        # Counts how many votes this player got
        self.current_ans = ""        # Current answer to task / current vote
        self.chose_category = False  # Has the player chosen a category this game?
        self.ready = False           # Is the player ready to start the game?

    def get_points(self):
        """
        :return: Total amount of points player has
        """
        return self.detective_points + self.faker_points
