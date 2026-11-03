stdout.detach(),
                                              encoding=stdio_encoding,
                                              errors=stdout_errors)
            print("tty =", sys.stdin.isatty() and sys.stdout.isatty(), file=wpipe)
            try:
                print(ascii(input(prompt)), file=wpipe)
            except BaseException as e:
                print(ascii(f'{e.__class__.__name__}: {e!s}'), file=wpipe)
        with self.detach_readline():
            lines = self.run_child(child, termina