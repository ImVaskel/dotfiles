fish_add_path $HOME/.cargo/bin
set -x JAVA_HOME $(/usr/libexec/java_home -v 17)
fish_add_path $HOME/.pub-cache/bin

function fish_greeting
    if test $SHLVL -eq 1 # don't show if we are in a nested shell.
        krabby random -i
    end
end
set -gx SSH_AUTH_SOCK $HOME/.1password/agent.sock
test -e {$HOME}/.iterm2_shell_integration.fish ; and source {$HOME}/.iterm2_shell_integration.fish
