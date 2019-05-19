from __future__ import division
import sys, os, socket
from _thread import *
import math, random
import datetime
import pygame

from protocol import read_command, set_command, get_ip, BattleProtocol

colors = {0:[0,0,0], 1:[255,0,0], 2:[0,255,0], 3:[0,0,255]}

def load_image_convert_alpha(filename):
    """Load an image with the given filename from the images directory"""
    return pygame.image.load(os.path.join('images', filename)).convert_alpha()

def draw_centered(surface1, surface2, position):
    """Draw surface1 onto surface2 with center at position"""
    rect = surface1.get_rect()
    rect = rect.move(position[0]-rect.width//2, position[1]-rect.height//2)
    surface2.blit(surface1, rect)

def rotate_center(image, rect, angle):
        """rotate the given image around its center & return an image & rect"""
        rotate_image = pygame.transform.rotate(image, angle)
        rotate_rect = rotate_image.get_rect(center=rect.center)
        return rotate_image,rotate_rect

def distance(p, q):
    """Helper function to calculate distance between 2 points"""
    return math.sqrt((p[0]-q[0])**2 + (p[1]-q[1])**2)

class Ship():
    def __init__(self, position, color=""):
        if color == "friend":
            self.image_off = load_image_convert_alpha("friend_ship_off.png")
            self.image_on = load_image_convert_alpha("friend_ship_on.png")
        else:
            self.image_off = load_image_convert_alpha("enemy_ship_off.png")
            self.image_on = load_image_convert_alpha("enemy_ship_on.png")

        self.position = position[:]
        self.speed = 0
        self.angle = 0
        self.active_missiles = []
        self.is_on = False
        self.direction = [0,-1]
        self.fire_missile = 0

        self.width = 800
        self.height = 600

    def draw(self, game_screen):
        if self.is_on:
            new_image, rect = rotate_center(self.image_on, self.image_on.get_rect(), self.angle)
        else:
            new_image, rect = rotate_center(self.image_off, self.image_off.get_rect(), self.angle)
        
        draw_centered(new_image, game_screen, self.position)

    def move(self):
        # calculate the direction from the angle variable
        self.direction[0] = math.sin(-math.radians(self.angle))
        self.direction[1] = -math.cos(math.radians(self.angle))

        # calculate the position from the direction and speed
        self.position[0] += self.direction[0]*self.speed
        self.position[1] += self.direction[1]*self.speed

        self.position[0] = min(self.position[0], self.width)
        self.position[0] = max(self.position[0], 0)

        self.position[1] = min(self.position[1], self.height)
        self.position[1] = max(self.position[1], 0)


    def fire(self):
        adjust = [0, 0]
        adjust[0] = math.sin(-math.radians(self.angle))*self.image_on.get_width()
        adjust[1] = -math.cos(math.radians(self.angle))*self.image_on.get_height()
        new_missile = Missile((self.position[0]+adjust[0],\
                               self.position[1]+adjust[1]/2),\
                               self.angle)
        self.active_missiles.append(new_missile)

    # def size(self):
    #     return max(self.image_on.get_height(),self.image_on.get_width())

    # def radius(self):
    #     return self.image_on.get_width()/2

class Missile():
    def __init__(self, position, angle, speed=15):
        self.angle = angle
        self.direction = [0, 0]
        self.speed = speed        
        self.image = load_image_convert_alpha("missile.png")
        self.position = list(position[:])
        self.speed = speed

    def draw_on(self, screen):
        draw_centered(self.image, screen, self.position)

    def size(self):
        return max(self.image.get_height(), self.image.get_width())

    def radius(self):
        return self.image.get_width()/2

    def out_of_screen(self):
        if self.position[0] < 0 or self.position[1] < 0 or self.position[0] > 800 or self.position[1] > 800:
            return True
        else:
            return False

    def move(self):
        self.direction[0] = math.sin(-math.radians(self.angle))
        self.direction[1] = -math.cos(math.radians(self.angle))
        self.position[0] += self.direction[0]*self.speed
        self.position[1] += self.direction[1]*self.speed

class Game(object):
    REFRESH, START, RESTART = range(pygame.USEREVENT, pygame.USEREVENT+3)

    def __init__(self, connection):
        pygame.mixer.init()
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()

        self.big_font = pygame.font.SysFont(None, 100)
        self.medium_font = pygame.font.SysFont(None, 50)
        self.small_font = pygame.font.SysFont(None, 25)

        self.angle = 0
        self.player = -1
        self.conn = connection
        self.hit = 0

        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))

        self.bg_color = 255, 255, 255
        self.fire_missile = 0

        self.FPS = 30
        pygame.time.set_timer(self.REFRESH, 1000//self.FPS)
        
        self.ship = None
        self.enimies_ships = {}

        self.fire_time = datetime.datetime.now()

    def run(self):

        # Inicia as primeiras naves inimigas 
        ans = self.conn.receive()
        command = read_command(ans)
        self.ship = Ship(command[:2], "friend")
        self.ship.angle = command[1]
        self.player = int(float(command[4]))

        self.conn.send("ok")
        ans = self.conn.receive()

        enimies = [read_command(cmd) for cmd in ans.split(";")]
        for e in enimies:
            pos = e[0:2]
            angle = e[2]
            player_id = e[4]

            ship = Ship(pos)
            ship.angle = angle
            self.enimies_ships[player_id] = ship
            
        running = True
        while running:
            self.fire_missile = 0
            
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                running = False 
            keys = pygame.key.get_pressed()
            
            if keys[pygame.K_SPACE]:
                new_time = datetime.datetime.now()
                if new_time - self.fire_time > datetime.timedelta(seconds=0.25):
                    self.fire_missile = 1
                    self.fire_time = new_time
           
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.ship.angle -= 10
                self.ship.angle %= 360

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.ship.angle += 10
                self.ship.angle %= 360

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.ship.is_on = True
                if self.ship.speed < 20:
                    self.ship.speed += 1
            else:
                if self.ship.speed > 0:
                    self.ship.speed -= 1
                self.ship.is_on = False   


            self.conn.send(set_command([self.ship.position[0], self.ship.position[1], self.ship.angle, self.fire_missile, self.player]))
            enimies = self.conn.receive()
            print("RECIEVE: " + enimies)
            if enimies.find("HIT") != -1:
                self.endGame(enimies)
                running = False
                break

            enimies = [read_command(cmd) for cmd in enimies.split(";")]

            self.update_ship(self.ship)
            if self.fire_missile:
                print("SENDINF FIRE NOW")
                self.ship.fire()

            for e in enimies:
                pos = e[0:2]
                angle = e[2]
                fire = e[3]
                player_id = int(float(e[4]))

                if self.enimies_ships[player_id].position == pos:
                    self.enimies_ships[player_id].is_on = False
                else:
                    self.enimies_ships[player_id].is_on = True

                self.enimies_ships[player_id].position = pos
                self.enimies_ships[player_id].angle = angle
                

                self.update_ship(self.enimies_ships[player_id])
                if fire: self.enimies_ships[player_id].fire()

            self.draw()

            for m in self.ship.active_missiles:
                for i in self.enimies_ships.keys():
                    if distance(m.position, self.enimies_ships[i].position) < 15:
                        print("PLAYER {} HIT PLAYER {}".format(self.player, i))
                        self.conn.send("HIT,{},{}".format(int(self.player), int(i)))
                        running = False
                        self.endGame("HIT,{},{}".format(int(self.player), int(i)))
                        break

    def update_ship(self, ship):
        ship.move()

        if len(ship.active_missiles) >  0:
            remove_list = []
            for i in range(len(ship.active_missiles)):
                ship.active_missiles[i].move()
                if ship.active_missiles[i].out_of_screen():
                    remove_list.append(i)

            for i in remove_list[::-1]:
                del ship.active_missiles[i]

    def draw(self):
        self.screen.fill(self.bg_color)
        self.ship.draw(self.screen)
        if len(self.ship.active_missiles) >  0:
            for missile in self.ship.active_missiles:
                missile.draw_on(self.screen)

        for key in self.enimies_ships.keys():
            e_ship = self.enimies_ships[key]
            e_ship.draw(self.screen)

            if len(e_ship.active_missiles) >  0:
                for missile in e_ship.active_missiles:
                    missile.draw_on(self.screen)

        self.draw_player_number()
        pygame.display.flip()
    
    def draw_player_number(self):
        player_text = self.small_font.render("Player {}".format(self.player), True, (0,0,0))
        draw_centered(player_text, self.screen, (self.width//2, player_text.get_height()))

    def endGame(self, command):
        running = True
        winner, loser = [int(i) for i in command.split(',')[1:]]
        if self.player == winner:
            self.title = self.big_font.render("Victory!", True, (255,215,0))
        else:
            self.title = self.big_font.render("Sorry :(", True, (255,215,0))
        
        self.reulst = self.medium_font.render("Player {} ended player {}".format(winner, loser), True, (35, 107, 142))
        self.return_msg = self.medium_font.render("Press [ENTER] to exit".format(winner, loser), True, (35, 107, 142))

        while running:
            self.screen.fill(self.bg_color)

            # draw the ending texts
            draw_centered(self.title, self.screen,\
                (self.width//2, self.height//2\
                    -self.title.get_height()))

            draw_centered(self.reulst, self.screen,\
                (self.width//2, self.height//2\
                    +self.reulst.get_height()))

            draw_centered(self.return_msg, self.screen,\
                (self.width//2, self.height//2\
                    +self.reulst.get_height() + self.return_msg.get_height()))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        running = False

    def welcome_screen(self):
        init_game = 0
        while True:

            if init_game == 1:
                reply = "init"
            else:
                reply = "wait"
            
            print("Sending " + reply)
            n.send(reply)

            ans = n.receive()
            print("Received " + ans)
            if ans == "play":
                # init_game = 1
                break

            self.players = self.welcome_asteroids = self.big_font.render("Battle",\
                                                True, (255, 215, 0))
            self.welcome_desc =  self.medium_font.render(\
            "[Press Space] to begin! {} players online".format(ans), True, (35, 107, 142))

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and ans != "1":
                        init_game = 1

            self.screen.fill(self.bg_color)

            # draw the welcome texts
            draw_centered(self.welcome_asteroids, self.screen,\
                (self.width//2, self.height//2\
                    -self.welcome_asteroids.get_height()))

            draw_centered(self.welcome_desc, self.screen,\
                (self.width//2, self.height//2\
                    +self.welcome_desc.get_height()))
    
            pygame.display.flip()
        
        print("Exit Welcome")


if __name__ == "__main__":
    
    n = BattleProtocol()
    game = Game(n)
    game.welcome_screen()
    game.run()