# Welcome to cursed lands.
# Adapted from https://dev.to/d4vsanchez/use-1password-ssh-agent-in-wsl-2j6m but fish:tm: (and more cursed)

# set the ssh socket first
# we don't really want to worry about the socket, so.
set -gx SSH_AUTH_SOCK /tmp/ssh-agent-$fish_pid.tmp

# reenable this if you're having issues with the relay and need to debug.
# echo "Starting the ssh-agent relay" >&2
setsid socat \
    UNIX-LISTEN:$SSH_AUTH_SOCK,fork \
    EXEC:"npiperelay.exe -ep -s //./pipe/openssh-ssh-agent",nofork &
