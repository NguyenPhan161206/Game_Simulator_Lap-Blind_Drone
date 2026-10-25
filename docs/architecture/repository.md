# Cây thư mục và trách nhiệm

```text
.
├── AGENTS.md                 # Quy tắc dùng chung cho agent
├── CLAUDE.md / GEMINI.md     # Điểm vào dẫn về AGENTS.md
├── agents/                   # Workflow, vai trò và mẫu bàn giao
├── configs/                  # TOML: manifest và preset dự thảo
│   ├── agents/
│   ├── environments/
│   ├── experiments/
│   ├── sensors/
│   └── vehicles/
├── docs/
│   ├── architecture/         # Trách nhiệm và hợp đồng dữ liệu
│   ├── decisions/            # Quyết định có lý do và trạng thái
│   └── research/             # Câu hỏi, kế hoạch và bằng chứng
├── simulation/webots/        # World, robot, entry point và plugin
├── src/blind_drone/          # Các module độc lập simulator + adapter
├── tests/                    # Nơi đặt kiểm tra hành vi khi có logic
├── tools/                    # Kiểm tra scaffold, launcher Codex, Git helper
├── data/                     # Dữ liệu sinh, không đưa vào Git
├── models/                   # Model/checkpoint sinh, không đưa vào Git
├── artifacts/                # Log/replay/báo cáo sinh, không đưa vào Git
└── .github/                  # CI và hướng dẫn Copilot
```

Thư mục có README mô tả trách nhiệm để giữ được trong Git; không tạo file runtime rỗng giả thành một simulator đã hoạt động. Mọi đường dẫn module có trong configs/project.toml phải tồn tại.

.local/ chỉ dành cho trạng thái máy và Git metadata thay thế trong workspace managed; không được commit. Checkout Git thông thường không cần nó.
