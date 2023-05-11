set fish_greeting

set -x EDITOR /usr/bin/nano





if status is-interactive
    # Starship
    starship init fish | source

    if command -sq kitty
        alias ssh="kitty +kitten ssh"
    end

    # SSH Stuff
    if command -sq gnome-keyring-daemon
        set -x (gnome-keyring-daemon | string split "=")
        set -x SSH_ASKPASS /usr/lib/seahorse/ssh-askpass
        set -x SSH_ASKPASS_REQUIRE force
    else
        set -x (ssh-agent | string split "=")
    end

    # In WSL
    if uname -a | grep WSL2 >/dev/null
        
    end
end
fish_add_path /home/austin/.spicetify
fish_add_path $HOME/.local/bin

# pnpm
set -gx PNPM_HOME "/home/austin/.local/share/pnpm"
if not string match -q -- $PNPM_HOME $PATH
    set -gx PATH "$PNPM_HOME" $PATH
end
# pnpm end
