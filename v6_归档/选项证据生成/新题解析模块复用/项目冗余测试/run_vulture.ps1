# 死代码检测：从本目录运行，扫描父目录（新题解析模块复用/）
# 用法：.\run_vulture.ps1

Set-Location $PSScriptRoot
vulture .. whitelist.py --sort-by-size
