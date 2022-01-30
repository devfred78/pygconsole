# -*- coding: utf-8 -*-

"""
	Module io : I/O interfaces to the terminal emulation provided by the console module.
"""


# Standard modules
#------------------
import logging
import io
import codecs

# Third party modules
#--------------------

# Internal modules
#-----------------
from pygconsole.console import Console as Console

# Global constants
#-----------------

# namedtuples
#------------

# Dataclasses
#------------

# Classes
#--------
class RawIOConsole(io.RawIOBase):
	"""
	RawIOConsole class provides the lower-level binary access to an underlying Console object, without buffering. It inherits io.RawIOBase. For further details about inherited elements, see https://docs.python.org/3/library/io.html . In normal cases, RawIOConsole objects do not have to be used directly to write characters on the console (use TextIOConsoleWrapper objects instead).
	
	Attributes
	----------
	console: pygconsole.console.Console object
		Underlying Console object associated to this API.
	log : logging.logger object
		logger used to track events that append when the instance is running (default is None).
		
	Inherited attributes remain unchanged.
	
	Overriden methods
	-----------------
	isatty()
		As the stream is not interactive, return always `False` in the current implementation of the RawIOConsole class. 
	readable()
		As the stream cannot be read from, return always `False` in the current implementation of the RawIOConsole class. 
	seekable()
		As the stream does not support random access, return always `False` in the current implementation of the RawIOConsole class.
	writable()
		As the stream supports writing, return always `True` in the current implementation of the RawIOConsole class.
	write(bytes_str)
		Write the given bytes-like object `bytes_str` to the underlying console, and return the number of bytes written.
	
	Other inherited methods remain unchanged.
	"""
	#############################################################
	# Class constants
	
	# ECMA-48 standard implementation (aka 'ANSI escape codes')
	# C0 control code set
	CTRL_RANGE = range(0x1f+1) # Range of possible values for the C0 control byte
	SUPPORTED_C0_CTRL = {
			0x0a:		'LF',	# LINE FIELD
			0x0d:		'CR',	# CARRIAGE RETURN
			0x1b:		'ESC'	# ESCAPE
						}
	# C1 control code set
	Fe_RANGE = range(0x40,0x5f+1) # Range of possible values for the Fe byte (byte following ESC in a C1 control code)
	SUPPORTED_C1_CTRL = {
			0x5b:		'CSI'	# '[' : CONTROL SEQUENCE INTRODUCER
						}
	# Control sequences
	FINAL_RANGE = range(0x40,0x7e+1) # Range of possibles values for the final byte in control sequences
	SUPPORTED_FINAL_CTRL = {
			0x4a:		'ED',	# 'J' : Erase in Display (Erase in Page in ECMA-48 standard): CSI n J (n=0:clear from cursor to end of screen,n=1:clear from cursor to beginning of the screen,n=2:clear entire screen,n=3:clear entire screen and delete all lines saved in the scrollback buffer (not part of the ECMA-48 standard, but introduced for xterm and supported now by all terminal applications))
			0x53:		'SU',	# 'S' : Scroll Up: CSI n S (n = nb of lines). New lines are added at the bottom.
			0x54:		'SD',	# 'T': Scroll Down CSI n T (n = nb of lines). New lines are added at the top.
			0x6d:		'SGR'	# 'm': Select Graphic Rendition: CSI n m (n = colour or style identifiers - see below)
							}
	# SGR parameters
	SEPARATORS = ";:" # Possible separators between parameters
	SUPPORTED_SGR_PARAMETERS = {
			'0':	'reset',			# default rendition, cancels the effect of any preceding occurrence of SGR
			'1':	'bold', 			# bold characters
			'3':	'italic', 			# italicized characters
			'4':	'underline',		# singly underlined characters
			'7':	'negative',			# negative image, swaps foreground and background colours
			'22':	'not_bold',			# normal intensity characters (not bold)
			'23':	'not_italic',		# not italicized characters
			'24':	'not_underline',	# not underlined characters
			'27':	'positive'			# positive image, colours are no more reversed
								}
	STANDARD_FOREGROUND_COLOURS = {
			'30':	'black',
			'31':	'red',
			'32':	'green',
			'33':	'yellow',
			'34':	'blue',
			'35':	'magenta',
			'36':	'cyan',
			'37':	'white',
			'90':	'bright_black',		# grey
			'91':	'bright_red',
			'92':	'bright_green',
			'93':	'bright_yellow',
			'94':	'bright_blue',
			'95':	'bright_magenta',
			'96':	'bright_cyan',
			'97':	'bright_white'
									}
	STANDARD_BACKGROUND_COLOURS = {
			'40':	'black',
			'41':	'red',
			'42':	'green',
			'43':	'yellow',
			'44':	'blue',
			'45':	'magenta',
			'46':	'cyan',
			'47':	'white',
			'100':	'bright_black',		# grey
			'101':	'bright_red',
			'102':	'bright_green',
			'103':	'bright_yellow',
			'104':	'bright_blue',
			'105':	'bright_magenta',
			'106':	'bright_cyan',
			'107':	'bright_white'
									}
	BRIGHT_SHIFT = 60 # shift between normal and bright colours
	
	#############################################################
	# Initialization
	
	def __init__(self, console_name = "pygame_console", logger = None):
		"""
		Parameters
		----------
		console_name: str
			Name of theuUnderlying pygconsole.console.Console object associated to this API (default is "pygame_console")
		logger: logging.Logger object, optional
			The parent logger used to track events that append when the instance is running. Mainly for status monitoring or fault investigation purposes. If None (the default), no event is tracked.
		"""
		
		
		if logger is None:
			handler = logging.NullHandler()
			self.log = logging.getLogger('RawIOConsole')
			self.log.addHandler(handler)
		else:
			self.log = logger.getChild('RawIOConsole')
		
		self._console = Console.get_console(console_name, logger = self.log)
		self._byte_esc_seq = bytearray() # undecoded escape sequence
		self._byte_displaying_char = bytearray() # undecoded displayable characters

	
	#############################################################
	# Public attributes
	
	@property
	def console(self):
		"""
		Underlying pygconsole.console.Console object associated to this API.
		
		If the set value is not a Console object, the attribute remains silently unchanged.
		"""
		return self._console
	
	@console.setter
	def console(self, value):
		if isinstance(value, Console):
			self._console = value
		else:
			self.log.warning(f"{value} is not a Console object. The previous value is kept: {self.console}")
			pass
	
	
	#############################################################
	# Public methods
	
	def isatty(self):
		"""
		Return True if the stream is interactive (i.e., connected to a terminal/tty device).
		"""
		return False
	
	def readable(self):
		"""
		Return True if the stream can be read from. If False, read() will raise OSError.
		"""
		return False
	
	def seekable(self):
		"""
		Return True if the stream supports random access. If False, seek(), tell() and truncate() will raise OSError.
		"""
		return False
	
	def writable(self):
		"""
		Return True if the stream supports writing. If False, write() and truncate() will raise OSError.
		"""
		return True
	
	def write(self, bytestream):
		"""
		Write the given bytes-like object, bytestream, to the underlying console, and return the number of bytes written.
		
		Only encoded utf-8 characters in bytestream are accepted. If a decoding error occurs, then only bytes before the undecoded byte are taken into account. The supported escape sequences are translated.
		
		Parameters
		----------
		bytestream: bytes, bytearray or memoryview object
			bytes sequence, that is, succession of positive integers less or equal to 255
		"""
		# bytestream translation into bytearray object
		byte_sequence = bytearray(bytestream)
		
		# utf-8 check
		try:
			codecs.decode(byte_sequence,encoding='utf-8',errors='strict')
		except UnicodeDecodeError as err:
			byte_sequence = byte_sequence[:err.start]
		finally:
			nb_decoded_bytes = len(byte_sequence)
		
		# byte treatment
		for byte in byte_sequence:
			if len(self._byte_esc_seq) > 0: # proceeding escape sequence
				self._byte_esc_seq.append(byte)
				decoded_esc_seq = self._esc_seq_decode(self._byte_esc_seq)
				if decoded_esc_seq == 'error':
					self.log.warning(f"The following escape sequence encountered an error: {list(self._byte_esc_seq)}")
					self._byte_esc_seq = bytearray()
				elif decoded_esc_seq == 'successful':
					self.log.debug(f"The follwing escape sequence was treated successfully: {list(self._byte_esc_seq)}")
					self._byte_esc_seq = bytearray()
				elif decoded_esc_seq == 'incomplete':
					pass
			elif byte in RawIOConsole.CTRL_RANGE: # Beginning of an escape sequence
				if len(self._byte_displaying_char) > 0:
					self.console.add_char(self._byte_displaying_char.decode(encoding='utf-8'))
					self._byte_displaying_char = bytearray()
				self._byte_esc_seq.append(byte)
				# 1-byte escape sequence
				decoded_esc_seq = self._esc_seq_decode(self._byte_esc_seq)
				if decoded_esc_seq == 'error':
					self.log.warning(f"The following escape sequence encountered an error: {list(self._byte_esc_seq)}")
					self._byte_esc_seq = bytearray()
				elif decoded_esc_seq == 'successful':
					self.log.debug(f"The follwing escape sequence was treated successfully: {list(self._byte_esc_seq)}")
					self._byte_esc_seq = bytearray()
				elif decoded_esc_seq == 'incomplete':
					pass
			else: # Displayable character (or part of)
				self._byte_displaying_char.append(byte)
		
		# Final treatment of displayable characters
		if len(self._byte_displaying_char) > 0:
			self.console.add_char(self._byte_displaying_char.decode(encoding='utf-8'))
			self._byte_displaying_char = bytearray() 
		
		return nb_decoded_bytes

	
	#############################################################
	# Private methods
	
	def _esc_seq_decode(self, sequence):
		"""
		Decode an escape sequence conforming to ECMA-48 standard (ANSI escape codes).
		
		Supported commands are sent to the console. Return 'successful' if the sequence is supported and successfully proceeded, 'error' if an error is encountered, or 'incomplete' if the sequence is recognized as the beginning of a supported sequence, but not yet complete.
		
		Parameters
		----------
		sequence: bytearray
			Escape sequence encoded using utf-8 codec
		"""
		if len(sequence) == 0:
			return 'incomplete'
		elif sequence[0] in RawIOConsole.CTRL_RANGE:
			if sequence[0] in RawIOConsole.SUPPORTED_C0_CTRL:
				if RawIOConsole.SUPPORTED_C0_CTRL[sequence[0]] == 'ESC': # Beginning of the escape sequence
					if len(sequence) > 1:
						if sequence[1] in RawIOConsole.Fe_RANGE:
							if sequence[1] in RawIOConsole.SUPPORTED_C1_CTRL:
								if RawIOConsole.SUPPORTED_C1_CTRL[sequence[1]] == 'CSI': # CONTROL SEQUENCE INTRODUCER
									if len(sequence) > 2:
										if sequence[-1] in RawIOConsole.FINAL_RANGE:
											if sequence[-1] in RawIOConsole.SUPPORTED_FINAL_CTRL:
												if RawIOConsole.SUPPORTED_FINAL_CTRL[sequence[-1]] == 'ED': # Erase in Display
													try:
														mode = int(sequence[2:len(sequence)-1].decode(encoding='utf-8'))
													except ValueError:
														mode = 3
													finally:
														if mode == 0:
															self.console.clear("after")
															return 'successful'
														elif mode == 1:
															self.console.clear("before")
															return 'successful'
														elif mode == 2:
															self.console.clear("all_without_memory")
															return 'successful'
														elif mode == 3:
															self.console.clear()
															return 'successful'
														else:
															return 'error'
												elif RawIOConsole.SUPPORTED_FINAL_CTRL[sequence[-1]] == 'SU': # Scroll Up
													try:
														nb_lines = int(sequence[2:len(sequence)-1].decode(encoding='utf-8'))
													except ValueError:
														nb_lines = 1
													finally:
														self.console.scroll(nb_lines, True)
														return 'successful'
												elif RawIOConsole.SUPPORTED_FINAL_CTRL[sequence[-1]] == 'SD': # Scroll Down
													try:
														nb_lines = int(sequence[2:len(sequence)-1].decode(encoding='utf-8'))
													except ValueError:
														nb_lines = 1
													finally:
														self.console.scroll(nb_lines, False)
														return 'successful'
												elif RawIOConsole.SUPPORTED_FINAL_CTRL[sequence[-1]] == 'SGR': # Select Graphic Rendition
													# All separators are replaced by the same character
													sep = RawIOConsole.SEPARATORS[0]
													formatted_sequence = sequence[2:len(sequence)-1].decode(encoding='utf-8')
													for any_sep in RawIOConsole.SEPARATORS:
														formatted_sequence = formatted_sequence.replace(any_sep,sep)
													
													# All parameters in a list
													seq_list = formatted_sequence.split(sep)
													
													# Empty list: equivalent to '0'
													if len(seq_list) == 0: seq_list = ['0']
													
													# Processing of each parameter
													for param in seq_list:
														if param in RawIOConsole.SUPPORTED_SGR_PARAMETERS:
															if RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'reset':
																self.console.bold = False
																self.console.italic = False
																self.console.underline = False
																self.console.foreground_colour = 'default'
																self.console.background_colour = 'default'
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'bold':
																self.console.bold = True
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'italic':
																self.console.italic = True
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'underline':
																self.console.underline = True
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'negative':
																temp_colour = self.console.foreground_colour
																self.console.foreground_colour = self.console.background_colour
																self.console.background_colour = temp_colour
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'not_bold':
																self.console.bold = False
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'not_italic':
																self.console.italic = False
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'not_underline':
																self.console.underline = False
															elif RawIOConsole.SUPPORTED_SGR_PARAMETERS[param] == 'positive':
																temp_colour = self.console.foreground_colour
																self.console.foreground_colour = self.console.background_colour
																self.console.background_colour = temp_colour
															else: # SGR parameter supported but not (yet) treated
																pass
														elif param in RawIOConsole.STANDARD_FOREGROUND_COLOURS:
															self.console.foreground_colour = RawIOConsole.STANDARD_FOREGROUND_COLOURS[param]
														elif param in RawIOConsole.STANDARD_BACKGROUND_COLOURS:
															self.console.background_colour = RawIOConsole.STANDARD_BACKGROUND_COLOURS[param]
														else: # valid but not supported SGR parameter 
															pass
													return 'successful'
												else: # Final byte supported but not (yet) treated
													return 'error'
											else: # Valid but not supported final byte
												return 'error'
										else: # Invalid final byte
											return 'incomplete'
									else: # incomplete control sequence
										return 'incomplete'
								else: # C1 control byte supported but not (yet) treated
									return 'error'
							else: # Valid but not supported C1 control byte
								return 'error'
						else: # Escape sequence not recognized
							return 'error'
					else: # Incomplete escape sequence
						return 'incomplete'
				elif RawIOConsole.SUPPORTED_C0_CTRL[sequence[0]] == 'LF': # Line Field (cursor moves to the following line)
					self.console.line_field()
					return 'successful'
				elif RawIOConsole.SUPPORTED_C0_CTRL[sequence[0]] == 'CR': # Carriage Return (cursor moves to the beginning of the current line)
					self.console.carriage_return()
					return 'successful'
				else: # C0 control byte supported but not (yet) treated
					return 'error'
			else: # Valid bu not supported C0 control byte
				return 'error'
		else: # Invalid C0 control byte
			return 'error'

