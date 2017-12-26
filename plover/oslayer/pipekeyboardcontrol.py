# coding: utf-8

import threading
import os

import plover.log


BACK_SPACE = '\b'
PIPE_DIR = None

def set_dir(d):
  """ Initialize fs driver"""
  global PIPE_DIR
  PIPE_DIR = d

def down(seq):
    return [(x, True) for x in seq]


def up(seq):
    return [(x, False) for x in reversed(seq)]


def down_up(seq):
    return down(seq) + up(seq)


class KeyboardCapture(threading.Thread):
    """Implementation of KeyboardCapture by external program writing to $PIPE_DIR/keys."""

    def __init__(self):
        threading.Thread.__init__(self, name="KeyPipeListenereThread")

        self.key_down = lambda key: None
        self.key_up = lambda key: None

    def run(self):
        for line in open(os.path.join(PIPE_DIR,"keys"), "r"):
          self.key_down(line)

    def cancel(self):
        self.join()

    def suppress_keyboard(self, suppressed_keys=()):
        # all keys are supressed by external keyboard capture
        #TODO use a third control pipe for this?
        pass


class KeyboardEmulation(object):

    def __init__(self):
        self._output = open(os.path.join(PIPE_DIR,"steno"), "w")

    def send_backspaces(self,number_of_backspaces):
        for _ in range(number_of_backspaces):
            self._output.write("\b \b")
        self._output.flush()

    def send_string(self, s):
        """

        Args:
            s: The string to emulate.

        """
        # TODO support non-plain text
        self._output.write(s)
        self._output.flush()

    def send_key_combination(self, combo_string):
        """Emulate a sequence of key combinations.

        Args:
            combo_string: A string representing a sequence of key
                combinations. Keys are represented by their names in the
                Xlib.XK module, without the 'XK_' prefix. For example, the
                left Alt key is represented by 'Alt_L'. Keys are either
                separated by a space or a left or right parenthesis.
                Parentheses must be properly formed in pairs and may be
                nested. A key immediately followed by a parenthetical
                indicates that the key is pressed down while all keys enclosed
                in the parenthetical are pressed and released in turn. For
                example, Alt_L(Tab) means to hold the left Alt key down, press
                and release the Tab key, and then release the left Alt key.

        """
        #TODO meaningful in a console context?
        raise NotImplementedError
