![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pygconsole)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/devfred78/pygconsole)
![GitHub](https://img.shields.io/github/license/devfred78/pygconsole)
![GitHub issues](https://img.shields.io/github/issues/devfred78/pygconsole)
![GitHub pull requests](https://img.shields.io/github/issues-pr/devfred78/pygconsole)

# pygconsole

ANSI terminal emulation for Pygame.

## About the project

This package provides a way to emulate a terminal onto a Pygame display, compliant with a subset of the [ECMA-48 standard](https://www.ecma-international.org/publications-and-standards/standards/ecma-48/) (aka **ANSI escape codes**). Once correctly implemented, it can replace entirely `sys.stdout` if you desire, or at least be used with `print()` built-in function, as simply as displaying a string on a legacy terminal.

## Getting started

### Prerequisites

Of course, pygconsole cannot run without Python ! More precisely, it requires at least the 3.8 version of our beloved language.

pygconsole depends on the following packages. The installation of pygconsole should install automatically those packages if they are missing on your system. If it fails, you can install them individually:

* pygame: version 2.1.0 or above

	```sh
	pip install pygame
	```

* colorlog: version 6.4.1 or above

	```sh
	pip install colorlog
	```

### Installation

Install from PyPi with:

```sh
pip install pygconsole
```

As an alternative, you can download the `*.whl` file from the last [release on the pygconsole Github repository](https://github.com/devfred78/pygconsole/releases), and execute the following command (replace "X.Y.Z" by the right version number):

```sh
pip install pygconsole-X.Y.Z-py3-none-any.whl
```

## Usage

First, import the package with the following command:

```python
import pygconsole
```

pygconsole is used in close coordination with pygame. So you have to import and initialize pygame for instance with the following lines:

```python
import pygame
from pygame.locals import *

DISPLAY_SIZE = (1920,1080)
RESOURCE_DIR = os.path.join(os.path.dirname(__file__),"resources") # directory where graphical resources are stored
BACKGROUND_IMAGE = os.path.join(RESOURCE_DIR,"background.jpg") # Background image

pygame.init()
flags = FULLSCREEN|SCALED|DOUBLEBUF
screen_surface = pygame.display.set_mode(size=DISPLAY_SIZE,flags=flags)
background_surface = pygame.image.load(BACKGROUND_IMAGE)
```

Those lines initalize a full HD, fullscreen display, with a background image named `background.jpg`. For deeper information about pygame, read the [official site](https://www.pygame.org/docs/).

Initialize an I/O text, buffered stream with:

```python
iotextstream = pygconsole.io.TextIOConsoleWrapper(console_name="pygame_console", newline='\r\n', line_buffering=True)
```

Retrieve the console created "under the hoods" with this I/O stream:

```python
console = pygconsole.console.Console.get_console(name="pygame_console")
```

Finally, retrieve the pygame.Surface object used for displaying the console on screen:

```python
surface = console.surface
```

It is now possible to enter the display loop ! A possible example of display loop can be (take care to previously import the builtin module `sys` otherwise the `sys.exit()` command will raise an exception !) :

```python
while True:
	# Events
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				sys.exit() # Exit when hitting the ESCAPE key
			elif event.key == K_RETURN:
				print("", file=iotextstream, flush=True) # New line
		if event.type == TEXTINPUT: # When typing a key with a writable character...
			print(event.text, end='', file=iotextstream, flush=True) # Display the character
		
	# Background display
	screen_surface.blit(background_surface,(0,0))
	
	# Console display at coordinates (1000,620)
	screen_surface.blit(console.surface,(1000,620))
	
	# Screen rendering
		pygame.display.flip()
```

If you wish to custom the console, you can initialize it independantly, and assign it to an I/O stream in a second step.

```python
my_console = pygconsole.console.get_console(name="custom_console",width=120,height=50)

iotextstream = pygconsole.io.TextIOConsoleWrapper(console_name="custom_console", newline='\r\n', line_buffering=True)
```

A console is identified by its name, 2 consoles with the same name are in reality the same instance of the Console class.

### Recognised ECMA-48 controls

Apart from recognising the main displayable unicode characters, pygconsole supports also the following non-displayable values in the byte stream sent to the console:

```
'\x0a' 		# LF (Line Field): move cursor to the corresponding character position of the following line
'\x0d' 		# CR (Carriage Return): move cursor to the first position of the current line
'\x1b' 		# ESC (Escape): start an escape sequence (see below)
```

Escape sequences supported by pygconsole take the form:

```
ESC [ <param> ; <param> ... <command>
```

Where `<param>` is an integer, and `<command>` is a single letter. Zero or more params are passed to a `<command>`. If no params are passed, it is generally synonymous with passing a single zero. No spaces exist in the sequence; they have been inserted here simply to read more easily.

The exhaustive list of escape sequences supported by pygconsole is the following:

```
# Erase in Display
ESC [ 0 J 		# clear from cursor to end of screen
ESC [ 1 J		# clear from cursor to beginning of the screen
ESC [ 2 J		# clear entire screen
ESC [ 3 J		# clear entire screen and delete all lines saved in the scrollback buffer

# Screen scrolling
ESC [ n S		# Scroll up of n lines. New lines are added at the bottom of the screen
ESC [ n T		# Scroll down of n lines. New lines are added at the top of the screen

# general graphic rendition commands
ESC [ 0 m		# default rendition, cancels the effect of any preceding occurrence of SGR sequence ("m" command)
ESC [ 1 m		# bold characters
ESC [ 3 m		# italicized characters
ESC [ 4 m		# singly underlined characters
ESC [ 7 m		# negative image, swaps foreground and background colours
ESC [ 22 m		# normal intensity characters (not bold)
ESC [ 23 m		# not italicized characters
ESC [ 24 m		# not underlined characters
ESC [ 27 m		# positive image, colours are no more reversed

# Foreground
ESC [ 30 m		# black
ESC [ 31 m		# red
ESC [ 32 m		# green
ESC [ 33 m		# yellow
ESC [ 34 m		# blue
ESC [ 35 m		# magenta
ESC [ 36 m		# cyan
ESC [ 37 m		# white
ESC [ 90 m		# bright black (grey)
ESC [ 91 m		# bright red
ESC [ 92 m		# bright green
ESC [ 93 m		# bright yellow
ESC [ 94 m		# bright blue
ESC [ 95 m		# bright magenta
ESC [ 96 m		# bright cyan
ESC [ 97 m		# bright white

# Background
ESC [ 40 m		# black
ESC [ 41 m		# red
ESC [ 42 m		# green
ESC [ 43 m		# yellow
ESC [ 44 m		# blue
ESC [ 45 m		# magenta
ESC [ 46 m		# cyan
ESC [ 47 m		# white
ESC [ 100 m		# bright black (grey)
ESC [ 101 m		# bright red
ESC [ 102 m		# bright green
ESC [ 103 m		# bright yellow
ESC [ 104 m		# bright blue
ESC [ 105 m		# bright magenta
ESC [ 106 m		# bright cyan
ESC [ 107 m		# bright white

```

For instance, to display "Hello world !" in red:

```python
print("\x1b[31mHello world !", file= iotextstream, flush=True)
```

Multiple numeric params to the 'm' command can be combined into a single sequence:

```
ESC [ 1 ; 92 ; 41 m		# bold, bright green characters on red background
```

The colon character `:` is also recognised as a separator (like the semicolon `;`).

All other escape sequences of the form `ESC [ <param> ; <param> ... <command>`, and, more generally, all other ECMA-48 controls, are silently stripped from the output.

### API documentation

The API documentation is not yet implemented, sorry for the inconvenience :-(. Until the completion of this chapter, you can refer to the source files, they are self-documented enough to understand how the package proceeds.

The most two important classes are:

```python
pygconsole.io.TextIOConsoleWrapper()
```

A buffered text stream providing higher-level access to a BufferedIOConsole buffered binary stream. It inherits io.TextIOWrapper in the `ìo` Python built-in library. For further details about inherited elements, see <https://docs.python.org/3/library/io.html> . This class is generally used directly to write characters on the console, by objects using I/O streams (like `print()`).

```python
pygconsole.console.Console()
```
Console objects represent terminals that can be displayed onto any `pygame.Surface` object (in particular the display surface given by the `pygame.display.get_surface()` method).
	
Note that this class should never be instantiated directly, but always through the `get_console()` static method. Multiple calls to `get_console()` with the same name will always return a reference to the same Console object.

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement" or "bug", according to whether you want to share a proposal of a new function, or to record an anomaly.

Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE.md` file for more information.

## Acknowledgments

I would like greatfully to thank:

[DejaVU](https://dejavu-fonts.github.io/) authors for their astounding work on that famous font family I chose as the default font on pygconsole.

[Karl MPhotography](https://www.pexels.com/fr-fr/photo/paysage-nature-ciel-sable-8092914/) for the great picture I chose for the background of the testing set.

[Make a README](https://www.makeareadme.com/), [Sayan Mondal](https://medium.com/swlh/how-to-make-the-perfect-readme-md-on-github-92ed5771c061), [Hillary Nyakundi](https://www.freecodecamp.org/news/how-to-write-a-good-readme-file/) and [othneildrew](https://github.com/othneildrew/Best-README-Template) for providing very interesting materials to write good README files (far better than I can write by myself !).

[Choose an open source license](https://choosealicense.com/) for helping to choose the best suitable license for this project.

[pygame](https://www.pygame.org) for their wonderful library.

[colorama](https://github.com/tartley/colorama) for their inspiring description regarding ANSI escape sequences.

[python-colorlog](https://github.com/borntyping/python-colorlog) for adding joyful colors to the logging outputs.

[ECMA International](https://www.ecma-international.org/) for maintaining over years the [ECMA-48 standard](https://www.ecma-international.org/publications-and-standards/standards/ecma-48/)

[Semantic Versioning](https://semver.org/) for providing clear specifications for versioning projects.

[Real Python](https://realpython.com/) for contributing really increasing skills in Python for everyone, novices or veterans.

[GitHub](https://github.com/) for hosting this project, and helping to share it.

[Pypi](https://pypi.org/) for providing a very convenient way to share modules and package to the entire Python community.

And, of course, all the former, current and further contributors of this project ! 