
import time
import pygame

print("Starting...")
start = time.time()

print("Before init")
pygame.display.init()
pygame.font.init()
print("After init:", time.time() - start)

print("Before display")
screen = pygame.display.set_mode((800, 600))
print("After display:", time.time() - start)
