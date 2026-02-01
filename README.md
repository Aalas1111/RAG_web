# LightRAG Web

基于 LightRAG 的知识图谱问答网站，前后端分离：**Vue 3** 前端 + **FastAPI** 后端。

## 功能概览

- **主界面**：选择现成数据图谱（名称 + 简介），选择查询模式（native / local / global / hybrid，默认 hybrid），在对话框中对图谱内容进行 query，下方展示 AI 生成回答。
- **管理员**（通过 `/login` 登录）：
  - 上传 txt 构建新数据图谱（命名 + 简介 + 每日限额）
  - 上传 txt 对现有图谱增量更新
  - 删除图谱、修改图谱名称或简介
  - 查看今日各图谱 query 次数，并修改各图谱每日 query 限额
  - 配置环境变量（修改 .env，敏感项不展示原值）

不同数据图谱单独存放，互不干扰。

## 项目结构

```
RAG_web/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   ├── rag_service.py
│   │   └── routers/
│   └── requirements.txt
├── frontend/         # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/    # 首页、登录、管理后台
│   │   ├── router/
│   │   └── api.js
│   ├── package.json
│   └── vite.config.js
├── data/             # 运行时生成：图谱数据与 SQLite
├── .env              # 配置与 API Key（勿提交到 Git）
├── .env.example
├── requirements.txt
└── README.md
```

---

## 一、本地部署与测试

### 1. 环境要求

- Python 3.10+
- Node.js 18+

### 2. 配置 .env

在项目根目录下复制 `.env.example` 为 `.env`（若已有 `.env` 可跳过），并填写：

- **必填**：`DEEPSEEK_API_KEY`、`SILICONCLOUD_API_KEY`
- **可选**：`ADMIN_USERNAME`、`ADMIN_PASSWORD`、`SECRET_KEY`（生产环境请修改）

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

看到 `Uvicorn running on http://0.0.0.0:8000` 即表示后端已启动。可访问 http://127.0.0.1:8000/docs 查看 API 文档。

### 4. 启动前端

另开终端：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173。前端会通过 Vite 代理将 `/api` 转发到 8000 端口。

### 5. 本地测试流程建议

1. 先访问首页，“选择数据图谱”可能为空（尚未创建图谱）。
2. 访问 http://localhost:5173/login 使用 .env 中的管理员账号登录。
3. 在管理后台上传一个 .txt 文件创建第一个图谱（填写名称、简介、每日限额）。
4. 回到首页，选择该图谱，选择查询模式（如 hybrid），输入问题并查看 AI 回答。
5. 在管理后台可查看今日查询统计、修改限额、增量更新或删除图谱。

---

## 二、部署到服务器（CentOS 8 + 宝塔面板）

### 1. 目录约定

- 项目在服务器上的工作目录示例：`/www/wwwroot/rag_web`（宝塔下常见为 `/www/wwwroot/域名`，请以实际为准）。

### 2. 上传代码与依赖

- 将整个项目上传到服务器（Git 或宝塔文件管理）。**不要**把 `.env` 中的真实密钥提交到公开仓库，在服务器上单独创建 `.env`。
- 后端依赖：
  ```bash
  cd /www/wwwroot/rag_web/backend
  pip3 install -r requirements.txt
  ```
  或使用宝塔「Python 项目」后在其虚拟环境中安装。
- 前端构建：
  ```bash
  cd /www/wwwroot/rag_web/frontend
  npm install
  npm run build
  ```
  构建完成后静态文件在 `frontend/dist`。

### 3. 后端以服务方式运行

- **方式 A：宝塔「Python 项目」**  
  新建 Python 项目，路径选 `backend` 目录，启动方式选 uvicorn，启动文件填 `app.main:app`，端口 8000；环境变量可从 .env 或宝塔界面填写。

- **方式 B：Supervisor**  
  新建配置 `/etc/supervisor/conf.d/rag_web.conf`：

  ```ini
  [program:rag_web_api]
  directory=/www/wwwroot/rag_web/backend
  command=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  environment=PATH="/www/server/pyenv/versions/你的Python路径/bin"
  autostart=true
  autorestart=true
  stdout_logfile=/www/wwwroot/rag_web/logs/uvicorn.log
  stderr_logfile=/www/wwwroot/rag_web/logs/uvicorn_err.log
  ```

  先创建日志目录：`mkdir -p /www/wwwroot/rag_web/logs`，再执行 `supervisorctl reread && supervisorctl update`。

### 4. 前端静态资源与 Nginx

