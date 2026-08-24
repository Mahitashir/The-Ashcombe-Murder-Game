# ============================================================
#  CSE423_project2.py
#  CSE423 - Computer Graphics Project
#  Rooms of the locked-room mystery house:
#    Room 1 - The Study
#    Room 2 - The Hallway (shared temperature control panel)
#    Room 3 - The Parlor
#    Room 4 - The Dining Room
#    Room 5 - Toby's Bedroom
# ============================================================

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

# ================= WINDOW / WORLD SETTINGS =================
WINDOW_W = 1000
WINDOW_H = 800
WINDOW_TITLE = b"CSE423 Project - Ashcombe House"

FOV_Y = 60
Z_NEAR = 0.1
Z_FAR = 3000

# ================= ROOM DIMENSIONS: THE STUDY =================
ROOM_HALF_X = 400      # room spans X: -400 .. 400
ROOM_HALF_Z = 250      # room spans Z: -250 .. 250
WALL_HEIGHT = 90
WALL_THICK = 10

DOOR_CENTER_X = -25    # gap on south wall (Z = +ROOM_HALF_Z)
DOOR_WIDTH = 80
WINDOW_CENTER_Z = -100  # gap on east wall (X = +ROOM_HALF_X)
WINDOW_WIDTH = 100

WALL_COLOR = (0.86, 0.83, 0.76)
BASEBOARD_COLOR = (0.32, 0.22, 0.13)
TRIM_COLOR = (0.42, 0.28, 0.15)

# ================= ROOM DIMENSIONS: THE HALLWAY =================
HALL_HALF_X = 380       # hallway spans X: -380 .. 380 (its long axis)
HALL_HALF_Z = 70        # hallway spans Z: -70 .. 70 (narrow width)

# ================= ROOM DIMENSIONS: THE PARLOR =================
PARLOR_HALF_X = 380     # room spans X: -380 .. 380
PARLOR_HALF_Z = 300     # room spans Z: -300 .. 300

# ================= ROOM DIMENSIONS: THE DINING ROOM =================
DINING_HALF_X = 340     # room spans X: -340 .. 340
DINING_HALF_Z = 260     # room spans Z: -260 .. 260

# ================= ROOM DIMENSIONS: TOBY'S BEDROOM =================
BEDROOM_HALF_X = 280    # room spans X: -280 .. 280
BEDROOM_HALF_Z = 220    # room spans Z: -220 .. 220

# ================= ROOMS / CAMERA TARGETS =================
ROOM_STUDY = 1
ROOM_HALLWAY = 2
ROOM_PARLOR = 3
ROOM_DINING = 4
ROOM_BEDROOM = 5
current_room = ROOM_STUDY

ROOM_CAMERA_DEFAULTS = {
    ROOM_STUDY:   {'azimuth': 45.0, 'elevation': 50.0, 'distance': 650.0, 'target': (0.0, 50.0, 0.0)},
    ROOM_HALLWAY: {'azimuth': 15.0, 'elevation': 32.0, 'distance': 950.0, 'target': (0.0, 45.0, 0.0)},
    ROOM_PARLOR:  {'azimuth': 25.0, 'elevation': 42.0, 'distance': 800.0, 'target': (0.0, 55.0, -110.0)},
    ROOM_DINING:  {'azimuth': 35.0, 'elevation': 45.0, 'distance': 750.0, 'target': (0.0, 50.0, 0.0)},
    ROOM_BEDROOM: {'azimuth': 30.0, 'elevation': 42.0, 'distance': 620.0, 'target': (0.0, 45.0, -40.0)},
}

# ================= ORBIT CAMERA (arrow-key navigation) =================
camera_azimuth = ROOM_CAMERA_DEFAULTS[ROOM_STUDY]['azimuth']
camera_elevation = ROOM_CAMERA_DEFAULTS[ROOM_STUDY]['elevation']
camera_distance = ROOM_CAMERA_DEFAULTS[ROOM_STUDY]['distance']
camera_target = ROOM_CAMERA_DEFAULTS[ROOM_STUDY]['target']

AZIMUTH_STEP = 4.0
ELEVATION_STEP = 3.0
ZOOM_STEP = 30.0
ELEVATION_MIN, ELEVATION_MAX = 8.0, 87.0
DISTANCE_MIN, DISTANCE_MAX = 250.0, 1300.0

# Right mouse button toggles this, same as bullet_frenzy.py's first_person
# flag - when it's on, setup_camera() looks out from the detective's own
# eyes along player_angle instead of orbiting the room.
first_person = False
FIRST_PERSON_EYE_HEIGHT = 65.0
FIRST_PERSON_EYE_FORWARD = 15.0
FIRST_PERSON_LOOK_AHEAD = 100.0

# In first person, Left/Right on the arrow keys turn the detective exactly
# like A/D do (there's no separate "look yaw" - a decoupled look that still
# visibly sweeps the whole view reads as turning regardless of what the
# underlying variable is called, so heading is just heading). Up/Down pitch
# the view independently of that, and *that's* what a clue's "look at it"
# check actually cares about: whether you're tilted toward the clue's real
# height, not just standing near it - e.g. a letter down in a wastebasket
# needs you looking down, not just facing its general direction.
look_pitch = 0.0
LOOK_PITCH_STEP = 4.0
LOOK_PITCH_MIN, LOOK_PITCH_MAX = -45.0, 60.0

# A clue is only interactable in first person if the camera's actual 3D view
# direction (yaw AND pitch together, exactly what setup_camera() renders) is
# aimed within this cone of the clue's real position - checking yaw and
# pitch as two separate, independently-toleranced angles let mismatches
# between them sneak a clue through (or, for one sitting close by like the
# desk teacup, made the two checks fight each other into an unsatisfiable
# combination). One real 3D angle-between-vectors check avoids both.
LOOK_CONE_DEG = 22.0
FP_CLUE_RADIUS = 65.0     # slightly more forgiving than INTERACT_RADIUS, to offset needing to aim

# ================= PLAYABLE DETECTIVE =================
ROOM_HALF_DIMS = {
    ROOM_STUDY:   (ROOM_HALF_X, ROOM_HALF_Z),
    ROOM_HALLWAY: (HALL_HALF_X, HALL_HALF_Z),
    ROOM_PARLOR:  (PARLOR_HALF_X, PARLOR_HALF_Z),
    ROOM_DINING:  (DINING_HALF_X, DINING_HALF_Z),
    ROOM_BEDROOM: (BEDROOM_HALF_X, BEDROOM_HALF_Z),
}

# A generic (x, z, angle) fast-travel spawn per room, used by the 1-5 keys -
# picked to sit clear of that room's furniture (the plain (0, 0) used to sit
# inside the Study's desk and the Dining Room's table once collision existed).
ROOM_SPAWN = {
    ROOM_STUDY: (200.0, 180.0, 0.0),
    ROOM_HALLWAY: (0.0, 0.0, 180.0),
    ROOM_PARLOR: (0.0, 0.0, 180.0),
    ROOM_DINING: (0.0, 180.0, 180.0),
    ROOM_BEDROOM: (0.0, 0.0, 180.0),
}

PLAYER_SPEED = 1.2        # world units per frame, applied continuously while a key is held (third person)
PLAYER_MARGIN = 35.0
PLAYER_RADIUS = 15.0
NPC_RADIUS = 18.0
WALK_CYCLE_SPEED = 0.30
LEG_SWING_DEG = 22.0
ARM_SWING_DEG = 18.0

# First-person movement copies bullet_frenzy.py's player controls exactly
# instead: no held-key state, W/S/A/D are applied once per keydown event
# directly in keyboard(), with the OS's own key repeat providing continuity
# while held. W/S step along player_angle, A/D turn it - like bullet_frenzy's
# player_x/y + gun_angle updates in its own keyboardListener.
FP_PLAYER_SPEED = 10.0    # world units per keydown event
FP_TURN_SPEED = 10.0      # degrees per keydown event
WALK_POSE_HOLD = 0.15     # how long the walking pose lingers after the last first-person step
last_fp_move_time = 0.0

# No other file in the project listens for key-release events, so "is this
# key still held" is inferred from when it was last seen going down, using
# one short timeout. A two-tier version (long grace for a fresh press, short
# grace once it's clearly repeating) was tried to avoid stutter, but it made
# a quick tap coast for the long grace period after release, which reads as
# a worse bug than the occasional stutter it was avoiding. A single short
# window keeps release snappy, at the cost of a possible brief stutter right
# after the first press - an accepted trade-off for this project.
KEY_HOLD_TIMEOUT = 0.15
key_last_seen = {}


def note_key_down(key):
    key_last_seen[key] = time.time()


def is_key_held(key):
    return time.time() - key_last_seen.get(key, -999.0) < KEY_HOLD_TIMEOUT

player_x, player_z = 0.0, 150.0
player_angle = 180.0
player_walk_phase = 0.0

# ================= INTERACTION (clues + NPC dialogue) =================
INTERACT_RADIUS = 45.0
# In first person the camera sits right at eye level, so closing to the same
# 45-unit radius used elsewhere would mean walking almost nose-to-nose with
# an NPC before a conversation can start. Talking distance is widened only
# for NPCs, and only in first person, so it reads as a normal conversational
# gap instead - clues and doors keep the closer, examine-it-up-close radius.
FP_TALK_RADIUS = 110.0
active_interactable = None    # {'type': 'clue'/'npc', 'name': ..., 'text': ...} or None
dialogue_open = False
dialogue_title = ''
dialogue_lines = []

# ================= DETECTIVE MODE =================
DETECTIVE_RANGE = 150.0
detective_mode = False

# ================= UI (buttons, notebook, accusation) =================
# ui_mode: 'title' | 'intro' | 'none' | 'howto' | 'notebook' | 'map' | 'incomplete' | 'accuse' | 'gameover' | 'win'
ui_mode = 'title'
collected_clues = set()
CULPRIT_NAME = 'Dr. Julian Reyes'
accuse_result_name = ''


# ============================================================
#  Text / HUD helper
# ============================================================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


# ============================================================
#  Setup camera (perspective, free orbit navigation)
# ============================================================
def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV_Y, WINDOW_W / WINDOW_H, Z_NEAR, Z_FAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        # Heading is just player_angle - the same value A/D and the arrow
        # keys both turn - with look_pitch tilting the view up/down on top
        # of it, independent of heading.
        facing_rad = math.radians(player_angle)
        pitch_rad = math.radians(look_pitch)

        eye_x = player_x + math.sin(facing_rad) * FIRST_PERSON_EYE_FORWARD
        eye_z = player_z + math.cos(facing_rad) * FIRST_PERSON_EYE_FORWARD
        eye_y = FIRST_PERSON_EYE_HEIGHT

        look_x = player_x + math.sin(facing_rad) * math.cos(pitch_rad) * FIRST_PERSON_LOOK_AHEAD
        look_z = player_z + math.cos(facing_rad) * math.cos(pitch_rad) * FIRST_PERSON_LOOK_AHEAD
        look_y = FIRST_PERSON_EYE_HEIGHT + math.sin(pitch_rad) * FIRST_PERSON_LOOK_AHEAD

        gluLookAt(eye_x, eye_y, eye_z,
                  look_x, look_y, look_z,
                  0, 1, 0)
    else:
        az = math.radians(camera_azimuth)
        el = math.radians(camera_elevation)

        eye_x = camera_target[0] + camera_distance * math.cos(el) * math.sin(az)
        eye_y = camera_target[1] + camera_distance * math.sin(el)
        eye_z = camera_target[2] + camera_distance * math.cos(el) * math.cos(az)

        gluLookAt(eye_x, eye_y, eye_z,
                  camera_target[0], camera_target[1], camera_target[2],
                  0, 1, 0)


# ============================================================
#  Primitive helpers
# ============================================================
def _quadric():
    return gluNewQuadric()


def draw_box_at(x, y, z, size_x, size_y, size_z, color):
    """Box centered exactly at (x, y, z)."""
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, y, z)
    glScalef(size_x, size_y, size_z)
    glutSolidCube(1)
    glPopMatrix()


def draw_box(x, z, size_x, size_y, size_z, color):
    """Box standing on the floor, footprint centered at (x, z)."""
    draw_box_at(x, size_y / 2.0, z, size_x, size_y, size_z, color)


def draw_upright_cylinder(x, z, base_r, top_r, height, color, base_y=0.0, slices=18):
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, base_y, z)
    glRotatef(-90, 1, 0, 0)  # local +Z axis -> world +Y
    gluCylinder(_quadric(), base_r, top_r, height, slices, 4)
    glPopMatrix()


def draw_upright_cone(x, z, base_r, height, color, base_y=0.0, slices=14):
    """Despite the name, this is a scaled sphere rather than a literal cone -
    kept as a stretched blob (same trick as the ceiling lamp's shade) so the
    small accents that use it (lamp shades, candle flames) stay a similar
    size and shape without needing a dedicated cone primitive."""
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, base_y + height / 2.0, z)
    glScalef(base_r, height / 2.0, base_r)
    gluSphere(_quadric(), 1.0, slices, slices)
    glPopMatrix()


def draw_sphere_at(x, y, z, radius, color, slices=16, stacks=16):
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, y, z)
    gluSphere(_quadric(), radius, slices, stacks)
    glPopMatrix()


# ============================================================
#  Room shell: floor, walls, baseboards, door & window trim
# ============================================================
def wall_segments_with_gap(full_lo, full_hi, gap_lo, gap_hi):
    return [(full_lo, gap_lo), (gap_hi, full_hi)]


def draw_floor():
    """Wood-plank floor made of alternating strips for visual texture."""
    hx, hz = ROOM_HALF_X, ROOM_HALF_Z
    plank_count = 16
    plank_w = (2 * hx) / plank_count
    for i in range(plank_count):
        cx = -hx + plank_w * (i + 0.5)
        color = (0.55, 0.42, 0.28) if i % 2 == 0 else (0.50, 0.37, 0.24)
        draw_box_at(cx, -1.0, 0.0, plank_w - 1.0, 2.0, 2 * hz, color)


def draw_wall_box(cx, cz, size_x, size_z, color=WALL_COLOR):
    draw_box_at(cx, WALL_HEIGHT / 2.0, cz, size_x, WALL_HEIGHT, size_z, color)


def draw_baseboard_box(cx, cz, size_x, size_z):
    draw_box_at(cx, 5.0, cz, size_x, 10.0, size_z, BASEBOARD_COLOR)


def draw_walls():
    hx, hz = ROOM_HALF_X, ROOM_HALF_Z
    win_lo, win_hi = WINDOW_CENTER_Z - WINDOW_WIDTH / 2.0, WINDOW_CENTER_Z + WINDOW_WIDTH / 2.0
    door_lo, door_hi = DOOR_CENTER_X - DOOR_WIDTH / 2.0, DOOR_CENTER_X + DOOR_WIDTH / 2.0

    # North wall (solid, back of the room)
    draw_wall_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK)
    draw_baseboard_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK + 4)

    # West wall (solid)
    draw_wall_box(-hx, 0, WALL_THICK, 2 * hz + 2 * WALL_THICK)
    draw_baseboard_box(-hx, 0, WALL_THICK + 4, 2 * hz + 2 * WALL_THICK)

    # East wall - split around the window gap
    for lo, hi in wall_segments_with_gap(-hz - WALL_THICK, hz + WALL_THICK, win_lo, win_hi):
        cz, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(hx, cz, WALL_THICK, length)
        draw_baseboard_box(hx, cz, WALL_THICK + 4, length)

    # South wall - split around the door gap
    for lo, hi in wall_segments_with_gap(-hx - WALL_THICK, hx + WALL_THICK, door_lo, door_hi):
        cx, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(cx, hz, length, WALL_THICK)
        draw_baseboard_box(cx, hz, length, WALL_THICK + 4)

    draw_window(hx, win_lo, win_hi)
    draw_door(hz, door_lo, door_hi)


