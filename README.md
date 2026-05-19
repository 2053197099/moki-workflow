# Moki Workflow

沐柒Moki 是一个半自动化自媒体出图流程，用于从 Midjourney 风格种子发现，到飞书多维表格管理，再到高清修复、Logo 融合和平台发布准备。

## Workflow

1. 刷种子
   - 在 Midjourney 网页版提交随机风格种子命令。
   - 标准命令：`1 --sref random --ar 1:1`

2. 刷种子图
   - 从飞书种子表读取候选种子。
   - 对每个种子生成四类测试图：`person`、`animal`、`architecture`、`environment`。
   - 标准命令示例：`person --ar 1:1 --sref 123456789`

3. 刷风格图
   - 选择评分较高的种子，分析适合的东方美学提示词。
   - 生成 9:16 成片候选。
   - 标准命令示例：`sacred snowy mountain --ar 9:16 --sref 123456789`

4. 融图
   - 对成片进行高清放大、轻度修复、质量检查。
   - 融入沐柒Moki Logo，保持原图风格不变。

5. 上传风格
   - 准备抖音和小红书图文草稿。
   - 上传前由人工确认，避免误发布。
   - 发布后把平台截图回填飞书。

## Feishu Tables

当前流程使用两张飞书表：

- 种子图与评分：保存风格种子、四类种子图、评分和种子状态。
- 风格图生成与最终上传：保存风格图、最终上传图、抖音截图、小红书截图和发布状态。

表格链接不写入代码。运行脚本时通过环境变量配置。

## Local Setup

复制 `.env.example`，设置飞书应用凭证和表格 ID：

```powershell
$env:FEISHU_APP_ID="your_app_id"
$env:FEISHU_APP_SECRET="your_app_secret"
$env:MOKI_SEED_APP_TOKEN="seed_base_app_token"
$env:MOKI_SEED_TABLE_ID="seed_table_id"
$env:MOKI_SEED_VIEW_ID="seed_view_id"
$env:MOKI_STYLE_APP_TOKEN="style_base_or_wiki_token"
$env:MOKI_STYLE_TABLE_ID="style_table_id"
$env:MOKI_STYLE_VIEW_ID="style_final_view_id"
```

运行健康检查：

```powershell
python moki_health_check.py
```

生成当前数据统计：

```powershell
python moki_feishu_stats.py
```

## Repository Notes

生成图片、发布截图、本地测试截图和 Logo 源文件默认不提交到 GitHub。它们会被 `.gitignore` 排除。

公开仓库不要提交：

- 飞书 App Secret
- 平台登录 Cookie
- 生成图片原图或平台草稿截图
- 任何包含账号隐私的截图

## Docs

- `moki-workflow.md`: 当前跑通流程
- `moki-dashboard-plan.md`: 飞书仪表盘建议
- `moki-optimization-plan.md`: 后续优化清单
