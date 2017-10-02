import pygame
import pickle
import math
import os.path
import random
import socket
from _thread import *
from queue import Queue
import inputbox

# global variables
black = (0,0,0)
white = (255,255,255)
blue = (50, 50, 255)
red = (255,0,0)
green = (20,245,45)
yellow = (255,255,50)
purple = (165,50,255)
orange = (255,155,0)

screen_width = 800
screen_height = 600



# player class
class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        # self.image = pygame.Surface((30,30))
        # self.image.fill(white)
        self.image = pygame.Surface((30,30))
        self.image.set_colorkey((0,0,0))
        self.rightImage = pygame.image.load("kidWalkRight.png").convert()
        self.leftImage = pygame.image.load("kidWalkLeft.png").convert()
        pygame.transform.scale(self.rightImage,(30,30),self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.change_x = 0
        self.change_y = 0
        self.spikes = None
        self.room = None
        self.double_jump = 2
        self.bullet_list = pygame.sprite.Group()
        self.direction = 1

    # calculate the gravity so the player can jump accordingly
    def gravity(self):
        if self.change_y == 0:
            self.change_y = 2
        else:
            self.change_y += 0.8


    def jump(self):
        # go down a little bit to check if we are on the ground
        self.rect.y += 2
        wall_hit_list = pygame.sprite.spritecollide(self, 
            self.room.wall_list,False)
        platform_hit_list = pygame.sprite.spritecollide(self,
            self.room.platform_list,False)
        self.rect.y -= 2
        # if the player is on the ground, we can jump
        if len(wall_hit_list) > 0 or len(platform_hit_list) > 0:
            self.change_y = -9
            self.double_jump = 1
        # the player can double jump
        elif self.double_jump <= 1:
            self.change_y = -9
            self.double_jump += 1
        else:
            self.double_jump = 2

    # update the player's positions
    def updateWall(self):
        self.gravity()
        # make sure we don't cross the walls
        self.rect.x += self.change_x
        block_hit_list = pygame.sprite.spritecollide(self, 
            self.room.wall_list, False)
        for block in block_hit_list:
            self.rect.y += 2
            platform_hit_list = pygame.sprite.spritecollide(self,
                self.room.platform_list, False)
            self.rect.y -= 2
            if self.change_x > 0 and pygame.sprite.collide_rect(self,block):
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                self.rect.left = block.rect.right
            elif len(platform_hit_list) != 0:
                self.rect.top = block.rect.bottom
        self.rect.y += self.change_y
        block_hit_list = pygame.sprite.spritecollide(self, 
            self.room.wall_list, False)
        for block in block_hit_list:
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom
            self.change_y = 0
        if self.rect.bottom > screen_height + 30:
            self.room.over = True

    def updatePlatform(self):
        for platform in self.room.platform_list:
            if (platform.rect.bottom == self.rect.top and platform.rect.x <
                self.rect.x < platform.rect.right and 
                type(platform) == MovingPlatform):
                platform.change_y *= -1
            if platform.rect.top == self.rect.bottom:
                block_hit_list = pygame.sprite.spritecollide(self,
                    self.room.wall_list,False)
                if len(block_hit_list) > 0:
                    platform.change_y *= -1

    def updateBullet(self):
        self.bullet_list.update()
        for bullet in self.bullet_list:
            bullet_hit_list = pygame.sprite.spritecollide(bullet, 
                self.room.wall_list, False)
            if len(bullet_hit_list) > 0:
                self.bullet_list.remove(bullet)
            if bullet.rect.x < -5 or bullet.rect.x > screen_width:
                self.bullet_list.remove(bullet)

    def update(self):
        self.updatePlatform()
        self.updateBullet()
        self.updateWall()

    def go_left(self):
        self.change_x = -5
        self.direction = -1
        pygame.transform.scale(self.leftImage,(30,30),self.image)


    def go_right(self):
        self.change_x = 5
        self.direction = 1
        pygame.transform.scale(self.rightImage,(30,30),self.image)

    def stop(self):
        self.change_x = 0

    def fire(self):
        bullet = Bullet(self.direction,0)
        bullet.rect.x = self.rect.x
        bullet.rect.y = self.rect.y + 15
        self.bullet_list.add(bullet)


class ConveyorBelt(pygame.sprite.Sprite):
    def __init__(self, x, y, player, changex = 0, changey = 0, width = 40, height = 40):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.leftImage = pygame.image.load("ConveyorBeltLeft.png").convert()
        self.rightImage = pygame.image.load("ConveyorBeltRight.png").convert()
        self.upImage = pygame.image.load("ConveyorBeltUp.png").convert()
        pygame.transform.scale(self.rightImage,(width,height),self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.change_x = changex
        self.change_y = changey
        self.player = player

    def update(self):
        if (self.rect.x - self.player.rect.width < self.player.rect.x < self.rect.right 
            and self.player.rect.bottom == self.rect.top):
            self.player.change_x += self.change_x
            self.player.change_y += self.change_y
        if self.change_x > 0:
            pygame.transform.scale(self.rightImage,(self.rect.width,
                self.rect.height),self.image)
        if self.change_x < 0:
            pygame.transform.scale(self.leftImage,(self.rect.width,
                self.rect.height),self.image)
        if self.change_y < 0:
            pygame.transform.scale(self.upImage,(self.rect.width,
                self.rect.height),self.image)            
        

class Bullet(pygame.sprite.Sprite):
    def __init__(self,xdirection,ydirection):
        super().__init__()
        self.image = pygame.Surface([4,4])
        self.image.fill(black)
        self.rect = self.image.get_rect()
        self.xdirection = xdirection
        self.ydirection = ydirection

    def update(self):
        self.rect.x += self.xdirection * 10
        self.rect.y += self.ydirection * 10


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width = 40, height = 40):
        super().__init__()
        self.image = pygame.Surface([width, height])
        image = pygame.image.load("Block2.png").convert()
        pygame.transform.scale(image,(width,height),self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class DisappearWall(Wall):
    def __init__(self, x, y,width = 40,height = 40):
        super().__init__(x,y,width,height)


class StickyWall(Wall):
    def __init__(self,x,y,player,width = 40, height = 40):
        super().__init__(x,y,width,height)
        self.image = pygame.Surface([width, height])
        image = pygame.image.load("StickyWall.png").convert()
        pygame.transform.scale(image,(width,height),self.image)
        self.player = player

    def update(self):
        if (self.rect.y - 30 <= self.player.rect.y <= self.rect.bottom and 
            (self.rect.right == self.player.rect.left or 
            self.rect.left == self.player.rect.right)):
            self.player.double_jump = 1





class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y,width = 80, height = 30):
        super().__init__()
        self.width = width
        self.height = height
        self.image = pygame.Surface([width, height])
        image = pygame.image.load("Platform.png").convert()
        pygame.transform.scale(image,(width,height),self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class MovingPlatform(Platform):
    def __init__(self,x,y,player,width = 80,height = 30):
        super().__init__(x,y,width,height)
        self.change_x = 0
        self.change_y = 0
        self.boundary_top = 0
        self.boundary_bottom = 0
        self.boundary_left = 0
        self.boundary_right = 0
        self.player = player

    def update(self):
        self.rect.x += self.change_x
        hit = pygame.sprite.collide_rect(self, self.player)
        if hit:
            if self.change_x < 0:
                self.player.rect.right = self.rect.left
            elif self.change_x < 0:
                self.player.rect.left = self.rect.right
            else:
                if self.rect.left < self.player.rect.right < self.rect.right:
                    self.player.rect.right = self.rect.left
                else:
                    self.player.rect.left = self.rect.right
        if (self.player.rect.bottom == self.rect.top and
            self.rect.x - 30 <= self.player.rect.x <= self.rect.right):
            self.player.rect.x += self.change_x
        self.rect.y += self.change_y
        hit = pygame.sprite.collide_rect(self, self.player)
        if hit:
            if self.change_y < 0:
                self.player.rect.bottom = self.rect.top
            else:
                self.player.rect.top = self.rect.bottom
        if (self.rect.bottom > self.boundary_bottom or 
            self.rect.top < self.boundary_top):
            self.change_y *= -1
        if (self.rect.left < self.boundary_left or 
            self.rect.right > self.boundary_right):
            self.change_x *= -1


# 4 spike classes, because the collision checking method of triangles
# depend on the shape, I write 4 classes instead of 4 subclasses of 
# one spike class
class DownSpike(pygame.sprite.Sprite):
    # startx, starty is the position of the player when spike can move
    def __init__(self,x,y,startx = None, starty = None, size = 40):
        super().__init__()
        width = size
        height = size
        self.image = pygame.Surface([width, height],pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.size = size
        self.startx = startx
        self.starty = starty
        self.change_x = 0
        self.change_y = 0
        image = pygame.image.load("DownSpike.png")
        pygame.transform.scale(image,(size,size),self.image)

    def checkCollision(self, player):
        if (player.rect.right < self.rect.x or player.rect.x > self.rect.right
            or player.rect.top > self.rect.bottom or 
            player.rect.bottom < self.rect.top):
            return False
        if (self.rect.x < player.rect.x < self.rect.right and
            40 <= player.rect.bottom - self.rect.y <= 70):
            return True
        if (player.rect.right > self.rect.x and player.rect.right < 
            self.rect.x + self.size/2):
            d = player.rect.right - self.rect.x
            if self.rect.bottom - player.rect.bottom <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.x < self.rect.right and player.rect.x > 
            self.rect.x + self.size/2):
            d = self.rect.right - player.rect.x
            if self.rect.bottom - player.rect.bottom <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.right == self.rect.x or player.rect.x == 
            self.rect.right):
            if player.rect.bottom == self.rect.bottom: return True
            else: return False
        else:
            if (0 <= self.rect.bottom - player.rect.bottom <= self.size):
                return True
            else:
                return False

    def flySpike(self, player):
        if self.startx != None or self.starty != None:
            if (self.startx - 40 <= player.rect.x <= self.startx + 40 and 
                self.starty - 150 <= player.rect.y <= self.starty + 30):
                self.change_y = -7

    def update(self, player):
        self.flySpike(player)
        self.rect.y += self.change_y


class UpSpike(pygame.sprite.Sprite):
    def __init__(self,x,y,startx = None, starty = None, size = 40):
        super().__init__()
        width = size
        height = size
        self.image = pygame.Surface([width, height],pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.size = size
        self.startx = startx
        self.starty = starty
        self.change_x = 0
        self.change_y = 0
        image = pygame.image.load("UpSpike.png")
        pygame.transform.scale(image,(size,size),self.image)

    def checkCollision(self, player):
        if (player.rect.right < self.rect.x or player.rect.x > self.rect.right
            or player.rect.top > self.rect.bottom or 
            player.rect.bottom < self.rect.top):
            return False
        if (self.rect.x < player.rect.x < self.rect.right and
            40 <= self.rect.bottom - player.rect.y <= 70):
            return True
        if (player.rect.right > self.rect.x and player.rect.right < 
            self.rect.x + self.size/2):
            d = player.rect.right - self.rect.x
            if 0 <= player.rect.top - self.rect.top <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.x < self.rect.right and player.rect.x > 
            self.rect.x + self.size/2):
            d = self.rect.right - player.rect.x
            if 0 <= player.rect.top - self.rect.top <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.right == self.rect.x or player.rect.x == 
            self.rect.right):
            if player.rect.top == self.rect.top: return True
            else: return False
        else:
            if (0 <= self.rect.bottom - player.rect.bottom <= self.size):
                return True
            else:
                return False

    def flySpike(self, player):
        if self.startx != None or self.starty != None:
            if (self.startx - 30 <= player.rect.x <= self.startx + 40 and 
                self.starty - 30 <= player.rect.y <= self.starty + 150):
                self.change_y = 7

    def update(self, player):
        self.flySpike(player)
        self.rect.y += self.change_y