def draw_window(hx, win_lo, win_hi):
    win_bottom, win_top = 12.0, WALL_HEIGHT - 12.0
    mid_z = (win_lo + win_hi) / 2.0
    mid_y = (win_bottom + win_top) / 2.0

    # Glass pane
    draw_box_at(hx - 2, mid_y, mid_z, 4, win_top - win_bottom, (win_hi - win_lo) - 6, (0.68, 0.82, 0.90))

    # Frame border
    draw_box_at(hx - 3, win_bottom, mid_z, 6, 6, win_hi - win_lo, TRIM_COLOR)
    draw_box_at(hx - 3, win_top, mid_z, 6, 6, win_hi - win_lo, TRIM_COLOR)
    draw_box_at(hx - 3, mid_y, win_lo, 6, win_top - win_bottom, 6, TRIM_COLOR)
    draw_box_at(hx - 3, mid_y, win_hi, 6, win_top - win_bottom, 6, TRIM_COLOR)

    # Mullions (cross bars)
    draw_box_at(hx - 3, mid_y, mid_z, 6, win_top - win_bottom, 4, TRIM_COLOR)
    draw_box_at(hx - 3, mid_y, mid_z, 6, 4, win_hi - win_lo, TRIM_COLOR)

    # Curtains on either side
    draw_box(hx - 15, win_lo - 12, 10, WALL_HEIGHT - 15, 14, (0.55, 0.12, 0.16))
    draw_box(hx - 15, win_hi + 12, 10, WALL_HEIGHT - 15, 14, (0.55, 0.12, 0.16))


def draw_door(hz, door_lo, door_hi):
    mid_x = (door_lo + door_hi) / 2.0
    width = door_hi - door_lo

    # Door leaf (closed)
    draw_box_at(mid_x, (WALL_HEIGHT - 15) / 2.0, hz - 3, width - 6, WALL_HEIGHT - 15, 6, (0.30, 0.18, 0.09))

    # Frame posts + header
    draw_box_at(door_lo + 3, WALL_HEIGHT / 2.0, hz - 5, 6, WALL_HEIGHT, 10, TRIM_COLOR)
    draw_box_at(door_hi - 3, WALL_HEIGHT / 2.0, hz - 5, 6, WALL_HEIGHT, 10, TRIM_COLOR)
    draw_box_at(mid_x, WALL_HEIGHT - 15, hz - 5, width, 8, 10, TRIM_COLOR)

    # Handle
    draw_sphere_at(mid_x + width / 2.0 - 12, (WALL_HEIGHT - 15) / 2.0, hz - 6, 3.5, (0.75, 0.65, 0.20))


# ============================================================
#  Furniture
# ============================================================
def draw_bookshelf(x, z, along='x', inward_sign=1):
    """`along` is the axis that runs parallel to the wall it's flush against
    ('x' for a north/south wall, 'z' for an east/west wall); `inward_sign`
    is which direction along the other axis opens into the room.

    Built as an actual open-fronted case (back/top/bottom/side panels with
    nothing across the front) rather than a solid block, so the shelves and
    books drawn inside it are actually visible instead of being buried
    inside opaque geometry."""
    width, depth, height = 150, 30, 90
    wood = (0.36, 0.20, 0.09)
    trim = (0.30, 0.16, 0.07)

    def ax(w_val, d_val):
        return (w_val, d_val) if along == 'x' else (d_val, w_val)

    # Back panel (against the wall)
    back_t = 4
    off = ax(0, -inward_sign * (depth / 2.0 - back_t / 2.0))
    size = ax(width - 8, back_t)
    draw_box_at(x + off[0], height / 2.0, z + off[1], size[0], height, size[1], trim)

    # Top and bottom panels
    size = ax(width, depth)
    draw_box_at(x, height - 4, z, size[0], 8, size[1], wood)
    draw_box_at(x, 4, z, size[0], 8, size[1], wood)

    # Side panels
    for w_side in (-1, 1):
        off = ax(w_side * (width / 2.0 - 4), 0)
        size = ax(8, depth)
        draw_box_at(x + off[0], height / 2.0, z + off[1], size[0], height, size[1], wood)

    # Crown molding + base plinth, proud of the open front
    size = ax(width + 8, depth + 6)
    draw_box_at(x, height + 3, z, size[0], 6, size[1], trim)
    size = ax(width + 4, depth + 4)
    draw_box_at(x, -2, z, size[0], 4, size[1], trim)

    # Shelf boards and books, sitting inside the now-open cavity
    book_colors = [(0.55, 0.1, 0.1), (0.15, 0.35, 0.55), (0.2, 0.45, 0.2),
                   (0.45, 0.35, 0.1), (0.35, 0.15, 0.45)]
    for row, shelf_y in enumerate((26, 50, 74)):
        size = ax(width - 12, depth - 6)
        draw_box_at(x, shelf_y, z, size[0], 3, size[1], trim)

        for i in range(9):
            off = ax(-60 + i * 15, 0)
            size = ax(10, depth - 12)
            color = book_colors[(row * 9 + i) % len(book_colors)]
            draw_box_at(x + off[0], shelf_y + 12, z + off[1], size[0], 22, size[1], color)


def draw_desk(x, z):
    top_y = 42.0
    draw_box_at(x, top_y, z, 130, 6, 65, (0.42, 0.26, 0.13))
    leg_positions = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    for lx, lz in leg_positions:
        draw_box_at(x + lx * 58, top_y / 2.0, z + lz * 27, 8, top_y, 8, (0.30, 0.18, 0.09))

    # Drawer block on one side
    draw_box_at(x + 45, top_y / 2.0, z - 15, 35, top_y - 4, 45, (0.36, 0.22, 0.11))
    for dy in (14, 27):
        draw_sphere_at(x + 45, dy, z - 15 + 18, 1.8, (0.75, 0.65, 0.25))

    # Papers and desk lamp on top
    draw_box_at(x - 35, top_y + 2, z + 10, 26, 2, 20, (0.95, 0.95, 0.90))
    draw_box_at(x - 33, top_y + 4, z + 12, 24, 2, 18, (0.92, 0.92, 0.86))
    draw_desk_lamp(x - 45, z - 15, top_y)

    # Teacup and saucer, set down within easy reach of the chair
    draw_upright_cylinder(x + 25, z + 20, 9, 9, 1.5, (0.90, 0.90, 0.86), base_y=top_y + 3)
    draw_upright_cylinder(x + 25, z + 20, 5.5, 5.5, 8, (0.95, 0.95, 0.92), base_y=top_y + 4.5)


def draw_desk_lamp(x, z, base_y):
    draw_upright_cylinder(x, z, 10, 10, 4, (0.2, 0.2, 0.2), base_y=base_y)
    draw_upright_cylinder(x, z, 3, 3, 45, (0.25, 0.25, 0.25), base_y=base_y + 4)
    draw_upright_cone(x, z, 14, 20, (0.85, 0.80, 0.60), base_y=base_y + 45)
    draw_sphere_at(x, base_y + 42, z, 5, (1.0, 0.95, 0.6))


def angle_toward(from_x, from_z, to_x, to_z):
    """Compass angle (degrees, for draw_seat_base's `angle_deg`) that turns
    a seat at (from_x, from_z) to face the point (to_x, to_z)."""
    return math.degrees(math.atan2(to_x - from_x, to_z - from_z))


def draw_seat_base(x, z, seat_w, seat_d, back_h, angle_deg, seat_color, wood_color, armrests=True):
    """Generic seat, built facing local +Z then rotated to `angle_deg`
    (0 = faces world +z/south, 180 = faces -z/north, and anything in
    between/beyond for a seat that needs to angle toward a specific point)."""
    seat_y = 22.0
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(angle_deg, 0, 1, 0)

    draw_box_at(0, seat_y, 0, seat_w, 6, seat_d, seat_color)

    back_local_z = -(seat_d / 2.0 - 3)
    draw_box_at(0, seat_y + back_h / 2.0, back_local_z, seat_w, back_h, 6, seat_color)

    if armrests:
        draw_box_at(-seat_w / 2.0 + 2.5, seat_y + 10, 0, 5, 18, seat_d - 4, wood_color)
        draw_box_at(seat_w / 2.0 - 2.5, seat_y + 10, 0, 5, 18, seat_d - 4, wood_color)

    # Legs
    for lx, lz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        draw_box_at(lx * (seat_w / 2.0 - 6), seat_y / 2.0, lz * (seat_d / 2.0 - 6),
                    5, seat_y, 5, wood_color)

    glPopMatrix()


def draw_chair(x, z):
    # Faces north (-z), toward the desk
    draw_seat_base(x, z, 42, 42, 45, 180, (0.55, 0.35, 0.15), (0.45, 0.28, 0.12))


def draw_sofa(x, z, facing):
    """`facing`: -1 faces north, +1 faces south (kept simple since every
    sofa placed so far only ever needs to face along the room's length)."""
    seat_w, seat_d, back_h = 100, 40, 50
    color = (0.20, 0.30, 0.45)
    seam = (0.14, 0.21, 0.32)
    angle_deg = 0 if facing >= 0 else 180
    draw_seat_base(x, z, seat_w, seat_d, back_h, angle_deg, color, (0.28, 0.20, 0.13))

    # Center seam so it reads as a 2-seat sofa
    draw_box_at(x, 25, z, 3, 2, seat_d - 4, seam)
    back_z = z - facing * (seat_d / 2.0 - 3)
    draw_box_at(x, 22 + back_h / 2.0, back_z, 3, back_h - 4, 4, seam)


def draw_coffee_table(x, z):
    top_y = 20.0
    draw_box_at(x, top_y, z, 70, 5, 45, (0.42, 0.26, 0.13))
    for lx, lz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        draw_box_at(x + lx * 30, top_y / 2.0, z + lz * 18, 6, top_y, 6, (0.30, 0.18, 0.09))

    # A small vase and a stack of books as tabletop detail
    draw_upright_cylinder(x, z, 6, 4, 14, (0.55, 0.55, 0.60), base_y=top_y + 2.5)
    draw_sphere_at(x, top_y + 18.5, z, 8, (0.25, 0.45, 0.22))
    draw_box_at(x - 18, top_y + 4.5, z + 10, 20, 4, 14, (0.50, 0.15, 0.15))
    draw_box_at(x - 18, top_y + 8.5, z + 10, 18, 4, 12, (0.15, 0.35, 0.55))


def draw_fireplace(z):
    """Flush against the west wall, opening and mantel facing into the room (+X)."""
    wall_x = -ROOM_HALF_X + WALL_THICK / 2.0
    width, depth, height = 130, 42, 78

    body_cx = wall_x + depth / 2.0
    draw_box_at(body_cx, height / 2.0, z, depth, height, width, (0.35, 0.35, 0.37))

    front_x = wall_x + depth
    draw_box_at(front_x - 2, 26, z, 8, 40, 70, (0.08, 0.07, 0.07))  # firebox opening

    mantel_depth = depth + 20
    mantel_y = height + 4
    draw_box_at(wall_x + mantel_depth / 2.0, mantel_y, z, mantel_depth, 8, width + 12, TRIM_COLOR)

    candle_x = wall_x + mantel_depth - 8
    top_y = mantel_y + 4
    for cz in (z - 40, z + 40):
        draw_upright_cylinder(candle_x, cz, 3, 3, 22, (0.75, 0.70, 0.60), base_y=top_y)
        draw_upright_cone(candle_x, cz, 3, 6, (0.95, 0.55, 0.15), base_y=top_y + 22)


def draw_radiator(x, z):
    draw_box(x, z, 60, 45, 15, (0.65, 0.65, 0.68))
    for i in range(5):
        draw_box_at(x - 24 + i * 12, 22.5, z, 4, 40, 16, (0.55, 0.55, 0.58))


def draw_wastebasket(x, z):
    draw_upright_cylinder(x, z, 12, 16, 25, (0.15, 0.15, 0.15))
    draw_sphere_at(x + 4, 26, z + 3, 5, (0.92, 0.92, 0.88))  # crumpled paper


def draw_rug(x, z, size_x, size_z):
    draw_box_at(x, 0.6, z, size_x, 1.2, size_z, (0.55, 0.10, 0.12))
    draw_box_at(x, 1.3, z, size_x - 20, 0.6, size_z - 20, (0.65, 0.55, 0.20))


def draw_wall_picture(x, y, z, w, h, frame_color, canvas_color):
    """For an east/west wall (its normal runs along X)."""
    draw_box_at(x, y, z, 4, h, w, frame_color)
    draw_box_at(x - 2, y, z, 2, h - 8, w - 8, canvas_color)


def draw_wall_picture_ns(x, y, z, w, h, frame_color, canvas_color, inward_sign=1):
    """For a north/south wall (its normal runs along Z)."""
    draw_box_at(x, y, z, w, h, 4, frame_color)
    draw_box_at(x, y, z + inward_sign * 2, w - 8, h - 8, 2, canvas_color)


def draw_wall_clock(x, y, z, radius, inward_sign=1):
    """A disk-faced clock flush against a north/south wall, facing into the room."""
    glPushMatrix()
    glColor3f(0.90, 0.88, 0.80)
    glTranslatef(x, y, z)
    if inward_sign < 0:
        glRotatef(180, 0, 1, 0)
    gluCylinder(_quadric(), radius, radius, 5, 20, 1)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.12, 0.12, 0.12)
    glTranslatef(x, y, z + inward_sign * 5.2)
    if inward_sign < 0:
        glRotatef(180, 0, 1, 0)
    gluCylinder(_quadric(), radius - 4, radius - 4, 1, 20, 1)
    glPopMatrix()


def draw_potted_plant(x, z):
    draw_upright_cylinder(x, z, 14, 10, 22, (0.55, 0.30, 0.15))
    draw_sphere_at(x, 32, z, 16, (0.20, 0.45, 0.20))
    draw_sphere_at(x - 8, 26, z + 6, 11, (0.25, 0.50, 0.22))
    draw_sphere_at(x + 9, 28, z - 5, 12, (0.22, 0.48, 0.24))


def draw_ceiling_lamp(x, z):
    top_y = WALL_HEIGHT - 24
    draw_upright_cylinder(x, z, 2, 2, 24, (0.25, 0.25, 0.25), base_y=top_y)
    glPushMatrix()
    glColor3f(0.85, 0.80, 0.55)
    glTranslatef(x, top_y - 4, z)
    glScalef(1.0, 0.55, 1.0)
    gluSphere(_quadric(), 14, 16, 16)
    glPopMatrix()
    draw_sphere_at(x, top_y - 12, z, 5, (1.0, 0.95, 0.7))


# ============================================================
#  Draw the scene: Room 1 - The Study
# ============================================================
def draw_study_scene():
    draw_floor()
    draw_walls()

    draw_rug(20, 20, 170, 150)

    draw_bookshelf(-275, -230)
    draw_bookshelf(-105, -230)

    draw_desk(0, -30)
    draw_chair(20, 55)

    draw_fireplace(100)
    draw_radiator(370, 125)
    draw_wastebasket(80, 10)

    draw_wall_picture(-398, 62, -100, 60, 40, TRIM_COLOR, (0.35, 0.45, 0.55))
    draw_wall_clock(148, 65, -249, 14)
    draw_potted_plant(-320, 205)

    # Sitting nook in the south-east corner
    draw_coffee_table(280, 165)
    draw_sofa(280, 100, facing=1)    # faces south, toward the table
    draw_sofa(280, 225, facing=-1)   # faces north, toward the table

    draw_ceiling_lamp(20, 40)


