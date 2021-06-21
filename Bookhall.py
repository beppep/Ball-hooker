import pygame
import pygame_gui
import time
import Box2D
import math
import random

ppm=75
time_step = 1.0/90
resolution = (1200, 675)

levels = [ #shape means radius btw
[(1,-3), 1, [ #level 0
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(3,-6), (2, 2)],
    [(14.5,-4.5), (0.5, 3.5), "win"],
    ],[
    #[(8,-5), [(-1,0),(1,-1),(1,1),(-1,1)]],
]],
[(4.4,-4), 2, [ #level 1
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(3,-7), (3, 2)],
    [(14,-7), (0.5, 0.5), "win"],
    ],[
    [(7,-6.5), [(-1,-3),(1,-3),(1,3),(-1, 3)]],
]],
[(3,-7.4), 2.2, [ #roof goal
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(8,-1.5), (7, 0.5), "win"],
]],
[(1,-3), 1, [ #3: lava floor
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(2,-7), (2, 1)],
    [(8,-9), (4, 1), "death"],
    [(14,-7), (0.5, 0.5), "win"],
]],
[(1,-3), 1, [ #4: momentum jump
    [(8,-9), (8, 1)],
    [(4,0), (4, 1),], #left roof
    [(12,0), (4, 1), "nograb"], #right roof
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5), "nograb"],
    [(2,-6), (2, 2)],
    [(8,-2), (0.2, 2)],
    [(14.5,-1.5), (0.5, 0.5), "win"],
]],
[(2,-resolution[1]/ppm+3), 2, [ #level noel
    [(0,0), (resolution[0]/ppm,1)],
    [(0,0), (1,resolution[1]/ppm)],
    [(resolution[0]/ppm/2,0), (0.5,resolution[1]/ppm/2-1),"death"],
    [(resolution[0]/ppm/2,-resolution[1]/ppm*3/4-1), (0.5,resolution[1]/ppm/4-0.2),"death"],
    [(0,-resolution[1]/ppm), (resolution[0]/ppm,1)],
    [(resolution[0]/ppm,0), (1,resolution[1]/ppm)],
]],
]

pygame.init()

managers={
    "":pygame_gui.UIManager(resolution), #
    "l":pygame_gui.UIManager(resolution), #Level select
    "p":pygame_gui.UIManager(resolution), #Playing
    }

# Main
level_buttons = []
for i in range(10):
    button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((100+i*100, 100), (100, 100)),text="Level "+str(i),manager=managers["l"])
    level_buttons.append(button)


def loadImage(name,r):
    image = pygame.image.load("BookhallFiles/textures/"+name)
    image = pygame.transform.scale(image, (int(r*2*ppm), int(r*2*ppm)))
    return image

def rot_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle*180/math.pi) #degrees
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

class Game():

    def __init__(self):
        self.mode = "l"
        self.levelNum = 0
        self.currentLevel = None
        self.imminentDeath = False
        self.imminentWin = False

    def startLevel(self, num=0):
        self.levelNum = num
        self.currentLevel = Level(*levels[num])

    def update(self):
        if(self.imminentDeath):
            self.currentLevel.killPlayer()
            self.currentLevel.spawnPlayer()
            self.imminentDeath=False
        if(self.imminentWin):
            self.currentLevel.killPlayer()
            self.currentLevel.destroy()
            self.levelNum+=1
            self.startLevel(self.levelNum)
            self.imminentWin=False
        if self.currentLevel:
            self.currentLevel.update()

    def draw(self):
        if self.currentLevel:
            self.currentLevel.draw()

