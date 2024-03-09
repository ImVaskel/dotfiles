set fish_greeting

set -x EDITOR $(which nvim)

# Global, then local
if status is-interactive
    # Starship
    function starship_transient_prompt_func
        starship module character
    end
    starship init fish | source
    enable_transience
end

set local_config ~/.config/fish/config.local.fish
test -r $local_config; and source $local_config

fish_add_path $HOME/.local/bin