# ============================================================
#  Room shell: Room 2 - The Hallway
# ============================================================
def draw_hallway_floor():
    hx, hz = HALL_HALF_X, HALL_HALF_Z
    plank_count = 20
    plank_w = (2 * hx) / plank_count
    for i in range(plank_count):
        cx = -hx + plank_w * (i + 0.5)
        color = (0.55, 0.42, 0.28) if i % 2 == 0 else (0.50, 0.37, 0.24)
        draw_box_at(cx, -1.0, 0.0, plank_w - 1.0, 2.0, 2 * hz, color)


def draw_hallway_door(wall_z, x_lo, x_hi, inward_sign):
    mid_x, width = (x_lo + x_hi) / 2.0, x_hi - x_lo
    leaf_z = wall_z + inward_sign * 3

    draw_box_at(mid_x, (WALL_HEIGHT - 15) / 2.0, leaf_z, width - 6, WALL_HEIGHT - 15, 6, (0.30, 0.18, 0.09))
    draw_box_at(x_lo + 3, WALL_HEIGHT / 2.0, wall_z + inward_sign * 5, 6, WALL_HEIGHT, 10, TRIM_COLOR)
    draw_box_at(x_hi - 3, WALL_HEIGHT / 2.0, wall_z + inward_sign * 5, 6, WALL_HEIGHT, 10, TRIM_COLOR)
    draw_box_at(mid_x, WALL_HEIGHT - 15, wall_z + inward_sign * 5, width, 8, 10, TRIM_COLOR)
    draw_sphere_at(mid_x + width / 2.0 - 12, (WALL_HEIGHT - 15) / 2.0, leaf_z + inward_sign * 3, 3.5, (0.75, 0.65, 0.20))


def draw_open_archway(wall_x, z_lo, z_hi, inward_sign):
    """A doorless opening (both hallway ends) - just a finished frame, no leaf."""
    mid_z = (z_lo + z_hi) / 2.0
    draw_box_at(wall_x + inward_sign * 3, WALL_HEIGHT / 2.0, z_lo + 3, 6, WALL_HEIGHT, 10, TRIM_COLOR)
    draw_box_at(wall_x + inward_sign * 3, WALL_HEIGHT / 2.0, z_hi - 3, 6, WALL_HEIGHT, 10, TRIM_COLOR)
    draw_box_at(wall_x + inward_sign * 3, WALL_HEIGHT - 8, mid_z, 6, 8, z_hi - z_lo, TRIM_COLOR)


def draw_temperature_panel(x, z, inward_sign):
    """The shared control panel - one dial per room in the house."""
    panel_w, panel_h = 95, 45
    mount_y = 58

    draw_box_at(x, mount_y, z + inward_sign * 3, panel_w, panel_h, 6, (0.30, 0.20, 0.12))
    draw_box_at(x, mount_y, z + inward_sign * 6, panel_w - 10, panel_h - 10, 2, (0.85, 0.83, 0.78))

    dial_colors = [
        (0.75, 0.20, 0.20), (0.20, 0.45, 0.75), (0.75, 0.65, 0.20),
        (0.30, 0.60, 0.30), (0.55, 0.30, 0.65), (0.70, 0.45, 0.20),
    ]
    for i, color in enumerate(dial_colors):
        dx = x - 36 + i * 14.5
        draw_sphere_at(dx, mount_y, z + inward_sign * 9, 4.5, color)


def draw_console_table(x, wall_z, inward_sign):
    """`wall_z` is the wall's own z-coordinate; the table stands out from it,
    the mirror hangs flush against it, on the correct (room-facing) side."""
    table_z = wall_z + inward_sign * 15
    top_y = 40.0
    draw_box_at(x, top_y, table_z, 90, 5, 25, (0.42, 0.26, 0.13))
    for lx in (-1, 1):
        draw_box_at(x + lx * 40, top_y / 2.0, table_z, 6, top_y, 6, (0.30, 0.18, 0.09))
    draw_upright_cylinder(x, table_z, 6, 4, 12, (0.55, 0.55, 0.60), base_y=top_y + 2.5)
    draw_sphere_at(x, top_y + 16.5, table_z, 7, (0.45, 0.20, 0.50))

    mirror_y = 75.0
    mirror_z = wall_z + inward_sign * 7
    draw_wall_picture_ns(x, mirror_y, mirror_z, 55, 40, TRIM_COLOR, (0.75, 0.82, 0.85), inward_sign)


def draw_coat_stand(x, z):
    draw_upright_cylinder(x, z, 6, 6, 6, (0.30, 0.18, 0.09))
    draw_upright_cylinder(x, z, 2.5, 2.5, 72, (0.35, 0.22, 0.11), base_y=6)
    for i, ang in enumerate((30, 110, 210, 290)):
        hx_off = 12 * math.cos(math.radians(ang))
        hz_off = 12 * math.sin(math.radians(ang))
        draw_sphere_at(x + hx_off, 68 - i, z + hz_off, 3, (0.20, 0.20, 0.20))
    draw_upright_cylinder(x + 15, z + 8, 8, 5, 30, (0.25, 0.25, 0.28))  # closed umbrella


def draw_grandfather_clock(x, z, inward_sign):
    body_h = 82
    draw_box(x, z, 32, body_h, 24, (0.26, 0.15, 0.07))
    draw_box_at(x, body_h - 12, z, 34, 10, 26, (0.30, 0.18, 0.09))  # crown
    draw_wall_clock(x, body_h - 22, z + inward_sign * 12, 9, inward_sign)
    draw_box_at(x, body_h / 2.0 - 15, z + inward_sign * 12, 16, 45, 1.5, (0.85, 0.83, 0.80))  # pendulum door


def draw_wall_sconce(x, y, z, inward_sign):
    draw_box_at(x, y, z + inward_sign * 2, 8, 10, 4, (0.30, 0.25, 0.15))
    draw_sphere_at(x, y + 6, z + inward_sign * 6, 4, (1.0, 0.92, 0.65))


def draw_hallway_walls():
    hx, hz = HALL_HALF_X, HALL_HALF_Z

    n_door_lo, n_door_hi = -195.0, -125.0
    s_door_lo, s_door_hi = 55.0, 125.0
    e_open_lo, e_open_hi = -50.0, 50.0
    w_open_lo, w_open_hi = -50.0, 50.0

    # North wall - bedroom door
    for lo, hi in wall_segments_with_gap(-hx - WALL_THICK, hx + WALL_THICK, n_door_lo, n_door_hi):
        cx, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(cx, -hz, length, WALL_THICK)
        draw_baseboard_box(cx, -hz, length, WALL_THICK + 4)
    draw_hallway_door(-hz, n_door_lo, n_door_hi, inward_sign=1)

    # South wall - the Parlor's door
    for lo, hi in wall_segments_with_gap(-hx - WALL_THICK, hx + WALL_THICK, s_door_lo, s_door_hi):
        cx, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(cx, hz, length, WALL_THICK)
        draw_baseboard_box(cx, hz, length, WALL_THICK + 4)
    draw_hallway_door(hz, s_door_lo, s_door_hi, inward_sign=-1)

    # East wall - open archway toward the Study
    for lo, hi in wall_segments_with_gap(-hz - WALL_THICK, hz + WALL_THICK, e_open_lo, e_open_hi):
        cz, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(hx, cz, WALL_THICK, length)
        draw_baseboard_box(hx, cz, WALL_THICK + 4, length)
    draw_open_archway(hx, e_open_lo, e_open_hi, inward_sign=-1)

    # West wall - open archway toward the Dining Room
    for lo, hi in wall_segments_with_gap(-hz - WALL_THICK, hz + WALL_THICK, w_open_lo, w_open_hi):
        cz, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(-hx, cz, WALL_THICK, length)
        draw_baseboard_box(-hx, cz, WALL_THICK + 4, length)
    draw_open_archway(-hx, w_open_lo, w_open_hi, inward_sign=1)

    draw_temperature_panel(90, -hz, inward_sign=1)
    draw_wall_sconce(-50, 65, -hz, inward_sign=1)
    draw_wall_sconce(250, 65, -hz, inward_sign=1)
    draw_wall_picture_ns(-100, 62, hz - 7, 55, 38, TRIM_COLOR, (0.40, 0.45, 0.35), inward_sign=-1)


# ============================================================
#  Draw the scene: Room 2 - The Hallway
# ============================================================
def draw_hallway_scene():
    draw_hallway_floor()
    draw_hallway_walls()

    draw_rug(0, 0, 640, 45)

    draw_console_table(-260, HALL_HALF_Z, inward_sign=-1)
    draw_grandfather_clock(330, HALL_HALF_Z - 18, inward_sign=-1)
    draw_coat_stand(-330, -35)

    draw_ceiling_lamp(-180, 0)
    draw_ceiling_lamp(180, 0)


# ============================================================
#  Room shell + furniture: Room 3 - The Parlor
# ============================================================
def draw_parlor_floor():
    """A basket-weave parquet in warm mahogany tones, distinct from the Study's plain oak planks."""
    hx, hz = PARLOR_HALF_X, PARLOR_HALF_Z
    tiles_x, tiles_z = 10, 8
    tile_w, tile_d = (2 * hx) / tiles_x, (2 * hz) / tiles_z
    color_a = (0.45, 0.24, 0.14)
    color_b = (0.33, 0.17, 0.10)

    for i in range(tiles_x):
        for j in range(tiles_z):
            cx = -hx + tile_w * (i + 0.5)
            cz = -hz + tile_d * (j + 0.5)
            if (i + j) % 2 == 0:
                # Pair of planks laid across the tile's width
                draw_box_at(cx, -1.0, cz - tile_d / 4.0, tile_w - 1.5, 2.0, tile_d / 2.0 - 1.0, color_a)
                draw_box_at(cx, -1.0, cz + tile_d / 4.0, tile_w - 1.5, 2.0, tile_d / 2.0 - 1.0, color_b)
            else:
                # Pair of planks laid across the tile's depth (perpendicular, basket-weave look)
                draw_box_at(cx - tile_w / 4.0, -1.0, cz, tile_w / 2.0 - 1.0, 2.0, tile_d - 1.5, color_a)
                draw_box_at(cx + tile_w / 4.0, -1.0, cz, tile_w / 2.0 - 1.0, 2.0, tile_d - 1.5, color_b)


def draw_fireplace_ns(wall_z, x, inward_sign):
    """Same design as the Study's fireplace, rebuilt for a north/south wall."""
    width, depth, height = 130, 42, 78

    body_cz = wall_z + inward_sign * depth / 2.0
    draw_box_at(x, height / 2.0, body_cz, width, height, depth, (0.35, 0.35, 0.37))

    front_z = wall_z + inward_sign * depth
    draw_box_at(x, 26, front_z - inward_sign * 4, 70, 40, 8, (0.08, 0.07, 0.07))  # firebox opening

    mantel_depth = depth + 20
    mantel_y = height + 4
    mantel_cz = wall_z + inward_sign * mantel_depth / 2.0
    draw_box_at(x, mantel_y, mantel_cz, width + 12, 8, mantel_depth, TRIM_COLOR)

    candle_z = wall_z + inward_sign * (mantel_depth - 8)
    top_y = mantel_y + 4
    for cx in (x - 40, x + 40):
        draw_upright_cylinder(cx, candle_z, 3, 3, 22, (0.75, 0.70, 0.60), base_y=top_y)
        draw_upright_cone(cx, candle_z, 3, 6, (0.95, 0.55, 0.15), base_y=top_y + 22)


def draw_armchair(x, z, angle_deg):
    draw_seat_base(x, z, 46, 46, 46, angle_deg, (0.50, 0.30, 0.15), (0.40, 0.25, 0.12))


def draw_side_table(x, z):
    top_y = 40.0
    draw_upright_cylinder(x, z, 14, 14, 36, (0.45, 0.28, 0.14))
    draw_box_at(x, top_y, z, 34, 4, 34, (0.45, 0.28, 0.14))
    draw_upright_cylinder(x, z, 7, 7, 3, (0.2, 0.2, 0.2), base_y=top_y + 2)
    draw_upright_cylinder(x, z, 2, 2, 18, (0.25, 0.25, 0.25), base_y=top_y + 5)
    draw_upright_cone(x, z, 9, 14, (0.90, 0.85, 0.65), base_y=top_y + 23)


def draw_piano(x, wall_z, inward_sign):
    body_w, body_d, body_h = 130, 55, 45
    body_cz = wall_z + inward_sign * body_d / 2.0

    draw_box_at(x, body_h / 2.0, body_cz, body_w, body_h, body_d, (0.15, 0.10, 0.06))
    draw_box_at(x, body_h + 3, body_cz, body_w + 6, 6, body_d + 6, (0.12, 0.08, 0.05))

    front_z = wall_z + inward_sign * body_d
    draw_box_at(x, 20, front_z - inward_sign * 3, body_w - 20, 8, 6, (0.90, 0.88, 0.82))  # keyboard

    bench_z = wall_z + inward_sign * (body_d + 22)
    draw_box_at(x, 20, bench_z, 40, 6, 20, (0.30, 0.18, 0.09))
    for lx, lz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        draw_box_at(x + lx * 17, 8, bench_z + lz * 7, 4, 16, 4, (0.25, 0.15, 0.08))


def draw_chandelier(x, z):
    top_y = WALL_HEIGHT - 20
    draw_upright_cylinder(x, z, 2, 2, 20, (0.55, 0.50, 0.30), base_y=top_y)
    ring_y = top_y - 22
    draw_upright_cylinder(x, z, 22, 22, 3, (0.60, 0.55, 0.35), base_y=ring_y)
    for ang in range(0, 360, 60):
        bx = x + 22 * math.cos(math.radians(ang))
        bz = z + 22 * math.sin(math.radians(ang))
        draw_sphere_at(bx, ring_y - 4, bz, 4, (1.0, 0.95, 0.7))


def draw_parlor_walls():
    hx, hz = PARLOR_HALF_X, PARLOR_HALF_Z
    door_lo, door_hi = -45.0, 45.0
    win_lo, win_hi = -70.0, 70.0

    # North wall (solid, holds the fireplace)
    draw_wall_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK)
    draw_baseboard_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK + 4)

    # West wall (solid, holds the bookshelves)
    draw_wall_box(-hx, 0, WALL_THICK, 2 * hz + 2 * WALL_THICK)
    draw_baseboard_box(-hx, 0, WALL_THICK + 4, 2 * hz + 2 * WALL_THICK)

    # East wall - window
    for lo, hi in wall_segments_with_gap(-hz - WALL_THICK, hz + WALL_THICK, win_lo, win_hi):
        cz, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(hx, cz, WALL_THICK, length)
        draw_baseboard_box(hx, cz, WALL_THICK + 4, length)
    draw_window(hx, win_lo, win_hi)

    # South wall - door back to the hallway
    for lo, hi in wall_segments_with_gap(-hx - WALL_THICK, hx + WALL_THICK, door_lo, door_hi):
        cx, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(cx, hz, length, WALL_THICK)
        draw_baseboard_box(cx, hz, length, WALL_THICK + 4)
    draw_door(hz, door_lo, door_hi)

    draw_fireplace_ns(-hz, 0, inward_sign=1)
    draw_wall_picture_ns(-150, 60, -hz + 7, 45, 32, TRIM_COLOR, (0.30, 0.35, 0.45), inward_sign=1)
    draw_wall_picture_ns(150, 60, -hz + 7, 45, 32, TRIM_COLOR, (0.45, 0.30, 0.30), inward_sign=1)


