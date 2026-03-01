##Main script location for "Wrath of Stone"
##All central code comprised here for major game functions and systems
from math import trunc

#Imports
import pygame
import time
import sprite_sheet_handler
from pygame.locals import *
import random

# pygame setup
#setup for widely used/general variables
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((2048, 1080))
pygame.display.set_caption("Wrath of stone alpha 2.1.0")
clock = pygame.time.Clock()
startTime = time.time()
hours, minutes, seconds = 0, 0, 0
score = 0
running = True
paused = False
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
motion = "none"
font = pygame.font.SysFont("comicsans", 30)
collisonList = []
enemyHitList = []
coinCollisionList = []
enemyCollisionList = []
buyableCollisionList = []
itemCollisionList = []
#active item data list, keep collapsed
activeitemlist = {
    "Power Stone": {
        "image": "textures/items/powerstone.png",
        "name": "powerstone",
        "requiredcharge": 2
    },
    "Hungry Skull": {
        "image": "textures/items/hungryskull.png",
        "name": "hungryskull",
        "requiredcharge": 5
    }
}
enemyMoveCooldown = 4
enemyMoveCooldownCount = 0
DEVMODE = False #used to enable devmode which "unlocks" featured for game testing
hit = -1
classPicked = False
characterselectscreen = pygame.image.load("textures/ui/characterselect.png").convert_alpha()
pausescreen = pygame.image.load("textures/ui/pausescreen.png").convert_alpha()
pausescreen.set_alpha(100)
pausefirsttick = True
mixer_initialised = False
floorClearedCheck = False
floorlist = []
floorcount = 0
dispTrapdoor = False

#variables for timed active items
powerstonetick = 0
powerstoneactive = False

#sound manager
def playSound(sound):
    global mixer_initialised
    if not mixer_initialised:
        pygame.mixer.init()
        mixer_initialised = True
    toplay = pygame.mixer.Sound(sound)
    pygame.mixer.Sound.play(toplay)

#class creation: obstacles in rooms
class Obstacle:
    def __init__(self, position, sprite):
        self.position = position
        self.image = pygame.transform.scale(sprite, (24 * 4, 24 * 4))
        self.boundingBox = pygame.Rect(self.position[0], self.position[1], self.image.get_width(), self.image.get_height())

class Buyable(Obstacle):
    def __init__(self,position, sprite, price, buytype):
        super().__init__(position, sprite)
        self.image.set_colorkey(WHITE)
        self.price = price
        self.type = buytype

    def bought(self, wallet):
        if wallet >= self.price:
            return wallet - self.price
        else:
            return False

class Coin():
    def __init__(self,posx, posy, value, image):
        self.value = value
        self.image = pygame.image.load(image).convert_alpha()
        self.position = (posx + 30, posy + 30)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.image = pygame.transform.scale(self.image, (self.width * 2, self.height * 2))
        self.boundingBox = pygame.Rect(self.position[0], self.position[1], self.image.get_width(), self.image.get_height())
        self.image.set_colorkey(WHITE)

    def getValue(self):
        return self.value

class Active():
    def __init__(self, image, name, requiredcharge):
        self.position = ((screen.get_width() / 2) -30, 400)
        self.image = pygame.image.load(image).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.image = pygame.transform.scale(self.image, (self.width * 4, self.height * 4))
        self.image.set_colorkey(WHITE)
        self.boundingBox = pygame.Rect(self.position[0], self.position[1], self.image.get_width(), self.image.get_height())
        self.charge = requiredcharge
        self.name = name

    def drawChargeBar(self, surface, charge):
        width = 100
        height = 40
        x = 570
        y = 280
        ratio = charge / self.charge
        currentWidth = width * ratio
        pygame.draw.rect(surface, (100, 100, 100), (x, y, width, height))
        pygame.draw.rect(surface, (0, 200, 0), (x, y, currentWidth, height))
        pygame.draw.rect(surface, BLACK, (x, y, width, height), 3)

#class creation: hostile enemies in rooms
class Enemy():
    def __init__(self, image, x, y, health, step):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.scale = 2
        self.image = pygame.transform.scale(image, (self.width * self.scale, self.height * self.scale))
        self.maxhealth = health
        self.health = self.maxhealth
        self.stepdistance = step
        self.boundingBox = pygame.Rect(self.x, self.y, self.width * self.scale, self.height * self.scale)
        self.image.set_colorkey(WHITE)

    def drawBoundingBox(self):
        self.boundingBox = pygame.Rect(self.x, self.y, self.width * self.scale, self.height * self.scale)

    def chooseMovement(self):
        direction = random.randint(1, 8)
        return direction, self.stepdistance

class Boss(Enemy):
    def __init__(self, image, x, y, health, dist):
        super().__init__(image, x, y, health, dist)
        self.scale = 4
        self.image = pygame.transform.scale(image, (self.width * self.scale, self.height * self.scale))
        self.image.set_colorkey(WHITE)

    def drawHealthBar(self, surface):
        width = 500
        height = 80
        x = 800
        y = 900
        ratio = self.health / self.maxhealth
        currentWidth = width * ratio
        pygame.draw.rect(surface, (100,100,100), (x, y, width, height))
        pygame.draw.rect(surface, (200,0,0),(x, y, currentWidth, height))
        pygame.draw.rect(surface, BLACK, (x, y, width, height), 3)
