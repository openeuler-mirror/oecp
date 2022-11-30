#!/usr/bin/python3
import subprocess
from .log import logger


def cmd(
    cmds: str,
    cwd=None,
):
    """
    :returns: Result is a tuple,exp: (status code,output,err)
    """
    try:
        pipe = subprocess.Popen(
            cmds.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=cwd,
        )
    except FileNotFoundError:
        logger.error(f"Command not found:{cmds}.")
        return 1, None, f"Command not found:{cmds}."
    for line in iter(pipe.stdout.readline, b""):
        print(line)
    pipe.stdout.close()
    pipe.wait()
    # output, error = pipe.communicate()

    return pipe.returncode, pipe.stdout, pipe.stderr


__all__ = "cmd"
