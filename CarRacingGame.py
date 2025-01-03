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

player1_position = [-370, -15]
player1_angle = 270
player1_speed = 2.0
player1_original_speed = player1_speed
player1_debuff = False

player2_position = [-320, -15]
player2_angle = 270
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

TELEPORTATION_COOLDOWN = 15
teleportation_available = {"player1": True, "player2": True}
teleportation_start_time = {"player1": 0, "player2": 0}



def draw_start_finish_line():
    glColor3f(1, 1, 0)
    draw_line_midpoint(-390, 0, -300, 0)

def check_lap_completion():
    global player1_laps, player2_laps
    crossing_threshold = 5
    global player1_crossing_cooldown, player2_crossing_cooldown

    current_time = time.time()
    cooldown_duration = 5

    if -400 <= player1_position[0] <= -300 and -crossing_threshold <= player1_position[1] <= crossing_threshold:
        if current_time - player1_crossing_cooldown > cooldown_duration:
            print(f"Player 1 completed lap {player1_laps}")
            player1_laps += 1
            player1_crossing_cooldown = current_time
            

    if -400 <= player2_position[0] <= -300 and -crossing_threshold <= player2_position[1] <= crossing_threshold:
        if current_time - player2_crossing_cooldown > cooldown_duration:
            print(f"Player 2 completed lap {player2_laps}")
            player2_laps += 1
            player2_crossing_cooldown = current_time
            

    if player1_laps > MAX_LAPS:
        return "Player 1 Wins!"
    elif player2_laps > MAX_LAPS:
        return "Player 2 Wins!"
    return None

def plotting(x, y):

    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def move_to_0(x, y, zone):
    zone_map = {0: (x, y),1: (y, x),2: (y, -x),3: (-x, y),4: (-x, -y),5: (-y, -x),6: (-y, x),7: (x, -y)}
    return zone_map[zone]


def move_from_0(x, y, zone):
    zone_map = {0: (x, y),1: (y, x),2: (-y, x),3: (-x, y),4: (-x, -y),5: (-y, -x),6: (y, -x),7: (x, -y)
}
    return zone_map[zone]


def draw_line_midpoint(x0, y0, x1, y1):
    dx= x1 - x0
    dy= y1 - y0
    zone = 0
    if abs(dx) > abs(dy):
        if dx>=0 and dy>=0:
            zone= 0
        elif dx<0 and dy>=0:
            zone= 3
        elif dx< 0 and dy < 0:
            zone= 4
        elif dx>= 0 and dy < 0:
            zone= 7
    else:
        if dx>=0 and dy>= 0:
            zone=1
        elif dx<0 and dy>= 0:
            zone= 2
        elif dx<0 and dy< 0:
            zone = 5
        elif dx>= 0 and dy< 0:
            zone= 6

    x0, y0 = move_to_0(x0, y0, zone)
    x1, y1 = move_to_0(x1, y1, zone)
    dx = x1 - x0
    dy = y1 - y0
    d = 2 * dy - dx
    incrE = 2 * dy
    incrNE = 2 * (dy - dx)
    x, y = x0, y0
    x3, y3 = move_from_0(x, y, zone)
    plotting(x3, y3)
    while x < x1:
        if d <= 0:
            d += incrE
            x += 1
        else:
            d += incrNE
            x += 1
            y += 1
        x3, y3 = move_from_0(x, y, zone)
        plotting(x3, y3)

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

def is_within_boundaries(position):
    x, y = position
    outer_bound = (-390 <= x <= 390) and (-250 <= y <= 250)
    inner_bound = (-300 <= x <= 300) and (-160 <= y <= 160)
    return outer_bound and not inner_bound

def check_collision(pos1, pos2):
    distance = math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return distance < 20

def generate_power_up(value):
    if len(power_ups) < MAX_POWER_UPS:
        x = random.randint(-390, 390)
        y = random.randint(-250, 250)
        while not is_within_boundaries([x, y]):
            x = random.randint(-390, 390)
            y = random.randint(-250, 250)
        power_ups.append((x, y, time.time()))
    glutTimerFunc(POWER_UP_INTERVAL, generate_power_up, 0)

def draw_power_ups():
    glColor3f(0, 1, 0)
    for x, y, _ in power_ups:
        draw_circle_midpoint(x, y, 5)

