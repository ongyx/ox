# coding: utf8

from .runtime import Runtime
from .__version__ import __version__

BANNER = f"""
Ox {__version__}
Type Ctrl-C/Ctrl-D to exit.
"""


class Shell:
    def __init__(self, ps1: str = "ox> ", ps2: str = "--> "):
        self.ps1 = ps1
        self.ps2 = ps2
        self.runtime = Runtime()

    def interact(self):

        print(BANNER)

        code = []
        counter = {c: 0 for c in "()[]{}"}

        complete = True

        while True:
            if complete:
                prompt = self.ps1
            else:
                prompt = self.ps2

            line = input(prompt)
            if not line and complete:
                continue

            code.append(line)

            for char in line:
                if char in counter:
                    counter[char] += 1

            for left, right in ("()", "[]", "{}"):
                if counter[left] != counter[right]:
                    complete = False
                    break
                else:
                    complete = True

            if complete:
                try:
                    self.runtime.execute("\n".join(code))
                except RuntimeError as e:
                    print(e)

                code = []
                counter = counter.fromkeys(counter, 0)

    def repl(self):
        try:
            self.interact()
        except (EOFError, KeyboardInterrupt):
            return


def main():
    shell = Shell()
    shell.repl()


if __name__ == "__main__":
    main()