class LeftSpike(pygame.sprite.Sprite):
    def __init__(self,x,y,startx = None, starty = None, size = 40):
        super().__init__()
        width = size
        height = size
        self.image = pygame.Surface([width, height],pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.size = size
        self.startx = startx
        self.starty = starty
        self.change_x = 0
        self.change_y = 0
        image = pygame.image.load("LeftSpike.png")
        pygame.transform.scale(image,(size,size),self.image)

    def checkCollision(self, player):
        if (player.rect.right < self.rect.x or player.rect.x > self.rect.right
            or player.rect.top > self.rect.bottom or 
            player.rect.bottom < self.rect.top):
            return False
        if (self.rect.y < player.rect.y < self.rect.bottom and
            40 <= self.rect.right - player.rect.x <= 70):
            return True
        if (player.rect.top < self.rect.bottom and player.rect.top > 
            self.rect.y + self.size/2):
            d = self.rect.bottom - player.rect.top
            if 0 <= player.rect.x - self.rect.x <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.bottom > self.rect.top and player.rect.bottom <
            self.rect.y + self.size/2):
            d = player.rect.bottom - self.rect.top
            if 0 <= player.rect.x - self.rect.x <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.top == self.rect.bottom or player.rect.bottom == 
            self.rect.top):
            if player.rect.bottom == self.rect.bottom: return True
            else: return False
        else:
            if (0 <= player.rect.x - self.rect.x <= self.size):
                return True
            else:
                return False

    def flySpike(self, player):
        if self.startx != None or self.starty != None:
            if (self.startx - 30  <= player.rect.x <= self.startx + 300 and 
                self.starty - 30 <= player.rect.y <= self.starty + 30):
                self.change_x = 7

    def update(self, player):
        self.flySpike(player)
        self.rect.x += self.change_x



