# Build the image and push it to ECR in ap-southeast-2 (Sydney).
# Requires Docker Desktop running and: aws configure
#
#   .\deploy\aws.ps1
#
# Postgres must be reachable as DATABASE_URL before the container will boot.
# Use Neon, or an Amazon RDS PostgreSQL instance. SQLite is not kept across restarts.

param(
    [string]$Region = "ap-southeast-2",
    [string]$Repository = "bloom"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "Install the AWS CLI and run: aws configure"
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Install Docker Desktop and start it."
}

aws sts get-caller-identity --output text | Out-Host
$account = (aws sts get-caller-identity --query Account --output text).Trim()
$registry = "$account.dkr.ecr.$Region.amazonaws.com"
$image = "$registry/${Repository}:latest"

aws ecr describe-repositories --repository-names $Repository --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name $Repository --region $Region --image-scanning-configuration scanOnPush=true | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Could not create the ECR repository" }
}

# Windows Credential Manager rejects the long ECR token, so keep the token
# in a temporary Docker config instead of calling docker login.
$dockerConfig = Join-Path $env:TEMP "bloom-docker-config"
New-Item -ItemType Directory -Force -Path $dockerConfig | Out-Null
$password = aws ecr get-login-password --region $Region
if ($LASTEXITCODE -ne 0 -or -not $password) { throw "Could not get an ECR password" }
$pair = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("AWS:$password"))
@"
{"auths":{"$registry":{"auth":"$pair"}}}
"@ | Set-Content -Path (Join-Path $dockerConfig "config.json") -Encoding ascii

docker --config $dockerConfig build -t $image .
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }

docker --config $dockerConfig push $image
if ($LASTEXITCODE -ne 0) { throw "Docker push failed" }

Write-Host ""
Write-Host "Image pushed: $image"
Write-Host ""
Write-Host "Create an App Runner service in $Region from this image."
Write-Host "Port 8080. Health check path: /health"
Write-Host "Set these environment variables in the service (values stay in AWS, not in the image):"
Write-Host "  FLASK_ENV=production"
Write-Host "  SECRET_KEY, DATABASE_URL, PINECONE_API_KEY, JINA_API_KEY"
Write-Host "  OPENROUTER_API_KEY, GROQ_API_KEY, GOOGLE_MAPS_API_KEY"
Write-Host "  GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET"
Write-Host "  TELEGRAM_BOT_TOKEN, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST"
Write-Host "  BEDROCK_GUARDRAILS_ENABLED=1"
Write-Host "  BEDROCK_GUARDRAILS_REGION=$Region"
Write-Host "Instance role needs bedrock:InvokeGuardrailChecks in $Region."
Write-Host "That API is resourceless, so the IAM resource is *. It does not grant other Bedrock actions."
Write-Host "  APP_URL=https://<your-app-runner-url>"
Write-Host ""
Write-Host "After the URL exists, add this OAuth redirect in Google Cloud:"
Write-Host "  https://<your-app-runner-url>/calendar/callback"
Write-Host "And point the Telegram webhook at:"
Write-Host "  https://<your-app-runner-url>/api/telegram"