#class creation: create the room class to contain content, used in floors
class Room:
    def __init__(self, sprite, obnum):
        self.obnum = obnum
        self.width = 240
        self.height = 240
        self.scale = 4
        self.cleared = False
        self.oblist = []
        self.enemylist = []
        self.pickuplist = []
        self.itemlist = []
        self.exit = ""
        self.doorBoxList = []
        self.usedCoords = []
        self.image = pygame.transform.scale(sprite, [self.width * self.scale, self.height * self.scale])
        self.rect = self.image.get_rect()
        self.rect.center = (screen.get_width() / 2, screen.get_height() / 2)
        self.walls = [pygame.rect.Rect(self.rect.x, self.rect.y, 34 * self.scale, self.height * self.scale),
                      pygame.rect.Rect(self.rect.x + (self.scale * self.width - (34 * self.scale)), self.rect.y, 34 * self.scale, self.height * self.scale),
                      pygame.rect.Rect(self.rect.x, self.rect.y, self.width * self.scale, 34 * self.scale),
                      pygame.rect.Rect(self.rect.x, self.rect.y + (self.scale * self.height - (28 * (self.scale+1))), self.width * self.scale, 34 * self.scale)]

    def obstaclePlace(self):
        self.oblist = []
        self.usedCoords = []
        for i in range(self.obnum):
            valid = False
            while not valid:
                posx = ((random.randint(1,5) * 24 * 4) + 666 + 24) * 1
                posy = ((random.randint(1,5) * 24 * 4) + 182 + 24) * 1
                if (posx, posy) not in self.usedCoords:
                    valid = True
            if random.randint(1,5) != 1:
                self.oblist.append(Obstacle((posx, posy), pygame.image.load("textures/obstacles/obstacle.png").convert_alpha()))
            else:
                self.enemylist.append(Enemy(pygame.image.load("textures/enemies/enemy.png").convert_alpha(), posx, posy, 3, 45))
            self.usedCoords.append((posx, posy))
        self.doorBoxList.append(pygame.rect.Rect(590, 500, 96, 96))
        self.doorBoxList.append(pygame.rect.Rect(1360, 500, 96, 96))
        self.doorBoxList.append(pygame.rect.Rect(1000, 110, 96, 96))
        self.doorBoxList.append(pygame.rect.Rect(1000, 880, 96, 96))

    def spawnRewards(self):
        for i in range(random.randrange(1, 3)):
            valid = False
            while not valid:
                posx = ((random.randint(1, 5) * 24 * 4) + 666 + 24) * 1
                posy = ((random.randint(1, 5) * 24 * 4) + 182 + 24) * 1
                if (posx, posy) not in self.usedCoords:
                    valid = True
            if random.randrange(1, 6) != 1:
                self.pickuplist.append(Coin(posx, posy, 1, "textures/collectibles/coinicon.png"))
            else:
                self.pickuplist.append(Coin(posx, posy, 5, "textures/collectibles/silvercoinicon.png"))


    def summonBoss(self):
        self.enemylist.append(Boss(pygame.image.load("textures/enemies/boss.png").convert_alpha(), screen.get_width() / 2, screen.get_height() / 2, 40, 60))
        self.doorBoxList.append(pygame.rect.Rect(590, 500, 96, 96))
        self.doorBoxList.append(pygame.rect.Rect(1360, 500, 96, 96))
        self.doorBoxList.append(pygame.rect.Rect(1000, 110, 96, 96))
        self.doorBoxList.append(pygame.rect.Rect(1000, 880, 96, 96))


    def objectDraw(self):
        global dispTrapdoor
        for i in range(len(self.oblist)):
            screen.blit(self.oblist[i].image, self.oblist[i].position)
        for i in range(len(self.enemylist)):
            screen.blit(self.enemylist[i].image, (self.enemylist[i].x, self.enemylist[i].y))
        if dispTrapdoor:
            screen.blit(self.exit.image, self.exit.position)
        if len(self.pickuplist) > 0:
            for i in range(len(self.pickuplist)):
                screen.blit(self.pickuplist[i].image, self.pickuplist[i].position)
        if len(self.itemlist) > 0:
            for i in range(len(self.itemlist)):
                screen.blit(self.itemlist[i].image, self.itemlist[i].position)

class Shop(Room):
    def __init__(self,sprite):
        super().__init__(sprite,0)
        self.buyablelist = []
        self.cleared = True

    def generateBuyables(self):
        for i in range(3):
            if random.randrange(1,5) >= 3:
                self.buyablelist.append(Buyable(((877+(96*i)),488),pygame.image.load("textures/items/heartitem.png").convert_alpha(),5, "heart"))
            else:
                self.buyablelist.append(Buyable(((877 + (96 * i)), 488), pygame.image.load("textures/items/damageup.png").convert_alpha(), 10, "damage"))

    def buyableDraw(self):
        for i in range(len(self.buyablelist)):
            screen.blit(self.buyablelist[i].image, self.buyablelist[i].position)
            cost = font.render(f"${self.buyablelist[i].price}", True, BLACK)
            screen.blit(cost, (self.buyablelist[i].position[0]+20, self.buyablelist[i].position[1]+90))

