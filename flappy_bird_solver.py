import pygame
import neat
import time
import os
import random
pygame.font.init()

# constants
WIN_WIDTH = 500
WIN_HEIGHT = 800
# current bird generation
GEN = 0
# flappy bird GUI assets
# all three frames of bird flapping scaled and added to an array
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird3.png")))]
# pipe, base/floor, and background images
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "base.png")))
BG_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bg.png")))
# pygame font
STAT_FONT = pygame.font.SysFont("Calibri", 40, True)

# Bird object to control the velocity and rotation of the birds
class Bird:
    IMAGES = BIRD_IMAGES
    # for bird movement
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        # bird variables
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.image_count = 0
        self.image = self.IMAGES[0]

    def jump(self):
        # 0,0 in pygame is top left of screen, negative value = upwards movement
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        # calculating how many pixels to move, starts negative (upwards) and then
        # becomes positive (downwards) simulating a jump
        displacement = self.vel*self.tick_count + 1.5*self.tick_count**2
        # capping speed
        if displacement >= 16:
            displacement = 16
        if displacement < 0:
            displacement -= 2
        # adjusting y(bird height) based on pixel displacement value calculated 
        self.y = self.y + displacement
        # checking if we are still moving up to rotate bird upwards, else rotate down
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
      
    def draw(self, win):
        self.image_count += 1
        # checking what image to show for bird animation based on count
        # goes through all three flapping images then reverses
        if self.image_count < self.ANIMATION_TIME:
            self.image = self.IMAGES[0]
        elif self.image_count < self.ANIMATION_TIME*2:
            self.image = self.IMAGES[1]
        elif self.image_count < self.ANIMATION_TIME*3:
            self.image = self.IMAGES[2]
        elif self.image_count < self.ANIMATION_TIME*4:
            self.image = self.IMAGES[1]
        elif self.image_count == self.ANIMATION_TIME*4 + 1:
            self.image = self.IMAGES[0]
            self.image_count = 0

        if self.tilt <= -80:
            self.image = self.IMAGES[1]
            self.image_count = self.ANIMATION_TIME*2
        # rotating image around its center
        rotated_image = pygame.transform.rotate(self.image, self.tilt)
        new_rect = rotated_image.get_rect(center=self.image.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    # the collision area for the bird object
    def get_mask(self):
        return pygame.mask.from_surface(self.image)

# Pipe object that draws top and bottom pipes and checks collision with birds
class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        # storing both pipe images, one flipped to represent top screen pipe
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE
        # collision check for if a bird has passed a pipe
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # moving the pipes (since bird is static to simulate a moving screen)
    def move(self):
        self.x -= self.VEL

    # drawing each pipe
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        # offset from bird to top/bottom mask of pipe (distance between corners of bird and pipes)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        # checking for collision
        # finding point of overlap between bird mask and bottom/top pipe
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        # check if points exist, therefore colliding
        if t_point or b_point:
            return True
        return False

# the floor/ground of the game, uses two images cycling to represent movement
class Base:
    VEL = 5
    WIDTH = BASE_IMAGE.get_width()
    IMG = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        # two different x values to represent two different floor/ground images
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        # if first floor image moves completely off screen, cycle it back behind second
        # first floor image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        # second floor image
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        # drawing two copies of the floor for cycling
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

# creates the background window, draws birds, draws pipes, draws tracking, and updates display
def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMAGE, (0,0))
    for pipe in pipes:
        pipe.draw(win)
    # scoreboard on screen
    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    # display current generation on screen
    text = STAT_FONT.render("Gen: " + str(gen), 1, (255,255,255))
    win.blit(text, (10, 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()

# fitness function that controls multiple birds at the same time and determines fitness
def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []
    # setup neural network for genome with a bird object
    for _, g in genomes:
        # create a network with the genome and config settings, then add data to lists at matching index
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)
  
    # creating the screen objects
    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # moving the objects based on neural network
        pipe_ind = 0
        if len(birds) > 0:
            # check if the bird has passed the first pipe and edit index to next pipe if true
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            # if no birds left in current generation, quit game
            run = False
            break

        # increase fitness for successfully moving forward for each bird alive
        for x, bird in enumerate(birds):
            bird.move()            
            ge[x].fitness += 0.1
            # optain output value (0.0-1.0) by feeding the neural network the bird position and distances between the top and bottom pipes. Bird jumps if value > 0.5.
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        removed_pipes = []
        add_pipe = False
        # loop through all pipes and check if any bird is currently colliding with one
        for pipe in pipes:            
            for x, bird in enumerate(birds):                
                if pipe.collide(bird):
                    # remove 1 fitness point if a bird hits a pipe and remove its data from lists
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)                                
                # generate a new pipe is the bird successfully passes the pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            # check x position of pipe and add to removed list if its off screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                removed_pipes.append(pipe)                
            pipe.move()

        # increment score and add a new pipe if needed
        if add_pipe:
            # reward birds with 5 fitness points if they successfully pass a pipe
            for g in ge:
                g.fitness += 5
            score += 1
            pipes.append(Pipe(600))
        # remove the passed pipes from list
        for r in removed_pipes:
            pipes.remove(r)
        # check if any bird hits the floor/roof and remove it 
        for x, bird in enumerate(birds):
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        # drawing the objects on the screen
        draw_window(win, birds, pipes, base, score, GEN)

# neat setup configuration
def run(config_path):
    # load all neat config file settings
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    # create population
    p = neat.Population(config)
    # stats reporters to give statistics of neat while it runs
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # call main function 50 times per generation since main is the fitness function to determine bird fitness
    winner = p.run(main, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
