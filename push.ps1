param(
  [string]$Token = "",
  [string]$Repo  = "iptv-json"
)
$ErrorActionPreference = 'Continue'
$user = "zzzstarx"
$root = $PSScriptRoot

Write-Host "=== 推送助手: $user/$Repo ===" -ForegroundColor Cyan

if ($Token) {
    Write-Host "[通道] HTTPS + PAT" -ForegroundColor Yellow
    $env:HTTPS_PROXY = 'http://127.0.0.1:7890'
    $env:HTTP_PROXY  = 'http://127.0.0.1:7890'
    $env:GIT_TERMINAL_PROMPT = '0'

    Write-Host "[1/4] 检查仓库是否存在..."
    $hdr = @{ Authorization = "token $Token"; "User-Agent" = "push-helper" }
    $api = "https://api.github.com/repos/$user/$Repo"
    $exists = $false
    try { Invoke-RestMethod -Uri $api -Headers $hdr -Method Get -TimeoutSec 30 | Out-Null; $exists = $true } catch { $exists = $false }

    if (-not $exists) {
        Write-Host "[2/4] 创建仓库 $Repo ..."
        $body = @{ name = $Repo; private = $false; auto_init = $false } | ConvertTo-Json
        try {
            Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Headers $hdr -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 40 | Out-Null
            Write-Host "      已创建" -ForegroundColor Green
        } catch {
            Write-Host "      创建失败: $($_.Exception.Message)" -ForegroundColor Red; exit 1
        }
    } else {
        Write-Host "[2/4] 仓库已存在，跳过创建"
    }

    Write-Host "[3/4] 配置 remote (带 token)..."
    $remoteUrl = "https://" + $user + ":" + $Token + "@github.com/" + $user + "/" + $Repo + ".git"
    git -C $root remote remove origin 2>$null
    git -C $root remote add origin $remoteUrl
    git -C $root remote set-url origin $remoteUrl

    Write-Host "[4/4] push..."
    git -C $root push -u origin main 2>&1 | Out-String
    $rc = $LASTEXITCODE

    git -C $root remote set-url origin ("https://github.com/" + $user + "/" + $Repo + ".git")

    if ($rc -eq 0) { Write-Host "推送成功!" -ForegroundColor Green } else { Write-Host "推送失败 rc=$rc" -ForegroundColor Red }
    exit $rc
}

Write-Host "[通道] SSH (deploy key)" -ForegroundColor Yellow
Write-Host "[1/3] 测试 SSH 认证..."
$test = ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -T git@github.com 2>&1 | Out-String
Write-Host $test.Trim()

if ($test -match "successfully authenticated") {
    Write-Host "[2/3] 认证通过，配置 remote"
    git -C $root remote remove origin 2>$null
    git -C $root remote add origin ("git@github.com:" + $user + "/" + $Repo + ".git")
    Write-Host "[3/3] push..."
    git -C $root push -u origin main 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) { Write-Host "推送成功!" -ForegroundColor Green } else { Write-Host "推送失败（仓库可能还没建）" -ForegroundColor Red }
} else {
    Write-Host ""
    Write-Host "SSH 还没通过。请先在 GitHub 上完成：新版部署密钥添加到仓库" -ForegroundColor Cyan
    Write-Host "  1. 建仓库: https://github.com/new  ->  名字填 $Repo"
    Write-Host "  2. 加部署密钥: https://github.com/$user/$Repo/settings/keys"
    Write-Host ""
    Get-Content "$env:USERPROFILE\.ssh\iptv_json_ed25519.pub" | ForEach-Object { Write-Host "     $_" -ForegroundColor Green }
    Write-Host ""
    Write-Host "弄完再跑: .\push.ps1"
}
