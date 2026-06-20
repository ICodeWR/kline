# 贡献指南

感谢你考虑为本项目做出贡献！

## 如何贡献

### 报告 Bug

1. 在 Issues 中搜索是否已有相同问题
2. 如未找到，创建新 Issue，包含：
   - 运行环境（Python 版本、操作系统）
   - 复现步骤
   - 预期行为与实际行为
   - 相关截图或错误日志

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 编写代码并确保通过全部测试
4. 提交更改：`git commit -m "feat: 添加xxx功能"`
5. 推送分支：`git push origin feature/your-feature`
6. 创建 Pull Request

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构
- `style:` 代码格式调整

### 开发环境

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 运行测试

提交前请确保所有测试通过：

```bash
python -m pytest test_stock_data.py test_app.py -v
```

### 代码风格

- 遵循 PEP 8 规范
- 保持与现有代码风格一致
- 函数和类添加必要的文档字符串