if status is-interactive; and command -q eza
    # Only apply eza if we are in an interactive environment and it exists.
    # The reason this is not in functions/ is because fish searches for
    # functions lazily, specifically searching for files named that function.
    # so when ``ls`` is run, it searches for ls.fish, which of course does not exist.
    # If I didn't do it this way, I would have to make a file for *every* one of these functions.
    function ls --wraps eza
        eza $argv
    end
    function la --wraps eza
        eza -a $argv
    end
    function ll --wraps eza
        eza --git -lg --icons $argv
    end
    function lla --wraps eza
        eza --git -lag --icons $argv
    end
end
