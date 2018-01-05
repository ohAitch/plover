# Copyright (c) 2011 Hesky Fisher
# See LICENSE.txt for details.

"Thread-based monitoring of a stenotype machine using the TX Bolt protocol."

import plover.machine.base

# In the TX Bolt protocol, there are four sets of keys grouped in
# order from left to right. Each byte represents all the keys that
# were pressed in that set. The first two bits indicate which set this
# byte represents. The next bits are set if the corresponding key was
# pressed for the stroke.

# 00XXXXXX 01XXXXXX 10XXXXXX 11XXXXXX
#   HWPKTS   UE*OAR   GLBPRF   !#ZDST

# The protocol uses variable length packets of one, two, three or four
# bytes. Only those bytes for which keys were pressed will be
# transmitted. The bytes arrive in order of the sets so it is clear
# when a new stroke starts. Also, if a key is pressed in an earlier
# set in one stroke and then a key is pressed only in a later set then
# there will be a zero byte to indicate that this is a new stroke. So,
# it is reliable to assume that a stroke ended when a lower set is
# seen. Additionally, if there is no activity then the machine will
# send a zero byte every few seconds.

STENO_KEY_CHART = ("S-", "T-", "K-", "P-", "W-", "H-",  # 00
                   "R-", "A-", "O-", "*", "-E", "-U",   # 01
                   "-F", "-R", "-P", "-B", "-L", "-G",  # 10
                   "-T", "-S", "-D", "-Z", "#", "!")    # 11


class RtBolt(plover.machine.base.SerialStenotypeBase):
    """RT Bolt interface: TX bolt + "!" partial-stroke bit

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    KEYS_LAYOUT = '''
        #  #  #  #  #  #  #  #  #  #
        S- T- P- H- * -F -P -L -T -D
        S- K- W- R- * -R -B -G -S -Z
              A- O-   -E -U
    '''

    def __init__(self, params):
        super(RtBolt, self).__init__(params)
        self._reset_stroke_state()

    def _reset_stroke_state(self):
        self._pressed_keys = [[],[],[],[]]

    def _do_stroke(self):
        steno_keys = self.keymap.keys_to_actions([key for keys in self._pressed_keys for key in keys])
        if steno_keys:
          self._notify(steno_keys)
          if '!' in steno_keys:
              # Full stroke, is finished.
              self._reset_stroke_state()

    def run(self):
        """Overrides base class run method. Do not call directly."""
        settings = self.serial_port.getSettingsDict()
        settings['timeout'] = 0.1 # seconds
        self.serial_port.applySettingsDict(settings)
        self._ready()
        while not self.finished.isSet():
            # Grab data from the serial port, or wait for timeout if none available.
            raw = self.serial_port.read(max(1, self.serial_port.inWaiting()))

            if not raw: continue # timeout

            for byte in raw:
                key_set = byte >> 6
                keys = []
                for i in range(6):
                    if (byte >> i) & 1:
                        key = STENO_KEY_CHART[(key_set * 6) + i]
                        keys.append(key)
                if keys is not self._pressed_keys[key_set]:
                    self._pressed_keys[key_set] = keys
                    self._do_stroke()
