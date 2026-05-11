# 移动端AI生成功能修复 Spec

## Why
移动端AI生成功能存在多个串联Bug：保存API密钥后AI管理器未重新初始化导致"无可用模型"、线程UI更新静默失败导致没有任何视觉反馈、创建空章节名但无内容、缺少实时进度和字数统计。用户体验与桌面端完全不一致。

## What Changes
- **BREAKING**: 无
- `ai_generate.py` 完全重写：修复线程UI更新机制、增加实时进度/字数/日志反馈、修复AI调用链路
- `settings.py` 增加保存后自动重新初始化AI管理器的能力
- `main.py` 增加 `reinit_ai()` 函数供设置页面调用
- `models/ai_provider.py` AI管理器增加 `reinitialize()` 方法支持重新加载

## Impact
- Affected specs: 无
- Affected code: `mobile/views/ai_generate.py`, `mobile/views/settings.py`, `mobile/main.py`, `models/ai_provider.py`

## ADDED Requirements

### Requirement: AI管理器保存后自动重新初始化
系统 SHALL 在用户保存API密钥后自动重新初始化AI管理器以加载新配置。

#### Scenario: 用户保存API密钥后生成可用
- **GIVEN** 用户首次打开APP，AI管理器无可用模型
- **WHEN** 用户在设置页填入硅基流动API Key并点击保存
- **THEN** AI管理器自动重新加载配置，将硅基流动注册为可用模型

### Requirement: AI生成实时进度反馈
系统 SHALL 在AI生成过程中实时更新：进度条值、当前状态文字、日志列表、累计字数字。

#### Scenario: 续写生成显示完整进度
- **GIVEN** 用户在一个已有项目的章节列表页点击"AI续写"
- **WHEN** 用户选择起始章、目标章、每章字数后点击"续写生成"
- **THEN** 进度条从0开始递增，状态文字显示"正在写 第X章 (Y/N)"，日志区实时追加"📚 开始生成... → 📝 第X章 生成中... → ✅ 第X章 完成 - ZZZ字"，累计字数实时更新，全部完成后状态显示"✅ 全部完成"

### Requirement: 章节生成后必须有内容
系统 SHALL 在AI返回结果后调用 `save_chapter` 保存生成的内容。

#### Scenario: 每章生成成功后内容持久化
- **GIVEN** AI接口成功返回章节内容
- **WHEN** `_worker` 线程接收结果
- **THEN** 调用 `chapter_manager.save_chapter(cid, result)` 将内容存入数据库，通过 `chapter_manager.get_chapter(cid).get("content")` 可获取完整内容

## MODIFIED Requirements

### Requirement: `ai_manager` 支持运行时重新初始化
**原**: `ai_manager.initialize()` 仅在启动时调用一次
**改**: 新增 `ai_manager.reinitialize()` 方法，关闭现有provider连接后重新扫描配置，支持随时调用来刷新可用模型列表

### Requirement: 生成页面UI布局优化
**原**: 日志区仅180px高，状态和字数信息挤在同一个Row中
**改**: 日志区扩大到250px，状态文字和累计字数分行显示，进度条在下，布局与桌面端生成对话框视觉一致
