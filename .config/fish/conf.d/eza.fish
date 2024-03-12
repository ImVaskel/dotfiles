if status is-interactive
    # Only apply eza if we are in an interactive environment and it exists.
    if command -q eza
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
end