#class creation: class for the player entity
class Character(sprite_sheet_handler.SpriteSheet):
    def __init__(self, image, x, y):
        super().__init__(image)
        #size
        self.width = 24
        self.height = 24
        self.scale = 4
        #stats
        self.maxhealth = 3
        self.health = self.maxhealth
        self.speed = 2
        self.damage = 10
        self.range = 10
        self.attackspeed = 10
        self.iframes = 60
        self.damagecooldown = 0
        self.invulnerable = False
        self.attackoncooldown = False
        self.attackcooldown = 60
        self.attackcooldowncount = 0
        self.bgcolour = WHITE
        self.spawnpos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
        self.boxpos = pygame.Vector2(self.spawnpos[0], self.spawnpos[1])
        self.boundingBox = pygame.Rect(self.boxpos[0], self.boxpos[1], (self.width - 4) * self.scale, (self.height - 4) * self.scale)
        self.pos = self.spawnpos
        self.attackbox = pygame.Rect(0,0,96,96)
        self.attackboximagebase = pygame.image.load("textures/ui/attackbox.png").convert_alpha()
        #pickups
        self.coins = 0
        #items
        self.chargeneeded = 0
        self.charge = 0
        self.items = []
        self.heldactive = ""

    def collisionredraw(self, x, y):
        self.boundingBox = pygame.Rect(x + 10, y + 18, (self.width - 6) * self.scale, (self.height - 6) * self.scale)

    def attack(self,direction):
        if direction == 1:
            self.attackboximage = pygame.transform.scale(self.attackboximagebase, (24 * 4 * self.range, 24 * 4))
            self.attackbox = pygame.Rect (self.pos.x - (self.width * self.scale) - ((self.width * self.scale * self.range)-(self.width * self.scale)), self.pos.y, 96 * self.range, 96)
            screen.blit(self.attackboximage, self.attackbox)
        elif direction == 2:
            self.attackboximage = pygame.transform.scale(self.attackboximagebase, (24 * 4 * self.range, 24 * 4))
            self.attackbox = pygame.Rect(self.pos.x + (self.width * self.scale), self.pos.y, 96 * self.range, 96)
            screen.blit(self.attackboximage, self.attackbox)
        elif direction == 3:
            self.attackboximage = pygame.transform.scale(self.attackboximagebase, (24 * 4, 24 * 4 * self.range))
            self.attackbox = pygame.Rect(self.pos.x, self.pos.y - (self.height * self.scale) - ((self.height * self.scale * self.range)-(self.height * self.scale)), 96, 96 * self.range)
            screen.blit(self.attackboximage, self.attackbox)
        elif direction == 4:
            self.attackboximage = pygame.transform.scale(self.attackboximagebase, (24 * 4, 24 * 4 * self.range))
            self.attackbox = pygame.Rect(self.pos.x, self.pos.y + (self.height * self.scale), 96, 96 * self.range)
            screen.blit(self.attackboximage, self.attackbox)

#player creation
player = Character(pygame.image.load("textures/players/ston_right_walk.png").convert_alpha(), 100, 100)

