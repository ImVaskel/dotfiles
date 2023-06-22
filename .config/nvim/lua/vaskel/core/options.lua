local opt = vim.opt

-- line numbers
opt.relativenumber = true
opt.number = true

-- tabs and indentation
opt.tabstop = 4
opt.shiftwidth = 4
opt.expandtab = true
opt.autoindent = true

-- line wrapping
opt.wrap = false

-- search settings
opt.ignorecase = true
opt.smartcase = true

-- cursor line
opt.cursorline = true

-- appearance
opt.termguicolors = true
opt.background = "dark"


-- backspace
-- opt.backspace = "ident,eol,start"

-- clipboard
if jit.os == "OSX" then
    opt.clipboard:append("unnamedplus")
    print("hi")
end

-- split windows
opt.splitright = true
opt.splitbelow = true

opt.iskeyword:append("-")
