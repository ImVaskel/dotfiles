if command -q lsof
    function get-port --description "gets the process that is using a given port" --argument-names port
        argparse s/sudo -- $argv; or return
        if test -z $port
            echo "get-port: error: no argument provided"; and return 1
        end

        # If _flag_s is empty (sudo flag), then set sudo to true
        test -n "$_flag_s"; and set is_sudo true; or set is_sudo false

        set cmd "lsof -nP -i:$port"

        # if --sudo wasn't supplied, we are going to need it anyway
        # (lsof cannot read processes that it doesn't own and <1024 is "privileged" on linux at least)
        if test $is_sudo != true; and test $port -lt 1024
            read --nchars 1 -P 'The given port is privileged and the --sudo argument wasn\'t given, would you like to run as sudo [y\N]?: ' confirm
            if test (string lower $confirm) != y
                echo "Ok, exiting..."
                return 0
            end
            set is_sudo true
        end

        # if we are supposed to run sudo, prepend sudo to the command
        test $is_sudo = true; and set -p cmd sudo

        # Eval the command and set the "header" into header and "data" into data
        eval $cmd | read -L header data
        set cmd_status $pipestatus[1]
        if test $cmd_status -ne 0
            echo "get-port: error: lsof returned non-zero exit code $cmd_status, this likely means there was no port found."
        else
            # Replace the padding in the header and body with a single space
            set header (string replace -a -r -- '\s+' ' ' $header | string split ' ')
            set data (string replace -a -r -- '\s+' ' ' $data | string split ' ')
            # This kind of makes assumptions about indexes, but that should be fine.
            set pid $data[2]
            set comm_name (ps -p $pid -o comm=)

            # Returns the first arg rightpadded to the length of the second arg.
            function pad_to_length
                string pad -r -w (string length $argv[2]) $argv[1]
            end

            echo (pad_to_length "COMMAND" $comm_name) (pad_to_length "PID" $pid) (pad_to_length "NAME" $data[3])
            # Pad the command name length to at least the size of the header, COMMAND
            # This can also happen on PID, but it's significantly unlikely.
            echo (pad_to_length $comm_name "COMMAND") $pid $data[3]
        end
    end
end