# ============================================================
#  Draw the scene: Room 3 - The Parlor
# ============================================================
def draw_parlor_scene():
    draw_parlor_floor()
    draw_parlor_walls()

    draw_rug(0, -110, 300, 220)

    table_x, table_z = 0, -140
    draw_coffee_table(table_x, table_z)
    draw_sofa(0, -60, facing=-1)     # directly south of the table, faces north toward it

    # The armchairs sit off to the sides, so they need to angle inward
    # rather than just face north/south to actually point at the table.
    for ax, az in ((-120, -170), (120, -170)):
        draw_armchair(ax, az, angle_toward(ax, az, table_x, table_z))

    draw_side_table(-165, -170)

    draw_bookshelf(-360, -100, along='z')
    draw_bookshelf(-360, 150, along='z')
    draw_piano(-220, PARLOR_HALF_Z, inward_sign=-1)

    draw_potted_plant(300, 250)

    draw_chandelier(0, -110)


# ============================================================
#  Room shell + furniture: Room 4 - The Dining Room
# ============================================================
def draw_dining_floor():
    """A cream/terracotta tile checkerboard, distinct from the wood floors elsewhere in the house."""
    hx, hz = DINING_HALF_X, DINING_HALF_Z
    nx, nz = 11, 9
    tile_w, tile_d = (2 * hx) / nx, (2 * hz) / nz
    for i in range(nx):
        for j in range(nz):
            cx = -hx + tile_w * (i + 0.5)
            cz = -hz + tile_d * (j + 0.5)
            color = (0.82, 0.74, 0.60) if (i + j) % 2 == 0 else (0.70, 0.55, 0.42)
            draw_box_at(cx, -1.0, cz, tile_w - 2.0, 2.0, tile_d - 2.0, color)


def draw_dining_chair(x, z, angle_deg):
    draw_seat_base(x, z, 36, 36, 40, angle_deg, (0.30, 0.18, 0.10), (0.25, 0.15, 0.08), armrests=False)


def draw_dining_table(x, z, length_x, width_z):
    top_y = 45.0
    draw_box_at(x, top_y, z, length_x, 6, width_z, (0.40, 0.24, 0.13))
    for lx, lz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        draw_box_at(x + lx * (length_x / 2.0 - 15), top_y / 2.0, z + lz * (width_z / 2.0 - 10),
                    10, top_y, 10, (0.28, 0.16, 0.08))

    # Table runner
    draw_box_at(x, top_y + 2, z, length_x - 40, 2, width_z - 20, (0.85, 0.85, 0.80))

    # Centerpiece bowl of fruit
    draw_upright_cylinder(x, z, 11, 14, 6, (0.75, 0.75, 0.70), base_y=top_y + 3)
    fruit_colors = [(0.75, 0.10, 0.10), (0.85, 0.55, 0.10), (0.25, 0.55, 0.20), (0.80, 0.75, 0.15)]
    for i, color in enumerate(fruit_colors):
        ang = i * 90 + 40
        fx = x + 6 * math.cos(math.radians(ang))
        fz = z + 6 * math.sin(math.radians(ang))
        draw_sphere_at(fx, top_y + 12, fz, 5, color)

    # Place settings along the two long sides
    for sx in (x - 70, x, x + 70):
        for sz_sign in (-1, 1):
            plate_z = z + sz_sign * (width_z / 2.0 - 12)
            draw_upright_cylinder(sx, plate_z, 9, 9, 1.2, (0.95, 0.95, 0.92), base_y=top_y + 4)


def draw_sideboard(x, wall_z, inward_sign):
    top_y = 46.0
    depth = 28
    body_cz = wall_z + inward_sign * depth / 2.0

    draw_box_at(x, top_y / 2.0, body_cz, 160, top_y, depth, (0.32, 0.19, 0.10))
    draw_box_at(x, top_y + 2, body_cz, 166, 4, depth + 4, (0.28, 0.16, 0.08))

    draw_upright_cylinder(x - 45, body_cz, 13, 13, 3, (0.90, 0.90, 0.85), base_y=top_y + 4)
    draw_upright_cylinder(x + 45, body_cz, 13, 13, 3, (0.90, 0.90, 0.85), base_y=top_y + 4)
    draw_sphere_at(x, top_y + 9, body_cz, 6, (0.55, 0.30, 0.50))


def draw_china_cabinet(x, z):
    size_x, size_z = 30, 120
    draw_box(x, z, size_x, 95, size_z, (0.28, 0.16, 0.08))
    draw_box_at(x + size_x / 2.0 - 1, 55, z, 2, 70, size_z - 10, (0.72, 0.83, 0.88))

    for shelf_y in (30, 55, 80):
        draw_box_at(x, shelf_y, z, size_x - 6, 3, size_z - 14, (0.24, 0.14, 0.07))
        for i in range(4):
            pz = z - 42 + i * 28
            draw_upright_cylinder(x + 2, pz, 9, 9, 1.2, (0.90, 0.90, 0.85), base_y=shelf_y + 2)


def draw_dining_walls():
    hx, hz = DINING_HALF_X, DINING_HALF_Z
    door_lo, door_hi = -45.0, 45.0
    win_lo, win_hi = -65.0, 65.0

    # North wall (solid, holds the sideboard)
    draw_wall_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK)
    draw_baseboard_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK + 4)

    # West wall (solid, holds the china cabinet)
    draw_wall_box(-hx, 0, WALL_THICK, 2 * hz + 2 * WALL_THICK)
    draw_baseboard_box(-hx, 0, WALL_THICK + 4, 2 * hz + 2 * WALL_THICK)

    # East wall - window
    for lo, hi in wall_segments_with_gap(-hz - WALL_THICK, hz + WALL_THICK, win_lo, win_hi):
        cz, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(hx, cz, WALL_THICK, length)
        draw_baseboard_box(hx, cz, WALL_THICK + 4, length)
    draw_window(hx, win_lo, win_hi)

    # South wall - door back to the hallway (the hallway's west archway)
    for lo, hi in wall_segments_with_gap(-hx - WALL_THICK, hx + WALL_THICK, door_lo, door_hi):
        cx, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(cx, hz, length, WALL_THICK)
        draw_baseboard_box(cx, hz, length, WALL_THICK + 4)
    draw_door(hz, door_lo, door_hi)

    draw_sideboard(0, -hz, inward_sign=1)
    draw_wall_picture_ns(200, 60, hz - 7, 50, 36, TRIM_COLOR, (0.35, 0.30, 0.20), inward_sign=-1)


# ============================================================
#  Draw the scene: Room 4 - The Dining Room
# ============================================================
def draw_dining_scene():
    draw_dining_floor()
    draw_dining_walls()

    draw_rug(0, 0, 300, 220)

    table_x, table_z = 0, 0
    length_x, width_z = 220, 90
    draw_dining_table(table_x, table_z, length_x, width_z)

    # Three chairs down each long side, facing the table
    for cx in (-70, 0, 70):
        draw_dining_chair(cx, -65, 0)     # north side, faces south
        draw_dining_chair(cx, 65, 180)    # south side, faces north

    # One chair at each end, angled to face the table lengthwise
    draw_dining_chair(-130, 0, 90)   # west end, faces east
    draw_dining_chair(130, 0, -90)   # east end, faces west

    draw_china_cabinet(-DINING_HALF_X + 20, 100)
    draw_potted_plant(280, 220)

    draw_chandelier(0, 0)


# ============================================================
#  Room shell + furniture: Room 5 - Toby's Bedroom
# ============================================================
def draw_bedroom_floor():
    """Light birch planks - paler than every other room's floor."""
    hx, hz = BEDROOM_HALF_X, BEDROOM_HALF_Z
    plank_count = 14
    plank_w = (2 * hx) / plank_count
    for i in range(plank_count):
        cx = -hx + plank_w * (i + 0.5)
        color = (0.80, 0.70, 0.52) if i % 2 == 0 else (0.75, 0.65, 0.47)
        draw_box_at(cx, -1.0, 0.0, plank_w - 1.0, 2.0, 2 * hz, color)


def draw_bed(x, wall_z, inward_sign, width_x=110, length_z=180):
    frame_h = 22
    body_cz = wall_z + inward_sign * length_z / 2.0

    draw_box_at(x, frame_h / 2.0, body_cz, width_x, frame_h, length_z, (0.35, 0.22, 0.12))
    draw_box_at(x, frame_h + 6, body_cz, width_x - 6, 12, length_z - 6, (0.90, 0.90, 0.85))

    head_z = wall_z + inward_sign * 6
    draw_box_at(x, 45, head_z, width_x + 4, 50, 8, (0.35, 0.22, 0.12))

    blanket_cz = wall_z + inward_sign * (length_z * 0.62)
    draw_box_at(x, frame_h + 13, blanket_cz, width_x - 8, 4, length_z * 0.5, (0.25, 0.45, 0.65))

    pillow_cz = wall_z + inward_sign * 24
    draw_box_at(x, frame_h + 15, pillow_cz, width_x - 30, 8, 26, (0.95, 0.95, 0.90))


def draw_wardrobe(x, z, along='z', inward_sign=1):
    """A closed cabinet (unlike the bookshelf, it should stay solid-looking),
    but with molding and raised door panels instead of a bare box with a
    single seam line scratched onto it. `inward_sign` is which direction,
    along the shallow axis, the doors actually face into the room."""
    width, depth, height = 110, 30, 130
    wood = (0.30, 0.18, 0.10)
    trim = (0.24, 0.14, 0.07)
    panel_color = (0.36, 0.23, 0.12)

    size_x, size_z = (depth, width) if along == 'z' else (width, depth)
    draw_box(x, z, size_x, height, size_z, wood)

    # Crown molding + base plinth
    draw_box_at(x, height + 3, z, size_x + 8, 6, size_z + 8, trim)
    draw_box_at(x, 3, z, size_x + 4, 6, size_z + 4, trim)

    front_gap = depth / 2.0 + 0.8
    if along == 'z':
        front_x = x + inward_sign * front_gap
        for w_off in (-width / 4.0, width / 4.0):
            draw_box_at(front_x, height / 2.0, z + w_off, 1.5, height - 24, width / 2.0 - 14, panel_color)
        draw_box_at(front_x + inward_sign * 0.3, height / 2.0, z, 1.2, height - 20, 2, trim)
        for hw in (-14, 14):
            draw_sphere_at(front_x + inward_sign * 1.2, height / 2.0, z + hw, 2.2, (0.75, 0.65, 0.20))
    else:
        front_z = z + inward_sign * front_gap
        for w_off in (-width / 4.0, width / 4.0):
            draw_box_at(x + w_off, height / 2.0, front_z, width / 2.0 - 14, height - 24, 1.5, panel_color)
        draw_box_at(x, height / 2.0, front_z + inward_sign * 0.3, 2, height - 20, 1.2, trim)
        for hw in (-14, 14):
            draw_sphere_at(x + hw, height / 2.0, front_z + inward_sign * 1.2, 2.2, (0.75, 0.65, 0.20))


def draw_toy_shelf(x, z, along='x'):
    size_x, size_z = (100, 26) if along == 'x' else (26, 100)
    draw_box(x, z, size_x, 70, size_z, (0.40, 0.28, 0.15))
    for shelf_y in (25, 48):
        draw_box_at(x, shelf_y, z, size_x - 4, 3, size_z - 2, (0.34, 0.22, 0.11))

    toy_colors = [(0.85, 0.2, 0.2), (0.2, 0.5, 0.85), (0.9, 0.75, 0.15), (0.3, 0.7, 0.35)]
    for i, shelf_y in enumerate((14, 37, 60)):
        for k in range(3):
            color = toy_colors[(i * 3 + k) % len(toy_colors)]
            if along == 'x':
                draw_box_at(x - 30 + k * 30, shelf_y, z, 18, 20, 16, color)
            else:
                draw_box_at(x, shelf_y, z - 30 + k * 30, 16, 20, 18, color)


def draw_toy_chest(x, z):
    draw_box(x, z, 60, 30, 34, (0.55, 0.30, 0.12))
    draw_box_at(x, 32, z, 64, 6, 38, (0.45, 0.24, 0.10))
    draw_sphere_at(x - 15, 38, z, 8, (0.85, 0.2, 0.2))
    draw_box_at(x + 12, 36, z, 14, 10, 14, (0.2, 0.5, 0.85))


def draw_empty_terrarium_stand(x, z):
    """Toby's tarantula tank used to sit here - it's just an empty stand now."""
    top_y = 34.0
    draw_upright_cylinder(x, z, 12, 12, 32, (0.45, 0.28, 0.14))
    draw_box_at(x, top_y, z, 40, 4, 30, (0.45, 0.28, 0.14))
    draw_box_at(x, top_y + 2.2, z, 32, 0.6, 22, (0.55, 0.55, 0.50))


def draw_bedroom_walls():
    hx, hz = BEDROOM_HALF_X, BEDROOM_HALF_Z
    door_lo, door_hi = -40.0, 40.0
    win_lo, win_hi = -55.0, 55.0

    # North wall (solid, holds the bed)
    draw_wall_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK)
    draw_baseboard_box(0, -hz, 2 * hx + 2 * WALL_THICK, WALL_THICK + 4)

    # East wall (solid, holds the wardrobe)
    draw_wall_box(hx, 0, WALL_THICK, 2 * hz + 2 * WALL_THICK)
    draw_baseboard_box(hx, 0, WALL_THICK + 4, 2 * hz + 2 * WALL_THICK)

    # West wall - window
    for lo, hi in wall_segments_with_gap(-hz - WALL_THICK, hz + WALL_THICK, win_lo, win_hi):
        cz, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(-hx, cz, WALL_THICK, length)
        draw_baseboard_box(-hx, cz, WALL_THICK + 4, length)
    draw_window(-hx, win_lo, win_hi)

    # South wall - door back to the hallway
    for lo, hi in wall_segments_with_gap(-hx - WALL_THICK, hx + WALL_THICK, door_lo, door_hi):
        cx, length = (lo + hi) / 2.0, hi - lo
        draw_wall_box(cx, hz, length, WALL_THICK)
        draw_baseboard_box(cx, hz, length, WALL_THICK + 4)
    draw_door(hz, door_lo, door_hi)

    draw_wall_picture_ns(120, 58, -hz + 7, 40, 30, TRIM_COLOR, (0.35, 0.50, 0.30), inward_sign=1)


# ============================================================
#  Draw the scene: Room 5 - Toby's Bedroom
# ============================================================
def draw_bedroom_scene():
    draw_bedroom_floor()
    draw_bedroom_walls()

    draw_rug(20, -20, 220, 160)

    draw_bed(-90, -BEDROOM_HALF_Z, inward_sign=1)
    draw_side_table(-15, -195)

    desk_x, desk_z = 170, -120
    draw_desk(desk_x, desk_z)
    draw_dining_chair(desk_x, desk_z + 50, angle_toward(desk_x, desk_z + 50, desk_x, desk_z))

    draw_wardrobe(BEDROOM_HALF_X - 20, 100, along='z', inward_sign=-1)
    draw_toy_shelf(150, BEDROOM_HALF_Z - 18, along='x')
    draw_toy_chest(0, -40)
    draw_empty_terrarium_stand(-230, 90)

    draw_ceiling_lamp(0, -20)


