# Welcome to cursed lands.
# Adapted from https://dev.to/d4vsanchez/use-1password-ssh-agent-in-wsl-2j6m but fish:tm: (and more cursed)

# set the ssh socket first
# we don't want to share the socket, as it may exist but there is no command behind it.
set -gx SSH_AUTH_SOCK /tmp/ssh-agent-$fish_pid.tmp

# Cleans up the socat and temp sockets.
function cleanup-ssh-agent --on-event fish_exit
    if test -e $SSH_AUTH_SOCK
        if test -S $SSH_AUTH_SOCK
            rm $SSH_AUTH_SOCK
        end
    end
    # TODO: Check if this is the best way of grepping socat.
    if pgrep -q "socat"
        killall "socat"
    end
end

# reenable this if you're having issues with the relay and need to debug.
# echo "Starting the ssh-agent relay" >&2
setsid socat \
    UNIX-LISTEN:$SSH_AUTH_SOCK,fork \
    EXEC:"npiperelay.exe -ep -s //./pipe/openssh-ssh-agent",nofork &
