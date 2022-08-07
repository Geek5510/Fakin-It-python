# GitHub:
# https://github.com/Rabbid76/PyGameExamplesAndAnswers/blob/master/documentation/pygame/pygame_event_and_application_loop.md
#
# Stack Overflow:
# https://stackoverflow.com/questions/46390231/how-to-create-a-text-input-box-with-pygame/64613666#64613666

import pygame


class TextInputBox(pygame.sprite.Sprite):

    def __init__(self, color, x, y, w, font, backcolor=None, max_letters=None, default_text="Type Here...", def_color=(128, 128, 128)):
        """
        Constructor
        :param color: color of box and test
        :param x: x coordinate of top left corner of box
        :param y: y coordinate of top left corner of box
        :param w: width of box
        :param font: font to use
        :param backcolor: background color
        :param max_letters: max amount of letters to allow
        :param default_text: default text to show
        :param def_color: color of default text
        """
        super().__init__()
        self.text_color = color
        self.border_color = color
        self.backcolor = backcolor
        self.max_letters = max_letters
        self.pos = (x, y)
        self.width = w
        self.font = font
        self.active = False
        self.text = ""
        self.def_text = default_text
        self.def_color = def_color
        self._render_text()

    def _render_text(self):
        """
        Renders the text (Internal use only)
        """
        if self.text == "":  # If text is empty we display the default text in a gray color
            box_text = self.def_text
            draw_color = self.def_color
        else:  # Else we display the normal text
            box_text = self.text
            draw_color = self.text_color

        t_surf = self.font.render(box_text, True, draw_color, self.backcolor)  # Text surface
        self.image = pygame.Surface((max(self.width, t_surf.get_width()+10), t_surf.get_height()+10), pygame.SRCALPHA)
        if self.backcolor:
            self.image.fill(self.backcolor)  # Filling back color
        self.image.blit(t_surf, ((self.width-t_surf.get_width())/2, 5))  # Displaying image of text
        pygame.draw.rect(self.image, self.border_color, self.image.get_rect(), 1)  # Drawing rect on image
        self.rect = self.image.get_rect(topleft=self.pos)  # Updating self rect object

    def update(self, event_list):
        """
        Updates the text using the event list (use for sprite.Group)
        Needs to be called every tick for text to update correctly
        """
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)

            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if self.max_letters is None or len(self.text) < self.max_letters:
                        if event.unicode.isalpha() or event.unicode.isdigit() or event.unicode == " ":
                            self.text += event.unicode
                self._render_text()

    def get_text(self):
        """
        :return: text written in textbox
        """
        return self.text

    def clear(self):
        """
        clears the text written
        """
        self.text = ""
        self._render_text()


# ====== Example program of how to use text box ======
def main():

    pygame.init()
    window = pygame.display.set_mode((600, 600), pygame.DOUBLEBUF)
    window.fill(0)

    # Creating font object to use

    # font = pygame.font.Font("Sprites\Fonts\COMIC.TTF", 100) <-- How to use custom font
    # font = pygame.font.SysFont("Times New Roman", 100) <-- How to use different system font
    font = pygame.font.SysFont(None, 100)  # Leave font name None for default font

    # Creating two text boxes
    text_input_box = TextInputBox((0, 70, 255), 50, 50, 410, font, backcolor=(255, 255, 255), max_letters=10)
    text_input_box2 = TextInputBox((70, 0, 255), 50, 150, 410, font)

    # Creating group of text
    group = pygame.sprite.Group(text_input_box, text_input_box2)

    run = True
    while run:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    print(text_input_box.get_text())
                    text_input_box.clear()
        # Updating the text boxes
        group.update(event_list)
        window.fill(120)
        group.draw(window)
        pygame.display.flip()

    pygame.quit()
    exit()


if __name__ == "__main__":
    main()
