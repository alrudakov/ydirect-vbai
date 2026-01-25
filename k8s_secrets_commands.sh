#!/bin/bash
# =============================================================================
# kubectl команды для создания секретов ydirect-vbai
# =============================================================================

echo "=============================================="
echo "DEV Environment (namespace: dev)"
echo "=============================================="

echo "kubectl create secret generic ydirect-vbai-secret -n dev \\"
echo "  --from-literal=DATABASE_URL=\"mysql+aiomysql://ydirect_vbai:YdIr3ct_D3v_2026@172.16.0.35:3306/ydirect_vbai\" \\"
echo "  --dry-run=client -o yaml | kubectl apply -f -"

# Реальная команда:
# kubectl create secret generic ydirect-vbai-secret -n dev \
#   --from-literal=DATABASE_URL="mysql+aiomysql://ydirect_vbai:YdIr3ct_D3v_2026@172.16.0.35:3306/ydirect_vbai" \
#   --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "=============================================="
echo "STAGE Environment (namespace: stage)"
echo "=============================================="

echo "kubectl create secret generic ydirect-vbai-secret -n stage \\"
echo "  --from-literal=DATABASE_URL=\"mysql+aiomysql://ydirect_vbai:YdIr3ct_St4g3_2026@172.16.0.106:3306/ydirect_vbai\" \\"
echo "  --dry-run=client -o yaml | kubectl apply -f -"

# Реальная команда:
# kubectl create secret generic ydirect-vbai-secret -n stage \
#   --from-literal=DATABASE_URL="mysql+aiomysql://ydirect_vbai:YdIr3ct_St4g3_2026@172.16.0.106:3306/ydirect_vbai" \
#   --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "=============================================="
echo "PROD Environment (namespace: prod) - НЕ СОЗДАВАТЬ ПОКА"
echo "=============================================="
echo "# kubectl create secret generic ydirect-vbai-secret -n prod \\"
echo "#   --from-literal=DATABASE_URL=\"mysql+aiomysql://ydirect_vbai:PROD_PASSWORD@PROD_HOST:3306/ydirect_vbai\" \\"
echo "#   --dry-run=client -o yaml | kubectl apply -f -"

echo ""
echo "=============================================="
echo "Проверка секретов:"
echo "=============================================="
echo "kubectl get secret ydirect-vbai-secret -n dev -o yaml"
echo "kubectl get secret ydirect-vbai-secret -n stage -o yaml"