# ============================================================
#  Characters: the playable detective and the household's cast
# ============================================================
def draw_person(x, z, angle_deg, skin, shirt, pants, hair, hat=False, scale=1.0, walk_phase=0.0):
    """A simple blocky humanoid, built facing local +Z (matching the seats'
    convention) then rotated to `angle_deg` and dropped at (x, z).
    `walk_phase` swings the legs/arms for a walk cycle - leaving it at its
    default 0.0 (as every stationary NPC does) keeps them standing still,
    since sin(0) is 0."""
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(angle_deg, 0, 1, 0)
    glScalef(scale, scale, scale)

    leg_h = 28
    leg_swing = LEG_SWING_DEG * math.sin(walk_phase)
    for leg_x, phase_sign in ((-6, 1), (6, -1)):
        glPushMatrix()
        glTranslatef(leg_x, leg_h, 0)          # hip joint, at the top of the leg
        glRotatef(phase_sign * leg_swing, 1, 0, 0)
        draw_box_at(0, -leg_h / 2.0, 0, 7, leg_h, 9, pants)
        glPopMatrix()

    torso_h = 32
    torso_y = leg_h + torso_h / 2.0
    draw_box_at(0, torso_y, 0, 24, torso_h, 14, shirt)

    arm_h = 26
    shoulder_y = leg_h + torso_h - 2
    arm_swing = ARM_SWING_DEG * math.sin(walk_phase)
    for arm_x, phase_sign in ((-15, -1), (15, 1)):     # opposite the same-side leg, like a natural gait
        glPushMatrix()
        glTranslatef(arm_x, shoulder_y, 0)
        glRotatef(phase_sign * arm_swing, 1, 0, 0)
        draw_box_at(0, -arm_h / 2.0, 0, 6, arm_h, 8, shirt)
        draw_sphere_at(0, -arm_h - 2, 0, 3.2, skin)
        glPopMatrix()

    head_y = leg_h + torso_h + 10
    draw_sphere_at(0, head_y, 0, 10, skin)

    if hat:
        draw_upright_cylinder(0, 0, 15, 15, 1.5, (0.14, 0.14, 0.14), base_y=head_y + 6)
        draw_upright_cylinder(0, 0, 9, 9, 8, (0.16, 0.16, 0.16), base_y=head_y + 7)
    else:
        # Centered well above the head's own center and slightly larger, so
        # it actually pokes out past the skin sphere instead of being buried
        # inside it (the head has radius 10, so anything smaller sitting
        # near its center is entirely hidden behind its own surface).
        glPushMatrix()
        glColor3f(*hair)
        glTranslatef(0, head_y + 7, -1)
        glScalef(1.08, 0.62, 1.08)
        gluSphere(_quadric(), 10, 14, 14)
        glPopMatrix()

    glPopMatrix()


def draw_victim_body(x, z, angle_deg, skin, shirt, pants, hair):
    """Cornelius Vane, dead - slumped forward in his chair rather than
    standing, since he's the locked room's victim, not a living NPC."""
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(angle_deg, 0, 1, 0)

    leg_h = 28
    draw_box_at(-6, leg_h / 2.0, 4, 7, leg_h, 9, pants)
    draw_box_at(6, leg_h / 2.0, 4, 7, leg_h, 9, pants)

    # Torso, arms and head all pitch forward together from the hips
    glPushMatrix()
    glTranslatef(0, leg_h, 0)
    glRotatef(65, 1, 0, 0)

    torso_h = 32
    draw_box_at(0, torso_h / 2.0, 0, 24, torso_h, 14, shirt)

    arm_h = 26
    for arm_x in (-15, 15):
        draw_box_at(arm_x, torso_h - arm_h / 2.0 + 2, 0, 6, arm_h, 8, shirt)
        draw_sphere_at(arm_x, torso_h - arm_h - 2, 0, 3.2, skin)

    head_y = torso_h + 10
    draw_sphere_at(0, head_y, 0, 10, skin)

    glPushMatrix()
    glColor3f(*hair)
    glTranslatef(0, head_y + 7, -1)
    glScalef(1.08, 0.62, 1.08)
    gluSphere(_quadric(), 10, 14, 14)
    glPopMatrix()

    glPopMatrix()  # end forward pitch
    glPopMatrix()


DETECTIVE = {'skin': (0.85, 0.70, 0.55), 'shirt': (0.25, 0.25, 0.30),
             'pants': (0.15, 0.15, 0.18), 'hair': (0.25, 0.15, 0.08)}

CHARACTERS = [
    # Cornelius Vane - the victim, dead, slumped in his chair at the desk
    {'room': ROOM_STUDY, 'x': 20, 'z': 55, 'angle': 180, 'style': 'slumped',
     'name': 'Cornelius Vane', 'examine': True,
     'dialogue': "He's cold. There's no wound serious enough to have killed him - "
                 "just a few shallow cuts from broken glass. Whatever did this, "
                 "it wasn't a blade.",
     'skin': (0.80, 0.65, 0.52), 'shirt': (0.35, 0.30, 0.55), 'pants': (0.25, 0.22, 0.30), 'hair': (0.85, 0.85, 0.85)},
    # Nurse Ros Kerr - Study
    {'room': ROOM_STUDY, 'x': 220, 'z': 60, 'angle': 200,
     'name': 'Nurse Ros Kerr',
     'dialogue': "\"I've checked his medication log a dozen times, Inspector. "
                 "Nothing's missing, nothing's off. I don't know what could have "
                 "done this to him.\"",
     'skin': (0.70, 0.55, 0.42), 'shirt': (0.92, 0.92, 0.94), 'pants': (0.85, 0.85, 0.88), 'hair': (0.20, 0.15, 0.10)},
    # Dr. Julian Reyes - Hallway, by the temperature panel
    {'room': ROOM_HALLWAY, 'x': 90, 'z': -30, 'angle': 180,
     'name': 'Dr. Julian Reyes',
     'dialogue': "\"Cornelius was making real progress. I truly believe exposure "
                 "therapy was helping him face his fears. This is a tragedy.\"",
     'skin': (0.75, 0.60, 0.48), 'shirt': (0.20, 0.35, 0.30), 'pants': (0.20, 0.20, 0.22), 'hair': (0.10, 0.08, 0.06)},
    # Priya Anand - Hallway, by the console table
    {'room': ROOM_HALLWAY, 'x': -260, 'z': 20, 'angle': 0,
     'name': 'Priya Anand',
     'dialogue': "\"I- I didn't mean to tidy the room before you arrived, "
                 "Inspector. Force of habit. I do hope I haven't ruined anything "
                 "important.\"",
     'skin': (0.55, 0.40, 0.30), 'shirt': (0.55, 0.15, 0.15), 'pants': (0.30, 0.28, 0.26), 'hair': (0.08, 0.06, 0.05)},
    # Margot Vane - Parlor
    {'room': ROOM_PARLOR, 'x': 200, 'z': -50, 'angle': -90,
     'name': 'Margot Vane',
     'dialogue': "\"Father and I had our disagreements, yes. But he was still my "
                 "father, Inspector. I would never.\"",
     'skin': (0.85, 0.70, 0.58), 'shirt': (0.45, 0.20, 0.45), 'pants': (0.40, 0.18, 0.40), 'hair': (0.35, 0.20, 0.10)},
    # Aldous Finch - Parlor, by the piano
    {'room': ROOM_PARLOR, 'x': -150, 'z': 150, 'angle': 90,
     'name': 'Aldous Finch',
     'dialogue': "\"Cornelius and I had decades of partnership. Whatever you're "
                 "implying, our books are in perfect order.\"",
     'skin': (0.80, 0.65, 0.52), 'shirt': (0.15, 0.15, 0.40), 'pants': (0.12, 0.12, 0.30), 'hair': (0.35, 0.35, 0.35)},
    # Desmond Vane - Dining Room
    {'room': ROOM_DINING, 'x': 150, 'z': 150, 'angle': angle_toward(150, 150, 0, 0),
     'name': 'Desmond Vane',
     'dialogue': "\"Look, I owed some money, alright? That doesn't mean I killed "
                 "him. I wasn't even in the house when it happened.\"",
     'skin': (0.80, 0.65, 0.52), 'shirt': (0.55, 0.45, 0.15), 'pants': (0.25, 0.20, 0.15), 'hair': (0.20, 0.15, 0.10)},
    # Toby Vane - his own Bedroom
    {'room': ROOM_BEDROOM, 'x': 40, 'z': -60, 'angle': angle_toward(40, -60, 0, -40), 'scale': 0.65,
     'name': 'Toby Vane',
     'dialogue': "\"I looked everywhere! My spider's gone and Grandpa's dead and "
                 "everyone thinks it's my fault!\"",
     'skin': (0.85, 0.70, 0.58), 'shirt': (0.20, 0.55, 0.75), 'pants': (0.30, 0.25, 0.20), 'hair': (0.35, 0.22, 0.12)},
    # Charlotte Vane - Desmond's wife, Toby's mother, watching over him
    {'room': ROOM_BEDROOM, 'x': -20, 'z': -90, 'angle': angle_toward(-20, -90, 40, -60),
     'name': 'Charlotte Vane',
     'dialogue': "\"Toby hasn't done anything wrong. He's just a child who loves "
                 "his pet. Please don't frighten him any further.\"",
     'skin': (0.85, 0.68, 0.55), 'shirt': (0.35, 0.50, 0.40), 'pants': (0.30, 0.42, 0.34), 'hair': (0.45, 0.32, 0.18)},
]

SUSPECTS = [c['name'] for c in CHARACTERS if not c.get('examine')]  # everyone but the victim


def draw_room_npcs(room_id):
    for c in CHARACTERS:
        if c['room'] != room_id:
            continue
        if c.get('style') == 'slumped':
            draw_victim_body(c['x'], c['z'], c['angle'], c['skin'], c['shirt'], c['pants'], c['hair'])
        else:
            draw_person(c['x'], c['z'], c['angle'], c['skin'], c['shirt'], c['pants'], c['hair'],
                        scale=c.get('scale', 1.0))


def draw_detective():
    draw_person(player_x, player_z, player_angle, DETECTIVE['skin'], DETECTIVE['shirt'],
                DETECTIVE['pants'], DETECTIVE['hair'], hat=True, walk_phase=player_walk_phase)


# Axis-aligned footprints for the major floor-standing furniture in each
# room (small decor like lamps/pictures/rugs is left walkable). Each entry
# is {'room', 'x', 'z', 'hx', 'hz'} - a box centered at (x, z) with those
# half-extents, matching the actual dimensions passed to that furniture's
# draw call so the collision roughly matches what's on screen.
OBSTACLES = [
    # --- The Study ---
    {'room': ROOM_STUDY, 'x': -275, 'z': -230, 'hx': 75, 'hz': 15},   # bookshelf
    {'room': ROOM_STUDY, 'x': -105, 'z': -230, 'hx': 75, 'hz': 15},   # bookshelf
    {'room': ROOM_STUDY, 'x': 0, 'z': -30, 'hx': 65, 'hz': 33},       # desk
    {'room': ROOM_STUDY, 'x': 20, 'z': 55, 'hx': 24, 'hz': 24},       # chair
    {'room': ROOM_STUDY, 'x': -372, 'z': 100, 'hx': 27, 'hz': 71},    # fireplace + mantel
    {'room': ROOM_STUDY, 'x': 370, 'z': 125, 'hx': 30, 'hz': 8},      # radiator
    {'room': ROOM_STUDY, 'x': 80, 'z': 10, 'hx': 16, 'hz': 16},       # wastebasket
    {'room': ROOM_STUDY, 'x': -320, 'z': 205, 'hx': 16, 'hz': 16},    # potted plant
    {'room': ROOM_STUDY, 'x': 280, 'z': 165, 'hx': 35, 'hz': 23},     # coffee table
    {'room': ROOM_STUDY, 'x': 280, 'z': 100, 'hx': 50, 'hz': 20},     # sofa
    {'room': ROOM_STUDY, 'x': 280, 'z': 225, 'hx': 50, 'hz': 20},     # sofa

    # --- The Hallway ---
    {'room': ROOM_HALLWAY, 'x': -260, 'z': 55, 'hx': 45, 'hz': 13},   # console table
    {'room': ROOM_HALLWAY, 'x': 330, 'z': 52, 'hx': 16, 'hz': 12},    # grandfather clock
    {'room': ROOM_HALLWAY, 'x': -330, 'z': -35, 'hx': 15, 'hz': 15},  # coat stand

    # --- The Parlor ---
    {'room': ROOM_PARLOR, 'x': 0, 'z': -140, 'hx': 35, 'hz': 23},     # coffee table
    {'room': ROOM_PARLOR, 'x': 0, 'z': -60, 'hx': 50, 'hz': 20},      # sofa
    {'room': ROOM_PARLOR, 'x': -120, 'z': -170, 'hx': 25, 'hz': 25},  # armchair
    {'room': ROOM_PARLOR, 'x': 120, 'z': -170, 'hx': 25, 'hz': 25},   # armchair
    {'room': ROOM_PARLOR, 'x': -165, 'z': -170, 'hx': 18, 'hz': 18},  # side table
    {'room': ROOM_PARLOR, 'x': -360, 'z': -100, 'hx': 15, 'hz': 75},  # bookshelf (along z)
    {'room': ROOM_PARLOR, 'x': -360, 'z': 150, 'hx': 15, 'hz': 75},   # bookshelf (along z)
    {'room': ROOM_PARLOR, 'x': -220, 'z': 272, 'hx': 65, 'hz': 45},   # piano + bench
    {'room': ROOM_PARLOR, 'x': 300, 'z': 250, 'hx': 16, 'hz': 16},    # potted plant

    # --- The Dining Room ---
    {'room': ROOM_DINING, 'x': 0, 'z': 0, 'hx': 110, 'hz': 45},       # dining table
    {'room': ROOM_DINING, 'x': -70, 'z': -65, 'hx': 18, 'hz': 18},    # chair
    {'room': ROOM_DINING, 'x': 0, 'z': -65, 'hx': 18, 'hz': 18},      # chair
    {'room': ROOM_DINING, 'x': 70, 'z': -65, 'hx': 18, 'hz': 18},     # chair
    {'room': ROOM_DINING, 'x': -70, 'z': 65, 'hx': 18, 'hz': 18},     # chair
    {'room': ROOM_DINING, 'x': 0, 'z': 65, 'hx': 18, 'hz': 18},       # chair
    {'room': ROOM_DINING, 'x': 70, 'z': 65, 'hx': 18, 'hz': 18},      # chair
    {'room': ROOM_DINING, 'x': -130, 'z': 0, 'hx': 18, 'hz': 18},     # end chair
    {'room': ROOM_DINING, 'x': 130, 'z': 0, 'hx': 18, 'hz': 18},      # end chair
    {'room': ROOM_DINING, 'x': -320, 'z': 100, 'hx': 15, 'hz': 60},   # china cabinet
    {'room': ROOM_DINING, 'x': 280, 'z': 220, 'hx': 16, 'hz': 16},    # potted plant

    # --- Toby's Bedroom ---
    {'room': ROOM_BEDROOM, 'x': -90, 'z': -130, 'hx': 55, 'hz': 90},  # bed
    {'room': ROOM_BEDROOM, 'x': -15, 'z': -195, 'hx': 18, 'hz': 18},  # nightstand
    {'room': ROOM_BEDROOM, 'x': 170, 'z': -120, 'hx': 65, 'hz': 33},  # desk
    {'room': ROOM_BEDROOM, 'x': 170, 'z': -70, 'hx': 18, 'hz': 18},   # desk chair
    {'room': ROOM_BEDROOM, 'x': 260, 'z': 100, 'hx': 15, 'hz': 55},   # wardrobe
    {'room': ROOM_BEDROOM, 'x': 150, 'z': 202, 'hx': 50, 'hz': 13},   # toy shelf
    {'room': ROOM_BEDROOM, 'x': 0, 'z': -40, 'hx': 30, 'hz': 17},     # toy chest
    {'room': ROOM_BEDROOM, 'x': -230, 'z': 90, 'hx': 20, 'hz': 15},   # empty terrarium stand
]


