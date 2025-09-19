# API 密钥设置说明

## 重要提示
`API_KEY.py` 文件包含敏感信息，已被添加到 `.gitignore` 中，不会被提交到版本控制。

## 设置步骤

1. 复制模板文件：
   ```bash
   cp API_KEY.py.example API_KEY.py
   ```

2. 编辑 `API_KEY.py` 文件，填入你的真实 API 密钥：
   - 通义千问 QwenVL 系列密钥
   - 零一万物大模型密钥
   - 百度智能云千帆密钥
   - 私有化部署的 API 密钥

3. 确保 `API_KEY.py` 文件不会被意外提交到 git：
   ```bash
   git check-ignore API_KEY.py
   ```

## 安全提醒
- 永远不要将包含真实密钥的 `API_KEY.py` 文件提交到版本控制
- 定期轮换你的 API 密钥
- 如果密钥意外泄露，请立即更换