class RightSpike(pygame.sprite.Sprite):
    def __init__(self,x,y,startx = None, starty = None, size = 40):
        super().__init__()
        width = size
        height = size
        self.image = pygame.Surface([width, height],pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.size = size
        self.startx = startx
        self.starty = starty
        self.change_x = 0
        self.change_y = 0
        image = pygame.image.load("RightSpike.png")
        pygame.transform.scale(image,(size,size),self.image)

    def checkCollision(self, player):
        if (player.rect.right < self.rect.x or player.rect.x > self.rect.right
            or player.rect.top > self.rect.bottom or 
            player.rect.bottom < self.rect.top):
            return False
        if (self.rect.y < player.rect.y < self.rect.bottom and
            40 <= player.rect.right - self.rect.x <= 70):
            return True
        if (player.rect.top < self.rect.bottom and player.rect.top > 
            self.rect.y + self.size/2):
            d = self.rect.bottom - player.rect.top
            if 0 <= self.rect.right - player.rect.right <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.bottom > self.rect.top and player.rect.bottom <
            self.rect.y + self.size/2):
            d = player.rect.bottom - self.rect.top
            if 0 <= self.rect.right - player.rect.right <= d*math.sqrt(3):
                return True
            else:
                return False
        elif (player.rect.top == self.rect.bottom or player.rect.bottom == 
            self.rect.top):
            if player.rect.bottom == self.rect.bottom: return True
            else: return False
        else:
            if (0 <= self.rect.right - player.rect.right <= self.size):
                return True
            else:
                return False

    def flySpike(self, player):
        if self.startx != None or self.starty != None:
            if (self.startx - 300 <= player.rect.x <= self.startx + 30 and 
                self.starty - 30 <= player.rect.y <= self.starty + 30):
                self.change_x = -7

    def update(self, player):
        self.flySpike(player)
        self.rect.x += self.change_x



class Boss(pygame.sprite.Sprite):
    def __init__(self,x,y,player,width = 50,height=50):
        super().__init__()
        self.timer = 0
        self.image = pygame.image.load("kosbie.png")
        self.player = player
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.change_x = 0
        self.change_y = 0
        self.HP = 30
        self.bullet_list = pygame.sprite.Group()

    def updatePlayer(self):
        bullet_hit_list = pygame.sprite.spritecollide(self,
            self.player.bullet_list,False)
        for bullet in bullet_hit_list:
            self.HP -= 1
            self.player.bullet_list.remove(bullet)
        bullet_hit_list = pygame.sprite.spritecollide(self.player,
            self.bullet_list,False)
        if len(bullet_hit_list) > 0:
            self.player.room.over = True

    def update(self):
        self.updatePlayer()
        self.timer += 1
        if self.HP > 20 and self.timer % 10 == 0:
            xdirection = random.random()*random.choice([1,-1])
            ydirection = random.random()*random.choice([1,-1])
            bullet = Bullet(xdirection,ydirection)
            bullet.image.fill(red)
            bullet.rect.x = self.rect.x
            bullet.rect.y = self.rect.y
            self.bullet_list.add(bullet)
        if 0 <= self.HP <= 20 and self.timer % 50 == 0:
            xdirection = 1 if self.player.rect.x - self.rect.x > 0 else -1
            if self.rect.x == self.player.rect.x:
                xdirection = 0
                ydirection = 1
            else:
                ydirection = (self.player.rect.y - 
                    self.rect.y)/abs(self.player.rect.x - self.rect.x)
            bullet = Bullet(xdirection,ydirection)
            bullet.image.fill(red)
            bullet.rect.x = self.rect.x
            bullet.rect.y = self.rect.y
            self.bullet_list.add(bullet)
        if 0 <= self.HP <= 8 and self.timer % 60 == 0:
            self.change_x = random.randint(-400,400)
            self.change_y = random.randint(-300,300)
            self.rect.x += self.change_x
            self.rect.y += self.change_y
            if self.rect.x < 40:
                self.rect.x = 40
            if self.rect.x > 710:
                self.rect.x = 710
            if self.rect.y < 40:
                self.rect.y = 40
            if self.rect.y > 510:
                self.rect.y = 510
        self.bullet_list.update()
        for bullet in self.bullet_list:
            bullet_hit_list = pygame.sprite.spritecollide(bullet, 
                self.player.room.wall_list, False)
            if len(bullet_hit_list) > 0:
                self.bullet_list.remove(bullet)
            if bullet.rect.x < -5 or bullet.rect.x > screen_width:
                self.bullet_list.remove(bullet)
        if self.HP <= 0:
            self.player.room.win = True
        player_hit_list = pygame.sprite.spritecollide(self.player,
            self.player.room.boss_list,False)
        if len(player_hit_list) > 0:
            self.player.room.over = True


            


