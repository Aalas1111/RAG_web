# LightRAG Web

基于 LightRAG 的知识图谱问答网站，前后端分离：**Vue 3** 前端 + **FastAPI** 后端。

## 功能概览

- **主界面**：选择现成数据图谱（名称 + 简介），选择查询模式（native / local / global / hybrid，默认 hybrid），在对话框中对图谱内容进行 query，下方展示 AI 生成回答。
- **管理员**：通过 `/login` 登录管理后台，可：
  - 上传 txt 构建新数据图谱（命名 + 简介）
  - 上传 txt 对现有图谱增量更新
  - 删除图谱、修改图谱名称或简介
  - 查看今日各图谱 query 次数，并修改各图谱每日 query 限额

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
├── frontend/          # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/     # 首页、登录、管理后台
│   │   ├── router/
│   │   └── api.js
│   ├── package.json
│   └── vite.config.js
├── data/              # 运行时生成：图谱数据与 SQLite
├── .env               # 配置与 API Key（勿提交到 Git）
├── .env.example
├── requirements.txt   # 根目录依赖说明
├── README.md
└── tutorial.txt       # 部署与调试教程
```

## 快速开始（本地）

1. **环境**：Python 3.10+，Node.js 18+
2. **配置**：复制 `.env.example` 为 `.env`，填写 DeepSeek、硅基流动 API Key 及管理员账号。
3. **后端**：
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. 浏览器访问：`http://localhost:5173`（前端会代理 `/api` 到后端 8000 端口）。

详细本地部署、服务器部署（CentOS8 + 宝塔）及调试方法见 **tutorial.txt**。

## 技术栈

- 后端：FastAPI、SQLite、LightRAG（lightrag-hku）、JWT 认证
- 前端：Vue 3、Vue Router、Vite、Axios
- LLM：DeepSeek；Embedding：硅基流动 BAAI/bge-m3

## License

MIT
