# ===========================================
# Claw Agent - 多阶段 Docker 构建
# ===========================================

# ---- 后端构建阶段 ----
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# 安装依赖
COPY claw-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY claw-gateway/ .

# ---- 前端构建阶段 ----
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# 安装依赖
COPY claw-ui/package*.json ./
RUN npm ci

# 复制前端代码
COPY claw-ui/ .

# 构建前端
RUN npm run build

# ---- 后端运行阶段 ----
FROM python:3.11-slim AS backend

WORKDIR /app

# 安装运行时依赖
COPY --from=backend-builder /root/.local /root/.local
COPY --from=backend-builder /app /app

# 创建非 root 用户
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- 前端运行阶段 ----
FROM nginx:alpine AS frontend

# 复制构建产物
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY claw-ui/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