#class creation: creates floors containing smaller rooms
class Floor():
    def __init__(self, number):
        self.roomnum = random.randint(12, 25)
        self.roomlist = []
        self.map = [[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]
        self.minimap = [[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,(1640,320),0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]
        self.finalroom = (0,0)
        self.finalroommap = (0,0)
        self.shoproommap = (0,0)
        self.shopMade = False
        self.numbr = number

    def generateFloorLayout(self):
        self.map[4][4] = Room(pygame.image.load("textures/rooms/testroom.png").convert_alpha(), 0)
        self.map[4][4].obstaclePlace()
        roomcount = 1
        rooms = [(4,4)]
        setobnum = 8
        currentminimapcoords = (1640,320)
        while roomcount < self.roomnum:
            choice = random.randint(1, 4)
            focusrow, focuscolumn = random.choice(rooms)
            if choice == 1 and focuscolumn < 8 and self.map[focusrow][focuscolumn+1] == 0:
                self.map[focusrow][focuscolumn+1] = Room(pygame.image.load("textures/rooms/testroom.png").convert_alpha(), setobnum)
                self.map[focusrow][focuscolumn+1].obstaclePlace()
                prevminimapcoords = self.minimap[focusrow][focuscolumn]
                focuscolumn += 1
                currentminimapcoords = (prevminimapcoords[0] + 40, prevminimapcoords[1])
                self.minimap[focusrow][focuscolumn] = currentminimapcoords
                if roomcount == self.roomnum - 1:
                    self.finalroom = (focusrow,focuscolumn)
                    self.finalroommap = currentminimapcoords
                    self.map[focusrow][focuscolumn].oblist = []
                    self.map[focusrow][focuscolumn].enemylist = []
                    self.map[focusrow][focuscolumn].summonBoss()
                roomcount += 1
                rooms.append((focusrow, focuscolumn))
            if choice == 2 and focuscolumn > 0 and self.map[focusrow][focuscolumn-1] == 0:
                self.map[focusrow][focuscolumn-1] = Room(pygame.image.load("textures/rooms/testroom.png").convert_alpha(), setobnum)
                self.map[focusrow][focuscolumn - 1].obstaclePlace()
                prevminimapcoords = self.minimap[focusrow][focuscolumn]
                focuscolumn -= 1
                currentminimapcoords = (prevminimapcoords[0] - 40, prevminimapcoords[1])
                self.minimap[focusrow][focuscolumn] = currentminimapcoords
                if roomcount == self.roomnum - 1:
                    self.finalroom = (focusrow,focuscolumn)
                    self.finalroommap = currentminimapcoords
                    self.map[focusrow][focuscolumn].oblist = []
                    self.map[focusrow][focuscolumn].enemylist = []
                    self.map[focusrow][focuscolumn].summonBoss()
                roomcount += 1
                rooms.append((focusrow, focuscolumn))
            if choice == 3 and focusrow > 0 and self.map[focusrow-1][focuscolumn] == 0:
                self.map[focusrow-1][focuscolumn] = Room(pygame.image.load("textures/rooms/testroom.png").convert_alpha(), setobnum)
                self.map[focusrow - 1][focuscolumn].obstaclePlace()
                prevminimapcoords = self.minimap[focusrow][focuscolumn]
                focusrow -= 1
                currentminimapcoords = (prevminimapcoords[0], prevminimapcoords[1] - 40)
                self.minimap[focusrow][focuscolumn] = currentminimapcoords
                if roomcount == self.roomnum - 1:
                    self.finalroom = (focusrow,focuscolumn)
                    self.finalroommap = currentminimapcoords
                    self.map[focusrow][focuscolumn].oblist = []
                    self.map[focusrow][focuscolumn].enemylist = []
                    self.map[focusrow][focuscolumn].summonBoss()
                roomcount += 1
                rooms.append((focusrow, focuscolumn))
            if choice == 4 and focuscolumn > 0 and self.map[focusrow+1][focuscolumn] == 0:
                self.map[focusrow+1][focuscolumn] = Room(pygame.image.load("textures/rooms/testroom.png").convert_alpha(), setobnum)
                self.map[focusrow+1][focuscolumn].obstaclePlace()
                prevminimapcoords = self.minimap[focusrow][focuscolumn]
                focusrow += 1
                currentminimapcoords = (prevminimapcoords[0], prevminimapcoords[1] + 40)
                self.minimap[focusrow][focuscolumn] = currentminimapcoords
                if roomcount == self.roomnum - 1:
                    self.finalroom = (focusrow,focuscolumn)
                    self.finalroommap = currentminimapcoords
                    self.map[focusrow][focuscolumn].oblist = []
                    self.map[focusrow][focuscolumn].enemylist = []
                    self.map[focusrow][focuscolumn].summonBoss()
                roomcount += 1
                rooms.append((focusrow, focuscolumn))
        shoprooms = []
        for r in rooms:
            if r != (4,4) and r != self.finalroom:
                shoprooms.append(r)
        print(shoprooms)
        shopcoords = random.choice(shoprooms)
        shoprow, shopcolumn = shopcoords
        self.map[shoprow][shopcolumn] = Shop(pygame.image.load("textures/rooms/shop.png").convert_alpha())
        self.map[shoprow][shopcolumn].obstaclePlace()
        self.map[shoprow][shopcolumn].enemylist = []
        self.map[shoprow][shopcolumn].oblist = []
        self.map[shoprow][shopcolumn].generateBuyables()
        self.shoproommap = self.minimap[shoprow][shopcolumn]

#player object creation

#variables used in animations
animation_list = []
animation_steps = [4,8,8,8]
action = 0
last_update = pygame.time.get_ticks()
animation_cooldown = 100
frame = 0
step_counter = 0

#first floor creation
def genFloor(num):
    floor = Floor(num)
    floor.generateFloorLayout()
    floorlist.append(floor)
    for i in range(9):
        print(floorlist[floorcount].map[i])
    currentroomrow = 4
    currentroomcol = 4
    currentroommapcoord = (1640,320)
    return currentroomrow,currentroomcol,currentroommapcoord

currentroomrow,currentroomcol,currentroommapcoord = genFloor(floorcount)

#used to change the room being displayed and used
def selectRoom():
    global currentroomrow, running
    global currentroomcol
    global collisonList, enemyHitList, enemyCollisionList, coinCollisionList, buyableCollisionList
    global currentroommapcoord
    global floorcount, dispTrapdoor
    moved = False
    if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) == 0:
        try:
            if player.boundingBox.collidelist(floorlist[floorcount].map[currentroomrow][currentroomcol].doorBoxList) == 0:
                if floorlist[floorcount].map[currentroomrow][currentroomcol-1] != 0:
                    currentroomcol = currentroomcol - 1
                    moved = True
                    player.pos.x = 1260
                    player.pos.y = 500
                    currentroommapcoord = (currentroommapcoord[0] - 40, currentroommapcoord[1])
            if player.boundingBox.collidelist(floorlist[floorcount].map[currentroomrow][currentroomcol].doorBoxList) == 1:
                if floorlist[floorcount].map[currentroomrow][currentroomcol+1] != 0:
                    currentroomcol = currentroomcol + 1
                    moved = True
                    player.pos.x = 700
                    player.pos.y = 500
                    currentroommapcoord = (currentroommapcoord[0] + 40, currentroommapcoord[1])
            if player.boundingBox.collidelist(floorlist[floorcount].map[currentroomrow][currentroomcol].doorBoxList) == 2:
                if floorlist[floorcount].map[currentroomrow-1][currentroomcol] != 0:
                    currentroomrow = currentroomrow - 1
                    moved = True
                    player.pos.x = 1000
                    player.pos.y = 780
                    currentroommapcoord = (currentroommapcoord[0], currentroommapcoord[1] - 40)
            if player.boundingBox.collidelist(floorlist[floorcount].map[currentroomrow][currentroomcol].doorBoxList) == 3:
                if floorlist[floorcount].map[currentroomrow+1][currentroomcol] != 0:
                    currentroomrow = currentroomrow + 1
                    moved = True
                    player.pos.x = 1000
                    player.pos.y = 210
                    currentroommapcoord = (currentroommapcoord[0], currentroommapcoord[1] + 40)
            if moved:
                playSound("doorenter.ogg")
                if floorlist[floorcount].map[currentroomrow][currentroomcol].exit != "":
                    dispTrapdoor = True
                else:
                    dispTrapdoor = False
                collisonList.clear()
                enemyHitList.clear()
                coinCollisionList.clear()
                buyableCollisionList.clear()
                itemCollisionList.clear()
                for i in range(len(room1.walls)):
                    collisonList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].walls[i])
                for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].oblist)):
                    collisonList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].oblist[i].boundingBox)
                for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist)):
                    enemyCollisionList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox)
                    enemyHitList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox)
                for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].pickuplist)):
                    coinCollisionList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].pickuplist[i].boundingBox)
                if isinstance(floorlist[floorcount].map[currentroomrow][currentroomcol], Shop):
                    for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist)):
                        buyableCollisionList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist[i].boundingBox)


        except IndexError:
            pass
    return moved