class BufferedIOConsole(io.BufferedWriter):
	"""
	BufferedIOConsole class provides the mid-level binary access to an underlying Console object, with buffering. It inherits io.BufferedWriter. For further details about inherited elements, see https://docs.python.org/3/library/io.html . In normal cases (except if the direct usage of binary sequences is required), BufferedIOConsole objects do not have to be used directly to write characters on the console (use TextIOConsoleWrapper objects instead).
	
	Attributes
	----------
	console: pygconsole.console.Console object
		Underlying Console object associated to this API.
	
	Methods
	-------
	All inherited methods remain unchanged. No new method added.

	"""
	
	#############################################################
	# Initialization
	
	def __init__(self, console_name = "pygame_console"):
		"""
		Parameters
		----------
		console_name: str
			Name of theuUnderlying pygconsole.console.Console object associated to this API (default is "pygame_console")
		"""
		raw = RawIOConsole(console_name)
		super().__init__(raw = raw)
	
	#############################################################
	# Public attributes
	
	@property
	def console(self):
		"""
		Underlying pygconsole.console.Console object associated to this API.
		
		If the set value is not a Console object, the attribute remains silently unchanged.
		"""
		return self.raw.console
	
	@console.setter
	def console(self, value):
		if isinstance(value, Console):
			self.raw.console = value
		else:
			pass

