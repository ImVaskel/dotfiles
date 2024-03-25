if status is-interactive; and test -n "$EDITOR"
    function edit --wraps $EDITOR
        $EDITOR $argv
    end
end