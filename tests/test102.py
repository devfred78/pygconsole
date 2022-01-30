# -*- coding: utf-8 -*-

"""
	'io' test set : tests regarding the pygconsole.io submodule
	Test 102 : Display a message in all supported colours.
	ESCAPE Key to exit.
"""


# Standard modules
#-----------------
import sys
import os
from collections import namedtuple
import logging

# Third party modules
#--------------------
import pygame
from pygame.locals import *
from colorlog import ColoredFormatter

# Internal modules
#-----------------
if __name__ == '__main__':
	sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
	import pygconsole
else:
	from .. import pygconsole

# namedtuples
#------------
Coordinates = namedtuple("Coordinates", "x y")
Colour = namedtuple("Colour", "red green blue alpha")

# Global constants
#-----------------
RESOURCE_DIR = os.path.join(os.path.dirname(__file__),"resources") # directory where graphical resources are stored
BACKGROUND_IMAGE = os.path.join(RESOURCE_DIR,"background.jpg") # Background image
FONT = None # Font displayed outside of the console (None = default pygame font)

DISPLAY_SIZE = Coordinates(1920,1080) # screen resolution
CONSOLE_COORDINATES = Coordinates(1000,620) # upper left corner coordinates of the console
FRAMERATE = 50 # Maximum number of displaying loops per second

FONT_SIZE = 40 # size of the font displayed on the screen, but out of the console
FONT_COLOUR = Colour(255,0,0,255) # Colour of the font displayed outside of the console
TEXT_COORDINATES = Coordinates(50,50) # Coordinates of the first line of the text displayed outside of the console

TEXT_LIST = [
	"Test 102: Display a message in coloured characters.",
	"press 'A' to write `Hello world !` at the cursor position,",
	"with a colour changing cyclicly.",
	"ESCAPE key to exit."
			]

COLOUR_LIST = ['\x1b[30m','\x1b[31m','\x1b[32m','\x1b[33m','\x1b[34m','\x1b[35m','\x1b[36m','\x1b[37m',
				'\x1b[90m','\x1b[91m','\x1b[92m','\x1b[93m','\x1b[94m','\x1b[95m','\x1b[96m','\x1b[97m']


# Dataclasses
#------------

# Classes
#--------


# Functions
#----------


# Main function
#--------------
def main():
	""" Main program execution"""
	
	# Logging initialization
	formatter = ColoredFormatter(
			'%(log_color)s[%(asctime)s][%(levelname)s][%(name)s]:%(message)s',
			datefmt='%Y-%m-%d %H:%M:%S',
			reset=True,
			log_colors={
					'DEBUG':	'cyan',
					'INFO':		'green',
					'WARNING':	'yellow',
					'ERROR':	'red',
					'CRITICAL':	'red,bg_white'
			},
			secondary_log_colors={},
			style='%'
		)
	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('display')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	
	
	# screen initialization
	pygame.init()
	clock = pygame.time.Clock() # timer to control framerate
	flags = FULLSCREEN|SCALED|DOUBLEBUF
	screen_surface = pygame.display.set_mode(size=DISPLAY_SIZE,flags=flags)
	background_surface = pygame.image.load(BACKGROUND_IMAGE)
	
	# Font initialization
	font = pygame.font.Font(FONT,FONT_SIZE)
	line_space = font.get_linesize()
	
	# console initialization
	console = pygconsole.console.Console.get_console(name="pygame_console",logger = log)
	iotextstream = pygconsole.io.TextIOConsoleWrapper(console_name="pygame_console", newline='\r\n', line_buffering=True)
	coloured_index = 0
	
	# Displaying loop
	while True:
		clock.tick(FRAMERATE)
		
		# Events
		for event in pygame.event.get():
			if event.type == QUIT: sys.exit()
			if event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					sys.exit()
				elif event.key == K_RETURN:
					print("", file=iotextstream, flush=True) # New line
				elif event.key == K_a:
					print(COLOUR_LIST[coloured_index] + "Hello world !", file=iotextstream, flush=True) # Print 'Hello World !' in colour
					coloured_index += 1
					if coloured_index >= len(COLOUR_LIST): coloured_index = 0
		
		# Background display
		screen_surface.blit(background_surface,(0,0))
		
		# Text display
		text_line_coordinates = TEXT_COORDINATES
		for text_line in TEXT_LIST:
			text_surface = font.render(text_line,True,FONT_COLOUR)
			screen_surface.blit(text_surface,text_line_coordinates)
			text_line_coordinates = text_line_coordinates._replace(y=text_line_coordinates.y+line_space)
		
		# Console display
		screen_surface.blit(console.surface,CONSOLE_COORDINATES)
		
		# Screen rendering
		pygame.display.flip()


# Main program,
# running only if the module is NOT imported (but directly executed)
#-------------------------------------------------------------------
if __name__ == '__main__':
	main()
	