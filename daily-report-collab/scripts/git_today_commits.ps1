<#
.SYNOPSIS
    采集指定根目录下所有 Git 仓库的今日/本周提交记录，输出规范化摘要。
    参考 leeguooooo/work-report 的规范化思路。
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "要扫描的根目录路径")]
    [string]$Root,

    [Parameter(Mandatory = $false)]
    [ValidateSet("daily", "weekly")]
    [string]$Period = "daily",

    [Parameter(Mandatory = $false)]
    [string]$Author = ""
)

$ErrorActionPreference = "Stop"

# 设置输出编码为 UTF-8，确保中文不乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================================
# 工具函数
# ============================================================

<#
    从 git config 读取当前用户的 author 名。
    返回：字符串形式的 author 名，读取失败返回空字符串。
#>
function Get-DefaultGitAuthor {
    try {
        $name = & git config --global user.name 2>$null
        if ($name) { return $name.Trim() }
    } catch {
        # 静默忽略，由调用方处理空值
    }
    return ""
}

<#
    计算 git log 的 --since 参数值。
    daily：从今天零点开始。
    weekly：从上周一零点开始。
#>
function Get-GitSinceParameter {
    param([string]$Period)
    
    if ($Period -eq "daily") {
        return "midnight"
    }
    
    # weekly：计算上周一的日期
    $today = Get-Date
    $daysFromMonday = if ($today.DayOfWeek -eq 'Sunday') { 6 } else { [int]$today.DayOfWeek - 1 }
    $thisMonday = $today.AddDays(-$daysFromMonday).Date
    $lastMonday = $thisMonday.AddDays(-7)
    return $lastMonday.ToString("yyyy-MM-dd HH:mm:ss")
}

<#
    规范化单条 commit message。
    规则参考 leeguooooo/work-report：
    - 去掉 conventional commit 前缀（feat:, fix:, chore: 等）
    - 将特定语义映射为业务层面的描述
#>
function ConvertTo-NormalizedCommitMessage {
    param([string]$RawMessage)

$msg = $RawMessage.Trim()

    # 先用原始消息匹配语义（含前缀），再决定返回什么
    if ($msg -match 'merge|conflict|rebase') {
        return "代码集成分支维护"
    }

    # 工程规范类：format / lint / ci
    if ($msg -match 'format\b|lint\b|ci\b') {
        return "工程规范与代码质量维护"
    }

    # 依赖更新类：deps / bump / upgrade
    if ($msg -match 'deps\b|bump\b|upgrade\b') {
        return "依赖更新与安全维护"
    }

    # refactor
    if ($msg -match 'refactor') {
        return "代码结构优化"
    }

    # test
    if ($msg -match '\btest(s)?\b') {
        return "测试完善"
    }

    # docs
    if ($msg -match '\bdocs?\b') {
        return "文档完善"
    }

    # config / build
    if ($msg -match '\bconfig\b|\bbuild\b') {
        return "构建配置优化"
    }

    # 其他：去掉 conventional commit 前缀后返回原文
    $msg = $msg -replace '^[a-z]+(\([^)]*\))?!?\s*:\s*', ''
    return $msg
}

<#
    递归扫描指定路径下所有包含 .git 子目录的仓库。
    返回：仓库根路径的字符串数组。
#>
function Find-AllGitRepos {
    param([string]$RootPath)

    $repos = @()

    try {
        # 使用 Get-ChildItem 递归查找所有 .git 目录
        # 排除 node_modules 和 vendor 以提升扫描性能
$gitDirs = Get-ChildItem -Path $RootPath -Directory -Filter ".git" -Recurse -Force -ErrorAction Stop `
            | Where-Object { $_.FullName -notmatch '\\node_modules\\' -and $_.FullName -notmatch '\\vendor\\' }

        foreach ($gitDir in $gitDirs) {
            $repoRoot = $gitDir.Parent.FullName
            $repos += $repoRoot
        }
    } catch {
        throw "扫描目录 '$RootPath' 失败：$($_.Exception.Message)"
    }

    return $repos
}

<#
    对单个仓库执行 git log 查询。
    返回：commit message 字符串数组，无提交时返回空数组。
#>
function Get-RepoCommits {
    param(
        [string]$RepoPath,
        [string]$Since,
        [string]$Author
    )

    $authorArg = @()
    if ($Author) {
        $authorArg = @("--author=$Author")
    }

    try {
        # 分开捕获 stdout 和 stderr，不受 2>&1 多行合并影响
        $stderr = $null
        $output = & git -C $RepoPath log --all --since="$Since" --pretty=format:"%s" @authorArg 2>$null

        if ($LASTEXITCODE -ne 0) {
            # 尝试获取错误信息
            $errMsg = & git -C $RepoPath log --all --since="$Since" --pretty=format:"%s" @authorArg 2>&1
            if ($errMsg -match 'not a git repository|fatal:') {
                throw "仓库 '$RepoPath' 无效：$errMsg"
            }
            return @()
        }

        if (-not $output) {
            return @()
        }

        $lines = if ($output -is [array]) { $output } else { @($output) }
        return $lines | Where-Object { $_.Trim() -ne "" }
    } catch {
        throw "查询仓库 '$RepoPath' 的提交记录失败：$($_.Exception.Message)"
    }
}

# ============================================================
# 主流程
# ============================================================

try {
    # 1. 校验 Root 路径
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "指定的根目录 '$Root' 不存在或不是目录"
    }
    $Root = (Resolve-Path -LiteralPath $Root).Path

    # 2. 确定 Author
    if (-not $Author) {
        $Author = Get-DefaultGitAuthor
    }

    # 3. 计算时间范围
    $sinceParam = Get-GitSinceParameter -Period $Period

    # 4. 扫描所有 Git 仓库
    $repos = Find-AllGitRepos -RootPath $Root

    if ($repos.Count -eq 0) {
        Write-Output "NO_COMMITS"
        exit 0
    }

    # 5. 遍历每个仓库，采集并规范化 commit
    $hasAnyCommit = $false
    foreach ($repo in ($repos | Sort-Object)) {
        $commits = Get-RepoCommits -RepoPath $repo -Since $sinceParam -Author $Author

        if ($commits.Count -eq 0) {
            continue
        }

        $hasAnyCommit = $true

        # 仓库名取最后一级目录名
        $repoName = Split-Path -Leaf $repo

        Write-Output $repoName

        foreach ($commit in $commits) {
            $normalized = ConvertTo-NormalizedCommitMessage -RawMessage $commit
            Write-Output "- $normalized"
        }

        # 不同项目之间空行分隔
        Write-Output ""
    }

    # 6. 无任何提交时输出 NO_COMMITS
    if (-not $hasAnyCommit) {
        Write-Output "NO_COMMITS"
    }

    exit 0

} catch {
    $errorMsg = "ERROR: $($_.Exception.Message)"
    # 输出到 stderr（控制台），同时保证 exit code 能被外部捕获
    [Console]::Error.WriteLine($errorMsg)
    exit 1
}