def is_blocked(room_id, x, z):
    for ob in OBSTACLES:
        if ob['room'] != room_id:
            continue
        if (ob['x'] - ob['hx'] - PLAYER_RADIUS <= x <= ob['x'] + ob['hx'] + PLAYER_RADIUS and
                ob['z'] - ob['hz'] - PLAYER_RADIUS <= z <= ob['z'] + ob['hz'] + PLAYER_RADIUS):
            return True

    for ch in CHARACTERS:
        if ch['room'] != room_id or ch.get('style') == 'slumped':
            continue  # the victim's body doesn't move - the chair obstacle already covers it
        radius = NPC_RADIUS * ch.get('scale', 1.0) + PLAYER_RADIUS
        if math.hypot(x - ch['x'], z - ch['z']) <= radius:
            return True

    return False


def fp_move_player(sign):
    """First-person W/S - one fixed step per keydown along player_angle,
    exactly bullet_frenzy.py's player_x/y update in its keyboardListener."""
    global player_x, player_z, last_fp_move_time
    if dialogue_open or ui_mode != 'none':
        return

    angle_rad = math.radians(player_angle)
    dx = math.sin(angle_rad) * sign
    dz = math.cos(angle_rad) * sign

    new_x = player_x + dx * FP_PLAYER_SPEED
    new_z = player_z + dz * FP_PLAYER_SPEED

    if is_blocked(current_room, new_x, player_z):
        new_x = player_x
    if is_blocked(current_room, new_x, new_z):
        new_z = player_z

    player_x, player_z = new_x, new_z

    half_x, half_z = ROOM_HALF_DIMS[current_room]
    player_x = max(-half_x + PLAYER_MARGIN, min(half_x - PLAYER_MARGIN, player_x))
    player_z = max(-half_z + PLAYER_MARGIN, min(half_z - PLAYER_MARGIN, player_z))

    last_fp_move_time = time.time()


def fp_turn_player(sign):
    """First-person A/D - one fixed rotation step per keydown, exactly
    bullet_frenzy.py's `gun_angle += 10` / `-= 10` per key event."""
    global player_angle
    if dialogue_open or ui_mode != 'none':
        return
    player_angle = (player_angle + sign * FP_TURN_SPEED) % 360.0


def update_player():
    """Third person: free movement on the world axes - W/S/A/D each push in
    their own fixed direction, and the detective automatically turns to
    face whichever way they're actually walking (or a diagonal blend of two
    keys), applied smoothly every idle() tick while a key reads held.

    First person: position/heading are updated directly by fp_move_player()/
    fp_turn_player() per keydown instead, so this only eases the walk-cycle
    animation back to neutral a moment after the last step."""
    global player_x, player_z, player_angle, player_walk_phase
    if dialogue_open or ui_mode != 'none':
        player_walk_phase = 0.0
        return

    if first_person:
        if time.time() - last_fp_move_time < WALK_POSE_HOLD:
            player_walk_phase += WALK_CYCLE_SPEED
        else:
            player_walk_phase = 0.0
        return

    dx = dz = 0.0
    if is_key_held(b'w'):
        dz -= 1.0
    if is_key_held(b's'):
        dz += 1.0
    if is_key_held(b'a'):
        dx -= 1.0
    if is_key_held(b'd'):
        dx += 1.0

    if dx == 0.0 and dz == 0.0:
        player_walk_phase = 0.0  # stand at a neutral pose when not walking
        return

    length = math.hypot(dx, dz)
    dx, dz = dx / length, dz / length
    player_angle = math.degrees(math.atan2(dx, dz))
    player_walk_phase += WALK_CYCLE_SPEED

    # Resolve X and Z separately so bumping into a piece of furniture at an
    # angle slides you along it instead of just halting all movement dead.
    new_x = player_x + dx * PLAYER_SPEED
    new_z = player_z + dz * PLAYER_SPEED

    if is_blocked(current_room, new_x, player_z):
        new_x = player_x
    if is_blocked(current_room, new_x, new_z):
        new_z = player_z

    player_x, player_z = new_x, new_z

    half_x, half_z = ROOM_HALF_DIMS[current_room]
    player_x = max(-half_x + PLAYER_MARGIN, min(half_x - PLAYER_MARGIN, player_x))
    player_z = max(-half_z + PLAYER_MARGIN, min(half_z - PLAYER_MARGIN, player_z))


def is_looking_at(target_x, target_y, target_z):
    """True if the first-person camera's actual 3D view direction - the
    same yaw+pitch combination setup_camera() renders from the same eye
    point - is aimed within LOOK_CONE_DEG of the given world point. Real
    vector math instead of separate yaw/pitch tolerances, so there's one
    single "am I looking at it" answer rather than two checks that can
    disagree with each other."""
    facing_rad = math.radians(player_angle)
    pitch_rad = math.radians(look_pitch)

    eye_x = player_x + math.sin(facing_rad) * FIRST_PERSON_EYE_FORWARD
    eye_y = FIRST_PERSON_EYE_HEIGHT
    eye_z = player_z + math.cos(facing_rad) * FIRST_PERSON_EYE_FORWARD

    view_x = math.sin(facing_rad) * math.cos(pitch_rad)
    view_y = math.sin(pitch_rad)
    view_z = math.cos(facing_rad) * math.cos(pitch_rad)

    to_x, to_y, to_z = target_x - eye_x, target_y - eye_y, target_z - eye_z
    to_len = math.sqrt(to_x * to_x + to_y * to_y + to_z * to_z)
    if to_len < 1e-6:
        return True
    to_x, to_y, to_z = to_x / to_len, to_y / to_len, to_z / to_len

    dot = max(-1.0, min(1.0, view_x * to_x + view_y * to_y + view_z * to_z))
    return math.degrees(math.acos(dot)) <= LOOK_CONE_DEG


def update_interactions():
    """Find the nearest clue, NPC, or door in the current room that's within
    its own reach radius. In first person, both clues and NPCs also require
    the camera to actually be aimed at them (is_looking_at) - not just
    standing nearby - and NPCs get a wider radius (FP_TALK_RADIUS) besides,
    since walking up close enough for a conversation looks awkward from eye
    level, while clues get a smaller bump (FP_CLUE_RADIUS). Doors, and
    third person throughout, keep the original proximity-only behavior."""
    global active_interactable
    best, best_dist = None, None
    npc_radius = FP_TALK_RADIUS if first_person else INTERACT_RADIUS
    clue_radius = FP_CLUE_RADIUS if first_person else INTERACT_RADIUS

    def consider(dist, radius, candidate):
        nonlocal best, best_dist
        if dist <= radius and (best_dist is None or dist < best_dist):
            best_dist = dist
            best = candidate

    for c in CLUES:
        if c['room'] != current_room:
            continue
        d = math.hypot(player_x - c['x'], player_z - c['z'])
        if first_person and not is_looking_at(c['x'], c['marker_y'], c['z']):
            continue  # in range, but the camera isn't actually aimed at it
        # The teacup sits boxed in between the desk and chair collision
        # boxes, so 'radius' widens its distance requirement to still reach
        # it. The temperature panel goes further: Reyes's own NPC collision
        # stands almost on top of it, so in first person there's no
        # satisfying distance requirement at all - 'ignore_distance_fp'
        # drops the cap there entirely and leaves is_looking_at (checked
        # above) as the only requirement, from anywhere in the room.
        if first_person and c.get('ignore_distance_fp'):
            radius = float('inf')
        else:
            radius = c.get('radius', clue_radius)
        consider(d, radius, {'type': 'clue', 'name': c['name'], 'text': c['text']})

    for ch in CHARACTERS:
        if ch['room'] != current_room:
            continue
        d = math.hypot(player_x - ch['x'], player_z - ch['z'])
        if first_person:
            head_y = 70.0 * ch.get('scale', 1.0)  # matches draw_person's own head-height math
            if not is_looking_at(ch['x'], head_y, ch['z']):
                continue  # in range, but the camera isn't aimed at them
        consider(d, npc_radius, {'type': 'npc', 'examine': ch.get('examine', False),
                                  'name': ch['name'], 'text': ch['dialogue']})

    for dr in DOORS:
        if dr['room'] != current_room:
            continue
        d = math.hypot(player_x - dr['x'], player_z - dr['z'])
        consider(d, INTERACT_RADIUS, {'type': 'door', 'name': dr['label'], 'door': dr})

    active_interactable = best


def wrap_text(text, max_chars=64):
    words = text.split()
    lines, current = [], ''
    for word in words:
        trial = (current + ' ' + word).strip()
        if len(trial) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


# No other file in the project queries real glyph metrics, so text width is
# estimated from a fixed average pixel width per character for each font
# instead - close enough to keep titles/buttons/labels visually centered.
# Keyed by the raw pointer value since the GLUT_BITMAP_* font constants
# (ctypes.c_void_p) aren't hashable themselves.
_AVG_CHAR_WIDTH = {
    GLUT_BITMAP_HELVETICA_10.value: 6,
    GLUT_BITMAP_HELVETICA_18.value: 10,
    GLUT_BITMAP_TIMES_ROMAN_24.value: 13,
}


def text_width(text, font=GLUT_BITMAP_HELVETICA_18):
    return len(text) * _AVG_CHAR_WIDTH.get(font.value, 10)


def draw_text_centered(y, text, font=GLUT_BITMAP_HELVETICA_18):
    draw_text((WINDOW_W - text_width(text, font)) / 2.0, y, text, font)


def draw_interact_prompt():
    if dialogue_open or ui_mode != 'none' or active_interactable is None:
        return
    if active_interactable['type'] == 'door':
        verb = 'go to'
    elif active_interactable['type'] == 'npc' and not active_interactable['examine']:
        verb = 'talk to'
    else:
        verb = 'examine'
    glDisable(GL_DEPTH_TEST)
    draw_text_centered(110, "Press F to %s %s" % (verb, active_interactable['name']))
    glEnable(GL_DEPTH_TEST)


