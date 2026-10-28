#!/usr/bin/env bash
# ==============================================================================
# Деплой стенда: 2 kind-кластера + Encryption at Rest + Calico +
#                Kyverno + Tetragon + Workloads + Dynamic Secrets.
# ==============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."

STAGE="$ROOT/.rendered"
rm -rf "$STAGE"
mkdir -p "$STAGE/cluster1" "$STAGE/cluster2"

# Имена кластеров и контекстов kubectl
C1_NAME="containerd-auth-client"
C2_NAME="containerd-auth-core"
CTX_C1="kind-${C1_NAME}"
CTX_C2="kind-${C2_NAME}"

# Служебные учетные данные администратора платформы
ADMIN_USER="admin"
ADMIN_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)

echo "=========================================================="
echo " [0/9] Проверка зависимостей хоста"
echo "=========================================================="
for tool in docker kind kubectl helm openssl envsubst jq; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "[-] ОШИБКА: Утилита '$tool' не установлена на хосте." >&2
    exit 1
  fi
done
echo "[+] Все необходимые утилиты присутствуют."

echo "=========================================================="
echo " [1/9] Подготовка Encryption at Rest для Кластера 2"
echo "=========================================================="
ENCRYPTION_DIR="$ROOT/cluster2/encryption"
ENCRYPTION_FILE="${ENCRYPTION_DIR}/encryption-config.yaml"
mkdir -p "${ENCRYPTION_DIR}"

if [ ! -f "${ENCRYPTION_FILE}" ]; then
  echo "[*] Генерация AES-CBC мастер-ключа шифрования etcd..."
  ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64)
  cat <<EOF > "${ENCRYPTION_FILE}"
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF
  chmod 600 "${ENCRYPTION_FILE}"
  echo "[+] Мастер-ключ сгенерирован с правами 0600."
fi

ENCRYPTION_CONFIG_PATH="$(realpath "${ENCRYPTION_FILE}")"
export ENCRYPTION_CONFIG_PATH
echo "[+] ENCRYPTION_CONFIG_PATH=${ENCRYPTION_CONFIG_PATH}"

echo "=========================================================="
echo " [2/9] Создание kind-кластеров"
echo "=========================================================="
if ! kind get clusters | grep -q "^${C1_NAME}$"; then
  echo "[*] Создание Кластера 1 (${C1_NAME})..."
  kind create cluster --name "$C1_NAME" --config "$ROOT/cluster1/kind-config.yaml"
fi

if ! kind get clusters | grep -q "^${C2_NAME}$"; then
  envsubst '$ENCRYPTION_CONFIG_PATH' < "$ROOT/cluster2/kind-config.yaml" > "$STAGE/cluster2-kind-config.yaml"

  echo "[*] Создание Кластера 2 (${C2_NAME})..."
  kind create cluster --name "$C2_NAME" --config "$STAGE/cluster2-kind-config.yaml"
fi

echo "=========================================================="
echo " [3/9] Определение сети Docker и рендер NetworkPolicy"
echo "=========================================================="
DOCKER_GATEWAY="$(docker network inspect kind | jq -r '.[0].IPAM.Config[] | select(.Gateway and (.Gateway | contains("."))) | .Gateway' | head -n 1)"
echo "[+] DOCKER_GATEWAY=${DOCKER_GATEWAY}"
export DOCKER_GATEWAY

for f in "$ROOT"/cluster1/2*-netpol-*.yaml; do
  [ -f "$f" ] && envsubst < "$f" > "$STAGE/cluster1/$(basename "$f")"
done
for f in "$ROOT"/cluster2/1*-netpol-*.yaml; do
  [ -f "$f" ] && envsubst < "$f" > "$STAGE/cluster2/$(basename "$f")"
done
if [ -f "$ROOT/cluster1/11-job-worker.yaml" ]; then
  envsubst < "$ROOT/cluster1/11-job-worker.yaml" > "$STAGE/cluster1/11-job-worker.yaml"
fi

