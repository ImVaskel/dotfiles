local status, _ = pcall(vim.cmd, "colorscheme gruvbox-material")
if not status then
	print("colorscheme not found")
	return
end
