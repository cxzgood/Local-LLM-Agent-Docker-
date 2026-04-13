# Local-LLM-Agent-Sandbox

记录一次本地部署大模型 Agent（Qwen 2.5 Coder）的沙箱隔离与踩坑排障过程。

## 项目背景
在测试大模型自主生成与执行代码时，为了防止 Agent 对宿主机（Windows）物理环境造成破坏，本项目摒弃了传统的裸机运行，基于 Docker 构建了物理隔离的执行沙箱，并打通了容器与宿主机本地模型（Ollama）的跨网通信。最终接入 QQ 机器人实现了基础的交互闭环。

## 核心架构
* **大模型算力**：宿主机运行 Ollama + `qwen2.5-coder:7b` 本地模型。
* **执行沙箱**：OpenClaw 框架部署于 Docker 容器内，限制物理盘访问权限。
* **存储分离**：通过 WSL 2 底层指令，将 Docker 引擎与 Agent 工作区整体挂载至外部数据盘，解决 C 盘存储压力。

---

## 排障记录 (Troubleshooting)

在整个部署与测试链路中，主要解决了以下几个核心冲突：

### 1. 跨平台路径解析错误导致 Agent 崩溃
* **现象**：容器启动正常，但首次接收交互指令时抛出 `500 Internal Error`。
* **排查**：挂载配置文件的 `workspace` 依然是 Windows 格式（`C:\Users\...`），Linux 容器内部拼凑出了 `/app/C:\...` 的畸形路径，导致持久化写入失败。
* **解决**：修改 `openclaw.json`，将路径适配为容器内的绝对路径 `/home/node/.openclaw/workspace`。

### 2. 嵌套沙箱权限缺失 (DooD 架构问题)
* **现象**：Agent 尝试执行代码时，提示 `spawn docker ENOENT`。
* **排查**：配置文件中开启了内部 Sandbox（挂载了 docker.sock），但官方轻量级镜像内未预装 Docker CLI，导致 API 调用失败。
* **解决**：鉴于外层 Docker 已经实现了系统级隔离，为避免过度设计，修改配置 `sandbox: off`，关闭内部沙箱，交由外层容器兜底。

### 3. WSL 2 虚拟磁盘撑爆系统盘
* **现象**：Docker 运行期间宿主机 C 盘空间耗尽导致引擎宕机。
* **排查**：Docker 默认的 `ext4.vhdx` 数据盘随时间膨胀。
* **解决**：使用 WSL 原生命令进行数据盘的导出与异地重建：
  `wsl --export docker-desktop E:\backup.tar`
  `wsl --unregister docker-desktop`
  `wsl --import docker-desktop E:\DockerData E:\backup.tar --version 2`

### 4. 7B 模型 Function Calling 的数据结构幻觉
* **现象**：在下发“全自动编写并运行 B 站热门爬虫”指令时，模型虽然生成了代码，但运行时报 `TypeError`。
* **排查**：7B 模型在处理复杂 API 时出现了“数据结构幻觉”。B 站 API 实际上返回的是 List，但模型凭空伪造了一个 `['vlist']` 字典键，试图用 String 索引 List。同时，小模型在严格格式输出时出现了指令泄露（未触发 JSON RPC，而是直接输出文本）。
* **总结**：小参数模型（7B）在复杂的工具调用链条中稳定性欠佳。在生产环境中，除了提示词约束，依然必须依赖宿主代码进行数据结构的断言与兜底验证。最终通过人工介入沙箱修复脚本并执行，完成链路验证：
  `docker exec openclaw-gateway python3 /home/node/.openclaw/workspace/bilibili_hot.py`