def _draw_panel_rect(x1, y1, x2, y2, color, filled=True):
    """Draws one solid rectangle in screen space (no alpha blending is used
    anywhere in this project, so panels are opaque rather than translucent).
    The caller is responsible for disabling GL_DEPTH_TEST before its first
    call and re-enabling it after its last (see the note in
    draw_dialogue_box) - background fills and the text drawn over them must
    share that disabled state for the whole pass, or the fill silently wins
    the depth tie against its own text."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(*color)
    glBegin(GL_QUADS if filled else GL_LINE_LOOP)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def draw_dialogue_box():
    if not dialogue_open:
        return

    line_h = 22
    box_h = 70 + line_h * len(dialogue_lines)
    box_left, box_right = 60, WINDOW_W - 60
    box_bottom, box_top = 20, 20 + box_h

    # See _draw_panel_rect's note: depth testing has to stay disabled across
    # both the fill/border AND the text, not just the fill, or the text
    # drawn right after loses the depth tie against its own background.
    glDisable(GL_DEPTH_TEST)
    _draw_panel_rect(box_left, box_bottom, box_right, box_top, (0.05, 0.05, 0.08))
    _draw_panel_rect(box_left, box_bottom, box_right, box_top, (0.85, 0.75, 0.35), filled=False)

    draw_text(box_left + 20, box_top - 32, dialogue_title, GLUT_BITMAP_TIMES_ROMAN_24)
    for i, line in enumerate(dialogue_lines):
        draw_text(box_left + 20, box_top - 62 - i * line_h, line)
    draw_text(box_left + 20, box_bottom + 12, "Press F to close")
    glEnable(GL_DEPTH_TEST)


# ============================================================
#  UI: top-right buttons, notebook, how-to-play, accusation,
#      game-over / win screens
# ============================================================
def get_ui_buttons():
    w, h, gap = 140, 34, 10
    top = WINDOW_H - 20
    bottom = top - h
    x2 = WINDOW_W - 20
    buttons = []
    for bid, label in (('accuse', 'Accuse!'), ('notebook', 'Notebook'), ('map', 'Map'), ('howto', 'How to Play')):
        x1 = x2 - w
        buttons.append({'id': bid, 'label': label, 'x1': x1, 'y1': bottom, 'x2': x2, 'y2': top})
        x2 = x1 - gap
    return list(reversed(buttons))


def _hit(px, py, r):
    return r['x1'] <= px <= r['x2'] and r['y1'] <= py <= r['y2']


def draw_ui_buttons():
    if ui_mode != 'none':
        return
    buttons = get_ui_buttons()
    glDisable(GL_DEPTH_TEST)
    for b in buttons:
        _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.20, 0.20, 0.26))
        _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.75, 0.70, 0.55), filled=False)
    for b in buttons:
        w = text_width(b['label'])
        draw_text((b['x1'] + b['x2']) / 2.0 - w / 2.0, (b['y1'] + b['y2']) / 2.0 - 6, b['label'])
    glEnable(GL_DEPTH_TEST)


def draw_centered_panel(width, height, title, lines, footer=None, title_font=GLUT_BITMAP_TIMES_ROMAN_24,
                         fill_color=(0.05, 0.05, 0.08), border_color=(0.85, 0.75, 0.35)):
    """Shared frame for the how-to/notebook/game-over/win screens: a
    centered box with a title, a block of pre-wrapped lines, and an
    optional footer line. Returns the box's screen-space rectangle so
    callers (like the accusation panel) can lay additional widgets over it."""
    cx, cy = WINDOW_W / 2.0, WINDOW_H / 2.0
    x1, x2 = cx - width / 2.0, cx + width / 2.0
    y1, y2 = cy - height / 2.0, cy + height / 2.0

    glDisable(GL_DEPTH_TEST)
    _draw_panel_rect(x1, y1, x2, y2, fill_color)
    _draw_panel_rect(x1, y1, x2, y2, border_color, filled=False)

    title_w = text_width(title, title_font)
    draw_text(cx - title_w / 2.0, y2 - 40, title, title_font)

    line_h = 22
    for i, line in enumerate(lines):
        line_w = text_width(line)
        draw_text(cx - line_w / 2.0, y2 - 78 - i * line_h, line)

    if footer:
        footer_w = text_width(footer)
        draw_text(cx - footer_w / 2.0, y1 + 18, footer)
    glEnable(GL_DEPTH_TEST)

    return {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}


def draw_howto_panel():
    lines = [
        "WASD walks your detective in any direction - they automatically turn",
        "to face the way you're moving. The camera stays free - arrow keys",
        "orbit it, and PgUp / PgDn zoom in and out.",
        "",
        "Right-click for a first-person view through the detective's own",
        "eyes - controls switch there too: W/S step forward and backward,",
        "A/D or Left/Right turn where you're facing. Up/Down tilts your view,",
        "and in this mode you have to actually be looking at a clue - facing",
        "it and tilted toward its real height - to examine it, not just",
        "standing near it. A letter down in a wastebasket needs you looking",
        "down at it, for instance.",
        "",
        "Walk up to a doorway and press F to step through into the next room -",
        "check the Map for how they connect. Number keys 1-5 also jump straight",
        "to any room if you'd rather skip the walk.",
        "",
        "Walk up to a clue or a member of the household and press F to",
        "examine it or start a conversation.",
        "",
        "Press V to toggle detective mode - any clue within reach starts",
        "flickering yellow so you don't have to search a room blind.",
        "",
        "Open your Notebook any time to review what you've found. When you're",
        "ready, click Accuse! and name the culprit - you only get one guess.",
    ]
    draw_centered_panel(700, 700, "How to Play", lines, footer="Click anywhere to close")


def draw_notebook_panel():
    lines = []
    for c in CLUES:
        if c['name'] in collected_clues:
            lines.extend(wrap_text("* %s - %s" % (c['name'], c['text']), 78))
        else:
            lines.append("* ??? (not yet examined)")

    # Sized to the actual content (all 11 clues collected wraps to roughly
    # this many lines), capped so it can never run off the bottom of the window.
    height = min(WINDOW_H - 60, 160 + 22 * len(lines))
    title = "Detective's Notebook  (%d/%d clues found)" % (len(collected_clues), len(CLUES))
    draw_centered_panel(780, height, title, lines, footer="Click anywhere to close")


def get_room_characters(room_id):
    return [c['name'] for c in CHARACTERS if c['room'] == room_id]


def draw_map_panel():
    """A hub-and-spoke floor plan: the Hallway connects to every other room,
    one per side, matching its actual wall openings - north to the Bedroom,
    south to the Parlor, east to the Study, west to the Dining Room."""
    width, height = 780, 580
    cx, cy = WINDOW_W / 2.0, WINDOW_H / 2.0
    x1, x2 = cx - width / 2.0, cx + width / 2.0
    y1, y2 = cy - height / 2.0, cy + height / 2.0
    map_cy = cy - 30

    hub = (cx, map_cy)
    spokes = [
        (ROOM_BEDROOM, "5: Toby's Bedroom", (cx, map_cy + 180)),
        (ROOM_PARLOR, "3: The Parlor", (cx, map_cy - 180)),
        (ROOM_STUDY, "1: The Study", (cx + 240, map_cy)),
        (ROOM_DINING, "4: The Dining Room", (cx - 240, map_cy)),
    ]
    box_w, box_h = 170, 64

    glDisable(GL_DEPTH_TEST)

    _draw_panel_rect(x1, y1, x2, y2, (0.05, 0.05, 0.08))
    _draw_panel_rect(x1, y1, x2, y2, (0.85, 0.75, 0.35), filled=False)

    # Connector lines from the Hallway hub out to every other room
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(0.55, 0.55, 0.48)
    glBegin(GL_LINES)
    for _, _, pos in spokes:
        glVertex2f(hub[0], hub[1])
        glVertex2f(pos[0], pos[1])
    glEnd()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    def draw_room_box(box_cx, box_cy, label, room_id):
        bx1, bx2 = box_cx - box_w / 2.0, box_cx + box_w / 2.0
        by1, by2 = box_cy - box_h / 2.0, box_cy + box_h / 2.0
        fill = (0.30, 0.27, 0.12) if room_id == current_room else (0.16, 0.16, 0.20)
        _draw_panel_rect(bx1, by1, bx2, by2, fill)
        _draw_panel_rect(bx1, by1, bx2, by2, (0.75, 0.70, 0.55), filled=False)

        lw = text_width(label)
        draw_text(box_cx - lw / 2.0, box_cy + 12, label)

        names = get_room_characters(room_id)
        name_text = ", ".join(names) if names else "(no one here)"
        for i, line in enumerate(wrap_text(name_text, 24)):
            nw = text_width(line, GLUT_BITMAP_HELVETICA_10)
            draw_text(box_cx - nw / 2.0, box_cy - 6 - i * 13, line, GLUT_BITMAP_HELVETICA_10)

    draw_room_box(hub[0], hub[1], "2: The Hallway", ROOM_HALLWAY)
    for room_id, label, pos in spokes:
        draw_room_box(pos[0], pos[1], label, room_id)

    title = "Ashcombe House"
    tw = text_width(title, GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(cx - tw / 2.0, y2 - 38, title, GLUT_BITMAP_TIMES_ROMAN_24)

    footer = "Click anywhere to close"
    fw = text_width(footer)
    draw_text(cx - fw / 2.0, y1 + 16, footer)

    glEnable(GL_DEPTH_TEST)


def get_accuse_rows():
    row_w, row_h, gap = 340, 36, 8
    cx = WINDOW_W / 2.0
    top = WINDOW_H / 2.0 + 150
    rows = []
    y = top
    for name in SUSPECTS:
        rows.append({'name': name, 'x1': cx - row_w / 2.0, 'x2': cx + row_w / 2.0,
                     'y1': y - row_h, 'y2': y})
        y -= (row_h + gap)
    return rows


def draw_accuse_panel():
    panel = draw_centered_panel(500, 560, "Who is the culprit?", [],
                                 footer="Click outside this box to cancel")

    rows = get_accuse_rows()
    glDisable(GL_DEPTH_TEST)
    for r in rows:
        _draw_panel_rect(r['x1'], r['y1'], r['x2'], r['y2'], (0.16, 0.16, 0.20))
        _draw_panel_rect(r['x1'], r['y1'], r['x2'], r['y2'], (0.6, 0.6, 0.55), filled=False)
    for r in rows:
        w = text_width(r['name'])
        draw_text((r['x1'] + r['x2']) / 2.0 - w / 2.0, (r['y1'] + r['y2']) / 2.0 - 6, r['name'])
    glEnable(GL_DEPTH_TEST)
    return panel


def draw_incomplete_panel():
    found, total = len(collected_clues), len(CLUES)
    lines = [
        "You haven't found every clue yet.",
        "",
        "%d of %d clues logged in your notebook. Keep investigating the" % (found, total),
        "house before you name a culprit - you only get one accusation.",
    ]
    draw_centered_panel(620, 320, "Not So Fast", lines, footer="Click anywhere to close")


def draw_title_panel():
    """The very first thing shown - a full-window title card, click anywhere
    to move on to the story setup (draw_intro_panel)."""
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Full-window backdrop, dark navy fading down into a deep maroon - a
    # single quad with a different color per vertex, which OpenGL
    # interpolates across the surface on its own (no blending involved).
    glBegin(GL_QUADS)
    glColor3f(0.03, 0.03, 0.08)
    glVertex2f(0, WINDOW_H)
    glVertex2f(WINDOW_W, WINDOW_H)
    glColor3f(0.16, 0.05, 0.06)
    glVertex2f(WINDOW_W, 0)
    glVertex2f(0, 0)
    glEnd()

    # Double gold frame, inset from the window edges
    glColor3f(0.85, 0.75, 0.35)
    for inset in (26, 34):
        glBegin(GL_LINE_LOOP)
        glVertex2f(inset, inset)
        glVertex2f(WINDOW_W - inset, inset)
        glVertex2f(WINDOW_W - inset, WINDOW_H - inset)
        glVertex2f(inset, WINDOW_H - inset)
        glEnd()

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    cx = WINDOW_W / 2.0

    title = "THE ASHCOMBE MURDER"
    title_font = GLUT_BITMAP_TIMES_ROMAN_24
    title_y = WINDOW_H * 0.66
    tw = text_width(title, title_font)
    # A dark offset copy behind the gold text reads as a cheap embossed/bold
    # title, since the bitmap font itself has no bold variant.
    draw_text(cx - tw / 2.0 + 3, title_y - 3, title, title_font, color=(0.05, 0.04, 0.04))
    draw_text(cx - tw / 2.0, title_y, title, title_font, color=(0.88, 0.78, 0.38))

    subtitle = "A Locked-Room Mystery"
    sw = text_width(subtitle)
    draw_text(cx - sw / 2.0, title_y - 38, subtitle, color=(0.82, 0.80, 0.74))

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(0.5, 0.45, 0.3)
    glBegin(GL_LINES)
    glVertex2f(cx - 170, title_y - 58)
    glVertex2f(cx + 170, title_y - 58)
    glEnd()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    credit_lines = [
        ("Credits", (0.85, 0.75, 0.35)),
        ("Samin Mohammad Tashir Mahi", (0.78, 0.78, 0.78)),
    ]
    start_y = WINDOW_H * 0.40
    for i, (line, color) in enumerate(credit_lines):
        w = text_width(line)
        draw_text(cx - w / 2.0, start_y - i * 26, line, color=color)

    prompt = "Click anywhere to play"
    pw = text_width(prompt)
    draw_text(cx - pw / 2.0, WINDOW_H * 0.14, prompt, color=(0.85, 0.75, 0.35))

    glEnable(GL_DEPTH_TEST)


def get_start_button():
    cx = WINDOW_W / 2.0
    return {'x1': cx - 130, 'x2': cx + 130, 'y1': WINDOW_H / 2.0 - 260, 'y2': WINDOW_H / 2.0 - 216}


def draw_intro_panel():
    lines = [
        "Ashcombe House, November 1923.",
        "",
        "Cornelius Vane has been found dead in his locked study - the door",
        "bolted from the inside, the windows latched, no visible wound. A",
        "storm has washed out the only bridge to the mainland, trapping the",
        "household inside with whatever happened to him.",
        "",
        "You are Detective Eleanor Cray. Explore the house, examine every",
        "clue, and speak with everyone inside - then name the culprit.",
        "You only get one accusation, so choose carefully.",
    ]
    draw_centered_panel(720, 560, "Ashcombe House", lines, fill_color=(0.05, 0.05, 0.08),
                         border_color=(0.85, 0.75, 0.35))

    b = get_start_button()
    glDisable(GL_DEPTH_TEST)
    _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.20, 0.20, 0.26))
    _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.85, 0.75, 0.35), filled=False)
    w = text_width("Begin Investigation")
    draw_text((b['x1'] + b['x2']) / 2.0 - w / 2.0, (b['y1'] + b['y2']) / 2.0 - 6, "Begin Investigation")
    glEnable(GL_DEPTH_TEST)


def get_restart_button():
    cx = WINDOW_W / 2.0
    return {'x1': cx - 90, 'x2': cx + 90, 'y1': WINDOW_H / 2.0 - 220, 'y2': WINDOW_H / 2.0 - 180}


def draw_gameover_panel():
    lines = [
        "You accused %s." % accuse_result_name,
        "",
        "%s had nothing to do with Cornelius's death." % accuse_result_name,
        "The real killer is still out there, and the case is closed - wrongly.",
    ]
    draw_centered_panel(640, 440, "GAME OVER", lines, fill_color=(0.12, 0.03, 0.03),
                         border_color=(0.75, 0.25, 0.25))

    b = get_restart_button()
    glDisable(GL_DEPTH_TEST)
    _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.35, 0.12, 0.12))
    _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.85, 0.75, 0.35), filled=False)
    w = text_width("Restart")
    draw_text((b['x1'] + b['x2']) / 2.0 - w / 2.0, (b['y1'] + b['y2']) / 2.0 - 6, "Restart")
    glEnable(GL_DEPTH_TEST)


def draw_win_panel():
    lines = [
        "You were right. Dr. Julian Reyes rigged Toby's missing tarantula above",
        "Cornelius's chair with wax from his own therapy candles, then used the",
        "shared temperature panel to heat the Study by remote and melt it loose.",
        "Cornelius's fragile heart gave out from the shock - no blade, no poison,",
        "just the exact fear his therapy was supposed to cure.",
        "",
        "Reyes had been falsifying his billing for years, and Cornelius was two",
        "weeks from exposing him to the medical board.",
    ]
    draw_centered_panel(700, 440, "CASE CLOSED", lines, fill_color=(0.03, 0.10, 0.05),
                         border_color=(0.45, 0.80, 0.45))

    b = get_restart_button()
    glDisable(GL_DEPTH_TEST)
    _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.12, 0.30, 0.15))
    _draw_panel_rect(b['x1'], b['y1'], b['x2'], b['y2'], (0.75, 0.85, 0.35), filled=False)
    w = text_width("Play Again")
    draw_text((b['x1'] + b['x2']) / 2.0 - w / 2.0, (b['y1'] + b['y2']) / 2.0 - 6, "Play Again")
    glEnable(GL_DEPTH_TEST)


def submit_accusation(name):
    global ui_mode, accuse_result_name
    accuse_result_name = name
    ui_mode = 'win' if name == CULPRIT_NAME else 'gameover'


def restart_game():
    global ui_mode, dialogue_open
    ui_mode = 'none'
    dialogue_open = False
    collected_clues.clear()
    switch_room(ROOM_STUDY)


# ============================================================
#  Clues
# ============================================================

def draw_spider(x, z, base_y=0.0, scale=1.0):
    glPushMatrix()
    glTranslatef(x, base_y, z)
    glScalef(scale, scale, scale)

    body = (0.08, 0.07, 0.07)
    draw_sphere_at(0, 4, -3, 4.5, body)
    draw_sphere_at(0, 4, 2, 3, body)

    for ang in (30, 60, 90, 120):
        lx = 6 * math.cos(math.radians(ang))
        lz = 6 * math.sin(math.radians(ang))
        draw_box_at(lx, 3, lz - 2, 7, 0.8, 0.8, body)
        draw_box_at(-lx, 3, lz - 2, 7, 0.8, 0.8, body)

    glPopMatrix()


def draw_glass_shards(x, z):
    shard_color = (0.75, 0.88, 0.88)
    for ox, oz, rot, size in ((-6, 3, 20, 6), (4, -4, 70, 5), (6, 5, 140, 7), (-3, -6, 100, 5), (0, 1, 10, 6)):
        glPushMatrix()
        glTranslatef(x + ox, 0.6, z + oz)
        glRotatef(rot, 0, 1, 0)
        glColor3f(*shard_color)
        glScalef(size, 0.6, size * 0.5)
        glutSolidCube(1)
        glPopMatrix()


def draw_wax_drip(x, y, z):
    color = (0.88, 0.84, 0.65)
    draw_sphere_at(x, y, z, 2.2, color)
    draw_sphere_at(x + 1.5, y - 1.5, z, 1.4, color)
    draw_sphere_at(x - 1.0, y - 2.5, z + 0.5, 1.1, color)


def draw_candle_stub(x, z, base_y=0.0):
    draw_upright_cylinder(x, z, 3, 3, 6, (0.90, 0.87, 0.78), base_y=base_y)
    draw_sphere_at(x, base_y + 6.3, z, 0.6, (0.15, 0.15, 0.15))


def draw_case_folder(x, z, base_y=0.0):
    draw_box_at(x, base_y + 0.8, z, 22, 1.6, 16, (0.20, 0.45, 0.30))


def draw_ledger_book(x, z, base_y=0.0):
    draw_box_at(x, base_y + 1.5, z, 20, 3, 26, (0.25, 0.18, 0.12))
    draw_box_at(x, base_y + 3.1, z, 19, 0.4, 25, (0.92, 0.90, 0.85))
    draw_box_at(x - 9.4, base_y + 3.3, z, 0.8, 0.6, 25, (0.65, 0.10, 0.10))


def draw_folded_note(x, z, base_y=0.0):
    draw_box_at(x, base_y + 0.6, z, 14, 1.2, 10, (0.93, 0.92, 0.86))
    draw_box_at(x, base_y + 1.3, z - 1, 12, 1.0, 4, (0.90, 0.89, 0.83))


def _draw_shattered_tank():
    draw_glass_shards(35, 48)
    draw_spider(32, 40)


CLUES = [
    {'room': ROOM_STUDY, 'x': 80, 'z': 10, 'marker_y': 40, 'draw': None,
     'name': 'Crumpled Letter',
     'text': "A cardiologist's letter, balled up in the wastebasket: \"...any severe "
             "fright could trigger a fatal cardiac event.\" Cornelius never mentioned "
             "this to anyone in the house."},
    {'room': ROOM_STUDY, 'x': 25, 'z': -10, 'marker_y': 60, 'draw': None, 'radius': 65,
     'name': 'Teacup',
     'text': "The tea is still lukewarm - odd, since the room was cold when the body "
             "was found. Someone heated this room, then let it cool again."},
    {'room': ROOM_STUDY, 'x': 28, 'z': -52, 'marker_y': 58,
     'draw': lambda: draw_case_folder(28, -52, base_y=48),
     'name': "Reyes's Session Notes",
     'text': "Dr. Reyes's notes push hard for Cornelius to \"confront the fear "
             "directly.\" Professionally worded, but the timing is suspicious."},
    {'room': ROOM_STUDY, 'x': 5, 'z': -58, 'marker_y': 62,
     'draw': lambda: draw_candle_stub(5, -58, base_y=48),
     'name': 'Candle Stub',
     'text': "A half-burned candle - the same distinctive scent Dr. Reyes always "
             "brings to therapy sessions."},
    {'room': ROOM_STUDY, 'x': 20, 'z': 73, 'marker_y': 85,
     'draw': lambda: draw_wax_drip(20, 66, 73),
     'name': 'Wax Drip',
     'text': "A drip of pale wax on the chair's backrest, with a faint scorch mark "
             "above it. Something was fastened to the ceiling here and melted loose."},
    {'room': ROOM_STUDY, 'x': 33, 'z': 44, 'marker_y': 20,
     'draw': _draw_shattered_tank,
     'name': 'Shattered Tank & Spider',
     'text': "A shattered glass tank and a very much alive tarantula. This matches "
             "the pet Toby reported missing that morning."},
    {'room': ROOM_HALLWAY, 'x': 90, 'z': -55, 'marker_y': 75, 'draw': None, 'radius': 55,
     'ignore_distance_fp': True,
     'name': 'Temperature Panel',
     'text': "A shared control panel with a dial for every room in the house. "
             "Anyone could adjust the Study's temperature from here without "
             "raising suspicion."},
    {'room': ROOM_PARLOR, 'x': -130, 'z': 140, 'marker_y': 18,
     'draw': lambda: draw_ledger_book(-130, 140, base_y=0),
     'name': "Finch's Ledger",
     'text': "Aldous Finch's business ledger - the numbers don't add up. It looks "
             "like he's been skimming from the family company for years."},
    {'room': ROOM_DINING, 'x': 150, 'z': 170, 'marker_y': 16,
     'draw': lambda: draw_folded_note(150, 170, base_y=0),
     'name': "Desmond's IOU",
     'text': "A crumpled gambling debt note in Desmond's name. He argued with his "
             "father about money just yesterday."},
    {'room': ROOM_BEDROOM, 'x': -230, 'z': 90, 'marker_y': 55, 'draw': None,
     'name': 'Empty Terrarium Stand',
     'text': "The stand where Toby's tarantula tank used to sit. It's been empty "
             "since this morning."},
    {'room': ROOM_BEDROOM, 'x': 15, 'z': -55, 'marker_y': 16,
     'draw': lambda: draw_folded_note(15, -55, base_y=0),
     'name': "Toby's Checklist",
     'text': "A torn scrap listing every room Toby searched for his missing pet. "
             "The Study is checked off last."},
]


# Every doorway/archway that actually exists in the built rooms, matching
# the Map panel one-for-one: Study<->Hallway, and Hallway<->{Bedroom,
# Parlor, Dining Room} through its north door, south door, and west
# archway respectively. Each physical opening gets one entry per side.
DOORS = [
    # Study <-> Hallway (Study's south door / Hallway's east archway)
    {'room': ROOM_STUDY, 'x': -25, 'z': 235, 'label': 'the Hallway',
     'to_room': ROOM_HALLWAY, 'spawn_x': 340, 'spawn_z': 0, 'spawn_angle': -90},
    {'room': ROOM_HALLWAY, 'x': 355, 'z': 0, 'label': 'the Study',
     'to_room': ROOM_STUDY, 'spawn_x': -25, 'spawn_z': 210, 'spawn_angle': 180},

    # Hallway <-> Toby's Bedroom (Hallway's north door)
    {'room': ROOM_HALLWAY, 'x': -160, 'z': -60, 'label': "Toby's Bedroom",
     'to_room': ROOM_BEDROOM, 'spawn_x': 0, 'spawn_z': 180, 'spawn_angle': 180},
    {'room': ROOM_BEDROOM, 'x': 0, 'z': 210, 'label': 'the Hallway',
     'to_room': ROOM_HALLWAY, 'spawn_x': -160, 'spawn_z': -30, 'spawn_angle': 0},

    # Hallway <-> The Parlor (Hallway's south door)
    {'room': ROOM_HALLWAY, 'x': 90, 'z': 60, 'label': 'the Parlor',
     'to_room': ROOM_PARLOR, 'spawn_x': 0, 'spawn_z': 260, 'spawn_angle': 180},
    {'room': ROOM_PARLOR, 'x': 0, 'z': 290, 'label': 'the Hallway',
     'to_room': ROOM_HALLWAY, 'spawn_x': 90, 'spawn_z': 30, 'spawn_angle': 180},

    # Hallway <-> The Dining Room (Hallway's west archway)
    {'room': ROOM_HALLWAY, 'x': -355, 'z': 0, 'label': 'the Dining Room',
     'to_room': ROOM_DINING, 'spawn_x': 0, 'spawn_z': 220, 'spawn_angle': 180},
    {'room': ROOM_DINING, 'x': 0, 'z': 250, 'label': 'the Hallway',
     'to_room': ROOM_HALLWAY, 'spawn_x': -340, 'spawn_z': 15, 'spawn_angle': 90},
]


def draw_clue_highlight(x, y, z):
    """A small flickering yellow glow - only shown over nearby clues while
    detective mode is on. Built from gluSphere (already used
    elsewhere in this file) rather than any new primitive."""
    brightness = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(time.time() * 9.0))
    glPushMatrix()
    glColor3f(brightness, brightness * 0.85, brightness * 0.15)
    glTranslatef(x, y, z)
    glScalef(6.0, 6.0, 6.0)
    gluSphere(_quadric(), 1.0, 10, 10)
    glPopMatrix()


def draw_room_clues(room_id):
    for c in CLUES:
        if c['room'] != room_id:
            continue
        if c['draw']:
            c['draw']()
        if detective_mode and math.hypot(player_x - c['x'], player_z - c['z']) <= DETECTIVE_RANGE:
            draw_clue_highlight(c['x'], c['marker_y'], c['z'])


def draw_hud():
    """Kept deliberately minimal - controls now live behind the How to Play
    button instead of being permanently on screen."""
    room_names = {ROOM_STUDY: "Room 1: The Study", ROOM_HALLWAY: "Room 2: The Hallway",
                  ROOM_PARLOR: "Room 3: The Parlor", ROOM_DINING: "Room 4: The Dining Room",
                  ROOM_BEDROOM: "Room 5: Toby's Bedroom"}
    glDisable(GL_DEPTH_TEST)
    draw_text(20, WINDOW_H - 34, room_names[current_room])
    glEnable(GL_DEPTH_TEST)


# ============================================================
#  GLUT callbacks
# ============================================================
def display():
    glClearColor(0.05, 0.05, 0.08, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)

    glViewport(0, 0, WINDOW_W, WINDOW_H)
    setup_camera()

    if current_room == ROOM_STUDY:
        draw_study_scene()
    elif current_room == ROOM_HALLWAY:
        draw_hallway_scene()
    elif current_room == ROOM_PARLOR:
        draw_parlor_scene()
    elif current_room == ROOM_DINING:
        draw_dining_scene()
    else:
        draw_bedroom_scene()

    draw_room_clues(current_room)
    draw_room_npcs(current_room)
    draw_detective()

    draw_hud()
    draw_ui_buttons()

    if ui_mode == 'none':
        draw_interact_prompt()
        draw_dialogue_box()
    elif ui_mode == 'howto':
        draw_howto_panel()
    elif ui_mode == 'notebook':
        draw_notebook_panel()
    elif ui_mode == 'map':
        draw_map_panel()
    elif ui_mode == 'incomplete':
        draw_incomplete_panel()
    elif ui_mode == 'accuse':
        draw_accuse_panel()
    elif ui_mode == 'gameover':
        draw_gameover_panel()
    elif ui_mode == 'win':
        draw_win_panel()
    elif ui_mode == 'intro':
        draw_intro_panel()
    elif ui_mode == 'title':
        draw_title_panel()

    glutSwapBuffers()


def idle():
    update_player()
    update_interactions()
    glutPostRedisplay()


def _apply_room_camera_defaults(room_id):
    global camera_azimuth, camera_elevation, camera_distance, camera_target
    defaults = ROOM_CAMERA_DEFAULTS[room_id]
    camera_azimuth = defaults['azimuth']
    camera_elevation = defaults['elevation']
    camera_distance = defaults['distance']
    camera_target = defaults['target']


def switch_room(room_id):
    """Fast-travel via the number keys - drops the detective at that room's
    generic (furniture-clear) spawn point rather than a specific doorway."""
    global current_room, player_x, player_z, player_angle, dialogue_open, look_pitch
    current_room = room_id
    player_x, player_z, player_angle = ROOM_SPAWN[room_id]
    dialogue_open = False
    look_pitch = 0.0
    _apply_room_camera_defaults(room_id)


def travel_through_door(door):
    """Walking through an actual doorway - arrives just inside the matching
    door on the other side, facing into that room."""
    global current_room, player_x, player_z, player_angle, dialogue_open, look_pitch
    current_room = door['to_room']
    player_x, player_z, player_angle = door['spawn_x'], door['spawn_z'], door['spawn_angle']
    dialogue_open = False
    look_pitch = 0.0
    _apply_room_camera_defaults(current_room)


def keyboard(key, x, y):
    global dialogue_open, dialogue_title, dialogue_lines, ui_mode, detective_mode

    if key == b'\x1b':  # Esc
        # No programmatic quit - closing the window itself is the only way
        # out. Esc still closes whatever dialogue/panel is currently open.
        if dialogue_open:
            dialogue_open = False
        elif ui_mode == 'gameover':
            restart_game()
        elif ui_mode != 'none':
            ui_mode = 'none'
        glutPostRedisplay()
        return

    if ui_mode != 'none':
        return  # modal screens are mouse-driven; only Esc affects them from the keyboard

    if key == b'f':
        if dialogue_open:
            dialogue_open = False
        elif active_interactable is not None:
            if active_interactable['type'] == 'door':
                travel_through_door(active_interactable['door'])
            else:
                dialogue_open = True
                dialogue_title = active_interactable['name']
                dialogue_lines = wrap_text(active_interactable['text'])
                if active_interactable['type'] == 'clue':
                    collected_clues.add(active_interactable['name'])
        glutPostRedisplay()
        return

    if dialogue_open:
        return  # ignore movement/room-switch keys while a dialogue is open

    if key == b'1':
        switch_room(ROOM_STUDY)
    if key == b'2':
        switch_room(ROOM_HALLWAY)
    if key == b'3':
        switch_room(ROOM_PARLOR)
    if key == b'4':
        switch_room(ROOM_DINING)
    if key == b'5':
        switch_room(ROOM_BEDROOM)
    if key == b'v':
        detective_mode = not detective_mode
    if key == b'n':
        # Debug/demo shortcut: simulate a completed investigation so the
        # Accuse gate (which normally requires every clue) opens right away.
        collected_clues.update(c['name'] for c in CLUES)
    if first_person:
        if key == b'w':
            fp_move_player(1.0)
        elif key == b's':
            fp_move_player(-1.0)
        elif key == b'a':
            fp_turn_player(1.0)
        elif key == b'd':
            fp_turn_player(-1.0)
    elif key in (b'w', b'a', b's', b'd'):
        note_key_down(key)
    glutPostRedisplay()


def special_keys(key, x, y):
    global camera_azimuth, camera_elevation, camera_distance, look_pitch

    if first_person:
        if key == GLUT_KEY_LEFT:
            fp_turn_player(1.0)     # same rotation as 'a' - no separate look heading
        if key == GLUT_KEY_RIGHT:
            fp_turn_player(-1.0)    # same rotation as 'd'
        if key == GLUT_KEY_UP:
            look_pitch = min(LOOK_PITCH_MAX, look_pitch + LOOK_PITCH_STEP)
        if key == GLUT_KEY_DOWN:
            look_pitch = max(LOOK_PITCH_MIN, look_pitch - LOOK_PITCH_STEP)
        glutPostRedisplay()
        return

    if key == GLUT_KEY_LEFT:
        camera_azimuth = (camera_azimuth - AZIMUTH_STEP) % 360.0
    if key == GLUT_KEY_RIGHT:
        camera_azimuth = (camera_azimuth + AZIMUTH_STEP) % 360.0
    if key == GLUT_KEY_UP:
        camera_elevation = min(ELEVATION_MAX, camera_elevation + ELEVATION_STEP)
    if key == GLUT_KEY_DOWN:
        camera_elevation = max(ELEVATION_MIN, camera_elevation - ELEVATION_STEP)
    if key == GLUT_KEY_PAGE_UP:
        camera_distance = max(DISTANCE_MIN, camera_distance - ZOOM_STEP)
    if key == GLUT_KEY_PAGE_DOWN:
        camera_distance = min(DISTANCE_MAX, camera_distance + ZOOM_STEP)

    glutPostRedisplay()


def mouse(button, state, x, y):
    global ui_mode, first_person, look_pitch

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person
        look_pitch = 0.0  # start each first-person session looking level
        glutPostRedisplay()
        return

    if button != GLUT_LEFT_BUTTON or state != GLUT_DOWN:
        return
    if dialogue_open:
        return  # close that with F/Esc first

    gl_x, gl_y = x, WINDOW_H - y  # GLUT gives top-left-origin pixels; our UI is bottom-left-origin

    if ui_mode == 'title':
        ui_mode = 'intro'  # any click moves on to the story setup
        return

    if ui_mode == 'intro':
        if _hit(gl_x, gl_y, get_start_button()):
            ui_mode = 'none'
        return

    if ui_mode == 'gameover' or ui_mode == 'win':
        if _hit(gl_x, gl_y, get_restart_button()):
            restart_game()
        return

    if ui_mode == 'accuse':
        panel = {'x1': WINDOW_W / 2.0 - 250, 'y1': WINDOW_H / 2.0 - 280,
                 'x2': WINDOW_W / 2.0 + 250, 'y2': WINDOW_H / 2.0 + 280}
        for row in get_accuse_rows():
            if _hit(gl_x, gl_y, row):
                submit_accusation(row['name'])
                return
        if not _hit(gl_x, gl_y, panel):
            ui_mode = 'none'
        return

    if ui_mode in ('howto', 'notebook', 'map', 'incomplete'):
        ui_mode = 'none'  # any of these panels closes on any click
        return

    for b in get_ui_buttons():
        if _hit(gl_x, gl_y, b):
            if b['id'] == 'accuse' and len(collected_clues) < len(CLUES):
                ui_mode = 'incomplete'
            else:
                ui_mode = b['id']
            return


def reshape(w, h):
    global WINDOW_W, WINDOW_H
    WINDOW_W, WINDOW_H = max(w, 1), max(h, 1)
    glViewport(0, 0, WINDOW_W, WINDOW_H)


# ============================================================
#  Main
# ============================================================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(WINDOW_TITLE)

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)

    glEnable(GL_DEPTH_TEST)

    glutMainLoop()


if __name__ == "__main__":
    main()
