function source-env --description "Sources environment files, with the syntax foo=bar, ignores comments."
    if test (count $argv) -eq 0
        echo 'source-env: error: no arguments given'
        return 1
    end
    for file in $argv
        # Validate the file exists
        if not test -e $file
            echo "source-env: error: file $file does not exist"
            return 1
        end

        set num 0
        # iterate over each line in the file
        while read -la line
            set num (math $num + 1)
            # First, check if the line is a comment
            if string match -q '#*' "$line"
                continue
            end
            # It's kind of rigged but does the following:
            # first, it gets rid of the comment, then it splits it by =, then it iterates over it
            # then when iterating it checks if the string is not empty AND trims it if so.
            # i am only checking if it is empty because of a bug where ``FOO = BAR`` somehow splits to 4, even with max
            set split (for i in (string replace -r "#.+" "" $line | string split -m 1 = ); test -n "$i"; and string trim $i; end)
            if string match -r '\s+' $split[1]
                # there is a space in the identifier
                echo "source-env: ignoring $file:$num as there is a space in the identifier"
                continue
            else if test (count $split) -ne 2
                echo "source-env: skipping $file:$num as it was not valid"
                continue
            end

            set -gx $split[1] $split[2]

            echo "source-env: set variable $split[1] from $file"
        end <$file
    end
end