#animation handler
def createAnimation():
    global step_counter, player
    step_counter = 0
    animation_list = []
    for animation in animation_steps:
        temp_img_list = []
        for _ in range(animation):
            temp_img_list.append(player.get_image(step_counter,24,24,4, WHITE))
            step_counter += 1
        animation_list.append(temp_img_list)
    return animation_list

animation_list = createAnimation()

#override for first floor creation, creates start room
room1 = floorlist[floorcount].map[4][4]
for i in range(len(room1.walls)):
    collisonList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].walls[i])
floorlist[floorcount].map[currentroomrow][currentroomcol].obstaclePlace()
for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].oblist)):
    collisonList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].oblist[i].boundingBox)

def roomCleared():
    global score
    floorlist[floorcount].map[currentroomrow][currentroomcol].cleared = True
    if player.health < player.maxhealth:
        player.health += 1
    buffchoice = random.randint(1, 6)
    if buffchoice == 1:
        player.damage += 1
    elif buffchoice == 2:
        player.speed += 0.2
    elif buffchoice == 3:
        player.range += 0.4
    elif buffchoice == 4:
        player.attackspeed += 0.5
    if player.chargeneeded != 0 and player.charge < player.chargeneeded:
        player.charge += 1
    floorlist[floorcount].map[currentroomrow][currentroomcol].spawnRewards()
    for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].pickuplist)):
        coinCollisionList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].pickuplist[i].boundingBox)
    score += 100

def enemyhit():
    global enemyCollisionList, running, coinCollisionList, score
    hitindex = player.attackbox.collidelist(enemyCollisionList)
    floorCleared = False
    if hitindex == -1:
        pass
    else:
        floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[hitindex].health -= player.damage
        if floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[hitindex].health <= 0:
            floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist.pop(hitindex)
            enemyCollisionList.pop(hitindex)
            score += 25
            if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) == 0:
                if floorlist[floorcount].map[currentroomrow][currentroomcol] != floorlist[floorcount].map[int(floorlist[floorcount].finalroom[0])][int(floorlist[floorcount].finalroom[1])]:
                    roomCleared()
                else:
                    floorCleared = True
                    activeData = random.choice(list(activeitemlist.values()))
                    floorlist[floorcount].map[currentroomrow][currentroomcol].itemlist.append(Active(**activeData))
                    itemCollisionList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].itemlist[0].boundingBox)
                    score += 1000
        return floorCleared


#main image loader
doortopimg = pygame.image.load("textures/obstacles/doortop.png").convert_alpha()
doortopimg = pygame.transform.scale(doortopimg, (24 * 4, 24 * 4))
doorleftimg = pygame.image.load("textures/obstacles/doorleft.png").convert_alpha()
doorleftimg = pygame.transform.scale(doorleftimg, (24 * 4, 24 * 4))
doorbottomimg = pygame.image.load("textures/obstacles/doorbottom.png").convert_alpha()
doorbottomimg = pygame.transform.scale(doorbottomimg, (24 * 4, 24 * 4))
doorrightimg = pygame.image.load("textures/obstacles/doorright.png").convert_alpha()
doorrightimg = pygame.transform.scale(doorrightimg, (24 * 4, 24 * 4))
lockeddoortopimage = pygame.image.load("textures/obstacles/lockeddoortop.png").convert_alpha()
lockeddoortopimage = pygame.transform.scale(lockeddoortopimage, (24 * 4, 24 * 4))
lockeddoorleftimage = pygame.image.load("textures/obstacles/lockeddoorleft.png").convert_alpha()
lockeddoorleftimage = pygame.transform.scale(lockeddoorleftimage, (24 * 4, 24 * 4))
lockeddoorbottomimage = pygame.image.load("textures/obstacles/lockeddoorbottom.png").convert_alpha()
lockeddoorbottomimage = pygame.transform.scale(lockeddoorbottomimage, (24 * 4, 24 * 4))
lockeddoorrightimage = pygame.image.load("textures/obstacles/lockeddoorright.png").convert_alpha()
lockeddoorrightimage = pygame.transform.scale(lockeddoorrightimage, (24 * 4, 24 * 4))
minimapimage = pygame.image.load("textures/ui/roommarker.png").convert_alpha()
currentroomimage = pygame.image.load("textures/ui/currentroom.png").convert_alpha()
startroomimage = pygame.image.load("textures/ui/startroom.png").convert_alpha()
healthimage = pygame.image.load("textures/ui/heart.png").convert_alpha()
damagedimage = pygame.image.load("textures/ui/damaged.png").convert_alpha()
finalroomimage = pygame.image.load("textures/ui/finalroom.png").convert_alpha()
shoproomimage = pygame.image.load("textures/ui/shoproom.png").convert_alpha()
healthfirstcoord = (300,165)
coinicon = pygame.image.load("textures/collectibles/coinicon.png").convert_alpha()
coinicon = pygame.transform.scale(coinicon, (coinicon.get_width()*3,coinicon.get_height()*3))
coinicon.set_colorkey(WHITE)

