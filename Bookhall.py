import pygame
import time
import Box2D
import math

ppm=50
time_step = 1.0/60
resolution = (1200, 675)

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
        for box in boxes:
            self.boxes.append(world.CreateStaticBody(position=box[0],shapes=Box2D.b2PolygonShape(box=box[1])))

        #self.player = Player(spawnpoint, spawnrotation)

    def destroy(self):
        for box in self.boxes:
            world.DestroyBody(box)

    def update(self):
        self.player.update()

    def draw(self):
        for box in self.boxShapes:
            rect = ((box[0][0]-box[1][0])*ppm, -(box[0][1]+box[1][1])*ppm, box[1][0]*2*ppm, box[1][1]*2*ppm)
            pygame.draw.rect(game_display, (200,250,100), rect,0)
        self.player.draw()

class Player():

    sprite = loadImage("Book.png", 0.5)

    def __init__(self, spawnpoint, spawnrotation=90):
        self.x, self.y = spawnpoint
        self.a = spawnrotation
        self.xv = 0
        self.yv = 0
        self.av = 0
        self.body = world.CreateDynamicBody(fixtures=Box2D.b2FixtureDef(shape=Box2D.b2CircleShape(radius=0.5),density=1.0, friction=0.01, restitution=0.2),bullet=True,position=spawnpoint, userData=self)
        self.rope = world.CreateDistanceJoint(bodyA=self.body, bodyB=game.currentLevel.boxes[1], anchorA=(1.3,-3),anchorB=(3.3,-1), collideConnected=True, userData=self)

    def hook(self):
        a = self.body.angle
        inp = Box2D.b2RayCastInput(p1=self.body.position, p2=self.body.position+(math.cos(a),math.sin(a)), maxFraction=50)
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
        if pressed[pygame.K_SPACE]:
            if self.rope:
                self.rope.length-=0.04
                print(self.rope.length)
            else:
                self.hook()
        if pressed[pygame.K_e]:
            if self.rope:
                world.DestroyJoint(self.rope)
                self.rope = None

        if self.rope:
            vect = (self.rope.anchorA[0] - self.rope.anchorB[0], self.rope.anchorA[1] - self.rope.anchorB[1])
            self.body.ApplyForce(force=vect, point=self.body.position, wake=True)

    def draw(self):
        image = rot_center(self.sprite, self.body.angle)
        x=self.body.position[0]
        y=self.body.position[1]
        game_display.blit(image, (int((x-0.5)*ppm), -int((y+0.5)*ppm)))

        if self.rope:
            ropeStart = (int(self.rope.anchorA[0]*ppm), -int(self.rope.anchorA[1]*ppm))
            ropeEnd = (int(self.rope.anchorB[0]*ppm), -int(self.rope.anchorB[1]*ppm))
            pygame.draw.line(game_display, (100,250,200), ropeStart, ropeEnd, 4)
        
pygame.init()
clock = pygame.time.Clock()
game_display = pygame.display.set_mode(resolution)#, pygame.FULLSCREEN)

world = Box2D.b2World()

game = Game()
game.currentLevel = Level((1,-3), 0, [
    [(0,-5.5), (10.1,1)],
    [(0,-1), (10,0.1)],
])
game.currentLevel.player = Player((1,-3), 0)

#groundBody = world.CreateStaticBody(position=(0,-6.1),shapes=Box2D.b2PolygonShape(box=(10.1,1)))
#roofBody = world.CreateStaticBody(position=(0,-1),shapes=Box2D.b2PolygonShape(box=(10,0.1)))
#player = Player((1,-3))

jump_out=False
while jump_out == False:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            jump_out = True

    game.update()

    world.Step(time_step, 10,10)
    world.ClearForces()

    game_display.fill((100,100,100))
    game.draw()

    pygame.display.flip()

    

    clock.tick(60)

pygame.quit()
quit()