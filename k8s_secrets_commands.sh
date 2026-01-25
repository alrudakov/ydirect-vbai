#!/bin/bash

# ========================================
# Kubernetes Secrets для stat-vbai
# ========================================

echo "Создание Kubernetes секретов для stat-vbai"
echo ""

# ========================================
# DEV ENVIRONMENT
# ========================================
echo "DEV Environment:"
echo "kubectl create secret generic stat-vbai-secret \\"
echo "  --from-literal=DATABASE_URL=\"mysql+aiomysql://stat_vbai:VvK8mN2pL9xR4tQ7@172.16.0.35:3306/stat_vbai\" \\"
echo "  -n default"
echo ""

# Или можешь выполнить:
# kubectl create secret generic stat-vbai-secret \
#   --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:VvK8mN2pL9xR4tQ7@172.16.0.35:3306/stat_vbai" \
#   -n default


# ========================================
# STAGE ENVIRONMENT
# ========================================
echo "STAGE Environment:"
echo "kubectl create secret generic stat-vbai-secret \\"
echo "  --from-literal=DATABASE_URL=\"mysql+aiomysql://stat_vbai:StAgE_VvK8mN2pL9xR4tQ7@172.16.0.106:3306/stat_vbai\" \\"
echo "  -n default"
echo ""

# Или можешь выполнить:
# kubectl create secret generic stat-vbai-secret \
#   --from-literal=DATABASE_URL="mysql+aiomysql://stat_vbai:StAgE_VvK8mN2pL9xR4tQ7@172.16.0.106:3306/stat_vbai" \
#   -n default


# ========================================
# PROD ENVIRONMENT
# ========================================
echo "PROD Environment (укажи свой пароль и хост):"
echo "kubectl create secret generic stat-vbai-secret \\"
echo "  --from-literal=DATABASE_URL=\"mysql+aiomysql://stat_vbai:PROD_PASSWORD@PROD_HOST:3306/stat_vbai\" \\"
echo "  -n production"
echo ""


# ========================================
# Проверка секретов
# ========================================
echo "Проверка созданных секретов:"
echo "kubectl get secret stat-vbai-secret -n default"
echo "kubectl describe secret stat-vbai-secret -n default"
echo ""

# Чтобы посмотреть значение:
echo "Посмотреть значение DATABASE_URL:"
echo "kubectl get secret stat-vbai-secret -n default -o jsonpath='{.data.DATABASE_URL}' | base64 -d"
echo ""

