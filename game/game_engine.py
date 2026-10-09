import random
import pygame
from game.rope import Rope
from game.player import Puller


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rope = Rope(width, height)
        self.player = Puller(90, height // 2, (50, 120, 220), "PLAYER (A/D)")
        self.computer = Puller(width - 90, height // 2, (220, 80, 50), "COMPUTER")

        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"

        # Computer pulling (base values)
        self.base_pull_cooldown = 180      # ms between pulls when calm
        self.computer_pull_cooldown = self.base_pull_cooldown
        self.last_computer_pull = pygame.time.get_ticks()

        # Panic surge settings
        self.panic_start = 0.6             # panic once player is 60% of the way to winning
        self.panic_min_cooldown = 150      # fastest pull interval at max panic (ms)
        self.panic_max_strength = 1.2      # strength multiplier at max panic
        self.panic_active = False
        self.panic_intensity = 0.0         # 0.0 = calm, 1.0 = max panic

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 26)

    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        # Every fresh KEYDOWN of the *other* key counts as a pull.
        # No lock / KEYUP dependency, so overlapping or very fast
        # alternating presses can never freeze input.
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_a, pygame.K_d):
            if event.key != self.last_key:
                self.rope.pull_left(1.0)
                self.last_key = event.key

    def update_panic(self):
        """Work out how scared the computer is based on how close the player is to winning."""
        center = self.width / 2
        distance_to_player_goal = center - self.rope.left_win_x
        progress = (center - self.rope.marker_x) / distance_to_player_goal
        progress = max(0.0, min(1.0, progress))   # 0 = center, 1 = player's goal line

        if progress >= self.panic_start:
            self.panic_active = True
            self.panic_intensity = (progress - self.panic_start) / (1.0 - self.panic_start)
        else:
            self.panic_active = False
            self.panic_intensity = 0.0

        # Faster pulls the more panicked it is
        self.computer_pull_cooldown = int(
            self.base_pull_cooldown
            - (self.base_pull_cooldown - self.panic_min_cooldown) * self.panic_intensity
        )

    def update(self):
        if self.game_state != "PLAYING":
            return

        self.update_panic()

        now = pygame.time.get_ticks()
        if now - self.last_computer_pull >= self.computer_pull_cooldown:
            computer_variance = random.uniform(0.7, 1.2)
            if self.panic_active:
                # Stronger pulls during panic (1.1x up to panic_max_strength)
                surge = 1.1 + (self.panic_max_strength - 1.1) * self.panic_intensity
                computer_variance *= surge
            self.rope.pull_right(computer_variance)
            self.last_computer_pull = now

        result = self.rope.check_winner()
        if result:
            self.winner = result
            self.game_state = "GAME_OVER"

    def reset(self):
        self.rope.reset()
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self.computer_pull_cooldown = self.base_pull_cooldown
        self.panic_active = False
        self.panic_intensity = 0.0
        self.last_computer_pull = pygame.time.get_ticks()

    def render(self, screen):
        screen.fill((30, 32, 36))

        mud_rect = pygame.Rect(self.width // 2 - 120, self.height // 2 - 80, 240, 160)
        pygame.draw.rect(screen, (45, 38, 30), mud_rect, border_radius=12)

        self.rope.render(screen)
        self.player.render(screen)
        self.computer.render(screen)

        inst_surf = self.font_small.render(
            "Alternate [A] and [D] keys rapidly to pull!", True, (210, 210, 210)
        )
        screen.blit(inst_surf, (self.width // 2 - inst_surf.get_width() // 2, 40))

        # Flashing panic warning
        if self.panic_active and self.game_state == "PLAYING":
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                panic_surf = self.font_big.render("COMPUTER PANIC!", True, (255, 70, 70))
                screen.blit(
                    panic_surf,
                    (self.width // 2 - panic_surf.get_width() // 2, self.height - 90)
                )

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            win_text = f"{self.winner} WINS!"
            color = (80, 220, 80) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(
                text_surf,
                (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 50)
            )

            restart_surf = self.font_small.render(
                "Press [R] to Play Again", True, (240, 240, 240)
            )
            screen.blit(
                restart_surf,
                (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 10)
            )