class Savingpoint(pygame.sprite.Sprite):
    def __init__(self,x,y,player,width = 40, height = 40):
        super().__init__()
        self.unsavedImage = pygame.image.load("Unsaved.png").convert()
        self.savedImage = pygame.image.load("Saved.png").convert()
        self.image = self.unsavedImage
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.saved = False
        self.player = player


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, texts, width = 199, height = 30):
        super().__init__()
        self.image = pygame.Surface([width, height])
        image = pygame.image.load("Button.png").convert()
        self.image.set_colorkey((0,0,0))
        pygame.transform.scale(image,(width,height),self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.text = texts

    def draw(self,screen):
        screen.blit(self.image,(self.rect.x,self.rect.y))


class Room(object):
    def __init__(self, player):
        self.platform_list = pygame.sprite.Group()
        self.wall_list = pygame.sprite.Group()
        self.spike_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.conveyorBelt_list = pygame.sprite.Group()
        self.savingpoint_list = pygame.sprite.Group()
        self.boss_list = pygame.sprite.Group()
        self.new_savingpoint = None
        self.player = player
        self.background = None
        self.over = False
        self.win = False

    def checkGameOver(self):
        for spikes in self.spike_list:
            if spikes.checkCollision(self.player):
                self.over = True


    def update(self):
        self.wall_list.update()
        for wall in self.wall_list:
            if type(wall) == DisappearWall:
                if (wall.rect.x - 30 < self.player.rect.x <= wall.rect.right 
                    and (self.player.rect.bottom == wall.rect.top or 
                    self.player.rect.top == wall.rect.bottom)):
                    self.wall_list.remove(wall)
                if (wall.rect.y - 30 < self.player.rect.y <= wall.rect.bottom
                    and (self.player.rect.right == wall.rect.left or 
                    self.player.rect.left == wall.rect.right)):
                    self.wall_list.remove(wall)
        self.platform_list.update()
        self.enemy_list.update()
        self.spike_list.update(self.player)
        self.conveyorBelt_list.update()
        # remove the spike from the list if it's outside the screen
        for spike in self.spike_list:
            if (spike.rect.x > screen_width or spike.rect.x < 0 - spike.size or
                spike.rect.y > screen_height or spike.rect.y < 0 - spike.size):
                self.spike_list.remove(spike)
        savingpoint = pygame.sprite.spritecollide(self.player, 
            self.savingpoint_list, False)
        if len(savingpoint) == 0:
            for savingpoints in self.savingpoint_list:
                if (self.new_savingpoint == None or 
                    savingpoints != self.new_savingpoint):
                    savingpoints.saved = False
        else:
            for savingpoints in self.savingpoint_list:
                if savingpoints == savingpoint[0]:
                    savingpoints.saved = True
                    savingpoints.image = savingpoints.savedImage
                    self.new_savingpoint = savingpoints
                else:
                    savingpoints.saved = False
                    savingpoints.image = savingpoints.unsavedImage
        for bullet in self.player.bullet_list:
            savingpoint = pygame.sprite.spritecollide(bullet, 
                self.savingpoint_list, False)
            if len(savingpoint) == 0:
                for savingpoints in self.savingpoint_list:
                    if (self.new_savingpoint == None or 
                        savingpoints != self.new_savingpoint):
                        savingpoints.saved = False
            else:
                for savingpoints in self.savingpoint_list:
                    if savingpoints == savingpoint[0]:
                        savingpoints.saved = True
                        savingpoints.image = savingpoints.savedImage
                        self.new_savingpoint = savingpoints
                    else:
                        savingpoints.saved = False
                        savingpoints.image = savingpoints.unsavedImage
        self.boss_list.update()

    def revive(self):
        saved = False
        for savingpoint in self.savingpoint_list:
            if savingpoint.saved:
                saved = True
                self.player.rect.x = savingpoint.rect.x
                self.player.rect.y = savingpoint.rect.y
                self.player.change_x = 0
                self.player.change_y = 0
        if not saved:
            self.player.rect.x = 50
            self.player.rect.y = 550
            self.player.change_x = 0
            self.player.change_y = 0

    def draw(self,screen,death,time):
        background = pygame.image.load("Background3.png").convert()
        screen.blit(background,(0,0))
        self.spike_list.draw(screen)
        self.player.bullet_list.draw(screen)
        self.wall_list.draw(screen)
        self.platform_list.draw(screen)
        self.enemy_list.draw(screen)
        self.conveyorBelt_list.draw(screen)
        self.savingpoint_list.draw(screen)
        self.boss_list.draw(screen)
        for boss in self.boss_list:
            pygame.draw.rect(screen,green,(boss.rect.x,boss.rect.y-15,
                boss.rect.width/30*boss.HP,10))
            pygame.draw.rect(screen,red,(boss.rect.x+boss.rect.width/30*boss.HP,
                boss.rect.y-15,boss.rect.width-boss.rect.width/30*boss.HP,10))
            pygame.draw.rect(screen,black,(boss.rect.x,boss.rect.y-15,
                boss.rect.width,10),1)
            boss.bullet_list.draw(screen)
        myfont = pygame.font.SysFont("comicsansms", 20)
        text = myfont.render("Death: %d Time: %d:%.2d" %(death,time//60,time%60),1,white)
        screen.blit(text,(20,10))

    def load(self,msg):
        self.boss_list = pygame.sprite.Group()
        self.wall_list = pygame.sprite.Group()
        self.conveyorBelt_list = pygame.sprite.Group()
        self.savingpoint_list = pygame.sprite.Group()
        self.spike_list = pygame.sprite.Group()
        self.platform_list = pygame.sprite.Group()
        for boss in msg.boss_list:
            new_boss = Boss(boss.rect.x,boss.rect.y,self.player)
            new_boss.HP = boss.HP
            new_boss.change_x = boss.change_x
            new_boss.change_y = boss.change_y
            self.boss_list.add(new_boss)
        for wall in msg.wall_list:
            if type(wall) == DisappearWall:
                self.wall_list.add(DisappearWall(wall.rect.x,wall.rect.y,30,30))
            elif type(wall) == StickyWall:
                self.wall_list.add(StickyWall(wall.rect.x,wall.rect.y,
                    self.player,30,30))
            elif type(wall) != MovingPlatform:
                self.wall_list.add(Wall(wall.rect.x,wall.rect.y,30,30))
        for conveyorBelt in msg.conveyorBelt_list:
            newConveyorBelt = ConveyorBelt(conveyorBelt.rect.x, 
                conveyorBelt.rect.y,self.player,conveyorBelt.change_x,
                conveyorBelt.change_y,30,30)
            self.conveyorBelt_list.add(newConveyorBelt)
        for savingpoint in msg.savingpoint_list:
            new_savingpoint = Savingpoint(savingpoint.rect.x,savingpoint.rect.y,
                self.player,30,30)
            new_savingpoint.saved = savingpoint.saved
            self.savingpoint_list.add(new_savingpoint)
        if msg.new_savingpoint != None:
            self.new_savingpoint = Savingpoint(msg.new_savingpoint.rect.x,
                msg.new_savingpoint.rect.y,self.player,30,30)
            self.new_savingpoint.saved = msg.new_savingpoint.saved
        else:self.new_savingpoint = None
        for spike in msg.spike_list:
            if type(spike) == DownSpike:
                self.spike_list.add(DownSpike(spike.rect.x,spike.rect.y,
                    spike.startx,spike.starty,30))
            if type(spike) == UpSpike:
                self.spike_list.add(UpSpike(spike.rect.x,spike.rect.y,
                    spike.startx,spike.starty,30))
            if type(spike) == LeftSpike:
                self.spike_list.add(LeftSpike(spike.rect.x,spike.rect.y,
                    spike.startx,spike.starty,30))
            if type(spike) == RightSpike:
                self.spike_list.add(RightSpike(spike.rect.x,spike.rect.y,
                    spike.startx,spike.starty,30))
        for platform in msg.platform_list:
            newPlatform = MovingPlatform(platform.rect.x,platform.rect.y,
                self.player,60,30)
            newPlatform.change_x = platform.change_x
            newPlatform.change_y = platform.change_y
            newPlatform.boundary_top = platform.boundary_top
            newPlatform.boundary_bottom = platform.boundary_bottom
            newPlatform.boundary_left = platform.boundary_left
            newPlatform.boundary_right = platform.boundary_right
            self.platform_list.add(newPlatform)
            self.wall_list.add(newPlatform)


    def resize(self):
        wall_list = pygame.sprite.Group()
        conveyorBelt_list = pygame.sprite.Group()
        savingpoint_list = pygame.sprite.Group()
        spike_list = pygame.sprite.Group()
        platform_list = pygame.sprite.Group()
        boss_list = pygame.sprite.Group()
        for boss in self.boss_list:
            new_boss = Boss((boss.rect.x-200)*4/3,
                (boss.rect.y-150)*4/3,self.player)
            new_boss.change_x = boss.change_x
            new_boss.change_y = boss.change_y
            new_boss.HP = boss.HP
            boss_list.add(new_boss)
        for wall in self.wall_list:
            if type(wall) == DisappearWall:
                wall_list.add(DisappearWall((wall.rect.x-200)*4/3,
                    (wall.rect.y-150)*4/3))
            elif type(wall) == StickyWall:
                wall_list.add(StickyWall((wall.rect.x-200)*4/3,
                    (wall.rect.y-150)*4/3,self.player))
            elif type(wall) != MovingPlatform:
                wall_list.add(Wall((wall.rect.x-200)*4/3,
                    (wall.rect.y-150)*4/3))
        for conveyorBelt in self.conveyorBelt_list:
            newConveyorBelt = ConveyorBelt((conveyorBelt.rect.x-200)*4/3, 
                (conveyorBelt.rect.y-150)*4/3,self.player,
                conveyorBelt.change_x,conveyorBelt.change_y)
            conveyorBelt_list.add(newConveyorBelt)
        for savingpoint in self.savingpoint_list:
            new_savingpoint = Savingpoint((savingpoint.rect.x-200)*4/3,
                (savingpoint.rect.y-150)*4/3,self.player)
            new_savingpoint.saved = savingpoint.saved
            savingpoint_list.add(new_savingpoint)
        if self.new_savingpoint != None:
            saved = self.new_savingpoint.saved
            self.new_savingpoint = Savingpoint((self.new_savingpoint.rect.x-200)*4/3,
                (self.new_savingpoint.rect.y-150)*4/3,self.player)
            self.new_savingpoint.saved = saved
        else: self.new_savingpoint = None
        for spike in self.spike_list:
            if type(spike) == DownSpike:
                if spike.startx != None and spike.starty != None:
                    spike_list.add(DownSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,(spike.startx-200)*4/3,
                        (spike.starty-150)*4/3))
                else:
                    spike_list.add(DownSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,None,None))
            if type(spike) == UpSpike:
                if spike.startx != None and spike.starty != None:
                    spike_list.add(UpSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,(spike.startx-200)*4/3,
                        (spike.starty-150)*4/3))
                else:
                    spike_list.add(UpSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,None,None))         
            if type(spike) == LeftSpike:
                if spike.startx != None and spike.starty != None:
                    spike_list.add(LeftSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,(spike.startx-200)*4/3,
                        (spike.starty-150)*4/3))
                else:
                    spike_list.add(LeftSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,None,None)) 
            if type(spike) == RightSpike:
                if spike.startx != None and spike.starty != None:
                    spike_list.add(RightSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,(spike.startx-200)*4/3,
                        (spike.starty-150)*4/3))
                else:
                    spike_list.add(RightSpike((spike.rect.x-200)*4/3,
                        (spike.rect.y-150)*4/3,None,None))
        for platform in self.platform_list:
            newPlatform = MovingPlatform((platform.rect.x-200)*4/3,
                (platform.rect.y-150)*4/3,self.player)
            newPlatform.change_x = platform.change_x
            newPlatform.change_y = platform.change_y
            newPlatform.boundary_top = (platform.boundary_top-150)*4/3
            newPlatform.boundary_bottom = (platform.boundary_bottom-150)*4/3
            newPlatform.boundary_left = (platform.boundary_left-200)*4/3
            newPlatform.boundary_right = (platform.boundary_right-200)*4/3
            platform_list.add(newPlatform)
            wall_list.add(newPlatform)
        self.wall_list = wall_list
        self.conveyorBelt_list = conveyorBelt_list
        self.platform_list = platform_list
        self.savingpoint_list = savingpoint_list
        self.spike_list = spike_list
        self.boss_list = boss_list



