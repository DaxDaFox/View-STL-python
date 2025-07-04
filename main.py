import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import tkinter as tk
from tkinter import filedialog
from stl import mesh
import numpy as np
import os


CAM_HEIGHT = 1.6
MOVE_SPEED = 0.1
RUN_MULTIPLIER = 2.0
MOUSE_SENSITIVITY = 0.1

pygame.init()
screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D STL Viewer")

gui_surface = pygame.Surface((800, 600), pygame.SRCALPHA)

pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

camera_pos = [0.0, CAM_HEIGHT, 5.0]
camera_rot = [0.0, 0.0]
fov = 75
clock = pygame.time.Clock()

slider_rect = pygame.Rect(20, 570, 200, 10)
slider_handle_x = 20 + (fov - 30) * (200 / 120)
slider_dragging = False
show_mouse = False
font = pygame.font.SysFont("Arial", 16)


model = None
model_display_list = None

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Select STL file", filetypes=[("STL files", "*.stl")])
if file_path and os.path.exists(file_path):
    model = mesh.Mesh.from_file(file_path)
else:
    model = None
    print("No STL selected. Using fallback cube room.")

def generate_model_display_list():
    global model_display_list
    if not model:
        return
    model_display_list = glGenLists(1)
    glNewList(model_display_list, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for triangle in model.vectors:
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        normal = normal / np.linalg.norm(normal) if np.linalg.norm(normal) > 0 else normal
        color = [(normal[0] + 1) / 2, (normal[1] + 1) / 2, (normal[2] + 1) / 2]
        glColor3fv(color)
        for vertex in triangle:
            scaled_vertex = vertex * 0.05
            glVertex3fv(scaled_vertex)
    glEnd()
    glEndList()

def draw_model():
    if model_display_list:
        glCallList(model_display_list)

def draw_fallback_room():
    ROOM_SIZE = 10
    glBegin(GL_QUADS)
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(-ROOM_SIZE, 0, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, 0, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, 0, ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, 0, ROOM_SIZE)

    glVertex3f(-ROOM_SIZE, ROOM_SIZE, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, ROOM_SIZE, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, ROOM_SIZE, ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, ROOM_SIZE, ROOM_SIZE)

    glColor3f(1, 0, 0)
    glVertex3f(-ROOM_SIZE, 0, -ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, ROOM_SIZE, -ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, ROOM_SIZE, ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, 0, ROOM_SIZE)

    glVertex3f(ROOM_SIZE, 0, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, ROOM_SIZE, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, ROOM_SIZE, ROOM_SIZE)
    glVertex3f(ROOM_SIZE, 0, ROOM_SIZE)

    glColor3f(0, 1, 0)
    glVertex3f(-ROOM_SIZE, 0, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, 0, -ROOM_SIZE)
    glVertex3f(ROOM_SIZE, ROOM_SIZE, -ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, ROOM_SIZE, -ROOM_SIZE)

    glVertex3f(-ROOM_SIZE, 0, ROOM_SIZE)
    glVertex3f(ROOM_SIZE, 0, ROOM_SIZE)
    glVertex3f(ROOM_SIZE, ROOM_SIZE, ROOM_SIZE)
    glVertex3f(-ROOM_SIZE, ROOM_SIZE, ROOM_SIZE)
    glEnd()

def update_camera():
    glLoadIdentity()
    glRotatef(camera_rot[0], 1, 0, 0)
    glRotatef(-camera_rot[1], 0, 1, 0)
    glTranslatef(-camera_pos[0], -camera_pos[1], -camera_pos[2])

if model:
    generate_model_display_list()

glEnable(GL_DEPTH_TEST)

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            quit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == K_q:
                show_mouse = not show_mouse
                pygame.mouse.set_visible(show_mouse)
                pygame.event.set_grab(not show_mouse)
        if event.type == MOUSEBUTTONDOWN and show_mouse:
            if slider_rect.collidepoint(event.pos):
                slider_dragging = True
        if event.type == MOUSEBUTTONUP:
            slider_dragging = False
        if event.type == MOUSEMOTION and slider_dragging:
            slider_handle_x = max(slider_rect.left, min(event.pos[0], slider_rect.right))
            fov = 30 + ((slider_handle_x - slider_rect.left) / slider_rect.width) * 120

    if not show_mouse:
        mx, my = pygame.mouse.get_rel()
        camera_rot[1] -= mx * MOUSE_SENSITIVITY
        camera_rot[0] += my * MOUSE_SENSITIVITY
        camera_rot[0] = max(-89, min(89, camera_rot[0]))

    keys = pygame.key.get_pressed()
    move_dir = [0.0, 0.0, 0.0]
    angle_rad = math.radians(-camera_rot[1])
    forward = [math.sin(angle_rad), 0, -math.cos(angle_rad)]
    right = [math.cos(angle_rad), 0, math.sin(angle_rad)]

    speed = MOVE_SPEED * (RUN_MULTIPLIER if keys[K_LSHIFT] or keys[K_RSHIFT] else 1)

    if keys[K_w]: move_dir[0] += forward[0]; move_dir[2] += forward[2]
    if keys[K_s]: move_dir[0] -= forward[0]; move_dir[2] -= forward[2]
    if keys[K_a]: move_dir[0] -= right[0]; move_dir[2] -= right[2]
    if keys[K_d]: move_dir[0] += right[0]; move_dir[2] += right[2]


    left_click_held = pygame.mouse.get_pressed()[0]
    right_click_held = pygame.mouse.get_pressed()[2]

    if left_click_held:
        camera_pos[1] -= MOVE_SPEED  
    if right_click_held:
        camera_pos[1] += MOVE_SPEED  

    length = math.sqrt(move_dir[0] ** 2 + move_dir[2] ** 2)
    if length > 0:
        move_dir[0] = move_dir[0] / length * speed
        move_dir[2] = move_dir[2] / length * speed

    camera_pos[0] += move_dir[0]
    camera_pos[2] += move_dir[2]

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, 800 / 600, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    update_camera()

    if model:
        draw_model()
    else:
        draw_fallback_room()

    if show_mouse:
        gui_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(gui_surface, (180, 180, 180, 200), slider_rect)
        pygame.draw.circle(gui_surface, (255, 255, 255), (int(slider_handle_x), slider_rect.centery), 8)
        label = font.render(f"FOV: {int(fov)}", True, (255, 255, 255))
        gui_surface.blit(label, (slider_rect.left, slider_rect.top - 20))
        screen.blit(gui_surface, (0, 0))

    pygame.display.flip()
