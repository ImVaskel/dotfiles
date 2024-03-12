fish_add_path $HOME/.cargo/bin
set -x JAVA_HOME $(/usr/libexec/java_home -v 17)
fish_add_path $HOME/.pub-cache/bin

function fish_greeting
    krabby random -i
end
set -gx SSH_AUTH_SOCK $HOME/.1password/agent.sock
