if status is-interactive
    # Abbreviations are better then wrapping the function
    # Allows me to know which command was actually executed rather than guessing.
    if command -q eza
        abbr -a -- ls eza
        abbr -a -- la eza -a
        abbr -a -- ll eza --git -lg --icons
        abbr -a -- lla eza --git -lag --icons
    end
end
