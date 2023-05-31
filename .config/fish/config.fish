set fish_greeting

set -x EDITOR /usr/bin/nano

# Global, then local
if status is-interactive
    # Starship
    function starship_transient_prompt_func
        starship module character
    end
    starship init fish | source
    enable_transience

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

set -q GHCUP_INSTALL_BASE_PREFIX[1]; or set GHCUP_INSTALL_BASE_PREFIX $HOME
set -gx PATH $HOME/.cabal/bin $PATH /home/austin/.ghcup/bin # ghcup-env
