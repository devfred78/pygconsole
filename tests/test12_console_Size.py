# -*- coding: utf-8 -*-

"""
	'console' test set : tests regarding only the pygconsole.console submodule
	Test 12 : Test console sizes.
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
CONSOLE_COORDINATES = Coordinates(700,100) # upper left corner coordinates of the console
FRAMERATE = 50 # Maximum number of displaying loops per second

FONT_SIZE = 40 # size of the font displayed on the screen, but out of the console
FONT_COLOUR = Colour(255,0,0,255) # Colour of the font displayed outside of the console
TEXT_COORDINATES = Coordinates(50,50) # Coordinates of the first line of the text displayed outside of the console
CONSOLE_DEFAULT_FONT_SIZE = 10 # Default font size displayed on the console
CONSOLE_DEFAULT_WIDTH = 80 # Default width of the console, in characters
CONSOLE_DEFAULT_HEIGHT = 24 # Default height of the console, in characters

TEXT_LIST = [
	"Test 12:  Test console sizes",
	"Press '+' to increase font size",
	"Press '-' to decrease size",
	"Press 'UP or DOWN arrow' to change height",
	"Press 'LEFT or RIGHT arrow' to change width",
	"ESCAPE key to exit."
			]

LONG_TEXT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque vitae nunc dictum, sagittis elit venenatis, efficitur justo. Etiam suscipit, ipsum accumsan aliquam elementum, massa tellus pellentesque lacus, ut porttitor ligula tortor at urna. Duis eu felis non tortor bibendum ultrices. Aliquam tortor velit, suscipit faucibus nunc quis, blandit posuere leo. Donec dignissim aliquam lectus, vitae lacinia risus feugiat non. Curabitur dapibus, massa quis eleifend lobortis, nulla sem ullamcorper turpis, vel sodales risus orci non velit. Nam ac neque faucibus, consequat eros eu, viverra neque. Nulla vel blandit lorem. Nam interdum nisl non sem pretium dictum. Phasellus id sapien vitae ipsum efficitur fringilla. Quisque suscipit consequat erat quis commodo. Aenean tristique felis libero, et ultrices justo porttitor eget. Vivamus sit amet urna nibh. Ut ultrices nulla et dui eleifend, ut sagittis ipsum condimentum. Mauris nec dolor eget augue gravida lacinia. "

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
	console_font_size = CONSOLE_DEFAULT_FONT_SIZE
	console_width = CONSOLE_DEFAULT_WIDTH
	console_height = CONSOLE_DEFAULT_HEIGHT
	console = pygconsole.console.Console.get_console(name = f"console{console_font_size}", width = console_width, height = console_height, font_size = console_font_size, logger = log)
	console.add_char(LONG_TEXT)
	
	# Displaying loop
	while True:
		clock.tick(FRAMERATE)
		
		# Events
		for event in pygame.event.get():
			if event.type == QUIT: sys.exit()
			if event.type == KEYDOWN:
				if event.key == K_ESCAPE: sys.exit()
				elif event.key == K_PLUS or event.key == K_KP_PLUS:
					console_font_size += 1
					console = pygconsole.console.Console.get_console(name = f"console{console_font_size}", width = console_width, height = console_height, font_size = console_font_size, logger = log)
					# set dimensions again for consoles already initialized
					console.height = console_height
					console.width = console_width
					console.clear()
					console.add_char(LONG_TEXT)
				elif event.key == K_MINUS or event.key == K_KP_MINUS:
					console_font_size -= 1
					if console_font_size <= 0: console_font_size = 1
					console = pygconsole.console.Console.get_console(name = f"console{console_font_size}", width = console_width, height = console_height, font_size = console_font_size, logger = log)
					# set dimensions again for consoles already initialized
					console.height = console_height
					console.width = console_width
					console.clear()
					console.add_char(LONG_TEXT)
				elif event.key == K_UP:
					console_height += 1
					console.height = console_height
					console.add_char(LONG_TEXT)
				elif event.key == K_DOWN:
					console_height -= 1
					if console_height <= 0: console_height = 1
					console.height = console_height
					console.add_char(LONG_TEXT)
				elif event.key == K_RIGHT:
					console_width += 1
					console.width = console_width
					console.add_char(LONG_TEXT)
				elif event.key == K_LEFT:
					console_width -= 1
					if console_width <= 0: console_width = 1
					console.width = console_width
					console.add_char(LONG_TEXT)
		
		# Background display
		screen_surface.blit(background_surface,(0,0))
		
		# Text display
		text_line_coordinates = TEXT_COORDINATES
		for text_line in TEXT_LIST:
			text_surface = font.render(text_line,True,FONT_COLOUR)
			screen_surface.blit(text_surface,text_line_coordinates)
			text_line_coordinates = text_line_coordinates._replace(y=text_line_coordinates.y+line_space)
		# Additional line: level of opacity
		text_line = f"Font size: {console_font_size}"
		text_surface = font.render(text_line,True,FONT_COLOUR)
		screen_surface.blit(text_surface,text_line_coordinates)
		
		# Console display
		screen_surface.blit(console.surface,CONSOLE_COORDINATES)
		
		# Screen rendering
		pygame.display.flip()


# Main program,
# running only if the module is NOT imported (but directly executed)
#-------------------------------------------------------------------
if __name__ == '__main__':
	main()
	