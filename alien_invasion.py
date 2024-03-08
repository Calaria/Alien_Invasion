import sys
import pygame
from time import sleep
# from created files
from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from button import Button
from game_stats import GameStats
from scoreboard import Scoreboard


class AlienInvasion:

    def __init__(self):
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.is_fullscreen = False
        pygame.display.set_caption("Alien Invasion")
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()
        self.play_button = Button(self, "play")

    def run_game(self):
        while True:
            self._check_events()
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            self._update_screen()

    def _change_fleet_direction(self):
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _check_bullet_alien_collisions(self):
        collision = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
        if not self.aliens:  # no aliens remaining
            self.bullets.empty()
            self._create_fleet()
            # aliens upgraded after complete annihilation
            self.settings.increase_speed()
            self.stats.level += 1
            # prepare remaining ships
            self.sb.prep_level()
        if collision:
            for aliens in collision.values():  # score correctly for multiple targets
                self.stats.score += self.settings.alien_points * len(aliens)
                self.sb.prep_score()   # prepare the diplay of score
                self.sb.check_high_score()   # prepare the highest score

    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            # make direction keys control the ship's movement
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            # detect the mouse click position
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        # make direction keys control the ship's movement
        moment_keys = {
            pygame.K_RIGHT: "moving_right",
            pygame.K_LEFT: "moving_left",
            pygame.K_UP: "moving_up",
            pygame.K_DOWN: "moving_down"}
        if event.key in moment_keys:
            setattr(self.ship, moment_keys[event.key], True)

        elif event.key == pygame.K_q:
            sys.exit()
        # personalized screen size
        elif event.key == pygame.K_f:
            self._toggle_fullscreen()
        # shoot bullets
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):  # make direction keys control the ship's movement
        moment_keys = {
            pygame.K_RIGHT: "moving_right",
            pygame.K_LEFT: "moving_left",
            pygame.K_UP: "moving_up",
            pygame.K_DOWN: "moving_down"}
        if event.key in moment_keys:
            setattr(self.ship, moment_keys[event.key], False)

    def _create_fleet(self):  # creat an alien swarm
        rows_number, alien_number_x = self._get_available_space()  # obtain alien alien capacity
        for row_number in range(rows_number):
            for alien_number in range(alien_number_x - 2):
                self._create_alien(alien_number, row_number)

    def _check_fleet_edges(self):  # aliens change direction when hitting boundry
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _check_play_button(self, mouse_pos):  # initialize all settings after clicking "play"
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and self.stats.game_active is False:
            # initialize settings
            self.settings.initialize_dynamic_settings()
            self.stats.reset_stats()
            self.stats.game_active = True
            # prepare game interface
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            pygame.mouse.set_visible(False)

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship.center_ship()

    def _create_alien(self, alien_number, row_number):  # fill the limited screen with aliens
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _fire_bullet(self):  # fire bullets
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _get_available_space(self):  # compute the spatial capacity for aliens
        alien = Alien(self)
        self.aliens.add(alien)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        alien_number_x = available_space_x // (2 * alien_width)
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height -
                             (3 * alien_height) - ship_height)
        rows_number = available_space_y // (2 * alien_height)
        return rows_number, alien_number_x


    def _ship_hit(self):
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1
            self.sb.prep_ships()
            self.aliens.empty()
            self.bullets.empty()
            self.ship.center_ship()
            self._create_fleet()
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _toggle_fullscreen(self):

        if not self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.is_fullscreen = not self.is_fullscreen

    def _update_bullets(self):
        self.bullets.update()
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _update_aliens(self):
        self._check_fleet_edges()
        self.aliens.update()
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
        self._check_aliens_bottom()

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        self.sb.show_score()
        if not self.stats.game_active:
            self.play_button.draw_button()
        pygame.display.flip()


if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()
