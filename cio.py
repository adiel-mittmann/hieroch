import sys
import datetime, time
import model
import debug

class CancelException(Exception):
    pass

class PreviousException(Exception):
    pass

class NewException(Exception):
    pass

class cio:

    def print_prompt(self, level, question):
        if not debug.BATCH:
            if question != None:
                print("  " * level + "! " + question)
            sys.stdout.write("  " * level + "> ")
        sys.stdout.flush()

    def read_line(self, level, question = None, new = False, previous = False):
        while True:
            self.print_prompt(level, question)
            line = sys.stdin.readline()

            if len(line) == 0:
                print
                raise CancelException("Cancel.")

            line = line.strip()

            if line == ",":
                raise CancelException("Cancel.")

            if line == "!":
                if previous:
                    raise PreviousException("Previous.")
                else:
                    continue

            if line == ".":
                if new:
                    raise NewException("New.")
                else:
                    continue

            return line

    def read(self, level, question, validate, null = False, new = False, previous = False):
        while True:
            value = self.read_line(level, question, new, previous)

            if null and len(value) == 0:
                return None

            value = validate(value)

            if value != None:
                return value

    def read_string(self, level, question, null = False, new = False, previous = False):
        return self.read(level, question, lambda value: value, null, new, previous)

    def read_date(self, level, question, null = False, new = False, previous = False):
        def validate(value):
            if len(value) != 8:
                return None
            try:
                year  = int(value[0:4])
                month = int(value[4:6])
                day   = int(value[6:8])
                return datetime.date(year, month, day)
            except:
                return None
        return self.read(level, question, validate, null, new, previous)

    def read_integer(self, level, question, null = False, new = False, previous = False):
        def validate(value):
            try:
                return int(value)
            except:
                return None
        return self.read(level, question, validate, null, new, previous)

    def read_float(self, level, question, null = False, new = False, previous = False):
        def validate(value):
            try:
                return float(value)
            except:
                try:
                    value = self.eval_float(value)
                    self.print_status(level, str(value))
                    return value
                except:
                    return None
        return self.read(level, question, validate, null, new, previous)

    def read_barcode(self, level, question, null = False, new = False, previous = False):
        def validate(value):
            if model.is_barcode_valid(value):
                return value
        return self.read(level, question, validate, null, new, previous)

    def read_unit(self, level, question, null = False, new = False, previous = False):
        return self.read(level, question, model.unit_by_name, null, new, previous)

    def read_money(self, level, question, null = False, new = False, previous = False):
        return int(self.read_float(level, question, null, new, previous) * 100)

    def eval_float(self, s):
        t = ""
        k = 0
        for c in s:
            if k == 0:
                if c >= "0" and c <= "9":
                    k = 1
                elif c == ".":
                    k = 2
            elif k == 1:
                if c == ".":
                    k = 2
                elif c < "0" or c > "9":
                    t = t + "."
                    k = 0
            elif k == 2:
                if c < "0" or c > "9":
                    k = 0
            t = t + c

        if k == 1:
            t = t + "."

        return float(eval(t))

    def print_status(self, level, status):
        if not debug.BATCH:
            print("  " * level + "= %s" %(status))

    def print_error(self, level, message):
        print("  " * level + "* " + message)

    ATTR_RESET = 0
    ATTR_BRIGHT = 1
    ATTR_DIM = 2
    ATTR_UNDERL = 3
    ATTR_BLINK = 4
    ATTR_REVERSE = 7
    ATTR_HIDDEN = 8

    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_YELLOW = 3
    COLOR_BLUE = 4
    COLOR_MAGENTA = 5
    COLOR_CYAN = 6
    COLOR_WHITE = 7

    def text_color(self, attr, fg, bg):
        sys.stdout.write(("%c[%d;%d;%dm" % (0x1b, attr, fg + 30, bg + 40)))
        sys.stdout.flush()


    def write(self, s):
        sys.stdout.write(s)
        sys.stdout.flush()

    def writeln(self, s, level = 0):
        print("  " * level + s)
