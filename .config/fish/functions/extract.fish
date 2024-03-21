function extract --description "Extracts common archive formats."
    if test -z $argv[1]
        echo "error: no argument given to extract"
        return 1
    else if ! test -e $argv[1]
        echo "error: $argv[1]: cannot find file."
        return 1
    end

    switch $argv[1]
        case '*.zip'
            if ! command -q unzip
                echo 'error: could not find the ``unzip`` command.'
                return 1
            end
            unzip $argv[1]
        case '*.tar.gz'
            if ! command -q tar
                echo 'error: could not find the ``tar`` command.'
                return 1
            end
            tar -xzvf $argv[1]
        case '*.tar'
            if ! command -q tar
                echo 'error: could not find the ``tar`` command.'
                return 1
            end
            tar -xzvf $argv[1]
        case '*.rar'
            if ! command -q unrar
                echo 'error: could not find the ``unrar`` command.'
                return 1
            end
            unrar x $argv[1]
        case '*.7z'
            if ! command -q 7z
                echo 'error: could not find the ``7z`` command.'
                return 1
            end
            7z e $argv[1]
        case '*'
            echo 'error: unknown file extension'
            return 1
    end
end