echo "=========================================================="
echo " [4/9] Установка Calico CNI и ожидание готовности нод"
echo "=========================================================="
CALICO_URL="https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/calico.yaml"
for ctx in "$CTX_C1" "$CTX_C2"; do
  echo "[*] Установка Calico в $ctx..."
  for i in 1 2 3 4 5; do
    kubectl --context "$ctx" apply -f "$CALICO_URL" && break
    echo "[!] apply: попытка $i/5 не удалась, жду 5с..."
    sleep 5
  done

  echo "[*] Ожидание готовности нод в $ctx..."
  kubectl --context "$ctx" -n kube-system rollout status ds/calico-node --timeout=600s
  kubectl --context "$ctx" wait --for=condition=Ready nodes --all --timeout=600s
done

echo "=========================================================="
echo " [5/9] Сборка и предзагрузка Docker-образов"
echo "=========================================================="
# Образ containerd-auth для Кластера 2
if [ -f "$ROOT/../../Dockerfile" ]; then
  echo "[*] Сборка containerd-auth:local..."
  docker build -t containerd-auth:local -f "$ROOT/../../Dockerfile" "$ROOT/../../"
  kind load docker-image --name "$C2_NAME" containerd-auth:local
fi

# Образ job-worker для Кластера 1
if [ -f "$ROOT/../../worker/Dockerfile" ]; then
  echo "[*] Сборка job-worker:local..."
  docker build -t job-worker:local -f "$ROOT/../../worker/Dockerfile" "$ROOT/../../worker"
  kind load docker-image --name "$C1_NAME" job-worker:local
fi

helm repo add kyverno https://kyverno.github.io/kyverno --force-update >/dev/null 2>&1
helm repo add cilium https://helm.cilium.io --force-update >/dev/null 2>&1
helm repo update >/dev/null 2>&1

PLATFORM="linux/amd64"   # для ARM-ноды: linux/arm64
RETRIES=5

get_images() {  # $1=release  $2=chart  $3=namespace  $4=фильтр
  helm template "$1" "$2" --namespace "$3" 2>/dev/null | \
    grep -E '^\s*image:\s*' | awk '{print $2}' | tr -d "\"' " | \
    grep "$4" | sort -u
}

pull_retry() {
  local ref="$1" i
  for ((i=1; i<=RETRIES; i++)); do
    timeout 180 docker pull --platform "$PLATFORM" "$ref" && return 0
    echo "[!] pull $ref: попытка $i/$RETRIES не удалась, жду 5с..."
    sleep 5
  done
  return 1
}

load_retry() {
  local tar="$1" i
  for ((i=1; i<=RETRIES; i++)); do
    kind load image-archive "$tar" --name "$C2_NAME" && return 0
    echo "[!] загрузка в ноду: попытка $i/$RETRIES не удалась, жду 3с..."
    sleep 3
  done
  return 1
}

load_image() {
  local img="$1"
  local src="${img/reg.kyverno.io/ghcr.io}"   # всегда берём с ghcr.io
  local tar rc
  tar=$(mktemp --suffix=.tar)

  echo "[+] Pull: $src"
  pull_retry "$src" || { echo "[-] Не удалось скачать: $src"; rm -f "$tar"; return 1; }

  # вернуть исходное имя, которое ожидает helm-манифест
  [[ "$src" != "$img" ]] && docker tag "$src" "$img"

  echo "[+] Загрузка в ноду $C2_NAME: $img"
  docker save --platform "$PLATFORM" "$img" -o "$tar" && load_retry "$tar"
  rc=$?
  rm -f "$tar"
  return $rc
}

echo "[*] Извлечение списка образов Kyverno..."
KYVERNO_IMAGES=$(get_images kyverno kyverno/kyverno kyverno kyverno)

echo "[*] Извлечение списка образов Tetragon..."
TETRAGON_IMAGES=$(get_images tetragon cilium/tetragon tetragon tetragon)

FAILED=()
for img in $KYVERNO_IMAGES $TETRAGON_IMAGES; do
  load_image "$img" || FAILED+=("$img")
done