class Block():

    def __init__(self, position, shape, typ=None, dynamic=False, isBox=True):
        self.type = typ
        self.dynamic = dynamic
        if isBox: #lol
            self.shape = [(-shape[0],-shape[1]),(shape[0],-shape[1]),(shape[0],shape[1]),(-shape[0],shape[1])]
        else:
            self.shape = shape
        self.bodyShape = Box2D.b2PolygonShape(vertices=self.shape)
        if self.dynamic:
            self.body = world.CreateDynamicBody(position=position,fixtures=Box2D.b2FixtureDef(shape=self.bodyShape,density=0.2, friction=0.1, restitution=0.2),bullet=True,userData=self)
        else:
            self.body = world.CreateStaticBody(position=position,shapes=self.bodyShape,userData=self)

    def draw(self):
        vertices = []
        for i in range(len(self.shape)):
            vertices.append((self.body.GetWorldPoint(self.shape[i])[0]*ppm, -self.body.GetWorldPoint(self.shape[i])[1]*ppm))
        if(self.type=="death"):
            color = (250,50,50)
        elif(self.type=="win"):
            color = (50,200,100)
        elif(self.type=="nograb"):
            color = (50,0,50)
        else:
            color = (50,50,100)
        pygame.draw.polygon(game_display, color, vertices, width=0)

class Level():

    def __init__(self, spawnpoint, spawnrotation, boxes, objects=[]):
        self.spawnpoint = spawnpoint
        self.spawnrotation = spawnrotation
        self.blocks = []
        self.objects = objects
        self.dynamicBlocks = [] #maybe put everything in blocks?
        self.player = None
        for block in boxes:
            self.blocks.append(Block(*block))
        self.spawnPlayer()

    def killPlayer(self):
        world.DestroyBody(self.player.body) #maybe not kill everything and just move it instead?
        self.player = None
        for block in self.dynamicBlocks:
            world.DestroyBody(block.body)
        self.dynamicBlocks = []

    def spawnPlayer(self):
        self.player = Player(self.spawnpoint, self.spawnrotation)
        for block in self.objects:
            self.dynamicBlocks.append(Block(*block, dynamic=True, isBox=False))

    def destroy(self):
        for block in self.blocks+self.dynamicBlocks:
            world.DestroyBody(block.body)
        self.blocks = []
        self.dynamicBlocks = []

    def update(self):
        self.player.update()

    def draw(self):
        for block in self.blocks+self.dynamicBlocks:
            block.draw()
        self.player.draw()

