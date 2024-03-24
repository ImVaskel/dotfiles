function fish_greeting
    if test $SHLVL -eq 1 # Don't apply greeting if we are in a nested shell.
        cbonsai -p
    end
end
