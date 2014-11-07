import sh

try:
    git = sh.git
except sh.CommandNoFound:
    raise SystemExit(
        "Could not find an installation of Git "
        "anywhere on the path. Is Git installed?"
    )

config = git.config
