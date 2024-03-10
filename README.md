# Dotfiles

My dotfiles.

## How does it work?

Everything is managed by ``dotfiles.py``. It does the following:
    1. Iterates over all the files in the dotfiles directory.
    2. Symlinks them based off of $HOME.
    3. Then, it symlinks itself to ``~/.local/bin`` so that you may call it from anywhere to relink new dotfiles.

It enters any folders in the root and then symlinks the files inside, rather than the folder themselves.
.gitignore is also a special cased file. If it needs to be linked, make a file called ``.gitignore_global``

However, ``bin/`` is a special folder, which the files are symlinked to ``.local/bin`` (you should put this on your path.)

``overrides/`` is also a special folder. It will iterate through the whole directory, doing some matching to allow for per-machine overrides.

The format is ``cond@name``. For example ``os.Darwin@.gitconfig.local``.

Currently, overrides supports the following:
1. Hostname matching: matches ``hostname``
2. OS matching: Matches the os. Currently checks ``uname -o``.
3. Defaults: The default. This will be overriden if any of the other matches succeed.