#function to update all images on the screen every frame
def screen_update():
    global currentroomrow
    global currentroomcol
    global currentroommapcoord, paused
    screen.fill((65, 69, 69))
    mousepos = pygame.mouse.get_pos()
    damagetext = font.render(f"Damage: {player.damage}", True, BLACK)
    speedtext = font.render(f"Speed: {player.speed}", True, BLACK)
    rangetext = font.render(f"Range: {player.range}", True, BLACK)
    attackspeedtext = font.render(f"Attack speed: {player.attackspeed}", True, BLACK)
    text = font.render(f"{paused}", True, BLACK)
    screen.blit(floorlist[floorcount].map[currentroomrow][currentroomcol].image, floorlist[floorcount].map[currentroomrow][currentroomcol].rect)
    if isinstance(floorlist[floorcount].map[currentroomrow][currentroomcol], Shop):
        floorlist[floorcount].map[currentroomrow][currentroomcol].buyableDraw()
    floorlist[floorcount].map[currentroomrow][currentroomcol].objectDraw()
    screen.blit(animation_list[action][frame], player.pos)
    try:
        if floorlist[floorcount].map[currentroomrow][currentroomcol-1] != 0:
            if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) == 0:
                screen.blit(doorleftimg, (590, 500))
            else:
                screen.blit(lockeddoorleftimage, (590, 500))
    except IndexError:
        pass
    try:
        if floorlist[floorcount].map[currentroomrow][currentroomcol+1] != 0:
            if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) == 0:
                screen.blit(doorrightimg, (1370, 500))
            else:
                screen.blit(lockeddoorrightimage, (1370, 500))
    except IndexError:
        pass
    try:
        if floorlist[floorcount].map[currentroomrow-1][currentroomcol] != 0:
            if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) == 0:
                screen.blit(doortopimg, (1000, 110))
            else:
                screen.blit(lockeddoortopimage, (1000, 110))
    except IndexError:
        pass
    try:
        if floorlist[floorcount].map[currentroomrow+1][currentroomcol] != 0:
            if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) == 0:
                screen.blit(doorbottomimg, (1000, 880))
            else:
                screen.blit(lockeddoorbottomimage, (1000, 880))
    except IndexError:
        pass
    screen.blit(text, [300, 100])
    screen.blit(damagetext, [300, 200])
    screen.blit(speedtext, [300, 250])
    screen.blit(rangetext, [300, 300])
    screen.blit(attackspeedtext, [300, 350])
    for i in range(9):
        for j in range(9):
            if floorlist[floorcount].minimap[i][j] != 0:

                screen.blit(minimapimage, floorlist[floorcount].minimap[i][j])
    screen.blit(startroomimage, [1640, 320])
    screen.blit(finalroomimage, floorlist[floorcount].finalroommap)
    screen.blit(shoproomimage, floorlist[floorcount].shoproommap)
    screen.blit(currentroomimage, currentroommapcoord)
    if player.health >= 1:
        screen.blit(healthimage, healthfirstcoord)
    healthcount = 1
    healthnextcoord = (healthfirstcoord[0] + 40, healthfirstcoord[1])
    while healthcount != player.maxhealth:
        if healthcount < player.health:
            screen.blit(healthimage, [healthnextcoord[0], healthnextcoord[1]])
        else:
            screen.blit(damagedimage, [healthnextcoord[0], healthnextcoord[1]])
        healthnextcoord = (healthnextcoord[0] + 40, healthnextcoord[1])
        healthcount += 1
    screen.blit(coinicon,[290,400])
    coinamount = font.render(f"{player.coins}", True, BLACK)
    screen.blit(coinamount, [370, 405])
    if len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist) > 0:
        if isinstance(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[0], Boss):
            floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[0].drawHealthBar(screen)
    if player.heldactive != "":
        screen.blit(player.heldactive.image, [580, 200])
        player.heldactive.drawChargeBar(screen, player.charge)

def descendCheck():
    hit = False
    if dispTrapdoor:
        hit = player.boundingBox.colliderect(floorlist[floorcount].map[currentroomrow][currentroomcol].exit.boundingBox)
    return hit

#checks if player collides with solid object
def collide():
    totalhit = 0
    totalhit += player.boundingBox.collidelist(collisonList)
    return totalhit

#checks if player is hit by an enemy
def playerHitCheck():
    global currentroomrow,currentroomcol
    hits = player.boundingBox.collidelist(enemyHitList)
    return hits

def pickupCollected():
    global score
    pickupindex = player.boundingBox.collidelist(coinCollisionList)
    if pickupindex != -1:
        playSound("coin.ogg")
        player.coins += floorlist[floorcount].map[currentroomrow][currentroomcol].pickuplist[pickupindex].value
        coinCollisionList.pop(pickupindex)
        floorlist[floorcount].map[currentroomrow][currentroomcol].pickuplist.pop(pickupindex)
        score += 10

