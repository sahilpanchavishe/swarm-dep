avg() -> tuple[float, float, float]:
        """
        Return average recent system load information.

        Return the number of processes in the system run queue averaged over
        the last 1, 5, and 15 minutes as a tuple of three floats.
        Raises OSError if the load average was unobtainable.
        """
        ...
    def sysconf(name: str | int, /) -> int:
        """Return an integer-valued system configuration variable."""
        ...

if sys.platform == "linux":
    def ge