# Использование:
#   .\demo.ps1 -Host_ 192.168.x.x [-AdminPass 'P@ssw0rd']

param(
    [string]$Host_ = "192.168.153.5",
    [int]$Port = 8443,
    [string]$AdminUser = "admin",
    [string]$AdminPass = "P@ssw0rd",
    [string]$UserPass = "UserPass123!"
)

$ErrorActionPreference = "Stop"
$Base = "https://${Host_}:${Port}"
$script:pass = 0
$script:fail = 0

function Step($label, $expected, $actual) {
    if ($expected -contains $actual) {
        Write-Host "[OK]   $label (HTTP $actual)" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "[FAIL] $label — ожидалось $($expected -join '/'), получено $actual" -ForegroundColor Red
        $script:fail++
    }
}

function Api($method, $path, $token, $body) {
    $args = @{
        Method = $method
        Uri = "$Base$path"
        SkipCertificateCheck = $true
        ContentType = "application/json"
        ErrorAction = "SilentlyContinue"
    }
    if ($token) { $args.Headers = @{ Authorization = "Bearer $token" } }
    if ($body) { $args.Body = ($body | ConvertTo-Json -Depth 5) }
    try {
        $resp = Invoke-WebRequest @args
        return $resp.StatusCode, ($resp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue)
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        $detail = $null
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $detail = ($stream | ForEach-Object { New-Object IO.StreamReader($_) }).ReadToEnd() | ConvertFrom-Json
        } catch {}
        return $code, $detail
    }
}

Write-Host "=== containerd-auth demo против $Base ===" -ForegroundColor Cyan

# --- 0. Сервер жив? (без TLS-проверок самоподписанного сертификата) ---
try {
    $null = Invoke-WebRequest -Uri "$Base/docs" -SkipCertificateCheck -ErrorAction Stop
    Write-Host "[OK]   сервер отвечает" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] сервер недоступен на $Base — проверь uvicorn/firewall" -ForegroundColor Red
    exit 1
}

# --- 1. Auth-missing: без токена должно быть 401 ---
($code, $null) = Api GET "/containers" $null $null
Step "GET /containers без токена -> 401" @(401) $code

# --- 2. Логин админа ---
($code, $r) = Api POST "/auth/login" $null @{ username = $AdminUser; password = $AdminPass }
Step "login admin -> 200" @(200) $code
$admin = $r.access_token

# --- 3. Создаём обычного пользователя user1 ---
($code, $r) = Api POST "/admin/users" $admin @{ username = "user1"; password = $UserPass; role = "user" }
Step "admin: создать user1 -> 201" @(201, 409) $code

# --- 4. Анти-перечисление: создать дубликат -> 409 (или 404-фолбэк) ---
($code, $null) = Api POST "/admin/users" $admin @{ username = "user1"; password = $UserPass; role = "user" }
Step "admin: дубликат user1 -> 409" @(409, 404) $code

# --- 5. user1 логин ---
($code, $r) = Api POST "/auth/login" $null @{ username = "user1"; password = $UserPass }
Step "login user1 -> 200" @(200) $code
$u1 = $r.access_token

# --- 6. user1 тянет alpine ---
($code, $null) = Api POST "/images" $u1 @{ image_ref = "docker.io/library/alpine:3.19" }
Step "user1: pull alpine:3.19 -> 200/201" @(200, 201) $code

# --- 7. user1 создаёт контейнер ---
($code, $r) = Api POST "/containers" $u1 @{ name = "u1-c1"; image = "docker.io/library/alpine:3.19" }
Step "user1: create u1-c1 -> 201" @(201) $code
$cid = $r.id

# --- 8. Старт/логи/стоп ---
($code, $null) = Api POST "/containers/u1-c1/start" $u1 $null
Step "user1: start -> 200" @(200) $code
Start-Sleep 1
($code, $r) = Api GET "/containers/u1-c1/logs" $u1 $null
Step "user1: logs -> 200" @(200) $code
($code, $null) = Api POST "/containers/u1-c1/stop" $u1 $null
Step "user1: stop -> 200" @(200) $code

# --- 9. IDOR: user1 лезет в чужой контейнер -> 404 (анти-перечисление) ---
($code, $null) = Api POST "/containers/ghost/start" $u1 $null
Step "user1: start чужого/несущ. -> 404" @(404) $code

# --- 10. Vertical: user1 в admin-панель -> 403 ---
($code, $null) = Api GET "/admin/users" $u1 $null
Step "user1: GET /admin/users -> 403" @(403) $code

# --- 11. user1 меняет себе пароль (self-management) ---
($code, $null) = Api PATCH "/auth/password" $u1 @{ old_password = $UserPass; new_password = "NewPass456!" }
Step "user1: сменить пароль -> 200" @(200) $code

# --- 12. Старый пароль больше не работает ---
($code, $null) = Api POST "/auth/login" $null @{ username = "user1"; password = $UserPass }
Step "user1: старый пароль -> 401" @(401) $code

# смена пароля инвалидирует старый JWT (tokens_revoked_before) — перелогин
($code, $r) = Api POST "/auth/login" $null @{ username = "user1"; password = "NewPass456!" }
Step "user1: новый пароль -> 200" @(200) $code
$u1 = $r.access_token

# --- 13. Ротация API-токена ---
($code, $r) = Api POST "/auth/tokens" $u1 @{ name = "demo" }
Step "user1: создать API-токен -> 201" @(201) $code
$tok = $r.token
($code, $null) = Api GET "/containers" $tok $null
Step "API-токен работает -> 200" @(200) $code

# --- 14. user1 удаляет свой контейнер ---
($code, $null) = Api DELETE "/containers/u1-c1" $u1 $null
Step "user1: delete u1-c1 -> 200" @(200) $code

# --- 15. Админский аудит-лог ---
($code, $r) = Api GET "/admin/log" $admin $null
Step "admin: log -> 200" @(200, 404) $code
if ($code -eq 200 -and $r) {
    Write-Host "       последних записей: $($r.Count)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== Итог: $script:pass OK, $script:fail FAIL ===" -ForegroundColor $(if ($script:fail) { "Red" } else { "Green" })
exit $(if ($script:fail) { 1 } else { 0 })
