set fish_greeting

set -x EDITOR $(which nvim)
fish_add_path $HOME/.local/bin

# Anything here is run before the local config.
if status is-interactive

end

set local_config ~/.config/fish/config.local.fish
test -r $local_config; and source $local_config

# Anything here is run after the local config
if status is-interactive
    # Due to starship being installed via brew, I need to init starship here after the script is run.
    if command -q starship
        function starship_transient_prompt_func
            starship module character
        end
        starship init fish | source
        enable_transience
    end
end