def check_power_up_collection(player_position, player_name):
    for (x, y, spawn_time) in power_ups:
        distance = math.sqrt((player_position[0] - x) ** 2 + (player_position[1] - y) ** 2)
        if distance < 10:
            power_ups.remove((x, y, spawn_time))
            power_up_times[player_name] = time.time()
            return True
    return False
def draw_debuffs():
    global debuffs
    glColor3f(1, 1, 1)
    for x, y, _ in debuffs:
        draw_circle_midpoint(x, y, 5)
def spawn_debuff(car_position, player_name):
    global debuffs
    debuffs.append((car_position[0] + random.randint(-20, 20), car_position[1] + random.randint(-20, 20), player_name))

def check_debuff(player_position, player_name):
    global debuff_times, player1_speed, player2_speed, debuffs
    current_time = time.time()
    

    for (x, y, creator) in debuffs:
        distance = math.sqrt((player_position[0] - x) ** 2 + (player_position[1] - y) ** 2)
        if distance < 10 and creator != player_name:
            debuffs.remove((x, y, creator))
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
def generate_obstacle(value):
    if len(obstacles) < 10:
        x = random.randint(-390, 390)
        y = random.randint(-250, 250)
        while not is_within_boundaries([x, y]):
            x = random.randint(-390, 390)
            y = random.randint(-250, 250)
        obstacles.append((x, y, time.time())) 
    glutTimerFunc(OBSTACLE_INTERVAL, generate_obstacle, 0)

def draw_obstacles():
    glColor3f(1, 0, 0) 
    for x, y, _ in obstacles:
        draw_circle_midpoint(x, y, 10) 

def check_obstacle_collisions(player_position):
    for (x, y, _) in obstacles:
        distance = math.sqrt((player_position[0] - x) ** 2 + (player_position[1] - y) ** 2)
        if distance < 20: 
            return True
    return False

def teleport_player(player_name):
    global player1_position, player2_position
    if player_name == "player1":
        if teleportation_available["player1"]:
            x = random.randint(-390, 390)
            y = random.randint(-250, 250)
            while not is_within_boundaries([x, y]):
                x = random.randint(-390, 390)
                y = random.randint(-250, 250)
            player1_position = [x, y]
            teleportation_available["player1"] = False
            teleportation_start_time["player1"] = time.time()
    else:
        if teleportation_available["player2"]:
            x = random.randint(-390, 390)
            y = random.randint(-250, 250)
            while not is_within_boundaries([x, y]):
                x = random.randint(-390, 390)
                y = random.randint(-250, 250)
            player2_position = [x, y]
            teleportation_available["player2"] = False
            teleportation_start_time["player2"] = time.time()


