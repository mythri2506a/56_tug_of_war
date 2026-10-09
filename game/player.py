import math
import pygame


class Puller:
    """Represents a puller character anchor on either side of the rope."""

    def __init__(self, x, y, color, label, facing=1):
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.facing = facing          # +1 = rope is to the right, -1 = rope is to the left
        self.lean = 0.0               # degrees; positive = leaning backward (away from rope)
        self.font = pygame.font.SysFont(None, 24)

    def update_lean(self, target_lean):
        """Smoothly move the lean angle toward the target."""
        self.lean += (target_lean - self.lean) * 0.15

    def reset(self):
        self.lean = 0.0

    def render(self, surface, hand_y=None):
        """Draw avatar (leaning around the feet) and label."""
        pivot_x, pivot_y = self.x, self.y + 35        # feet
        theta = math.radians(self.lean) * (-self.facing)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        def rot(rx, ry):
            return (pivot_x + rx * cos_t - ry * sin_t,
                    pivot_y + rx * sin_t + ry * cos_t)

        # Body (rotated rectangle)
        body = [rot(-20, 0), rot(20, 0), rot(20, -70), rot(-20, -70)]
        pygame.draw.polygon(surface, self.color, body)

        # Head
        head = rot(0, -85)
        pygame.draw.circle(surface, (240, 210, 180), (int(head[0]), int(head[1])), 16)

        # Arm reaching to the rope
        if hand_y is not None:
            shoulder = rot(self.facing * 12, -55)
            hand = (self.x + self.facing * 30, hand_y)
            pygame.draw.line(surface, (240, 210, 180), shoulder, hand, 6)
            pygame.draw.circle(surface, (240, 210, 180), (int(hand[0]), int(hand[1])), 5)

        # Name / control tag
        label_surf = self.font.render(self.label, True, (240, 240, 240))
        surface.blit(label_surf, (self.x - label_surf.get_width() // 2, self.y + 45))