if ((${#FAILED[@]})); then
  echo "[-] Не загружены:"
  printf '  %s\n' "${FAILED[@]}"
  exit 1
fi
echo "[+] Все образы загружены"

echo "=========================================================="
echo " [6/9] Инициализация Namespaces и Secrets"
echo "=========================================================="
# Namespaces
kubectl --context "$CTX_C1" apply -f "$ROOT/cluster1/00-ns.yaml"
kubectl --context "$CTX_C2" apply -f "$ROOT/cluster2/00-ns.yaml"

# 1. TLS сертификат для reverse-proxy (Кластер 2)
if ! kubectl --context "$CTX_C2" -n core get secret reverse-proxy-tls >/dev/null 2>&1; then
  echo "[*] Генерация самоподписанного TLS-сертификата..."
  TLS_DIR="$(mktemp -d)"
  openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
    -keyout "${TLS_DIR}/tls.key" -out "${TLS_DIR}/tls.crt" \
    -subj "/CN=containerd-auth-core" -addext "subjectAltName=IP:${DOCKER_GATEWAY},DNS:containerd-auth-core" >/dev/null 2>&1

  kubectl --context "$CTX_C2" -n core create secret tls reverse-proxy-tls \
    --cert="${TLS_DIR}/tls.crt" --key="${TLS_DIR}/tls.key"
  rm -rf "${TLS_DIR}"
fi

# 2. Динамические учетные данные БД PostgreSQL (Кластер 2)
PG_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
cat <<EOF | kubectl --context "$CTX_C2" apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
  namespace: core
type: Opaque
stringData:
  POSTGRES_PASSWORD: "${PG_PASSWORD}"
  POSTGRES_DB: "containerd-auth"
EOF

JWT_SECRET=$(openssl rand -hex 32)
cat <<EOF | kubectl --context "$CTX_C2" apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: containerd-auth-secret
  namespace: core
type: Opaque
stringData:
  APP_DB_URL: "postgresql+psycopg://postgres:${PG_PASSWORD}@postgres:5432/containerd-auth"
  ADMIN_USERNAME: "${ADMIN_USER}"
  ADMIN_PASSWORD: "${ADMIN_PASS}"
  JWT_SECRET: "${JWT_SECRET}"
  RUNTIME_ADAPTER: "containerd"
  APP_HOST: "0.0.0.0"
  APP_PORT: "8000"
  DEBUG: "false"
EOF

echo "=========================================================="
echo " [7/9] Развертывание базовых сервисов и NetworkPolicy"
echo "=========================================================="
# Кластер 2: База, Шлюз, Реверс-прокси
kubectl --context "$CTX_C2" apply -f "$ROOT/cluster2/01-postgres.yaml"
kubectl --context "$CTX_C2" apply -f "$ROOT/cluster2/02-containerd-auth.yaml"
kubectl --context "$CTX_C2" apply -f "$ROOT/cluster2/03-reverse-proxy.yaml"
kubectl --context "$CTX_C2" apply -f "$STAGE/cluster2/"

# Кластер 1: Очередь Redis
kubectl --context "$CTX_C1" apply -f "$ROOT/cluster1/01-redis.yaml"

if [ -f "$ROOT/cluster1/10-job-worker-configmap.yaml" ]; then
  kubectl --context "$CTX_C1" apply -f "$ROOT/cluster1/10-job-worker-configmap.yaml"
fi

kubectl --context "$CTX_C1" apply -f "$STAGE/cluster1/2*-netpol-*.yaml"

echo "=========================================================="
echo " [8/9] Установка Kyverno & Tetragon (Кластер 2)"
echo "=========================================================="
# Установка Kyverno
if ! kubectl --context "$CTX_C2" -n kyverno get deploy kyverno-admission-controller >/dev/null 2>&1; then
  echo "[*] Установка Kyverno..."
  helm upgrade --install kyverno kyverno/kyverno \
    --namespace kyverno --create-namespace --kube-context "$CTX_C2" --wait
fi

# Применение политик допуска
echo "[*] Применение политик Kyverno..."
kubectl --context "$CTX_C2" apply -f "$ROOT/policies/10-policy-target-app.yaml"
kubectl --context "$CTX_C2" apply -f "$ROOT/policies/20-policy-fullmoon.yaml"

# Установка Tetragon
if ! kubectl --context "$CTX_C2" -n tetragon get ds tetragon >/dev/null 2>&1; then
  echo "[*] Установка Tetragon..."
  helm upgrade --install tetragon cilium/tetragon \
    --namespace tetragon --create-namespace --kube-context "$CTX_C2" --wait
fi

echo "[*] Применение политик Tetragon..."
kubectl --context "$CTX_C2" apply -f "$ROOT/tetragon/10-tracingpolicy-security.yaml"

echo "=========================================================="
echo " [9/9] Выпуск M2M Service Token и запуск Job-Worker"
echo "=========================================================="
echo "[*] Ожидание готовности reverse-proxy и containerd-auth..."
kubectl --context "$CTX_C2" -n core rollout status deployment/reverse-proxy --timeout=300s
kubectl --context "$CTX_C2" -n core rollout status deployment/containerd-auth --timeout=300s

# Логинимся админом и выпускаем токен для сервисного воркера
ADMIN_TOKEN=""
for i in $(seq 1 30); do
  RESP=$(curl -k -s -w '\n%{http_code}' -X POST "https://${DOCKER_GATEWAY}:30443/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${ADMIN_USER}\", \"password\": \"${ADMIN_PASS}\"}") || true
  HTTP_CODE=$(echo "$RESP" | tail -n1)
  if [ "$HTTP_CODE" = "200" ]; then
    ADMIN_TOKEN=$(echo "$RESP" | sed '$d' | jq -r '.access_token')
    break
  fi
  echo "[*] auth не готов (HTTP ${HTTP_CODE}), попытка ${i}/30..."
  sleep 3
done
if [ -z "${ADMIN_TOKEN}" ] || [ "${ADMIN_TOKEN}" = "null" ]; then
  echo "[-] ОШИБКА: admin login не удался за 30 попыток"
  exit 1
fi
echo "[+] Admin login OK"

WORKER_PASS=$(openssl rand -hex 16)
# Создаем пользователя job-worker
curl -k -s -X POST "https://${DOCKER_GATEWAY}:30443/admin/users" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"job-worker\", \"password\": \"${WORKER_PASS}\", \"role\": \"user\"}" >/dev/null

# Выпускаем токен для воркера
WORKER_AUTH_TOKEN=$(curl -k -s -X POST "https://${DOCKER_GATEWAY}:30443/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"job-worker\", \"password\": \"${WORKER_PASS}\"}" | jq -r '.access_token')

WORKER_BEARER_TOKEN=$(curl -k -s -X POST "https://${DOCKER_GATEWAY}:30443/auth/tokens" \
  -H "Authorization: Bearer ${WORKER_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"worker-token\"}" | jq -r '.token // .access_token')

if [ -z "${WORKER_BEARER_TOKEN}" ] || [ "${WORKER_BEARER_TOKEN}" = "null" ]; then
  echo "[-] ОШИБКА: не удалось выпустить API-токен для job-worker" >&2
  exit 1
fi

# Кладем токен в Secret Кластера 1
cat <<EOF | kubectl --context "$CTX_C1" apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: worker-api-token
  namespace: client
type: Opaque
stringData:
  API_TOKEN: "${WORKER_BEARER_TOKEN}"
EOF

# Запускаем job-worker в Кластере 1
kubectl --context "$CTX_C1" apply -f "$STAGE/cluster1/11-job-worker.yaml"

# Деплой тестовых badPods в Кластер 2 (в отдельный namespace)
kubectl --context "$CTX_C2" apply -f "$ROOT/badpods/"

echo "=========================================================="
echo " [OK] Деплой успешно завершен!"
echo "=========================================================="
echo "Проверка состояния подов:"
echo "  kubectl --context ${CTX_C1} -n client get pods"
echo "  kubectl --context ${CTX_C2} -n core get pods"
echo "Мониторинг событий безопасности Tetragon:"
echo "  kubectl --context ${CTX_C2} -n tetragon logs -l app.kubernetes.io/name=tetragon -c export-stdout -f | tetra getevents -o compact"