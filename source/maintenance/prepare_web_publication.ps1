param([ValidateSet('sites', 'github-pages')][string]$Target = 'sites', [switch]$Progressive)
$ErrorActionPreference = 'Stop'
$publicationRoot = Join-Path $PSScriptRoot 'web-publication'
$bookRoot = 'C:\Users\Admin1\Documents\Codex\2026-09-12\referenced-chatgpt-conversation-this-is-an\outputs\IELTS-四科学习册'
$preparedAssets = Join-Path $PSScriptRoot 'web-assets-prepared'
$prepareArgs = @((Join-Path $publicationRoot 'prepare.py'), '--book', $bookRoot, '--assets', $preparedAssets, '--target', $Target)
if ($Progressive) { $prepareArgs += '--progressive' }
python @prepareArgs
if ($LASTEXITCODE -ne 0) { throw "目标 $Target 的发布内容准备或检查失败，线上版本保持不变。" }
Write-Host "目标 $Target 的发布内容已更新并检查通过，下一步推送并发布到原网站。"
