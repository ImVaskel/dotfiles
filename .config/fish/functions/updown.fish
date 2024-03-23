if status is-interactive; and command -q docker compose
    function updown --wraps "docker compose"
        docker compose down && docker compose up $argv
    end
end