- 将 `frontend/dist` 设为网站根目录，或在 Nginx 中配置 `root` 指向该目录。
- 反向代理 `/api` 到后端（例如 127.0.0.1:8000）：

  ```nginx
  location /api {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_connect_timeout 300s;
      proxy_send_timeout 300s;
      proxy_read_timeout 300s;
  }
  ```

- 若使用 Vue Router history 模式，需配置：

  ```nginx
  location / {
      try_files $uri $uri/ /index.html;
  }
  ```

  保存后执行：`nginx -t && nginx -s reload`。

### 5. 服务器上的 .env

在项目根目录（如 `/www/wwwroot/rag_web`）下创建 `.env`，内容与本地类似，填写服务器专用的 API Key 和管理员密码。后端从项目根目录的 `.env` 读取（config 使用 PROJECT_ROOT）。

### 6. 数据与权限

运行后会在项目根目录下生成 `data/`（SQLite 与各图谱数据），请保证运行用户对该目录有写权限，例如：`chown -R www:www /www/wwwroot/rag_web/data`。

---

## 三、调试方法

1. **后端接口**：本地访问 http://127.0.0.1:8000/docs 使用 Swagger。公开接口：`GET /api/graphs`、`POST /api/query`；管理员接口需在请求头加 `Authorization: Bearer <token>`（token 来自 `POST /api/admin/login`）。
2. **前端代理与跨域**：本地开发时 Vite 已将 `/api` 转到 8000；部署后由 Nginx 转发同域 `/api`。若前端单独部署到其它域名，需在后端 `main.py` 中设置 CORS。
3. **登录 401 或 token 失效**：检查 .env 中 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 与登录一致；`SECRET_KEY` 修改会导致旧 token 失效。
4. **查询 500 或超时**：查看后端日志；确认 `DEEPSEEK_API_KEY`、`SILICONCLOUD_API_KEY` 正确；大图谱可适当调大 Nginx 与 uvicorn 超时。
5. **图谱列表为空或创建失败**：先登录管理后台创建图谱；确认上传 .txt、编码 UTF-8/GBK、`data/` 可写；LightRAG 报错时检查 `pip show lightrag-hku`。
6. **今日查询与限额**：管理后台统计来自 `GET /api/admin/stats`；超限额后 `POST /api/query` 返回 429。
7. **宝塔路径**：若项目路径与本文不同，请将 `/www/wwwroot/rag_web` 替换为实际路径；Nginx 配置一般在宝塔「网站」->「设置」->「配置文件」。
8. **日志**：后端日志见 uvicorn 或 Supervisor 的 stdout/stderr 配置；可自行在 app 中增加 logging 写到 `logs/`。

---

## 四、常用命令速查

| 操作       | 命令 |
|------------|------|
| 本地后端   | `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| 本地前端   | `cd frontend && npm run dev` |
| 前端构建   | `cd frontend && npm run build` |
| API 文档   | http://127.0.0.1:8000/docs |
| 管理员登录 | 前端访问 `/login`，或 `POST /api/admin/login` 获取 token |

---

## 五、Git 与 GitHub（Cursor 内）

1. **打开源代码管理**：左侧边栏「源代码管理」图标，或 `Ctrl+Shift+G`。
2. **初始化仓库**：若未检测到 Git，点击「初始化存储库」，或终端执行 `git init`。
3. **.gitignore**：项目已配置忽略 `.env`、`data/`、`node_modules/`、`frontend/dist` 等。
4. **提交**：在源代码管理中暂存、填写提交说明、提交；或终端：`git add . && git commit -m "说明"`。
5. **在 GitHub 建仓**：GitHub 上 New repository，不要勾选「Add a README」。
6. **关联并推送**（将 `YOUR_USERNAME`、`RAG_web` 换成你的）：
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/RAG_web.git
   git branch -M main
   git push -u origin main
   ```
   SSH：`git remote add origin git@github.com:YOUR_USERNAME/RAG_web.git`
7. **日常**：修改后暂存、提交、点「同步」或「推送」；或 `git add . && git commit -m "说明" && git push`。

---

## 技术栈

- 后端：FastAPI、SQLite、LightRAG（lightrag-hku）、JWT 认证
- 前端：Vue 3、Vue Router、Vite、Axios、Tailwind CSS
- LLM：DeepSeek；Embedding：硅基流动 BAAI/bge-m3

如有问题，请先查看后端与 Nginx 日志，再根据报错对照上述条目排查。

## License

MIT
