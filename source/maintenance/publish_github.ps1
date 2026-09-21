param([string]$Message = 'Update IELTS learning materials')
$ErrorActionPreference = 'Stop'
$publishRoot = Join-Path $PSScriptRoot 'github-publication'
$repository = 'duf5391-ux/ielts-learning'
$expectedRemote = 'https://github.com/duf5391-ux/ielts-learning.git'

function Invoke-CheckedGit {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArguments)
    & git -C $publishRoot @GitArguments
    if ($LASTEXITCODE -ne 0) { throw 'Git 同步失败；线上状态尚未确认。' }
}

$previousHttpProxy = $env:HTTP_PROXY
$previousHttpsProxy = $env:HTTPS_PROXY
try {
# Reuse an existing explicit Windows proxy for this process only. Never disable TLS checks.
if (-not $env:HTTPS_PROXY) {
    $proxySettings = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
    if ($proxySettings.ProxyEnable -eq 1 -and $proxySettings.ProxyServer -match '^(?:http://)?127\.0\.0\.1:\d+$') {
        $proxyUrl = $proxySettings.ProxyServer
        if (-not $proxyUrl.StartsWith('http://')) { $proxyUrl = 'http://' + $proxyUrl }
        $env:HTTPS_PROXY = $proxyUrl
        if (-not $env:HTTP_PROXY) { $env:HTTP_PROXY = $proxyUrl }
    }
}
& gh auth status --hostname github.com *> $null
if ($LASTEXITCODE -ne 0) { throw '请先完成 GitHub CLI 官方设备登录，再重新运行同步命令。' }
$actualRoot = & git -C $publishRoot rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($actualRoot.Trim()) -ne [IO.Path]::GetFullPath($publishRoot)) {
    throw 'github-publication 必须是独立发布仓库。'
}
$remote = & git -C $publishRoot remote get-url origin
if ($LASTEXITCODE -ne 0 -or $remote.Trim() -ne $expectedRemote) { throw '发布远程仓库不匹配，停止同步。' }

& (Join-Path $PSScriptRoot 'prepare_github_publication.ps1') -Progressive
Invoke-CheckedGit add -- site manifest.json validate.py README.md .github .gitignore .gitattributes
& git -C $publishRoot diff --cached --quiet
if ($LASTEXITCODE -eq 1) { Invoke-CheckedGit commit -m $Message }
elseif ($LASTEXITCODE -ne 0) { throw '无法核对提交内容。' }
$commit = (& git -C $publishRoot rev-parse --verify HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw '发布仓库没有可用提交。' }
# Use the authenticated CLI through this invocation only; no token enters the repository.
Invoke-CheckedGit -c credential.helper= -c 'credential.helper=!gh auth git-credential' push origin HEAD:main
Write-Host "已同步提交 $commit，正在核实对应部署。"
$run = $null
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    $runJson = & gh run list --repo $repository --workflow pages.yml --branch main --commit $commit --limit 1 --json databaseId,status,conclusion,url
    if ($LASTEXITCODE -ne 0) { throw '无法读取 GitHub Actions 部署状态。' }
    $runs = @($runJson | ConvertFrom-Json)
    if ($runs.Count -gt 0) { $run = $runs[0]; break }
    Start-Sleep -Seconds 2
}
if ($null -eq $run) { throw "未找到对应部署，请查看 https://github.com/$repository/actions 。" }
if ($run.status -eq 'completed') {
    if ($run.conclusion -ne 'success') { throw "对应部署未成功：$($run.url)" }
} else {
    & gh run watch $run.databaseId --repo $repository --interval 10 --exit-status
    if ($LASTEXITCODE -ne 0) { throw "部署未成功：$($run.url)" }
}
Write-Host 'GitHub Actions 部署成功：https://duf5391-ux.github.io/ielts-learning/'
Write-Host "部署记录：$($run.url)"
Write-Host '上线后仍须检查首页和关键资源；个人学习记录不随内容发布同步。'
} finally {
    $env:HTTP_PROXY = $previousHttpProxy
    $env:HTTPS_PROXY = $previousHttpsProxy
}
