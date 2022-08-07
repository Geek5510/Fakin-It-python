import pygame as pyg


class Button(pyg.sprite.Sprite):
    """
    UI class for buttons
    """
    def __init__(self, color, pressed_color, x, y, width, height, font=None, text="", text_color=None, method=None):
        """
        Constructor of button class
        :param color: Button color
        :param pressed_color: Button color when pressed
        :param x: Top left x
        :param y: Top left y
        :param width: Button width
        :param height: Button Height
        :param font: Text font object
        :param text: Text to display on button
        :param text_color: Text color
        """
        super().__init__()
        self.color = color
        self.cur_color = color
        self.pressed_color = pressed_color
        self.pos = (x, y)
        self.width = width
        self.height = height
        self.method = method
        # If there's text
        if font and text and text_color:
            self.font = font
            self.text = text
            self.text_color = text_color
        else:  # If there isn't text
            self.font = pyg.font.SysFont(None, 0)
            self.text = ""
            self.text_color = (0, 0, 0)
        self.pressed = False    # Was the button pressed
        self._is_held = False   # Is the button held, for internal use
        self._render_button()   # Rendering for one time in order to set variables correctly

    def _render_button(self):
        """
            Renders the button (Internal use only)
        """
        t_surf = self.font.render(self.text, True, self.text_color, self.cur_color)  # Text surface
        self.image = pyg.Surface((self.width, self.height), pyg.SRCALPHA)
        pyg.draw.rect(self.image, self.cur_color, self.image.get_rect())  # Drawing rect on image
        self.image.blit(t_surf, ((self.width - t_surf.get_width()) / 2, (self.height - t_surf.get_height()) / 2))

        self.rect = self.image.get_rect(topleft=self.pos)  # Updating self rect object

    def update(self, event_list):
        """
        Updates the button using the event list (use for sprite.Group)
        Needs to be called every tick for button to update correctly
        """
        for event in event_list:

            if event.type == pyg.MOUSEBUTTONDOWN and event.button == 1:  # If the user pressed the mouse button down
                m_pos = pyg.mouse.get_pos()

                # If the mouse is on the button
                if self.rect.collidepoint(m_pos):
                    # Updating the color and held boolean
                    self.cur_color = self.pressed_color
                    self._is_held = True

            # If the mouse the button was released
            elif event.type == pyg.MOUSEBUTTONUP and event.button == 1:
                # If the user already started the press on the button
                if self._is_held:
                    self.cur_color = self.color
                    m_pos = pyg.mouse.get_pos()
                    if self.rect.collidepoint(m_pos):
                        # Updating the pressed variable
                        self.pressed = True
                self._is_held = False

        self._render_button()

    def clear_active(self):
        """
            Resets the button's state, use after using button's logic
        """
        self.pressed = False


def main():
    # Test program for button
    pyg.init()
    window = pyg.display.set_mode((600, 600), pyg.DOUBLEBUF)
    window.fill(0)

    font = pyg.font.SysFont(None, 50)  # Leave font name None for default font
    button1 = Button((200, 170, 30), (170, 30, 0), 50, 50, 125, 50, font=font, text="Press", text_color=(255, 255, 255))
    group = pyg.sprite.Group(button1)

    run = True
    while run:
        event_list = pyg.event.get()
        for event in event_list:
            if event.type == pyg.QUIT:
                run = False
        if button1.pressed:
            print("Press!")
            button1.clear_active()

        # Updating the button
        group.update(event_list)
        window.fill(120)
        group.draw(window)
        pyg.display.flip()


if __name__ == "__main__":
    main()
