if status is-interactive
    alias ssh="kitty +kitten ssh"

    set -x (gnome-keyring-daemon | string split "=")
    set -x SSH_ASKPASS_REQUIRE force
end

fish_add_path /home/austin/.spicetify