class Player():

    sprite = loadImage("Book.png", 0.5)

    def __init__(self, spawnpoint, spawnrotation=math.pi/4):
        self.body = world.CreateDynamicBody(fixtures=Box2D.b2FixtureDef(shape=Box2D.b2CircleShape(radius=0.5),density=1.0, friction=0.1, restitution=0.2),bullet=True,position=spawnpoint, userData=self)
        self.body.angle=spawnrotation
        self.type = "player" #för att vinnas
        self.rope = None

    def hook(self):
        a = self.body.angle
        inp = Box2D.b2RayCastInput(p1=self.body.position, p2=self.body.position+(math.cos(a),math.sin(a)), maxFraction=6)
        out = Box2D.b2RayCastOutput()
        candidates = []
        for block in game.currentLevel.blocks+game.currentLevel.dynamicBlocks:
            if block.type == "nograb":
                continue
            transform = block.body.transform
            hit = block.bodyShape.RayCast(out, inp, transform, 0)
            if hit:
                hit_point = inp.p1 + out.fraction*(inp.p2 - inp.p1)
                dist = math.sqrt((hit_point[0] - inp.p1[0])**2 + (hit_point[1] - inp.p1[1])**2)
                candidates.append((block.body, dist, hit_point))
        if candidates:
            closest = min(candidates, key=lambda x:x[1])
            ourPoint=self.body.position+(math.cos(a)/2,math.sin(a)/2)
            self.rope=world.CreateDistanceJoint(bodyA=self.body, bodyB=closest[0], anchorA=ourPoint,anchorB=closest[2], collideConnected=True, userData=self)
            
    def update(self):
        pressed = pygame.key.get_pressed()
        """
        if pressed[pygame.K_d]:
            self.body.ApplyTorque(-1, wake=True)
        if pressed[pygame.K_a]:
            self.body.ApplyTorque(1, wake=True)
        """
        if pressed[pygame.K_SPACE]:
            if self.rope:
                actualLength = math.sqrt((self.rope.anchorA[0]-self.rope.anchorB[0])**2 + (self.rope.anchorA[1]-self.rope.anchorB[1])**2)
                if actualLength > 0.5:
                    self.rope.length=actualLength-0.08
                    vect = ((self.rope.anchorB[0] - self.rope.anchorA[0])*1, (self.rope.anchorB[1] - self.rope.anchorA[1])*1)
                    self.body.ApplyForce(force=vect, point=self.body.position, wake=True) #jag ändrade forcen till att vara inåt. om du verkligen vill ha utåt kan du ändra tillbaka
                    #print(self.rope.length)
            else:
                self.hook()
                #print("hooked")
        if pressed[pygame.K_e]:
            if self.rope:
                world.DestroyJoint(self.rope)
                self.rope = None
        if pressed[pygame.K_r]:
            game.imminentDeath=True

        if self.rope:
            vect = (self.rope.anchorB[0] - self.rope.anchorA[0], self.rope.anchorB[1] - self.rope.anchorA[1])
            a = self.body.angle
            ourPoint=self.body.position+(math.cos(a)/2,math.sin(a)/2)
            self.body.ApplyForce(force=vect, point=ourPoint, wake=True)

    def draw(self):
        image = rot_center(self.sprite, self.body.angle)
        x=self.body.position[0]
        y=self.body.position[1]
        game_display.blit(image, (int((x-0.5)*ppm), -int((y+0.5)*ppm)))

        if self.rope:
            ropeStart = (int(self.rope.anchorA[0]*ppm), -int(self.rope.anchorA[1]*ppm))
            ropeEnd = (int(self.rope.anchorB[0]*ppm), -int(self.rope.anchorB[1]*ppm))
            pygame.draw.line(game_display, (100,100,100), ropeStart, ropeEnd, 4)
        else:
            a = self.body.angle
            ourPoint = ((self.body.position[0]+math.cos(a)/2)*ppm, -(self.body.position[1]+math.sin(a)/2)*ppm)
            endPoint = ((self.body.position[0]+math.cos(a)*6)*ppm, -(self.body.position[1]+math.sin(a)*6)*ppm)
            pygame.draw.line(game_display, (250,100,100), ourPoint, endPoint, 2)

class myContactListener(Box2D.b2ContactListener):
    def __init__(self):
        Box2D.b2ContactListener.__init__(self)
    def BeginContact(self, contact):
        if(contact.fixtureA.body.userData.type=="death" and contact.fixtureB.body.userData.type=="player"): #Kanske måste checka vilken Fixture som ska användas
            game.imminentDeath=True
        if(contact.fixtureA.body.userData.type=="win" and contact.fixtureB.body.userData.type=="player"):
            game.imminentWin=True
    def EndContact(self, contact):
        pass
    def PreSolve(self, contact, oldManifold):
        pass
    def PostSolve(self, contact, impulse):
        pass

clock = pygame.time.Clock()
game_display = pygame.display.set_mode(resolution)#, pygame.FULLSCREEN)
pygame.display.set_caption('Hall Booker!')

world = Box2D.b2World(contactListener=myContactListener())

game = Game()


jump_out=False
while jump_out == False:

    time_delta = clock.tick(60)
    manager=managers[game.mode]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            jump_out = True
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED or 1:
                print(2)
                
                #buttons
                if event.ui_element in level_buttons:
                    game.mode="p"
                    game.startLevel(level_buttons.index(event.ui_element))
    manager.update(time_delta)

    game.update()

    world.Step(time_step, 20,10)
    world.ClearForces()

    game_display.fill((200,200,250))
    game.draw()
    manager.draw_ui(game_display)

    pygame.display.flip()


pygame.quit()
quit()