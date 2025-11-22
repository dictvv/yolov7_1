# MCP Remote tmux Setup Guide

## 配置完成狀態

✅ 遠端環境已準備完成：
- Node.js v22.20.0
- npx 10.9.3 (位於 /usr/bin/npx)
- tmux 3.4
- vast.ai SSH: root@116.122.206.233:20430

✅ MCP 配置文件已創建：
- 主配置：`%APPDATA%\Claude\claude_desktop_config.json`

## 配置文件位置

```
C:\Users\Mike\AppData\Roaming\Claude\claude_desktop_config.json
```

## 當前使用的配置 (推薦)

```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "-p",
        "20430",
        "root@116.122.206.233",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

## 備用配置方案

### 方案 1: 使用 cmd 包裝 (如果遇到兼容性問題)

文件：`claude_desktop_config_backup.json`

```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "cmd",
      "args": [
        "/c",
        "ssh",
        "-p",
        "20430",
        "root@116.122.206.233",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

### 方案 2: 包含本地端口轉發 (如需備用)

文件：`claude_desktop_config_with_forward.json`

```json
{
  "mcpServers": {
    "remote-tmux": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "-p",
        "20430",
        "root@116.122.206.233",
        "-L",
        "8080:localhost:8080",
        "/usr/bin/npx",
        "-y",
        "tmux-mcp"
      ],
      "env": {}
    }
  }
}
```

## 使用方式

1. **重啟 Claude Code**
   - 完全關閉 Claude Code (包括系統托盤)
   - 重新啟動 Claude Code

2. **驗證連接**
   - 在 Claude Code 中，檢查 MCP 狀態
   - 應該能看到 `remote-tmux` 伺服器已連接

3. **測試 tmux 功能**
   ```
   列出所有 tmux sessions
   創建新的 tmux session
   在遠端執行命令
   ```

## 手動測試連接

在 Windows 命令行測試完整命令：

```bash
ssh -p 20430 root@116.122.206.233 "/usr/bin/npx -y tmux-mcp"
```

應該會看到 MCP 伺服器啟動並等待 STDIO 輸入。

## 故障排除

### 如果連接失敗

1. **檢查 SSH 連接**
   ```bash
   ssh -p 20430 root@116.122.206.233 "echo test"
   ```

2. **檢查遠端工具**
   ```bash
   ssh -p 20430 root@116.122.206.233 "node --version && npx --version"
   ```

3. **檢查配置文件語法**
   - 使用 JSON 驗證器確認配置文件格式正確

### 如果遇到參數解析問題

切換到使用 `cmd` 包裝的備用配置：

```bash
copy "%APPDATA%\Claude\claude_desktop_config_backup.json" "%APPDATA%\Claude\claude_desktop_config.json"
```

### 如果需要環境變數

在配置中添加 `env` 欄位：

```json
"env": {
  "PATH": "/usr/local/bin:/usr/bin:/bin",
  "LANG": "en_US.UTF-8"
}
```

## STDIO 模式優勢

- ✅ 不需要在遠端開放額外端口
- ✅ 所有通訊透過 SSH 加密
- ✅ Claude Code 自動管理連接生命週期
- ✅ 不需要設定 HTTP/SSE 伺服器

## 與 HTTP 模式的差異

| 功能 | STDIO 模式 | HTTP 模式 |
|------|-----------|----------|
| 連接方式 | SSH + STDIO | HTTP/SSE |
| 端口需求 | 僅 SSH (22/自定) | SSH + 8080 等 |
| 啟動管理 | Claude Code 自動 | 需手動/守護 |
| 安全性 | SSH 加密 | 需 HTTPS/隧道 |

## 相關文件

- SSH 連接字串：`ssh -p 20430 root@116.122.206.233 -L 8080:localhost:8080`
- 遠端工作目錄：`/workspace/yolov7_1/`
- YOLOv7 訓練指南：見 `VAST_AI_SETUP.md`

## 維護注意事項

1. **vast.ai 實例重啟後**
   - IP 或端口可能改變
   - 需更新配置文件中的連接資訊
   - 重新運行 `setup.sh` 確保環境完整

2. **Node.js 更新**
   ```bash
   ssh -p 20430 root@116.122.206.233 "npm install -g npm@latest"
   ```

3. **檢查 tmux-mcp 更新**
   ```bash
   ssh -p 20430 root@116.122.206.233 "npx -y tmux-mcp@latest --version"
   ```

## 下次使用檢查清單

- [ ] vast.ai 實例運行中
- [ ] SSH 連接正常
- [ ] Node.js/npx 可用
- [ ] Claude Code 配置文件存在
- [ ] Claude Code 已重啟

---

配置時間：2025-10-12
配置人：Claude Code