class TextIOConsoleWrapper(io.TextIOWrapper):
	"""
	A buffered text stream providing higher-level access to a BufferedIOConsole buffered binary stream. It inherits io.TextIOWrapper. For further details about inherited elements, see https://docs.python.org/3/library/io.html . This class is generally used directly to write characters on the console, by objects using I/O streams (like `print()`).
	
	Attributes
	----------
	All inherited attributes remain unchanged. No new attribute added.
	
	Methods
	-------
	All inherited methods remain unchanged. No new method added.
	"""
	
	#############################################################
	# Initialisation
	
	def __init__(self, console_name = "pygame_console", errors=None, newline=None, line_buffering=False, write_through=False):
		"""
		Parameters
		----------
		console_name: str
			Name of theuUnderlying pygconsole.console.Console object associated to this API (default is "pygame_console")
		error: str
			optional string that specifies how encoding and decoding errors are to be handled.
		newline: str
			controls how line endings are handled.  It can be None, '', '\n', '\r', and '\r\n'.
		line_buffering: bool
			If True, flush() is implied when a call to write contains a newline character or a carriage return. Default is False.
		write_through: bool
			If True, calls to write() are guaranteed not to be buffered. Default is False.
		"""
		buffer = BufferedIOConsole(console_name)
		# To be compliant with RawIOConsole, encoding must be utf-8.
		encoding = 'utf-8'
		super().__init__(buffer, encoding, errors, newline, line_buffering, write_through)
