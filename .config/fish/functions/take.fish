status is-interactive; and function take --wraps mkdir -d "Creates a directory and cd's into\
     it. All argv are passed into the mkdir."
    mkdir $argv
    cd $argv[1]
end
