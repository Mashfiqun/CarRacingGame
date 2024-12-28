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

def generate_track():
    glColor3f(1, 1, 1)
    for i in range(len(track_outer)):
        x1, y1 = track_outer[i]
        x2, y2 = track_outer[(i + 1) % len(track_outer)]
        draw_line_midpoint(x1, y1, x2, y2)

    for i in range(len(track_inner)):
        x1, y1 = track_inner[i]
        x2, y2 = track_inner[(i + 1) % len(track_inner)]
        draw_line_midpoint(x1, y1, x2, y2)

def is_within_boundaries(position):
    x, y = position
    outer_bound = (-390 <= x <= 390) and (-250 <= y <= 250)
    inner_bound = (-300 <= x <= 300) and (-160 <= y <= 160)
    return outer_bound and not inner_bound

def spawn_debuff(car_position):
    global debuffs
    debuffs.append((car_position[0] + random.randint(-20, 20), car_position[1] + random.randint(-20, 20)))

def check_debuff(player_position, player_name):
    global debuff_times, player1_speed, player2_speed, debuffs
    current_time = time.time()
    

    for (x, y) in debuffs:
        distance = math.sqrt((player_position[0] - x) ** 2 + (player_position[1] - y) ** 2)
        if distance < 10:
            debuffs.remove((x, y))
            debuff_times[player_name] = current_time
            if player_name == "player1":
                player1_speed = player1_original_speed / 2 
            else:
                player2_speed = player2_original_speed / 2  
            return True
    return False

def keyboardListener(key, x, y):
    global player1_position, player1_angle, player1_speed, player1_laps
    global player2_position, player2_angle, player2_speed, player2_laps
    global player1_original_speed, player2_original_speed, current_state
    if key == b'w':
        player1_position[0] += player1_speed * math.cos(math.radians(player1_angle))
        player1_position[1] += player1_speed * math.sin(math.radians(player1_angle))
    if key == b's':
        player1_position[0] -= player1_speed * math.cos(math.radians(player1_angle))
        player1_position[1] -= player1_speed * math.sin(math.radians(player1_angle))
    if key == b'a':
        player1_angle += 5
    if key == b'd':
        player1_angle -= 5
    if key == b'\x1b':
        current_state = MENU
        return
    
def specialKeyListener(key, x, y):
    global player1_position, player1_angle, player1_speed, player1_laps
    global player2_position, player2_angle, player2_speed, player2_laps
    global player1_original_speed, player2_original_speed, current_state
    if key == GLUT_KEY_UP:
        player2_position[0] += player2_speed * math.cos(math.radians(player2_angle))
        player2_position[1] += player2_speed * math.sin(math.radians(player2_angle))
    if key == GLUT_KEY_DOWN:
        player2_position[0] -= player2_speed * math.cos(math.radians(player2_angle))
        player2_position[1] -= player2_speed * math.sin(math.radians(player2_angle))
    if key == GLUT_KEY_LEFT:
        player2_angle += 5
    if key == GLUT_KEY_RIGHT:
        player2_angle -= 5

def check_collision(pos1, pos2):
    distance = math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return distance < 20

def check_lap_completion():
    global player1_laps, player2_laps
    crossing_threshold = 5
    global player1_crossing_cooldown, player2_crossing_cooldown

    current_time = time.time()
    cooldown_duration = 5

    if -400 <= player1_position[0] <= -300 and -crossing_threshold <= player1_position[1] <= crossing_threshold:
        if current_time - player1_crossing_cooldown > cooldown_duration:
            player1_laps += 1
            player1_crossing_cooldown = current_time
            print(f"Player 1 completed lap {player1_laps}")

    if -400 <= player2_position[0] <= -300 and -crossing_threshold <= player2_position[1] <= crossing_threshold:
        if current_time - player2_crossing_cooldown > cooldown_duration:
            player2_laps += 1
            player2_crossing_cooldown = current_time
            print(f"Player 2 completed lap {player2_laps}")

    if player1_laps > MAX_LAPS:
        return "Player 1 Wins!"
    elif player2_laps > MAX_LAPS:
        return "Player 2 Wins!"
    return None

def mouse_button(button, state, x, y):
    global current_state 
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:

        if current_state == MENU or current_state == WIN:
            
            x, y = convert_coordinate(x, y)
            print(x, y)
            if -70 < x < 70 and -10 < y < 30: 
                current_state = GAME
                print("Game Started")
                reset_game()
            elif -70 < x < 70 and -50 < y < -10:
                print("Game Exited")
                glutDestroyWindow(window)

def display():
    global current_state
    glClear(GL_COLOR_BUFFER_BIT)
    if current_state == MENU:
        draw_menu()
    elif current_state == GAME:
        generate_track()
        draw_start_finish_line()
        draw_car(player1_position[0], player1_position[1], player1_angle, (1, 0, 0))
        draw_car(player2_position[0], player2_position[1], player2_angle, (0, 0, 1))
        draw_power_ups()
        draw_obstacles() 
        draw_scores()
        draw_debuffs()
        draw_teleportation_timer("player1", teleportation_available["player1"], teleportation_start_time["player1"])
        draw_teleportation_timer("player2", teleportation_available["player2"], teleportation_start_time["player2"])
    elif current_state == WIN:
        draw_winner()

    glutSwapBuffers()

def keyboard(key, x, y):
    keys[key] = True

def keyboard_up(key, x, y):
    keys[key] = False

def special_keys(key, x, y):
    keys[key] = True

def special_keys_up(key, x, y):
    keys[key] = False

def idle():
    update_player()
    glutPostRedisplay()

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(window_width, window_height)
window = glutCreateWindow(b'Car Racing Game')

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(-400, 400, -300, 300, -1, 1)

glutDisplayFunc(display)
glutIdleFunc(idle)
glutKeyboardFunc(keyboard)
glutKeyboardUpFunc(keyboard_up)
glutSpecialFunc(special_keys)
glutSpecialUpFunc(special_keys_up)
glutMouseFunc(mouse_button)

glutTimerFunc(POWER_UP_INTERVAL, generate_power_up, 0)
glutTimerFunc(OBSTACLE_INTERVAL, generate_obstacle, 0)

glutMainLoop()