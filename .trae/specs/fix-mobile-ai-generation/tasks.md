# Tasks

- [x] Task 1: `models/ai_provider.py` 增加 `reinitialize()` 方法
  - [x] 在 `AIManager` 类中添加 `reinitialize()` 方法，先关闭现有providers（如有disconnect/close方法则调用），再调用 `initialize()`
  - [x] 无需更改 `initialize()` 的现有逻辑

- [x] Task 2: `mobile/views/settings.py` 保存API密钥后触发AI重新初始化
  - [x] 在 `_save()` 方法中，保存配置成功后调用 `ai_manager.reinitialize()`
  - [x] 显示SnackBar反馈用户"已保存，可用模型: siliconflow"

- [x] Task 3: `mobile/views/ai_generate.py` 完全重写——修复线程UI更新+AI调用链
  - [x] 引入 `utils/logger` 记录所有AI调用日志，方便排查问题
  - [x] 重写 `_build_new` 和 `_build_cont`：扩大日志区至250px，进度条和状态/字数分行展示
  - [x] 重写 `_worker`：使用 `page.run_thread_safe` 包装所有UI更新回调
  - [x] AI调用后增加空结果/错误结果检查，失败时日志标注原因
  - [x] 每章生成成功后立即 `save_chapter(cid, result)` 并更新累计字数
  - [x] 全部完成后状态文字改为"✅ 全部完成"

- [x] Task 4: 编译+导入+启动验证
  - [x] 编译全部6个文件确保无语法错误
  - [x] 导入验证确保无 import 错误
  - [x] 启动验证确保 exit code 为 0

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 is independent (can run in parallel with Task 1+2)
- Task 4 depends on Task 1, Task 2, Task 3