def update_player():
    global player1_position, player1_angle, player1_speed, player1_laps
    global player2_position, player2_angle, player2_speed, player2_laps
    global player1_original_speed, player2_original_speed, current_state, player1_debuff, player2_debuff
    current_time = time.time()
    if current_state == GAME:
        original_position1 = player1_position[:]
        original_position2 = player2_position[:]


        if keys.get(b'w', False):
            player1_position[0] += player1_speed * math.cos(math.radians(player1_angle))
            player1_position[1] += player1_speed * math.sin(math.radians(player1_angle))
        if keys.get(b's', False):
            player1_position[0] -= player1_speed * math.cos(math.radians(player1_angle))
            player1_position[1] -= player1_speed * math.sin(math.radians(player1_angle))
        if keys.get(b'a', False):
            player1_angle += 5
        if keys.get(b'd', False):
            player1_angle -= 5
        if keys.get(b't'): 
            teleport_player("player1")
        if keys.get(b'f', False) and not player1_debuff:
            spawn_debuff(player1_position, "player1")
            player1_debuff = True
        elif not keys.get(b'f', False):
            player1_debuff = False
        if keys.get(b'\x1b', False):
            current_state = MENU
            return

        if keys.get(GLUT_KEY_UP):
            player2_position[0] += player2_speed * math.cos(math.radians(player2_angle))
            player2_position[1] += player2_speed * math.sin(math.radians(player2_angle))
        if keys.get(GLUT_KEY_DOWN):
            player2_position[0] -= player2_speed * math.cos(math.radians(player2_angle))
            player2_position[1] -= player2_speed * math.sin(math.radians(player2_angle))
        if keys.get(GLUT_KEY_LEFT):
            player2_angle += 5
        if keys.get(GLUT_KEY_RIGHT):
            player2_angle -= 5
        if keys.get(b'n', False) and not player2_debuff:
            spawn_debuff(player2_position, "player2")
            player2_debuff = True
        elif not keys.get(b'n', False):
            player2_debuff = False
        if keys.get(b'm'): 
            teleport_player("player2")

        
        for player_name in ["player1", "player2"]:
            if not teleportation_available[player_name] and current_time - teleportation_start_time[player_name] >= TELEPORTATION_COOLDOWN:
                teleportation_available[player_name] = True

        if check_obstacle_collisions(player1_position):
            player1_speed = max(0, player1_speed - SPEED_PENALTY)
            player1_position = original_position1[:] 
        if check_obstacle_collisions(player2_position):
            player2_speed = max(0, player2_speed - SPEED_PENALTY) 
            player2_position = original_position2[:] 

        if not is_within_boundaries(player1_position):
            player1_position = original_position1[:]
        if not is_within_boundaries(player2_position):
            player2_position = original_position2[:]

        if check_collision(player1_position, player2_position):
            player1_position = original_position1[:]
            player2_position = original_position2[:]

        if check_power_up_collection(player1_position, "player1"):
            player1_speed = player1_original_speed + SPEED_BOOST
        if check_power_up_collection(player2_position, "player2"):
            player2_speed = player2_original_speed + SPEED_BOOST
        if check_debuff(player1_position, "player1"):
            player1_speed = player1_original_speed / 2 
            debuff_times["player1"] = current_time

        if check_debuff(player2_position, "player2"):
            player2_speed = player2_original_speed / 2 
            debuff_times["player2"] = current_time 
        if current_time - power_up_times["player1"] >= SPEED_BOOST_DURATION and current_time - debuff_times["player1"] >= debuff_duration:
            player1_speed = player1_original_speed
        if current_time - power_up_times["player2"] >= SPEED_BOOST_DURATION and current_time - debuff_times["player2"] >= debuff_duration:
            player2_speed = player2_original_speed



        winner = check_lap_completion()
        if winner:
            current_state = WIN
            print(winner)

def display():
    global current_state
    glClear(GL_COLOR_BUFFER_BIT)
    if current_state == MENU:
        draw_menu()
    elif current_state == GAME:
        generate_track()
        draw_start_finish_line()
        draw_car(player1_position[0], player1_position[1], player1_angle, (1, 0, 0))
        draw_car(player2_position[0], player2_position[1], player2_angle, (0.55, 0.8, 0.95))
        draw_power_ups()
        draw_obstacles() 
        draw_scores()
        draw_debuffs()
        if not teleportation_available["player1"]:
            draw_teleportation_timer("player1", teleportation_available["player1"], teleportation_start_time["player1"])
        if not teleportation_available["player2"]:
            draw_teleportation_timer("player2", teleportation_available["player2"], teleportation_start_time["player2"])
    elif current_state == WIN:
        draw_winner()

    glutSwapBuffers()

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
            position = (50 if player_name == "player1" else -200, 220) 
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
def mouse_button(button, state, x, y):
    global current_state 
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:

        if current_state == MENU or current_state == WIN:
            
            x, y = convert_coordinate(x, y)

            if -70 < x < 70 and -10 < y < 30: 
                current_state = GAME
                print("Game Started")
                reset_game()
            elif -70 < x < 70 and -50 < y < -10:
                print("Game Exited")
                glutDestroyWindow(window)

def reset_game():
    global player1_position, player1_angle, player1_speed, player1_laps
    global player2_position, player2_angle, player2_speed, player2_laps, teleportation_available, teleportation_start_time
    player1_position = [-370, -15]
    player1_angle = 270
    player1_speed = player1_original_speed
    player1_laps = 1

    player2_position = [-320, -15]
    player2_angle = 270
    player2_speed = player2_original_speed
    player2_laps = 1

    power_ups.clear()
    power_up_times["player1"] = 0
    power_up_times["player2"] = 0

    debuffs.clear()
    debuff_times["player1"] = 0
    debuff_times["player2"] = 0

    obstacles.clear()
    teleportation_available = {"player1": True, "player2": True}
    teleportation_start_time = {"player1": 0, "player2": 0}

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

