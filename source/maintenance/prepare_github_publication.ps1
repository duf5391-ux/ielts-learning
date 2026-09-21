param([switch]$Progressive)
$ErrorActionPreference = 'Stop'
# Always regenerate from the current formal workbook; never publish a stale copy.
& (Join-Path $PSScriptRoot 'prepare_web_publication.ps1') -Target github-pages -Progressive:$Progressive
python (Join-Path $PSScriptRoot 'stage_github_publication.py')
if ($LASTEXITCODE -ne 0) { throw 'GitHub Pages 文件校验失败，未发布。' }
Write-Host 'GitHub Pages 完整包已准备；提交并推送 main 后 Actions 自动部署。'