class LevelEditor(Room):
    def __init__(self,player):
        super().__init__(player)
        self.button_list = pygame.sprite.Group()
        self.button_list.add(Button(200,0,"Erase",200,75),Button(400,0,"Save",200,75),
            Button(600,0,"Load",200,75),Button(300,75,"Clear",200,75))
        (width,height) = (200,70)
        self.button_list.add(Button(0,30,"Wall",width,height),
            Button(0,100,"Disappear Wall",width,height),
            Button(0,170,"Sticky Wall",width,height),
            Button(0,240,"Spikes", width,height),
            Button(0,310,"Platforms",width,height),
            Button(0,380,"Conveyor Belt",width,height),
            Button(0,450,"Saving Point",width,height),
            Button(0,520,"Boss",width,height),
            Button(500,75,"Next Room",200,75))
        self.icon_list = pygame.sprite.Group()
        self.icon_list.add(Wall(60,50),DisappearWall(60,120),StickyWall(60,190,player),
            DownSpike(5,260),UpSpike(45,260),LeftSpike(90,260),
            RightSpike(135,260),Platform(50,330),ConveyorBelt(60,400,player),
            Savingpoint(70,470,player),Boss(90,530,player,40,40))
        for x in range(200,800,30):
            self.wall_list.add(Wall(x,150,30,30),
                Wall(x,570,30,30))
        for y in range(150,600,30):
            self.wall_list.add(Wall(200,y,30,30),Wall(770,y,30,30))
        self.mode = None
        self.last_spike = None
        self.lastConveyorBelt = None
        self.lastPlatform = None

    def drawUI(self,screen):
        image = pygame.image.load("Background3.png").convert()
        screen.blit(image,(0,0))
        self.button_list.draw(screen)
        myfont = pygame.font.SysFont("comicsansms",15,bold = True)
        for button in self.button_list:
            if button.text != "Next Room":
                text = myfont.render(button.text,1,black)
                if button.text in ["Erase", "Save", "Load", "Clear"]:
                    font = pygame.font.SysFont("comicsansms", 25, bold = True)
                    text = font.render(button.text,1,black)
                screen.blit(text,(button.rect.x+60,button.rect.y))
            else:
                font = pygame.font.SysFont("comicsansms", 25, bold = True)
                text = font.render(button.text,1,black)
                screen.blit(text,(button.rect.x+30,button.rect.y))


        self.icon_list.draw(screen)
        self.wall_list.draw(screen)

    def checkMode(self,pos):
        (x,y) = pos
        for button in self.button_list:
            if (button.rect.left <= x <= button.rect.right and 
                button.rect.top <= y <= button.rect.bottom):
                self.mode = button.text
                if self.mode == "Spikes":
                    if (260 <= y <= 300):
                        if x // 45 == 0: self.mode = "DownSpike"
                        if x // 45 == 1: self.mode = "UpSpike"
                        if x // 45 == 2: self.mode = "LeftSpike"
                        if x // 45 == 3: self.mode = "RightSpike"
                    else:
                        self.mode = None
        
    def makeWall(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.wall_list.add(Wall(x,y,30,30))

    def makeDisappearWall(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.wall_list.add(DisappearWall(x,y,30,30))

    def makeStickyWall(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.wall_list.add(StickyWall(x,y,self.player,30,30))

    def makeConveyorBelts(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.lastConveyorBelt = ConveyorBelt(x,y,self.player,0,0,30,30)
            self.conveyorBelt_list.add(self.lastConveyorBelt)
            self.mode = "ChangeBeltSpeed"


    def changeBeltSpeed(self, pos):
        lastConveyorBelt = self.lastConveyorBelt
        (x,y) = pos
        if lastConveyorBelt.rect.x < x < lastConveyorBelt.rect.right:
            if y < lastConveyorBelt.rect.y:
                lastConveyorBelt.change_y = -20
            elif y > lastConveyorBelt.rect.y:
                lastConveyorBelt.change_y = 20
        elif lastConveyorBelt.rect.y < y < lastConveyorBelt.rect.bottom:
            if x < lastConveyorBelt.rect.x:
                lastConveyorBelt.change_x = -5
            elif x > lastConveyorBelt.rect.x:
                lastConveyorBelt.change_x = 5
        self.mode = None

    def makeSavingPoint(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.savingpoint_list.add(Savingpoint(x,y,self.player,30,30))

    def makeBoss(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.boss_list.add(Boss(x,y,self.player,30,30))


    @staticmethod
    def writeFile(path,msg):
        with open(path, "wb") as f:
            pickle.dump(msg,f)

    @staticmethod
    def readFile(path):
        with open(path, "rb") as f:
            msg = pickle.load(f)
            return msg

    def makeSpikes(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            if self.mode == "DownSpike":
                self.last_spike = DownSpike(x,y,None,None,30)
                self.spike_list.add(self.last_spike)
                self.mode = "FlySpike"
            if self.mode == "UpSpike":
                self.last_spike = UpSpike(x,y,None,None,30)
                self.spike_list.add(self.last_spike)
                self.mode = "FlySpike"
            if self.mode == "LeftSpike":
                self.last_spike = LeftSpike(x,y,None,None,30)
                self.spike_list.add(self.last_spike)
                self.mode = "FlySpike"                
            if self.mode == "RightSpike":
                self.last_spike = RightSpike(x,y,None,None,30)
                self.spike_list.add(self.last_spike)
                self.mode = "FlySpike"


    def erase(self,pos):
        (x,y) = pos
        if (200 <= x < 800 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            for platform in self.platform_list:
                if (platform.rect.x - 40 < x < platform.rect.right + 40
                    and platform.rect.y - 20 < y < platform.rect.bottom + 20):
                    self.platform_list.remove(platform)
            for wall in self.wall_list:
                if wall.rect.x == x and wall.rect.y == y:
                    self.wall_list.remove(wall)
            for spike in self.spike_list:
                if spike.rect.x == x and spike.rect.y == y:
                    self.spike_list.remove(spike)
            for conveyorBelt in self.conveyorBelt_list:
                if conveyorBelt.rect.x == x and conveyorBelt.rect.y == y:
                    self.conveyorBelt_list.remove(conveyorBelt)
            for savingpoint in self.savingpoint_list:
                if savingpoint.rect.x == x and savingpoint.rect.y == y:
                    self.savingpoint_list.remove(savingpoint)
            for boss in self.boss_list:
                if boss.rect.x == x and boss.rect.y == y:
                    self.boss_list.remove(boss)


    def makePlatform(self,pos):
        (x,y) = pos
        if (200 <= x < 760 and 150 <= y < 600):
            x = (x-200)//30*30 + 200
            y = (y-150)//30*30 + 150
            self.lastPlatform = MovingPlatform(x,y,self.player,60,30)
            self.platform_list.add(self.lastPlatform)
            self.wall_list.add(self.lastPlatform)
            self.mode = "ChangePlatform"

    def changePlatform(self,pos):
        lastPlatform = self.lastPlatform
        (x,y) = pos
        if lastPlatform.rect.x < x < lastPlatform.rect.right:
            if y < lastPlatform.rect.y:
                lastPlatform.change_y = -1
                lastPlatform.boundary_top = y
                lastPlatform.boundary_bottom = lastPlatform.rect.y + 40
            elif y > lastPlatform.rect.y:
                lastPlatform.change_y = 1
                lastPlatform.boundary_top = lastPlatform.rect.y - 40
                lastPlatform.boundary_bottom = y
        elif lastPlatform.rect.y <= y <= lastPlatform.rect.bottom:
            if x < lastPlatform.rect.x:
                lastPlatform.change_x = -1
                lastPlatform.boundary_right = lastPlatform.rect.x + 60
                lastPlatform.boundary_left = x
            elif x > lastPlatform.rect.x:
                lastPlatform.change_x = 1
                lastPlatform.boundary_right = x
                lastPlatform.boundary_left = lastPlatform.rect.x 
        self.mode = None

    def save(self,path = "1.txt"):
        msg = self
        LevelEditor.writeFile(path,msg)
        self.mode = None

    def load(self,msg):
        super().load(msg)
        self.mode = None

    def nextRoom(self,path = "1.txt"):
        if not os.path.isfile(path):
            msg = []
            msg.append(self)
            LevelEditor.writeFile(path,msg)
        else:
            msg = LevelEditor.readFile(path)
            msg.append(self)
            LevelEditor.writeFile(path,msg)
        self.mode = None


    def makeGame(self,pos):
        if self.mode == "Wall":
            self.makeWall(pos)
        if self.mode == "Disappear Wall":
            self.makeDisappearWall(pos)
        if self.mode == "Sticky Wall":
            self.makeStickyWall(pos)
        if self.mode == "Saving Point":
            self.makeSavingPoint(pos)
        if "Spike" in self.mode:
            self.makeSpikes(pos)
        if self.mode == "Erase":
            self.erase(pos)
        if self.mode == "Conveyor Belt":
            self.makeConveyorBelts(pos)
        if self.mode == "Platforms":
            self.makePlatform(pos)
        if self.mode == "Boss":
            self.makeBoss(pos)


    def draw(self,screen):
        self.spike_list.draw(screen)
        self.wall_list.draw(screen)
        self.platform_list.draw(screen)
        self.conveyorBelt_list.draw(screen)
        self.savingpoint_list.draw(screen)
        self.player.bullet_list.draw(screen)
        self.boss_list.draw(screen)
        for boss in self.boss_list:
            boss.bullet_list.draw(screen)


def levelEditor(screen):
    player = Player(300,300)
    levelEditor = LevelEditor(player)
    player.room = levelEditor
    gameOver = False
    while not gameOver:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return 
            if event.type == pygame.MOUSEBUTTONDOWN:
                levelEditor.checkMode(pygame.mouse.get_pos())
            if levelEditor.mode != None:
                if (levelEditor.mode == "FlySpike"
                    and levelEditor.last_spike != None and
                    event.type == pygame.MOUSEBUTTONDOWN):
                    levelEditor.last_spike.startx = pygame.mouse.get_pos()[0]
                    levelEditor.last_spike.starty = pygame.mouse.get_pos()[1]
                    levelEditor.mode = None
                elif (levelEditor.mode == "ChangeBeltSpeed" and 
                    levelEditor.lastConveyorBelt != None and event.type ==
                    pygame.MOUSEBUTTONDOWN):
                    levelEditor.changeBeltSpeed(pygame.mouse.get_pos())
                elif (levelEditor.mode == "ChangePlatform" and 
                    levelEditor.lastPlatform != None and event.type == 
                    pygame.MOUSEBUTTONDOWN):
                    levelEditor.changePlatform(pygame.mouse.get_pos())
                elif (200 <= pygame.mouse.get_pos()[0]
                    <= 800 and 150 <= pygame.mouse.get_pos()[1] <= 600 and 
                    ((event.type == pygame.MOUSEMOTION and 
                    pygame.mouse.get_pressed()[0])
                    or event.type == pygame.MOUSEBUTTONDOWN)):
                    levelEditor.makeGame(pygame.mouse.get_pos())
            if levelEditor.mode == "Save":
                levelEditor.save("Save.txt")
            if levelEditor.mode == "Load":
                msg = LevelEditor.readFile("Save.txt")
                levelEditor.load(msg)
            if levelEditor.mode == "Next Room":
                path = inputbox.ask(screen,"Saved as")
                levelEditor.nextRoom(path)
            if levelEditor.mode == "Clear":
                levelEditor = LevelEditor(player)
                player.room = levelEditor
        levelEditor.update()
        levelEditor.drawUI(screen)
        levelEditor.draw(screen)
        pygame.display.flip()



class Level(object):
    def __init__(self,player,path):
        rooms = LevelEditor.readFile(path)
        self.rooms = []
        self.player = player
        self.msg = LevelEditor.readFile(path)
        self.loadLevel()
        self.new_savingpoint_room = 0
        self.death = 0
        self.time = 0

    def loadLevel(self):
        for room in self.msg:
            new_room = Room(self.player)
            new_room.load(room)
            new_room.resize()
            self.rooms.append(new_room)

class HighScores(object):
    def __init__(self):
        self.levels = dict()
        for level in range(1,5):
            self.levels[level] = [[None,None],[None,None],[None,None]]

    def addScore(self,level,death,time):
        index = 4
        for score in self.levels[level]:
            if (score == [None,None] or death < score[0] or 
                (death == score[0] and time < score[1])):
                index = self.levels[level].index(score)
                break
        self.levels[level] = (self.levels[level][:index] + [[death,time]]
            + self.levels[level][index+1:])
        while len(self.levels[level]) >= 4:
            self.levels[level].pop()

def highScores(level = 1,death = None,time = None,path = "HighScores.txt"):
    if not os.path.isfile(path):
        highScores = HighScores()
        highScores.addScore(level,death,time)
        LevelEditor.writeFile(path,highScores)
    else:
        highScores = LevelEditor.readFile(path)
        highScores.addScore(level,death,time)
        LevelEditor.writeFile(path,highScores)



class Level1(Level):
    def __init__(self,player):
        super().__init__(player,"1.txt")
        self.current_room = 0



class Level2(Level):
    def __init__(self,player):
        super().__init__(player,"2.txt")
        self.current_room = 0

class Level3(Level):
    def __init__(self,player):
        super().__init__(player,"3.txt")
        self.current_room = 0

class Level4(Level):
    def __init__(self,player):
        super().__init__(player,"4.txt")
        self.current_room = 0

class SavedLevel(Level):
    def __init__(self,player,path):
        if os.path.isfile(path) == False:
            print("1")
            self.current_room = None
        else:
            super().__init__(player,path)
            self.current_room = 0

def handleServerMsg(server, serverMsg):
    server.setblocking(1)
    msg = ""
    command = ""
    while True:
        msg += server.recv(1000).decode("UTF-8")
        command = msg.split("\n")
        if (len(command) > 1):
            readyMsg = command[0]
            msg = "\n".join(command[1:])
            serverMsg.put(readyMsg)




def play(screen, mode, MP):
    if MP:
        HOST = '128.237.133.144'
        PORT = 50000
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        server.connect((HOST,PORT))
        print("connected to server")
        serverMsg = Queue(100)
        start_new_thread(handleServerMsg, (server, serverMsg))
        others = {}
        haveOthers = False
        MPwin = False
    image = pygame.Surface((30,30))
    image.set_colorkey((0,0,0))
    player_image = pygame.image.load("other.png").convert()
    pygame.transform.scale(player_image,(30,30),image)
    gameOver = False
    allSprites = pygame.sprite.Group()
    player = Player(50,550)
    death = 0
    time = 0
    cur_time = pygame.time.get_ticks()
    if mode == "Homework":
        current_level = Level1(player)
        current_level_no = 1
    if mode == "Midterm":
        current_level = Level2(player)
        current_level_no = 2
    if mode == "Final":
        current_level = Level3(player)
        current_level_no = 3
    if mode == "Term Project":
        current_level = Level4(player)
        current_level_no = 4
    if mode == "Load Saved Game":
        path = inputbox.ask(screen,"Which File?")
        current_level = SavedLevel(player,path)
        if current_level.current_room == None:
            return
        current_level_no = 5
    allSprites.add(player)
    current_room = current_level.rooms[current_level.current_room]
    player.room = current_room
    while not gameOver:
        if not (current_room.over or current_room.win):
            time = (pygame.time.get_ticks()-cur_time)/1000
            if MP:
                timerFired(server,serverMsg,player,death,time,current_room.win,others)
                if len(others) != 0: 
                    haveOthers = True
                else: 
                    haveOthers = False
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 
                    if event.key == pygame.K_LEFT:
                        player.go_left()
                    if event.key == pygame.K_RIGHT:
                        player.go_right()
                    if event.key == pygame.K_UP:
                        player.jump()
                    if event.key == pygame.K_SPACE:
                        player.fire()
                    if event.key == pygame.K_r:
                        savingpoints = (current_level.rooms[current_level.current_room-1].savingpoint_list)
                        current_room_no = current_level.current_room
                        current_level.current_room = current_room_no - 1
                        if current_level.current_room == -1:
                            current_level.current_room = 0
                        for savingpoint in current_room.savingpoint_list:
                            if savingpoint.saved == True:
                                current_level.current_room = current_room_no
                        if current_level.current_room == current_room_no:
                            savingpoints = current_room.savingpoint_list
                            current_room = current_level.rooms[current_level.current_room]
                        else:
                            current_room = current_level.rooms[current_level.current_room]
                        current_room.savingpoint_list = savingpoints
                        player.room = current_room
                        allSprites = pygame.sprite.Group()
                        current_room.revive()                        
                        allSprites.add(player)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT and player.change_x < 0:
                        player.stop()
                    if event.key == pygame.K_RIGHT and player.change_x > 0:
                        player.stop()
                if player.rect.x >= screen_width - 10:
                    current_level.current_room = ((current_level.current_room + 1)
                        % len(current_level.rooms))
                    current_room = current_level.rooms[current_level.current_room]
                    player.rect.x = -10
                    player.room = current_room
                if player.rect.x < -10:
                    current_level.current_room = ((current_level.current_room - 1)
                        % len(current_level.rooms))
                    current_room = current_level.rooms[current_level.current_room]
                    player.rect.x = screen_width - 11
                    player.room = current_room
            current_room.update()
            allSprites.update()
            current_room.checkGameOver()
            current_room.draw(screen,death,time)
            if MP and haveOthers:
                for other in others:
                    screen.blit(image,(others[other][0],others[other][1]))
            allSprites.draw(screen)
            pygame.display.flip()
        elif current_room.over:
            #restart
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 
                    if event.key == pygame.K_r:
                        death += 1
                        savingpoints = (current_level.rooms[current_level.current_room-1].savingpoint_list)
                        current_room_no = current_level.current_room
                        if current_level_no == 1:
                            current_level = Level1(player)
                        if current_level_no == 2:
                            current_level = Level2(player)
                        if current_level_no == 3:
                            current_level = Level3(player)
                        if current_level_no == 4:
                            current_level = Level4(player)
                        if current_level_no == 5:
                            current_level = SavedLevel(player,path)
                        current_level.current_room = current_room_no - 1
                        if current_level.current_room == -1:
                            current_level.current_room = 0
                        for savingpoint in current_room.savingpoint_list:
                            if savingpoint.saved == True:
                                current_level.current_room = current_room_no
                        if current_level.current_room == current_room_no:
                            savingpoints = current_room.savingpoint_list
                            current_room = current_level.rooms[current_level.current_room]
                        else:
                            current_room = current_level.rooms[current_level.current_room]
                        current_room.savingpoint_list = savingpoints
                        player.room = current_room
                        allSprites = pygame.sprite.Group()
                        current_room.revive()                       
                        allSprites.add(player)
            allSprites.update()
            current_room.update()
            myfont = pygame.font.SysFont("comicsansms", 60)
            gameOverImage = pygame.image.load("GameOver.png").convert()
            screen.blit(gameOverImage,(100,50))
            text = myfont.render("Press r to restart!", 1, white)
            screen.blit(text,(150,250))
            pygame.display.flip()
        elif current_room.win:
            time = (pygame.time.get_ticks()-cur_time)/1000
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        highScores(current_level_no,death,time)
                        return
            if MP:
                for other in others:
                    if others[other][4] == False:
                        MPwin = True
                        break
            winImage = pygame.image.load("Win.png").convert()
            screen.blit(winImage,(150,150))
            myfont = pygame.font.SysFont("comicsansms", 30)
            text = myfont.render("Press Esc to go to main menu!", 1, white)
            screen.blit(text,(150,250))
            if MP and MPwin:
                text = myfont.render("Congratulations! You win!",1,white)
                screen.blit(text,(200,450))
            elif MP and not MPwin:
                text = myfont.render("Sorry! You lose!",1,white)
                screen.blit(text,(250,500))
            pygame.display.flip()


def timerFired(server,serverMsg,player,death,time,win,others):
    sendMSG(server,"%d %d %d %d %s" %(player.rect.x,player.rect.y,
        death,time,win))
    if serverMsg.qsize() > 0:
        msg = serverMsg.get(False)
    try:
        if msg.startswith("newPlayer"):
            msg = msg.split()
            newPID = int(msg[1])
            x = int(msg[2])
            y = int(msg[3])
            death = int(msg[4])
            time = int(msg[5])
            Win = eval(msg[6])
            others[newPID] = [x,y,death,time,Win]
        elif msg.startswith("playerMoved"):
            msg = msg.split()
            PID = int(msg[1])
            x = int(msg[2])
            y = int(msg[3])
            death = int(msg[4])
            time = int(msg[5])
            Win = eval(msg[4])
            others[PID] = [x,y,death,time,Win]
    except:
        pass
    # serverMsg.task_done()



class Splashscreen(object):
    def __init__(self, mode):
        self.MP = False
        self.image = pygame.Surface((800,600))
        self.mode = mode
        self.button_list = pygame.sprite.Group()
        if mode == "Welcome":
            self.button_list.add(Button(250,500,"Play", 250,80))
        if mode == "Mainpage":
            self.button_list.add(Button(300,75, "Single Player",200,80))
            self.button_list.add(Button(300,150, "Competition",200,80))
            self.button_list.add(Button(300,225, "Game Editor",200,80))
            self.button_list.add(Button(300,300, "Instruction",200,80))
            self.button_list.add(Button(300,375, "High Scores",200,80))
            self.button_list.add(Button(300,450, "Load Saved Game",200,80))
        if mode == "Single Player":
            self.button_list.add(Button(75,50, "Homework",200,80))
            self.button_list.add(Button(475,50, "Midterm",200,80))
            self.button_list.add(Button(75,350, "Final",200,80))
            self.button_list.add(Button(475,350, "Term Project",200,80))
        if mode == "Competition":
            self.button_list.add(Button(75,50, "Homework",200,80))
            self.button_list.add(Button(475,50, "Midterm",200,80))
            self.button_list.add(Button(75,350, "Final",200,80))
            self.button_list.add(Button(475,350, "Term Project",200,80))
        if mode == "Instruction":
            self.page = 1
            self.button_list.add(Button(600,550,"Next page",200,50))
            self.button_list.add(Button(10,550,"Previous page",200,50))


    def draw(self, screen):
        self.background_image = pygame.image.load("Background.png").convert()
        background_image2 = pygame.image.load("Background3.png").convert()
        self.background_image2 = pygame.Surface((800,600))
        pygame.transform.scale(background_image2,(800,600),self.background_image2)
        myfont = pygame.font.SysFont("comicsansms", 20)
        if self.mode == "Welcome":
            screen.blit(self.background_image,(0,0))
        else:
            screen.blit(self.background_image2,(0,0))
        if (self.mode == "Instruction" or self.mode == "Next page" or 
            self.mode == "Previous page"):
            self.drawInstruction(screen)
        for button in self.button_list:
            if button.text == "Play":
                font = pygame.font.SysFont("comicsansms",50)
                text = font.render(button.text, 1, black)
                screen.blit(text, (button.rect.x + 70, button.rect.y))
            elif button.text == "Load Saved Game":
                button.draw(screen)
                text = myfont.render(button.text,1,black)
                screen.blit(text,(button.rect.x + 20,button.rect.y+15))
            else:
                button.draw(screen)
                text = myfont.render(button.text, 1, black)
                screen.blit(text, (button.rect.x + 50, button.rect.y+15))
        if self.mode == "High Scores":
            i = 0
            for texts in ["Level1", "Level2", "Level3", "Level4"]:
                text = myfont.render(texts,1,black)
                screen.blit(text,(i*200+70,150))
                text = myfont.render("Death  Time",1,black)
                screen.blit(text,(i*200+50,180))
                i += 1
                if not os.path.isfile("HighScores.txt"):
                    highScores()
                HighScores = LevelEditor.readFile("HighScores.txt")
                j = 1
                for scores in HighScores.levels[i]:
                    if scores[0] == None:
                        text = myfont.render("---   ---",1,black)
                        screen.blit(text,((i-1)*200+60,180+j*40))
                        j += 1
                    else:
                        text = myfont.render(str(scores[0]) + 
                            "     %d:%.2d" %(scores[1]//60,scores[1]%60),1,black)
                        screen.blit(text,((i-1)*200+60,180+j*40))
                        j += 1


    def drawInstruction(self,screen):
        image = pygame.image.load("I"+str(self.page)+".png").convert()
        pygame.transform.scale(image,(800,600),self.image)
        screen.blit(self.image,(0,0))


            

    def mousePressed(self, pos):
        for button in self.button_list:
            top = button.rect.top
            bottom = button.rect.bottom
            left = button.rect.left
            right = button.rect.right
            (x, y) = pos
            if top <= y <= bottom and left <= x <= right:
                self.mode = button.text







def sendMSG(server,msg):
    msg += "\n"
    server.send(bytes(msg,"UTF-8"))



def main():
    pygame.init()
    screen = pygame.display.set_mode([800, 600])
    pygame.display.set_caption("I wanna pass 112")
    gameOver = False
    clock = pygame.time.Clock()
    mode = Splashscreen("Welcome")
    while not gameOver:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gameOver = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                mode.mousePressed(event.pos)
                if mode.mode == "Play":
                    mode = Splashscreen("Mainpage")
                if mode.mode in ("Homework","Midterm","Final", "Term Project"):
                    play(screen, mode.mode,mode.MP)
                if mode.mode == "Game Editor":
                    levelEditor(screen)
                if mode.mode == "Mainpage":
                    mode = Splashscreen("Mainpage")
                if mode.mode == "Single Player":
                    mode = Splashscreen("Single Player")
                if mode.mode == "Instruction":
                    mode = Splashscreen("Instruction")
                if mode.mode == "Competition":
                    mode = Splashscreen("Competition")
                    mode.MP = True
                if mode.mode == "High Scores":
                    mode = Splashscreen("High Scores")
                if mode.mode == "Load Saved Game":
                    play(screen,mode.mode,False)
                if mode.mode == "Next page":
                    mode.page += 1
                    if mode.page == 7:
                        mode.page = 1
                if mode.mode == "Previous page":
                    mode.page -= 1
                    if mode.page == 0:
                        mode.page = 6
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mode = Splashscreen("Mainpage")
        mode.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()



if __name__ == "__main__":
    main()