def buyableBought():
    global score
    buyindex = player.boundingBox.collidelist(buyableCollisionList)
    if buyindex != -1:
        coinupdate = floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist[buyindex].bought(player.coins)
        if coinupdate != False and floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist[buyindex].type == "heart":
            if player.health < player.maxhealth:
                player.health += 1
                buyableCollisionList.pop(buyindex)
                floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist.pop(buyindex)
                player.coins = coinupdate
                score += 50
        elif coinupdate != False and floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist[buyindex].type == "damage":
            player.damage += 2
            buyableCollisionList.pop(buyindex)
            floorlist[floorcount].map[currentroomrow][currentroomcol].buyablelist.pop(buyindex)
            player.coins = coinupdate
            score += 50

def itemCollected():
    global score
    index = player.boundingBox.collidelist(itemCollisionList)
    if index != -1:
        player.heldactive = floorlist[floorcount].map[currentroomrow][currentroomcol].itemlist[index]
        player.chargeneeded = floorlist[floorcount].map[currentroomrow][currentroomcol].itemlist[index].charge
        itemCollisionList.pop(index)
        floorlist[floorcount].map[currentroomrow][currentroomcol].itemlist.pop(index)
        player.charge = 0
        score += 100

def useActive():
    global powerstoneactive
    usefailed = False
    if player.charge == player.chargeneeded:
        if player.heldactive.name == "powerstone":
            player.damage *= 1.5
            player.damage = trunc(player.damage)
            powerstoneactive = True
        if player.heldactive.name == "hungryskull":
            if floorlist[floorcount].map[currentroomrow][currentroomcol] != floorlist[floorcount].map[int(floorlist[floorcount].finalroom[0])][int(floorlist[floorcount].finalroom[1])]:
                enemiesRemaining = len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist)
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist.clear()
                enemyCollisionList.clear()
                if enemiesRemaining > 0:
                    roomCleared()
            else:
                usefailed = True
        if not usefailed:
            player.charge = 0

