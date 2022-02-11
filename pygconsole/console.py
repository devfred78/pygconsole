# -*- coding: utf-8 -*-

"""
Module console : Terminal emulation onto a pygame display.
"""


# Standard modules
#------------------
import sys
import logging
import threading
from collections import namedtuple, deque
from dataclasses import dataclass
import io
import pkgutil

# Third party modules
#--------------------
import pygame
from pygame.locals import *
from colorlog import ColoredFormatter

# Internal modules
#-----------------
from pygconsole import RESOURCE_LOCATION

# Global constants
#-----------------

# namedtuples
#------------
Coordinates = namedtuple("Coordinates", "x y")
Colour = namedtuple("Colour", "red green blue alpha")

# Dataclasses
#------------
@dataclass
class CharArgs:
	"""
	Character caracteristics
	"""
	foreground_colour: Colour = Colour(255,255,255,255) # Font colour
	background_colour: Colour = Colour(0,0,0,255) # Background colour
	italic: bool = False # If True, character is italic (default is False)
	bold: bool = False # If True, character is bold (default is False)
	underline: bool = False # If True, character is underlined (default is False)
	str: str = " " # Character representation

# Classes
#--------
class Console():
	"""
	Console objects represent terminals that can be displayed onto any `pygame.Surface` object (in particular the display surface given by the `pygame.display.get_surface()` method).
	
	Note that this class should never be instantiated directly, but always through the `get_console()` static method. Multiple calls to `get_console()` with the same name will always return a reference to the same Console object.
	
	Once instantiated, a typical cycling use-case of the object is:
	- If necessary, modify attributes `italic`, `bold`, `underline`, `foreground_colour` or `background_colour` in accordance with the desired format to be rendered
	- Call the `add_char()` method to add a string onto the console display
	- Render the console screen onto the display by the use of the `surface` attribute in the Pygame display loop.
	
	In addition to this cycle, several other methods can be called for specific commands to the console, like `clear()` or `scroll()`.
	
	At last, a `logging.logger` object can be applied to facilitate status monitoring or fault investigation. In this case, the `create_log()` static method can be used to create a colorized, well-formed logger before calling `get_console()`. CAUTION: To prevent infinite loops, NEVER use the Console object to display its proper logger's outputs !
	
	Attributes
	----------
	log : logging.logger object
		logger used to track events that append when the instance is running (default is None).
	name : str
		the name of the console. Read-only attribute (default is the module name (eg: "pygconsole")).
	surface : pygame.Surface object
		represents the console rendering. Should be applied in the display loop. Read-only attribute.
	foreground_colour : namedtuple(red,green,blue,alpha)
		font colour that will be applied to the next printed character (default is `bright_white` (255,255,255,255)).
	background_colour : namedtuple(red,green,blue,alpha)
		background colour that will be applied to the next printed character (default is `black` (0,0,0,255)).
	font_transparency : int
		font transparency, using a value range of 0 (invisible) to 255 (opaque) inclusive (default 255).
	background_transparency : int
		Background transparency, using a value range of 0 (invisible) to 255 (opaque) inclusive (default 255).
	italic : bool
		gets or sets whether the font should be rendered in italics (default False).
	bold : bool
		gets or sets whether the font should be rendered in bold (default False).
	underline : bool
		gets or sets whether the font should be rendered with an underline (default False).
	memory_size : int
		amount of memorized characters (default 19200).
	 width : int
		console width, in characters (default 80).
	height : int
		console height, in characters (default 24).
	
	Static methods
	--------------
	get_console(name = __name__, width = 80, height = 24, font_size = 10, font_transparency = 255, background_transparency = 255, logger = None)
		Return a Console instance.
	create_log(name, level = logging.DEBUG, writestream = sys.stdout)
		Return a logger with the specified name, level and output stream.
	
	Methods
	-------
	add_char(char)
		Display one or several characters on the console, at the current cursor position.
	clear(mode = "all")
		Clear full or part of screen.
	scroll(nb_lines = 1, up = True)
		Vertical scrolling of the display.
	carriage_return()
		Move cursor to the first position of the current line.
	line_field()
		Move cursor to the corresponding character position of the following line.
	"""

	#############################################################
	# Class attributes
	
	DEFAULT_NORMAL_FONT = RESOURCE_LOCATION + "/fonts/DejaVu/DejaVuSansMono.ttf"
	DEFAULT_BOLD_FONT = RESOURCE_LOCATION + "/fonts/DejaVu/DejaVuSansMono-Bold.ttf"
	DEFAULT_ITALIC_FONT = RESOURCE_LOCATION + "/fonts/DejaVu/DejaVuSansMono-Oblique.ttf"
	DEFAULT_BOLDITALIC_FONT = RESOURCE_LOCATION + "/fonts/DejaVu/DejaVuSansMono-BoldOblique.ttf"
	DEFAULT_LICENCE_FONT = RESOURCE_LOCATION + "/fonts/DejaVu/LICENSE"
	DEFAULT_AUTHOR_FONT = RESOURCE_LOCATION + "/fonts/DejaVu/AUTHORS"
	# Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved. Bitstream Vera is a trademark of Bitstream, Inc.
	# https://dejavu-fonts.github.io/
	DEFAULT_ALPHA = 255 # Default console transparency (0=invisible, 255=opaque)
	DEFAULT_FOREGROUND_COLOUR = Colour(255,255,255,DEFAULT_ALPHA) # Default font colour
	DEFAULT_BACKGROUND_COLOUR = Colour(0,0,0,DEFAULT_ALPHA) # Default background colour
	DEFAULT_CHAR_MEMORY_SIZE = 80*24*10 # Default amount of memorized characters
	
	STANDARD_COLOURS = {
						'black':			Colour(0,0,0,DEFAULT_ALPHA),
						'red':				Colour(170,0,0,DEFAULT_ALPHA),
						'green':			Colour(0,170,0,DEFAULT_ALPHA),
						'yellow':			Colour(170,85,0,DEFAULT_ALPHA),
						'blue':				Colour(0,0,170,DEFAULT_ALPHA),
						'magenta':			Colour(170,0,170,DEFAULT_ALPHA),
						'cyan':				Colour(0,170,170,DEFAULT_ALPHA),
						'white':			Colour(170,170,170,DEFAULT_ALPHA),
						'bright_black':		Colour(85,85,85,DEFAULT_ALPHA),
						'bright_red':		Colour(255,85,85,DEFAULT_ALPHA),
						'bright_green':		Colour(85,255,85,DEFAULT_ALPHA),
						'bright_yellow':	Colour(255,255,85,DEFAULT_ALPHA),
						'bright_blue':		Colour(85,85,255,DEFAULT_ALPHA),
						'bright_magenta':	Colour(255,85,255,DEFAULT_ALPHA),
						'bright_cyan':		Colour(85,255,255,DEFAULT_ALPHA),
						'bright_white':		Colour(255,255,255,DEFAULT_ALPHA)
						}	
	
	_instances = dict()
	
	#############################################################
	# Static methods
	
	@staticmethod
	def get_console(name = __name__, width = 80, height = 24, font_size = 10, font_transparency = DEFAULT_ALPHA, background_transparency = DEFAULT_ALPHA, logger = None):
		"""
		Return a Console instance.
		
		If a new name is given, a new instance is created. All calls to this method with a given name return the same Console instance. in this case, other parameters are ignored.
		
		Parameters
		----------
		name : str, optional
			The name of the console. Default is the module name (eg: "pygconsole")
		width : int, optional
			The width of the console, in characters (default is 80).
		height : int, optional
			The height of the console, in characters (default is 24).
		font_size : int, optional
			The height of the font, in pixels (default is 10).
		font_transparency : int, optional
			The transparency of the font, using a value range of 0 to 255 inclusive. 0 means invisible, 255 means fully opaque (default is 255).
		background_transparency : int, optional
			The transparency of the background, using a value range of 0 to 255 inclusive. 0 means invisible, 255 means fully opaque (default is 255).
		logger : logging.Logger object, optional
			The parent logger used to track events that append when the instance is running. Mainly for status monitoring or fault investigation purposes. If None (the default), no event is tracked.
		"""
		if name not in Console._instances:
			with threading.Lock():
				if name not in Console._instances:
					if logger is None:
						log = Console.create_log(name, writestream = None)
					else:
						log = logger.getChild(name)
					
					Console(name,width,height,font_size,font_transparency,background_transparency,log)
					log.info("------------------------------")
					log.info(f"Creation of a new Console instance with the name '{name}'")
					log.info("Characteristics:")
					log.info(f"- dimensions (in chars) : {width}x{height}")
					log.info(f"- font size : {font_size}")
					log.info(f"- font transparency : {font_transparency}")
					log.info(f"- background transparency : {background_transparency}")
					log.info("------------------------------")
					log.debug(f"List of Console instances: {Console._instances}")
				else:
					Console._instances[name].log.info(f"Usage of the already instanciated console '{name}'")
					Console._instances[name].log.debug(f"List of Console instances: {Console._instances}")
		else:
			Console._instances[name].log.info(f"Usage of the already instanciated console '{name}'")
			Console._instances[name].log.debug(f"List of Console instances: {Console._instances}")
		
		return Console._instances[name]

	@staticmethod
	def create_log(name, level = logging.DEBUG, writestream = sys.stdout):
		"""
		Return a logger with the specified name, level and output stream.
		
		This method wraps the logging.getLogger() function, adding colorization for ECMA-48 compliant terminals (almost all modern terminals are concerned). Hence, all calls to this method with a given name return the same logger instance.
		
		Parameters
		----------
		name : str
			The name of the logger
		level : int, optional
			The threshold of the logger. Logging messages which are less severe than level will be ignored; logging messages which have severity level or higher will be emitted. See https://docs.python.org/3/library/logging.html#levels for the possible values (default is logging.DEBUG)
		writestream : writable text file-like object with buffering implementation, optional
			Output stream where logging messages should be printed. For instance, all subclasses of io.TextIOBase should be available. Can also be None. In this case, no logging messages will be printed. (default is sys.stdout).
		"""
		# Colorized formatter
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
		
		# Handler to specified output
		if writestream is None:
			handler = logging.NullHandler()
		else:
			handler = logging.StreamHandler(writestream)
		handler.setLevel(level)
		handler.setFormatter(formatter)
		
		# logging
		log = logging.getLogger(name)
		log.setLevel(level)
		log.addHandler(handler)
		
		return log
	
	#############################################################
	# Initialization
	
	def __init__(self, name = __name__, width = 80, height = 24, font_size = 10, font_transparency = DEFAULT_ALPHA, background_transparency = DEFAULT_ALPHA, logger = None):
		"""
		Parameters
		----------
		See get_console() method.
		"""
		if logger is None:
			self.log = self.create_log(name, writestream = None)
		else:
			self.log = logger
		
		if name not in Console._instances:
			# New instance recording
			Console._instances[name] = self
			
			# console carateristics recording
			self._width = width
			self._height = height
			self._font_size = font_size
			self._name = name
			self._font_transparency = font_transparency
			self._background_transparency = background_transparency
			
			# Console initialization
			self._init_console()
	
	def _init_console(self):
		"""
		Console initialization, with associated internal variables.
		"""
		# Pygame initialization
		if not pygame.get_init(): pygame.init()
		
		# Fonts initialization
		self._init_font(self._font_size)
		self._italic = False
		self._bold = False
		self._underline = False
		
		# Default colours initialization
		self._default_foreground_colour = Console.DEFAULT_FOREGROUND_COLOUR._replace(alpha = self.font_transparency)
		self._default_background_colour = Console.DEFAULT_BACKGROUND_COLOUR._replace(alpha = self.background_transparency)
		
		# Current colours initialization
		self._current_foreground_colour = Console.DEFAULT_FOREGROUND_COLOUR._replace(alpha = self.font_transparency)
		self._current_background_colour = Console.DEFAULT_BACKGROUND_COLOUR._replace(alpha = self.background_transparency)
		
		# pygame.Surface objects initialization
		char_width, char_height = self._normal_font.size(" ") # Works only with fixed-width fonts !
		surf_width = char_width * self._width
		surf_height = char_height * self._height
		self._current_surface = pygame.Surface((surf_width, surf_height), flags=SRCALPHA)
		with pygame.PixelArray(self._current_surface) as currentpxarray:
			currentpxarray[:] = pygame.Color(0, 0, 0, 0) # invisible surface by default
		self._previous_surface = self._current_surface.copy()
		
		# Presentation stream initialization
		self._char_memory_size = Console.DEFAULT_CHAR_MEMORY_SIZE
		self._presentation_stream = deque([None] * self._width * self._height, self._char_memory_size)
		
		# Other initializations
		self._cursor = 0 # Cursor position in the presentation stream (ie: the index where the next character will be added)
		self._start_window = 0 # First rendered character position in the presentation stream
		self._end_window = self._width * self._height - 1 # Last rendered character position in the presentation stream
		self._update_surface_lock = threading.Lock() # Protect the _current_surface object during its update
		
		# Initial surfaces populating
		self._render_all()
	
	def _init_font(self, font_size):
		"""
		Fonts initialization.
		
		Parameters
		----------
		font_size: int
			size of initialized fonts
		"""
		# get binary resources
		normal_font_bin = pkgutil.get_data(__name__, Console.DEFAULT_NORMAL_FONT)
		bold_font_bin = pkgutil.get_data(__name__, Console.DEFAULT_BOLD_FONT)
		italic_font_bin = pkgutil.get_data(__name__, Console.DEFAULT_ITALIC_FONT)
		bolditalic_font_bin = pkgutil.get_data(__name__, Console.DEFAULT_BOLDITALIC_FONT)
		
		# translate binaries into file-like objects
		normal_font_file = io.BytesIO(normal_font_bin)
		bold_font_file = io.BytesIO(bold_font_bin)
		italic_font_file = io.BytesIO(italic_font_bin)
		bolditalic_font_file = io.BytesIO(bolditalic_font_bin)
		
		# Creation of pygame.font.Font objects
		self._normal_font = pygame.font.Font(normal_font_file, font_size)
		self._bold_font = pygame.font.Font(bold_font_file, font_size)
		self._italic_font = pygame.font.Font(italic_font_file, font_size)
		self._bolditalic_font = pygame.font.Font(bolditalic_font_file, font_size)
		
	
	#############################################################
	# Private attributes

	def __repr__(self):
		"""
		"Official" String representation of the instance.
		"""
		return f"<Console '{self.name}' with dimensions {self.width}x{self.height}>"
	
	def __str__(self):
		"""
		"Informal" String representation of the instance.
		"""
		return f"Console instance called '{self.name}'"

	#############################################################
	# Public attributes
	
	@property
	def name(self):
		"""
		Name of the instance. Read-only attribute.
		"""
		return self._name
	
	@property
	def surface(self):
		"""
		pygame.Surface object representing the console rendering. Should be applied in the display loop. Read-only attribute.
		"""
		if self._update_surface_lock.locked(): return self._previous_surface
		else: return self._current_surface
	
	@property
	def foreground_colour(self):
		"""
		Font colour that will be applied to the next printed character.
		
		The return value is a namedtuple Colour "red green blue alpha".
		The value can be set using one of the following formats:
			- namedtuple Colour
			- tuple (red, green, blue, alpha) (each element is an int in the range of 0 to 255 inclusive)
			- tuple (red, green, blue) (each element is an int in the range of 0 to 255 inclusive)
			- string 'default': font default colour
			- string among the following: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
		if none of these formats is used, the attribute remains unchanged.
		"""
		return self._current_foreground_colour
	
	@foreground_colour.setter
	def foreground_colour(self, value):
		if isinstance(value, str):
			if value in Console.STANDARD_COLOURS:
				self._current_foreground_colour = Console.STANDARD_COLOURS[value]._replace(alpha = self.font_transparency)
				self.log.debug(f"The font colour is set to {value}.")
			elif value == 'default':
				self._current_foreground_colour = self._default_foreground_colour._replace(alpha = self.font_transparency)
				self.log.debug(f"The font colour is set to {value}.")
		elif len(value) == 4:
			if -1 < value[0] < 256 and -1 < value[1] < 256 and -1 < value[2] < 256 and -1 < value[3] < 256:
				self._current_foreground_colour = Colour._make(value)
				self.font_transparency = value[3]
				self.log.debug(f"The font colour is set to {value}.")
			else: self.log.warning(f"{value} cannot be applied to a foreground colour. The previous value is kept: {self._current_foreground_colour}")
		elif len(value) == 3:
			if -1 < value[0] < 256 and -1 < value[1] < 256 and -1 < value[2] < 256:
				self._current_foreground_colour = Colour._make(list(value) + [self.font_transparency])
				self.log.debug(f"The font colour is set to {value}.")
			else: self.log.warning(f"{value} cannot be applied to a foreground colour. The previous value is kept: {self._current_foreground_colour}")
		else: self.log.warning(f"{value} cannot be applied to a foreground colour. The previous value is kept: {self._current_foreground_colour}")
	
	@property
	def background_colour(self):
		"""
		Background colour that will be applied to the next printed character.
		
		The return value is a namedtuple Colour "red green blue alpha".
		The value can be set using one of the following formats:
			- namedtuple Colour
			- tuple (red, green, blue, alpha) (each element is an int in the range of 0 to 255 inclusive)
			- tuple (red, green, blue) (each element is an int in the range of 0 to 255 inclusive)
			- string 'default': background default colour
			- string among the following: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
		if none of these formats is used, the attribute remains unchanged.
		"""
		return self._current_background_colour
	
	@background_colour.setter
	def background_colour(self, value):
		if isinstance(value, str):
			if value in Console.STANDARD_COLOURS:
				self._current_background_colour = Console.STANDARD_COLOURS[value]._replace(alpha = self.background_transparency)
				self.log.debug(f"The background colour is set to {value}.")
			elif value == 'default':
				self._current_background_colour = self._default_background_colour._replace(alpha = self.background_transparency)
				self.log.debug(f"The background colour is set to {value}.")
		elif len(value) == 4:
			if -1 < value[0] < 256 and -1 < value[1] < 256 and -1 < value[2] < 256 and -1 < value[3] < 256:
				self._current_background_colour = Colour._make(value)
				self.background_transparency = value[3]
				self.log.debug(f"The background colour is set to {value}.")
			else: self.log.warning(f"{value} cannot be applied to a background colour. The previous value is kept: {self._current_background_colour}")
		elif len(value) == 3:
			if -1 < value[0] < 256 and -1 < value[1] < 256 and -1 < value[2] < 256:
				self._current_background_colour = Colour._make(list(value) + [self.background_transparency])
				self.log.debug(f"The background colour is set to {value}.")
			else: self.log.warning(f"{value} cannot be applied to a background colour. The previous value is kept: {self._current_background_colour}")
		else: self.log.warning(f"{value} cannot be applied to a background colour. The previous value is kept: {self._current_background_colour}")
	
	@property
	def font_transparency(self):
		"""
		Font transparency, using a value range of 0 (invisible) to 255 (opaque) inclusive.
		"""
		return self._font_transparency
	
	@font_transparency.setter
	def font_transparency(self, value):
		try:
			value_int = int(value)
		except ValueError:
			self.log.warning(f"{value} cannot be applied to a transparency value. The default value is kept: {self.Console.DEFAULT_ALPHA}")
			value_int = Console.DEFAULT_ALPHA
		finally:
			if value_int > 255: value_int = 255
			elif value_int < 0: value_int = 0
			self._font_transparency = value_int
			self.log.debug(f"The font transparency is set to {value_int}.")
			self._render_all()
	
	@property
	def background_transparency(self):
		"""
		Background transparency, using a value range of 0 (invisible) to 255 (opaque) inclusive.
		"""
		return self._background_transparency
	
	@background_transparency.setter
	def background_transparency(self, value):
		try:
			value_int = int(value)
		except ValueError:
			self.log.warning(f"{value} cannot be applied to a transparency value. The default value is kept: {self.Console.DEFAULT_ALPHA}")
			value_int = Console.DEFAULT_ALPHA
		finally:
			if value_int > 255: value_int = 255
			elif value_int < 0: value_int = 0
			self._background_transparency = value_int
			self.log.debug(f"The background transparency is set to {value_int}.")
			self._render_all()
	
	@property
	def italic(self):
		"""
		Gets or sets whether the font should be rendered in italics.
		
		If the set value is not a boolean, the attribute remains unchanged.
		"""
		return self._italic
	
	@italic.setter
	def italic(self, value):
		if isinstance(value, bool):
			self._italic = value
		else: self.log.warning(f"{value} cannot be applied to 'italic' attribute. The previous value is kept: {self._italic}")
	
	@property
	def bold(self):
		"""
		Gets or sets whether the font should be rendered in bold.
		
		If the set value is not a boolean, the attribute remains unchanged.
		"""
		return self._bold
	
	@bold.setter
	def bold(self, value):
		if isinstance(value, bool):
			self._bold = value
		else: self.log.warning(f"{value} cannot be applied to 'bold' attribute. The previous value is kept: {self._bold}")
	
	@property
	def underline(self):
		"""
		Gets or sets whether the font should be rendered with an underline.
		
		If the set value is not a boolean, the attribute remains unchanged.
		"""
		return self._underline
	
	@underline.setter
	def underline(self, value):
		if isinstance(value, bool):
			self._underline = value
		else: self.log.warning(f"{value} cannot be applied to 'underline' attribute. The previous value is kept: {self._underline}")
	
	@property
	def memory_size(self):
		"""
		Amount of memorized characters.
		
		If modified, the console is re-initialized, and all memorized characters are lost. Its value must be higher or equal to the amount of displayable characters on the console surface. If not, the set value is ignored, and the attribute remains unchanged.
		"""
		return self._char_memory_size
	
	@memory_size.setter
	def memory_size(self, value):
		if value >= self._width * self._height:
			self._char_memory_size = value
			# Console re-init
			self._presentation_stream = deque([None] * self._width * self._height, self._char_memory_size)
			self._cursor = 0
			self._start_window = 0
			self._end_window = self._width * self._height - 1
		else: self.log.warning(f"Memory cannot be less than {self._width * self._height}. The previous value is kept: {self._char_memory_size}")
	
	@property
	def width(self):
		"""
		Console width, in characters.
		
		If modified, the console is re-initialized, and all memorized characters are lost. If the set value is negative or null, it is ignored, and the attribute remains unchanged.
		"""
		return self._width
	
	@width.setter
	def width(self, value):
		if value > 0:
			self._width = value
			# Console re-init
			self._presentation_stream = deque([None] * self._width * self._height, self._char_memory_size)
			self._cursor = 0
			self._start_window = 0
			self._end_window = self._width * self._height - 1
		else: self.log.warning(f"Console width cannot be negative. The previous value is kept: {self._width}")
	
	@property
	def height(self):
		"""
		Console height, in characters.
		
		If modified, the console is re-initialized, and all memorized characters are lost. If the set value is negative or null, it is ignored, and the attribute remains unchanged.
		"""
		return self._height
	
	@height.setter
	def height(self, value):
		if value > 0:
			self._height = value
			# Console re-init
			self._presentation_stream = deque([None] * self._width * self._height, self._char_memory_size)
			self._cursor = 0
			self._start_window = 0
			self._end_window = self._width * self._height - 1
		else: self.log.warning(f"Console height cannot be negative. The previous value is kept: {self._height}")
		
	#############################################################
	# Public methods
	
	def add_char(self, char):
		"""
		Display one or several characters on the console, at the current cursor position.
		
		The rendered surface is updated. The cursor moves to the position just after the last character printed. If `char` is empty, nothing is modified, and the cursor remains at the same place. All characters included in `char` share the same caracteristics (foregroung and background colours, italic, bold and underline) from the corresponding attributes.
		
		Parameters
		----------
		char: string
			Characters that will be displayed. 
		"""
		if len(char) == 0:
			self.log.debug("An empty string is displayed: nothing is done.")
		elif len(char) == 1:
			self.log.debug(f"Position: {self._cursor} - displayed character: '{char}'")
			render_all = False
			
			# Caracteristics of the character
			char_args = CharArgs()
			char_args.foreground_colour = self.foreground_colour
			char_args.background_colour = self.background_colour
			char_args.italic = self.italic
			char_args.bold = self.bold
			char_args.underline = self.underline
			char_args.str = char
			
			# Adding a new line in the presentation stream if needed
			if self._cursor >= len(self._presentation_stream):
				self._presentation_stream.extend([None] * self.width)
				# rendered window move
				self._start_window += self.width
				self._end_window += self.width
				# The complete rendered surface must be updated
				render_all = True
				
			# Adding character in the presentation stream
			self._presentation_stream[self._cursor] = char_args
			
			# Surface rendering
			if render_all:
				self._render_all()
			else:
				self._render_char(self._cursor)

			# Increasing cursor position
			self._cursor += 1
		
		else: # More than 1 character to display
			self.log.debug(f"Position: {self._cursor} - displayed string: '{char}'")
			render_all = False
			list_of_indexes = []
			for single_char in char:
				# Caracteristics of the character
				char_args = CharArgs()
				char_args.foreground_colour = self.foreground_colour
				char_args.background_colour = self.background_colour
				char_args.italic = self.italic
				char_args.bold = self.bold
				char_args.underline = self.underline
				char_args.str = single_char
				# Adding a new line in the presentation stream if needed
				if self._cursor >= len(self._presentation_stream):
					self._presentation_stream.extend([None] * self.width)
					# rendered window move
					self._start_window += self.width
					self._end_window += self.width
					# The complete rendered surface must be updated
					render_all = True
				# Adding character in the presentation stream
				self._presentation_stream[self._cursor] = char_args
				# Adding cursor position in the characters list to display
				list_of_indexes.append(self._cursor)
				# Increasing cursor position
				self._cursor += 1
			# Surface rendering
			if render_all:
				self._render_all()
			else:
				self._render_chars(list_of_indexes)
	
	def clear(self, mode = "all"):
		"""
		Clear full or part of screen.
		
		According to the value of `mode`, this function has one of the follwing behaviours:
			"all" (the default): all character positions of the page are cleared, and the cursor is moved to the upper left position. All memorized characters are lost.
			"before": the character positions from the beginning of the page up to the cursor are cleared.
			"after": the cursor position and the character positions up to the end of the page are cleared.
			"all_without_memory": all character positions of the page are cleared, but cursor position and memorized characters are preserved
		
		Parameters
		----------
		mode: string
			type of clearing
		"""
		if mode == "before":
			self.log.debug("All characters before the cursor are cleared.")
			for index_char in range(self._start_window,self._cursor):
				self._presentation_stream[index_char] = None
		elif mode == "after":
			self.log.debug("All characters after the cursor are cleared.")
			for index_char in range(self._cursor,self._end_window+1):
				self._presentation_stream[index_char] = None
		elif mode == "all_without_memory":
			self.log.debug("All characters of the page are cleared, preserving memorized characters.")
			for index_char in range(self._start_window,self._end_window+1):
				self._presentation_stream[index_char] = None
		else:
			self.log.debug("Clear full screen and memory.")
			# Console re-init
			self._presentation_stream = deque([None] * self._width * self._height, self._char_memory_size)
			self._cursor = 0
			self._start_window = 0
			self._end_window = self._width * self._height - 1
		
		# Surface rendering
		self._render_all()
	
	def scroll(self, nb_lines = 1, up = True):
		"""
		Vertical scrolling of the display.
		
		The rendered characters are moved down or up by `nb_lines`, depending on the value of `up`.
		
		PARAMETERS
		----------
		nb_lines: int, optional
			number of lines the display is moved of (default is 1).
		up: bool, optional
			direction of the move. `True` for moving up (the default), `False` for moving down.
		"""
		# Rendered window update
		if up:
			if nb_lines == 1:
				self.log.debug(f"Display moving up of 1 line.")
			else:
				self.log.debug(f"Display moving up of {nb_lines} lines.")
			if self._start_window - self._width * nb_lines < 0:
				self._start_window = 0
			else:
				self._start_window -= self._width * nb_lines
			self._end_window = self._start_window + self._width * self._height - 1
		else:
			if nb_lines == 1:
				self.log.debug(f"Display moving down of 1 line.")
			else:
				self.log.debug(f"Display moving down of {nb_lines} lines.")
			if self._end_window + self._width * nb_lines > len(self._presentation_stream):
				self._end_window = len(self._presentation_stream) - 1
			else:
				self._end_window += self._width * nb_lines
			self._start_window = self._end_window - self._width * self._height + 1
		
		# Surface rendering
		self._render_all()
	
	def carriage_return(self):
		"""
		Carriage return.
		
		The cursor is moved to the first position of the current line.
		"""
		self.log.debug(f"Carriage return at the line n° {self._cursor // self._width}")
		self._cursor = (self._cursor // self._width) * self._width
	
	def line_field(self):
		"""
		Line field.
		
		The cursor is moved to the corresponding character position of the following line.
		"""
		self.log.debug(f"Cursor move to the line n° {self._cursor // self._width + 1}")
		self._cursor += self._width
	
	#############################################################
	# Private methods
	
	def _chartopixcoord(self, index_char = 0):
		"""
		Return coordinates of a specific character on the rendered surface.
		
		This function returns a Coordinates namedtuple object, corresponding to the coordinates of the upper left pixel of the displayed character, on the rendered surface where the upper left pixel is (0,0).
		Return `None`if the character is out of the rendered surface.
		
		PARAMETERS
		----------
		index_char: int, optional
			character index in the presentation stream (default is 0).
		"""
		if index_char < self._start_window: return None
		if index_char > self._end_window: return None
		
		# Calculing column and row
		column = (index_char - self._start_window) % self._width
		row = (index_char - self._start_window) // self._width
		
		# Figuring out character dimensions
		char_width, char_height = self._normal_font.size(" ") # Works only with fixed-width fonts !
		
		# Calculing abscissa and ordinate
		x = column * char_width
		y = row * char_height
		
		# Returning calculated coordinates
		return Coordinates(x, y)
		
	def _render_char(self, index):
		"""
		Update the rendered surface with a specified character.
		
		The image of the character is drawn onto the rendered surface at the appropriate coordinates, and the rest of the surface remains unchanged.
		
		PARAMETERS
		----------
		index: int
			character index in the presentation stream.
		"""
		coord_char = self._chartopixcoord(index)
		if self._presentation_stream[index] is None:
			font_surf = self._normal_font.render(" ", True, self.foreground_colour, self.background_colour)
		else:
			if self._presentation_stream[index].bold and self._presentation_stream[index].italic:
				local_font = self._bolditalic_font
			elif self._presentation_stream[index].bold and not self._presentation_stream[index].italic:
				local_font = self._bold_font
			elif self._presentation_stream[index].italic and not self._presentation_stream[index].bold:
				local_font = self._italic_font
			else:
				local_font = self._normal_font
			local_font.underline = self._presentation_stream[index].underline
			font_surf = local_font.render(self._presentation_stream[index].str, True, self._presentation_stream[index].foreground_colour, self._presentation_stream[index].background_colour)
		
		with self._update_surface_lock:
			self._current_surface.blit(font_surf,coord_char)
			# self._current_surface = self._current_surface.convert_alpha()
		
		self._previous_surface = self._current_surface.copy()
	
	def _render_chars(self, list_of_indexes):
		"""
		Update the rendered surface with several specified characters.
		
		The images of the characters are drawn onto the rendered surface at the appropriate coordinates, and the rest of the surface remains unchanged.
		
		PARAMETERS
		----------
		list_of_indexes: iterable of integers
			list of character indexes to be drawn onto the rendered surface
		"""
		surf_to_blit = []
		for index in list_of_indexes:
			coord_char = self._chartopixcoord(index)
			if self._presentation_stream[index] is None:
				font_surf = self._normal_font.render(" ", True, self.foreground_colour, self.background_colour)
			else:
				if self._presentation_stream[index].bold and self._presentation_stream[index].italic:
					local_font = self._bolditalic_font
				elif self._presentation_stream[index].bold and not self._presentation_stream[index].italic:
					local_font = self._bold_font
				elif self._presentation_stream[index].italic and not self._presentation_stream[index].bold:
					local_font = self._italic_font
				else:
					local_font = self._normal_font
				local_font.underline = self._presentation_stream[index].underline
				font_surf = local_font.render(self._presentation_stream[index].str, True, self._presentation_stream[index].foreground_colour, self._presentation_stream[index].background_colour)
			
			surf_to_blit.append((font_surf,coord_char))
		
		with self._update_surface_lock:		
			self._current_surface.blits(surf_to_blit,doreturn=False)
			# self._current_surface = self._current_surface.convert_alpha()
		
		self._previous_surface = self._current_surface.copy()
	
	def _render_all(self):
		"""
		Update the complete rendered surface.
		"""
		surf_to_blit = []
		for index in range(self._start_window, self._end_window + 1):
			coord_char = self._chartopixcoord(index)
			if self._presentation_stream[index] is None:
				font_surf = self._normal_font.render(" ", True, self.foreground_colour, self.background_colour)
			else:
				if self._presentation_stream[index].bold and self._presentation_stream[index].italic:
					local_font = self._bolditalic_font
				elif self._presentation_stream[index].bold and not self._presentation_stream[index].italic:
					local_font = self._bold_font
				elif self._presentation_stream[index].italic and not self._presentation_stream[index].bold:
					local_font = self._italic_font
				else:
					local_font = self._normal_font
				local_font.underline = self._presentation_stream[index].underline
				font_surf = local_font.render(self._presentation_stream[index].str, True, self._presentation_stream[index].foreground_colour, self._presentation_stream[index].background_colour)
			
			surf_to_blit.append((font_surf,coord_char))
		
		with self._update_surface_lock:		
			self._current_surface.blits(surf_to_blit,doreturn=False)
			# self._current_surface = self._current_surface.convert_alpha()
		
		self._previous_surface = self._current_surface.copy()
