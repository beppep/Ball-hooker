import pygame
import time
import Box2D
import math
import random

ppm=75
time_step = 1.0/60
resolution = (1200, 675)

levels = [ #shape means radius btw
[(1,-3), 0, [ #level 1
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(3,-6), (2, 2)],
]],
[(1,-3), 0, [ #level 2
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(3,-7), (3, 2)],
    [(7,-6.5), (1, 3)],
]],
[(1,-3), 0, [ #level
    [(8,-9), (8, 1)],
    [(8,0), (8, 1)],
    [(0,-4.5), (1, 4.5)],
    [(16,-4.5), (1, 4.5)],
    [(8,-9), (4, 1), "death"],
]],
[(2,-resolution[1]/ppm+3), math.pi/4, [ #level noel
    [(0,0), (resolution[0]/ppm,1)],
    [(0,0), (1,resolution[1]/ppm)],
    [(resolution[0]/ppm/2,0), (0.5,resolution[1]/ppm/2-1),"death"],
    [(resolution[0]/ppm/2,-resolution[1]/ppm*3/4-1), (0.5,resolution[1]/ppm/4-0.2),"death"],
    [(0,-resolution[1]/ppm), (resolution[0]/ppm,1)],
    [(resolution[0]/ppm,0), (1,resolution[1]/ppm)],
]],
]

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
        self.currentLevel = None
        self.imminentDeath = False

    def destroyPlayer(self):
        if(self.imminentDeath):
            self.currentLevel.killPlayer()
            self.currentLevel.spawnPlayer()
            self.imminentDeath=False

    def update(self):
        self.currentLevel.update()

    def draw(self):
        self.currentLevel.draw()

class Level():

    def __init__(self, spawnpoint, spawnrotation, boxes):
        self.spawnpoint = spawnpoint
        self.spawnrotation = spawnrotation
        self.boxShapes = boxes
        self.boxes = []
        self.player = None
        for box in boxes:
            body = world.CreateStaticBody(position=box[0],shapes=Box2D.b2PolygonShape(box=box[1]))
            if(len(box)>2):
                body.userData = box[2]
            self.boxes.append(body)

        #self.player = Player(spawnpoint, spawnrotation)

    def killPlayer(self):
        world.DestroyBody(self.player.body)
        self.player = None

    def spawnPlayer(self):
        self.player = Player(self.spawnpoint, self.spawnrotation)

    def destroy(self):
        for box in self.boxes:
            world.DestroyBody(box)

    def update(self):
        self.player.update()

    def draw(self):
        for i in range(len(self.boxShapes)):
            box=self.boxShapes[i]
            body=self.boxes[i]
            rect = ((box[0][0]-box[1][0])*ppm, -(box[0][1]+box[1][1])*ppm, box[1][0]*2*ppm, box[1][1]*2*ppm)
            if(body.userData=="death"):
                pygame.draw.rect(game_display, (250,50,50), rect,0)
            else:
                pygame.draw.rect(game_display, (200,250,100), rect,0)
        self.player.draw()

class Player():

    sprite = loadImage("Book.png", 0.5)

    def __init__(self, spawnpoint, spawnrotation=math.pi/4):
        self.body = world.CreateDynamicBody(fixtures=Box2D.b2FixtureDef(shape=Box2D.b2CircleShape(radius=0.5),density=1.0, friction=0.1, restitution=0.2),bullet=True,position=spawnpoint, userData=self)
        self.body.angle=spawnrotation
        self.rope = None #world.CreateDistanceJoint(bodyA=self.body, bodyB=game.currentLevel.boxes[1], anchorA=(1.3,-3),anchorB=(3.3,-1), collideConnected=True, userData=self)

    def hook(self):
        a = self.body.angle
        inp = Box2D.b2RayCastInput(p1=self.body.position, p2=self.body.position+(math.cos(a),math.sin(a)), maxFraction=5)
        out = Box2D.b2RayCastOutput()
        dists = []
        for i in range(len(game.currentLevel.boxShapes)):
            box = game.currentLevel.boxShapes[i]
            transform = game.currentLevel.boxes[i].transform
            shape = Box2D.b2PolygonShape(box=box[1])
            hit = shape.RayCast(out, inp, transform, 0)
            if hit:
                hit_point = inp.p1 + out.fraction*(inp.p2 - inp.p1)
                dist = math.sqrt((hit_point[0] - inp.p1[0])**2 + (hit_point[1] - inp.p1[1])**2)
                dists.append((i,dist,hit_point))
        if dists:
            dist = min(dists, key=lambda x:x[1])
            ourPoint=self.body.position+(math.cos(a)/2,math.sin(a)/2)
            self.rope=world.CreateDistanceJoint(bodyA=self.body, bodyB=game.currentLevel.boxes[dist[0]], anchorA=ourPoint,anchorB=dist[2], collideConnected=True, userData=self)
            
    def update(self):
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_d]:
            self.body.ApplyTorque(-1, wake=True)
        if pressed[pygame.K_a]:
            self.body.ApplyTorque(1, wake=True)

        if pressed[pygame.K_SPACE]:
            if self.rope:
                actualLength = math.sqrt((self.rope.anchorA[0]-self.rope.anchorB[0])**2 + (self.rope.anchorA[1]-self.rope.anchorB[1])**2)
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
            pygame.draw.line(game_display, (100,250,200), ropeStart, ropeEnd, 4)
        else:
            a = self.body.angle
            ourPoint = ((self.body.position[0]+math.cos(a)/2)*ppm, -(self.body.position[1]+math.sin(a)/2)*ppm)
            endPoint = ((self.body.position[0]+math.cos(a)*5)*ppm, -(self.body.position[1]+math.sin(a)*5)*ppm)
            pygame.draw.line(game_display, (250,10,100), ourPoint, endPoint, 2)

class myContactListener(Box2D.b2ContactListener):
    def __init__(self):
        Box2D.b2ContactListener.__init__(self)
    def BeginContact(self, contact):
        if(contact.fixtureA.body.userData=="death"): #Kanske måste checka vilken Fixture som ska användas
            game.imminentDeath=True
    def EndContact(self, contact):
        pass
    def PreSolve(self, contact, oldManifold):
        pass
    def PostSolve(self, contact, impulse):
        pass

pygame.init()
clock = pygame.time.Clock()
game_display = pygame.display.set_mode(resolution)#, pygame.FULLSCREEN)

world = Box2D.b2World(contactListener=myContactListener())

game = Game()

game.currentLevel = Level(*random.choice(levels))
#game.currentLevel = Level((1,-3), 0, [[(random.random()*22,-random.random()*13), (random.random()*2,random.random()*2)] for i in range(12)])
game.currentLevel.spawnPlayer()

jump_out=False
while jump_out == False:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            jump_out = True

    game.update()

    world.Step(time_step, 20,10)
    world.ClearForces()

    game_display.fill((100,100,100))
    game.draw()

    pygame.display.flip()

    game.destroyPlayer()

    clock.tick(60)

pygame.quit()
quit()