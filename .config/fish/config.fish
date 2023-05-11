set fish_greeting

set -x EDITOR /usr/bin/nano

# Global, then local
if status is-interactive
    # Starship
    starship init fish | source
    # SSH Stuff
    set -x (ssh-agent | string split "=")
end

set local_config ~/.config/fish/config.local.fish
test -r $local_config; and source $local_config

fish_add_path $HOME/.local/bin

# pnpm
set -gx PNPM_HOME "/home/austin/.local/share/pnpm"
if not string match -q -- $PNPM_HOME $PATH
    set -gx PATH "$PNPM_HOME" $PATH
end
# pnpm end
