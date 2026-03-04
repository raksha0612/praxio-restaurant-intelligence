# do.ps1 — Windows PowerShell runner (equivalent of ./do on Mac/Linux)
# Usage: .\do.ps1 <command>
# Requires uv: winget install astral-sh.uv  OR  irm https://astral.sh/uv/install.ps1 | iex

param([string]$Command = "")

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

switch ($Command) {
    "install" {
        Write-Host "-> Installing all dependencies with uv..." -ForegroundColor Cyan
        uv sync
        Write-Host "✓ Done — run .\do.ps1 app to start the dashboard" -ForegroundColor Green
    }
    "app" {
        Write-Host "-> Starting Restaurant Intelligence dashboard..." -ForegroundColor Cyan
        uv run streamlit run app/app.py
    }
    "lint" {
        Write-Host "-> Running ruff linter..." -ForegroundColor Cyan
        uv run ruff check app/ --fix
        Write-Host "✓ Lint complete" -ForegroundColor Green
    }
    "test" {
        Write-Host "-> Running tests..." -ForegroundColor Cyan
        uv run pytest tests/ -v
    }
    "clean" {
        Write-Host "-> Cleaning cache..." -ForegroundColor Cyan
        Get-ChildItem -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "✓ Clean complete" -ForegroundColor Green
    }
    default {
        Write-Host ""
        Write-Host "Usage: .\do.ps1 <command>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  install   Install all dependencies via uv"
        Write-Host "  app       Start the Streamlit dashboard"
        Write-Host "  lint      Run ruff linter with auto-fix"
        Write-Host "  test      Run pytest"
        Write-Host "  clean     Remove __pycache__ and .pyc files"
        Write-Host ""
        Write-Host "First time setup:" -ForegroundColor Cyan
        Write-Host "  .\do.ps1 install"
        Write-Host "  copy .env.example .env   # then add your ANTHROPIC_API_KEY"
        Write-Host "  .\do.ps1 app"
        Write-Host ""
    }
}
