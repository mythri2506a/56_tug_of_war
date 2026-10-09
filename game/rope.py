import math
import pygame


class Rope:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_y = screen_height // 2
        self.marker_x = screen_width // 2

        self.left_win_x = 180
        self.right_win_x = screen_width - 180
        self.pull_step = 12

        # Visual tension: 0.0 = slack (sags), 1.0 = very tight (vibrates)
        self.tension = 0.0
        self.max_sag = 18
        self.vibration_amp = 5
        self.rope_left = 60
        self.rope_right = screen_width - 60

    def pull_left(self, strength=1.0):
        self.marker_x -= int(self.pull_step * strength)

    def pull_right(self, strength=1.0):
        self.marker_x += int(self.pull_step * strength)

    def set_tension(self, tension):
        self.tension = max(0.0, min(1.0, tension))

    def check_winner(self):
        if self.marker_x <= self.left_win_x:
            return "PLAYER"
        if self.marker_x >= self.right_win_x:
            return "COMPUTER"
        return None

    def reset(self):
        self.marker_x = float(self.screen_width // 2)
        self.velocity = 0.0
        self.tension = 0.0

    def get_y_at(self, x):
        """Rope height at a given x: sag when slack, vibration when tight."""
        t = (x - self.rope_left) / (self.rope_right - self.rope_left)
        t = max(0.0, min(1.0, t))
        envelope = math.sin(math.pi * t)                 # 0 at ends, 1 in the middle
        sag = (1.0 - self.tension) * self.max_sag * envelope
        now = pygame.time.get_ticks()
        vibration = (self.tension * self.vibration_amp
                     * math.sin(t * math.pi * 12 + now * 0.05) * envelope)
        return self.center_y + sag + vibration

    def render(self, surface):
        # Rope colour gets brighter as it gets tighter
        base = (180, 140, 90)
        tight = (235, 200, 120)
        color = tuple(int(b + (tt - b) * self.tension) for b, tt in zip(base, tight))

        points = [(x, self.get_y_at(x))
                  for x in range(self.rope_left, self.rope_right + 1, 6)]
        pygame.draw.lines(surface, color, False, points, 8)

        pygame.draw.line(
            surface,
            (50, 200, 50),
            (self.left_win_x, self.center_y - 40),
            (self.left_win_x, self.center_y + 40),
            4
        )
        pygame.draw.line(
            surface,
            (200, 50, 50),
            (self.right_win_x, self.center_y - 40),
            (self.right_win_x, self.center_y + 40),
            4
        )

        pygame.draw.line(
            surface,
            (120, 120, 120),
            (self.screen_width // 2, self.center_y - 20),
            (self.screen_width // 2, self.center_y + 20),
            2
        )

        # Flag follows the rope's current shape
        flag_y = int(self.get_y_at(self.marker_x))
        flag_rect = pygame.Rect(int(self.marker_x) - 12, flag_y - 24, 24, 48)
        pygame.draw.rect(surface, (230, 40, 40), flag_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), flag_rect, width=2, border_radius=4)