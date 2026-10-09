import random
import pygame
from game.rope import Rope
from game.player import Puller


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rope = Rope(width, height)
        self.player = Puller(90, height // 2, (50, 120, 220), "PLAYER (A/D)", facing=1)
        self.computer = Puller(width - 90, height // 2, (220, 80, 50), "COMPUTER", facing=-1)

        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"

        # Computer pulling (base values)
        self.base_pull_cooldown = 180      # ms between pulls when calm
        self.computer_pull_cooldown = self.base_pull_cooldown
        self.last_computer_pull = pygame.time.get_ticks()

        # Panic surge settings (Task 2)
        self.panic_start = 0.6
        self.panic_min_cooldown = 150
        self.panic_max_strength = 1.2
        self.panic_active = False
        self.panic_intensity = 0.0

        # Animation state (Task 3)
        self.player_activity = 0.0
        self.momentum = 0.0
        self.prev_marker_x = self.rope.marker_x

        # Match timer & sudden death (Task 4)
        self.sudden_death_time = 45        # seconds before sudden death starts
        self.match_start_time = pygame.time.get_ticks()
        self.elapsed_seconds = 0.0
        self.sudden_death = False

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 26)
        self.font_timer = pygame.font.SysFont(None, 34)

    def power_multiplier(self):
        """Double pulling power for everyone during sudden death."""
        return 2.0 if self.sudden_death else 1.0

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
                self.rope.pull_left(1.0 * self.power_multiplier())
                self.last_key = event.key
                self.player_activity += 0.25

    def update_timer(self):
        """Track match time and switch on sudden death at the limit."""
        now = pygame.time.get_ticks()
        self.elapsed_seconds = (now - self.match_start_time) / 1000.0
        if not self.sudden_death and self.elapsed_seconds >= self.sudden_death_time:
            self.sudden_death = True

    def update_panic(self):
        """Work out how scared the computer is based on how close the player is to winning."""
        center = self.width / 2
        distance_to_player_goal = center - self.rope.left_win_x
        progress = (center - self.rope.marker_x) / distance_to_player_goal
        progress = max(0.0, min(1.0, progress))

        if progress >= self.panic_start:
            self.panic_active = True
            self.panic_intensity = (progress - self.panic_start) / (1.0 - self.panic_start)
        else:
            self.panic_active = False
            self.panic_intensity = 0.0

        self.computer_pull_cooldown = int(
            self.base_pull_cooldown
            - (self.base_pull_cooldown - self.panic_min_cooldown) * self.panic_intensity
        )

    def update_animations(self):
        """Rope tension and puller leaning based on struggle and momentum."""
        self.player_activity *= 0.95
        tension = self.player_activity
        if self.panic_active:
            tension += 0.3 + 0.4 * self.panic_intensity
        if self.sudden_death:
            tension += 0.3
        self.rope.set_tension(min(1.0, tension))

        velocity = self.rope.marker_x - self.prev_marker_x
        self.prev_marker_x = self.rope.marker_x
        self.momentum = self.momentum * 0.9 + velocity * 0.1
        advantage = max(-1.0, min(1.0, -self.momentum / 2.0))

        self.player.update_lean(6 + 14 * advantage)
        self.computer.update_lean(6 - 14 * advantage)

    def update(self):
        if self.game_state != "PLAYING":
            return

        self.update_timer()
        self.update_panic()

        now = pygame.time.get_ticks()
        if now - self.last_computer_pull >= self.computer_pull_cooldown:
            computer_variance = random.uniform(0.7, 1.2)
            if self.panic_active:
                surge = 1.1 + (self.panic_max_strength - 1.1) * self.panic_intensity
                computer_variance *= surge
            computer_variance *= self.power_multiplier()
            self.rope.pull_right(computer_variance)
            self.last_computer_pull = now

        self.update_animations()

        result = self.rope.check_winner()
        if result:
            self.winner = result
            self.game_state = "GAME_OVER"   # timer freezes here (update stops running)

    def reset(self):
        self.rope.reset()
        self.player.reset()
        self.computer.reset()
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self.computer_pull_cooldown = self.base_pull_cooldown
        self.panic_active = False
        self.panic_intensity = 0.0
        self.player_activity = 0.0
        self.momentum = 0.0
        self.prev_marker_x = self.rope.marker_x
        self.match_start_time = pygame.time.get_ticks()
        self.elapsed_seconds = 0.0
        self.sudden_death = False
        self.last_computer_pull = pygame.time.get_ticks()

    def render_timer(self, screen):
        total = int(self.elapsed_seconds)
        minutes, seconds = divmod(total, 60)
        timer_text = f"TIME  {minutes}:{seconds:02d}"
        color = (255, 80, 80) if self.sudden_death else (240, 240, 240)
        timer_surf = self.font_timer.render(timer_text, True, color)
        screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 10))

    def render(self, screen):
        screen.fill((30, 32, 36))

        mud_rect = pygame.Rect(self.width // 2 - 120, self.height // 2 - 80, 240, 160)
        pygame.draw.rect(screen, (45, 38, 30), mud_rect, border_radius=12)

        self.rope.render(screen)
        self.player.render(screen, self.rope.get_y_at(self.player.x + 30))
        self.computer.render(screen, self.rope.get_y_at(self.computer.x - 30))

        self.render_timer(screen)

        inst_surf = self.font_small.render(
            "Alternate [A] and [D] keys rapidly to pull!", True, (210, 210, 210)
        )
        screen.blit(inst_surf, (self.width // 2 - inst_surf.get_width() // 2, 40))

        # Flashing sudden death banner
        if self.sudden_death and self.game_state == "PLAYING":
            if (pygame.time.get_ticks() // 300) % 2 == 0:
                sd_surf = self.font_big.render("SUDDEN DEATH!  x2 POWER", True, (255, 200, 50))
                screen.blit(sd_surf, (self.width // 2 - sd_surf.get_width() // 2, 75))

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