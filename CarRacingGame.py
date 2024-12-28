from OpenGL.GL import *
from OpenGL.GLUT import *
import math
import random
import time

window_width = 800
window_height = 600
window = None

MENU = 0
GAME = 1
WIN = 2

current_state = MENU

player1_position = [0, -190]
player1_angle = 0
player1_speed = 2.0
player1_original_speed = player1_speed
player1_debuff = False

player2_position = [0, -220]
player2_angle = 0
player2_speed = 2.0
player2_original_speed = player2_speed
player2_debuff = False

player1_crossing_cooldown = 0
player2_crossing_cooldown = 0

SPEED_BOOST = 1.0
POWER_UP_INTERVAL = 5000
SPEED_BOOST_DURATION = 4
MAX_POWER_UPS = 5

track_outer = [(-390, -250), (390, -250), (390, 250), (-390, 250)]
track_inner = [(-300, -160), (300, -160), (300, 160), (-300, 160)]

power_ups = []
debuffs = []

keys = {}
debuff_duration = 3
power_up_times = {"player1": 0, "player2": 0}
debuff_times = {"player1": 0, "player2": 0}
player1_laps = 0
player2_laps = 0
MAX_LAPS = 3

obstacles = []
OBSTACLE_INTERVAL = 3000
OBSTACLE_LIFETIME = 5000
SPEED_PENALTY = 1.0

TELEPORTATION_COOLDOWN = 8000
teleportation_available = {"player1": True, "player2": True}
teleportation_start_time = {"player1": 0, "player2": 0}



def draw_start_finish_line():
    glColor3f(1, 1, 0)
    draw_line_midpoint(-390, 0, -300, 0)


def draw_line_midpoint(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    glBegin(GL_POINTS)
    while True:
        glVertex2f(x1, y1)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
    glEnd()

def draw_circle_midpoint(xc, yc, radius):
    x = 0
    y = radius
    p = 1 - radius

    glBegin(GL_POINTS)
    while x <= y:
        glVertex2f(xc + x, yc + y)
        glVertex2f(xc - x, yc + y)
        glVertex2f(xc + x, yc - y)
        glVertex2f(xc - x, yc - y)
        glVertex2f(xc + y, yc + x)
        glVertex2f(xc - y, yc + x)
        glVertex2f(xc + y, yc - x)
        glVertex2f(xc - y, yc - x)
        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1
    glEnd()

def draw_car(x, y, angle, color):
    glColor3f(*color)
    points = [(-10, -5), (10, -5), (10, 5), (-10, 5)]
    position = []
    for dx, dy in points:
        position.append((x + dx * math.cos(math.radians(angle)) - dy * math.sin(math.radians(angle)),
                         y + dx * math.sin(math.radians(angle)) + dy * math.cos(math.radians(angle))))
    
    for i in range(len(position)):
        if i == len(position) - 1:
            draw_line_midpoint(int(position[i][0]), int(position[i][1]), int(position[0][0]), int(position[0][1]))
        else:
            draw_line_midpoint(int(position[i][0]), int(position[i][1]), int(position[i + 1][0]), int(position[i + 1][1]))

def draw_power_ups():
    glColor3f(0, 1, 0)
    for x, y, _ in power_ups:
        draw_circle_midpoint(x, y, 5)

def draw_debuffs():
    global debuffs
    glColor3f(1, 1, 1)
    for x, y in debuffs:
        draw_circle_midpoint(x, y, 5)

def draw_obstacles():
    glColor3f(1, 0, 0) 
    for x, y, _ in obstacles:
        draw_circle_midpoint(x, y, 10) 
def draw_menu():
    glColor3f(1, 1, 0) 
    if current_state == MENU:
        glRasterPos2f(-30, 0)
        for char in "START":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    elif current_state == WIN:
        glRasterPos2f(-40, 0)
        for char in "RESTART":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    draw_button(-70, -10, 140, 40)
    glRasterPos2f(-25, -40)
    for char in "EXIT":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    draw_button(-70, -50, 140, 40)
def draw_button(x, y, width, height):
    glColor3f(1, 1, 0)
    draw_line_midpoint(x, y, x + width, y)
    draw_line_midpoint(x + width, y, x + width, y + height) 
    draw_line_midpoint(x + width, y + height, x, y + height) 
    draw_line_midpoint(x, y + height, x, y) 

def draw_winner():
    global current_state 
    glColor3f(1, 1, 0) 
    glRasterPos2f(-60, 70)
    winner_text = "Player 1 Wins!" if player1_laps > MAX_LAPS else "Player 2 Wins!"
    for char in winner_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    draw_menu()
def draw_teleportation_timer(player_name, is_available, start_time):
    if not is_available:
        current_time = time.time()
        remaining_time = TELEPORTATION_COOLDOWN - (current_time - start_time)
        if remaining_time > 0:
            glColor3f(0, 0, 1) 
            position = (50 if player_name == "player1" else -150, 220) 
            glRasterPos2f(position[0], position[1])
            for char in f"{player_name.capitalize()} Teleport: {remaining_time:.1f}s":
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))

def draw_scores():
    glColor3f(1, 1, 1)
    glRasterPos2f(-380, 285)
    for char in f"Player 1 Laps: {player1_laps}/{MAX_LAPS}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    glRasterPos2f(-380, 270)
    for char in f"Player 2 Laps: {player2_laps}/{MAX_LAPS}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))


def convert_coordinate(x, y):
    global window_width, window_height
    a = x - window_width // 2
    b = window_height // 2 - y
    return a, b