#main game loop
while running:
    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen_update()

    while not classPicked:
        assasinbox = pygame.rect.Rect(208,621,257,243)
        speedsterbox = pygame.rect.Rect(557, 365, 257, 243)
        warriorbox = pygame.rect.Rect(924, 130, 257, 243)
        rangerbox = pygame.rect.Rect(1285, 363, 257, 243)
        tankbox = pygame.rect.Rect(1612, 639, 257, 243)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if assasinbox.collidepoint(event.pos):
                    player = Character(pygame.image.load("textures/players/asassin_walk.png").convert(),100,100)
                    animation_list.clear()
                    animation_list = createAnimation()
                    player.attackspeed += 0.8
                    classPicked = True
                    playSound("mouse.ogg")
                elif speedsterbox.collidepoint(event.pos):
                    player = Character(pygame.image.load("textures/players/speedster_walk.png").convert(), 100, 100)
                    animation_list.clear()
                    animation_list = createAnimation()
                    player.speed += 0.4
                    classPicked = True
                    playSound("mouse.ogg")
                elif warriorbox.collidepoint(event.pos):
                    player = Character(pygame.image.load("textures/players/warrior_walk.png").convert(), 100, 100)
                    animation_list.clear()
                    animation_list = createAnimation()
                    player.damage += 1
                    classPicked = True
                    playSound("mouse.ogg")
                elif rangerbox.collidepoint(event.pos):
                    player = Character(pygame.image.load("textures/players/ranger_walk.png").convert(), 100, 100)
                    animation_list.clear()
                    animation_list = createAnimation()
                    player.range += 0.6
                    classPicked = True
                    playSound("mouse.ogg")
                elif tankbox.collidepoint(event.pos):
                    player = Character(pygame.image.load("textures/players/tank_walk.png").convert(), 100, 100)
                    animation_list.clear()
                    animation_list = createAnimation()
                    player.maxhealth += 1
                    player.health += 1
                    classPicked = True
                    playSound("mouse.ogg")

        screen.blit(characterselectscreen,(0,0))

        pygame.display.flip()

        clock.tick(60)

    while paused:

        screen_update()
        screen.blit(pausescreen, (0, 0))


        timerTime = int(time.time() - startTime)
        hours = timerTime // 3600
        minutes = (timerTime % 3600) // 60
        seconds = timerTime % 60

        resumebox = pygame.rect.Rect(900, 675, 320, 75)
        exitbox = pygame.rect.Rect(980, 900, 140, 75)
        timertext = font.render("You have been lost in the cave for:", True, BLACK)
        timertextrect = timertext.get_rect(center=(screen.get_width() / 2, (screen.get_height() / 2) - 100))
        timer = font.render(f"{hours:02d}:{minutes:02d}:{seconds:02d}", True, BLACK)
        timerrect = timer.get_rect(center=(screen.get_width() / 2, (screen.get_height() / 2) - 50))
        scoretext = font.render(f"Score: {score}", True, BLACK)
        scoretextrect = scoretext.get_rect(center=(screen.get_width() / 2, (screen.get_height() / 2)))
        screen.blit(timertext, timertextrect)
        screen.blit(timer, timerrect)
        screen.blit(scoretext, scoretextrect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if resumebox.collidepoint(event.pos):
                    paused = False
                    pausefirsttick = True
                elif exitbox.collidepoint(event.pos):
                    paused = False
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            paused = False

        pygame.display.flip()

        clock.tick(60)

    #keeps track of frames (in-game time)
    current_time = pygame.time.get_ticks()
    if current_time - last_update >= animation_cooldown:
        frame += 1
        last_update = current_time
        if frame >= len(animation_list[action]):
            frame = 0

    if powerstoneactive:
        powerstonetick += 1
        if powerstonetick == 900:
            powerstonetick = 0
            powerstoneactive = False
            player.damage /= 1.5
            player.damage = trunc(player.damage)

    #movement engine, also used for other key inputs
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        if not player.attackoncooldown:
            player.attack(1)
            floorClearedCheck = enemyhit()
            player.attackbox = pygame.Rect(0,0,96,96)
            player.attackoncooldown = True
    if keys[pygame.K_RIGHT]:
        if not player.attackoncooldown:
            player.attack(2)
            floorClearedCheck = enemyhit()
            player.attackbox = pygame.Rect(0, 0, 96, 96)
            player.attackoncooldown = True
    if keys[pygame.K_UP]:
        if not player.attackoncooldown:
            player.attack(3)
            floorClearedCheck = enemyhit()
            player.attackbox = pygame.Rect(0, 0, 96, 96)
            player.attackoncooldown = True
    if keys[pygame.K_DOWN]:
        if not player.attackoncooldown:
            player.attack(4)
            floorClearedCheck = enemyhit()
            player.attackbox = pygame.Rect(0, 0, 96, 96)
            player.attackoncooldown = True
    if keys[pygame.K_SPACE]:
        if player.heldactive != "":
            useActive()

    #stores player movement
    dx = 0
    dy = 0
    moving = False

    if keys[pygame.K_w]:
        dy -= 10 * player.speed
        action = 0
        moving = True

    if keys[pygame.K_s]:
        dy += 10 * player.speed
        action = 3
        moving = True

    if keys[pygame.K_a]:
        dx -= 10 * player.speed
        action = 2
        motion = "right"
        moving = True

    if keys[pygame.K_d]:
        dx += 10 * player.speed
        action = 1
        motion = "right"
        moving = True

    if moving:

        stepx = int(dx)
        countx = 1 if dx > 0 else -1

        for i in range(abs(stepx)):
            player.pos.x += countx
            player.collisionredraw(player.pos.x, player.pos.y)
            if collide() >= 0:
                player.pos.x -= countx
                break

        stepy = int(dy)
        county = 1 if stepy > 0 else -1

        for i in range(abs(stepy)):
            player.pos.y += county
            player.collisionredraw(player.pos.x, player.pos.y)
            if collide() >= 0:
                player.pos.y -= county
                break

        #resets animation frame if animation has finished cycling
        if frame >= animation_steps[action]:
            frame = 0

        #redraws the players collision box
        hit = playerHitCheck()

        #if the player hasn't moved rooms, checks for collision or item pickup
        if not selectRoom():
            pickupCollected()
            if isinstance(floorlist[floorcount].map[currentroomrow][currentroomcol], Shop):
                buyableBought()
            itemCollected()


    #pause function
    if keys[pygame.K_ESCAPE]:
        paused = True

    #stops animation if the player isn't moving
    if not moving:
        motion = "none"
        action = 0
        if frame >= animation_steps[action]:
            frame = 0

    #updates wether or not player should exit inulnerability
    if player.invulnerable:
        if player.damagecooldown == player.iframes:
            player.invulnerable = False
            player.damagecooldown = 0
        else:
            player.damagecooldown += 1

    if player.attackoncooldown:
        player.attackcooldowncount += 1 * player.attackspeed
        if player.attackcooldowncount >= player.attackcooldown:
            player.attackoncooldown = False
            player.attackcooldowncount = 0

    #begins player hit sequence
    if hit >= 0 and player.invulnerable == False:
        player.invulnerable = True
        player.health -= 1
        if player.health <= 0:
            byeText = font.render("GAME OVER!", True, [255, 0, 255])
            screen.blit(byeText, pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2))
            screen.blit(damagedimage, healthfirstcoord)
            running = False

    if enemyMoveCooldownCount == enemyMoveCooldown:
        enemyMoveCooldownCount = 0
        for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist)):
            movement, dist = floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].chooseMovement()
            if movement == 1:
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].x -= dist
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
                if floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox.collidelist(collisonList) >= 0:
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].x += dist
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
            elif movement == 2:
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].x += dist
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
                if floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox.collidelist(collisonList) >= 0:
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].x -= dist
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
            elif movement == 3:
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].y -= dist
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
                if floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox.collidelist(collisonList) >= 0:
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].y += dist
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
            elif movement == 4:
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].y += dist
                floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
                if floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox.collidelist(collisonList) >= 0:
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].y -= dist
                    floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].drawBoundingBox()
        enemyHitList.clear()
        for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist)):
            enemyHitList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox)
        enemyCollisionList.clear()
        for i in range(len(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist)):
            enemyCollisionList.append(floorlist[floorcount].map[currentroomrow][currentroomcol].enemylist[i].boundingBox)

    enemyMoveCooldownCount += 1

    if floorClearedCheck:
        floorClearedCheck = False
        floorlist[floorcount].map[currentroomrow][currentroomcol].exit = Obstacle((screen.get_width() / 2, screen.get_height() / 2), pygame.image.load("textures/obstacles/descend.png").convert_alpha())
        dispTrapdoor = True

    if descendCheck() and keys[pygame.K_RETURN]:
        floorcount += 1
        currentroomrow,currentroomcol,currentroommapcoord = genFloor(floorcount)
        dispTrapdoor = False
        itemCollisionList.clear()

    pygame.display.flip()

    clock.tick(60) # limits FPS to 60

pygame.quit()