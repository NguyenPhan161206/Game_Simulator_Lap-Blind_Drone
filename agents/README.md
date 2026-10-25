# Hướng dẫn agent theo dự án

[AGENTS.md](../AGENTS.md) là nguồn hướng dẫn chung. Đọc nó trước mỗi nhiệm vụ; sau đó đọc hướng dẫn cục bộ ở phần đang làm.

## Codex
- Codex tự đọc AGENTS.md tại gốc dự án. Các quy tắc quan trọng không phụ thuộc file cấu hình bổ sung.
- Cấu hình di động nằm ở [configs/agents/codex.toml](../configs/agents/codex.toml).
- Chạy: `python3 tools/run_codex.py`. Xem lệnh mà không mở phiên: `python3 tools/run_codex.py --dry-run`.
- Launcher chuyển từng khóa cấu hình sang tùy chọn chính thức `codex -c key=value`; không đổi cấu hình toàn máy, tài khoản, model hay quyền sandbox.
- File trong configs/ không được Codex tự nạp khi chạy trực tiếp lệnh `codex`. Khi đó AGENTS.md vẫn là điểm vào chung.
- Trong checkout thông thường có thể dùng cùng nội dung ở .codex/config.toml sau khi người dùng thiết lập trust của dự án. Phiên managed hiện tại bảo vệ .codex nên dùng launcher.
- Không tự đặt trust, ghi đè developer instructions toàn cục hoặc vô hiệu cơ chế phê duyệt.

## Các agent khác
CLAUDE.md, GEMINI.md và .github/copilot-instructions.md dẫn về cùng AGENTS.md. Nếu công cụ không tự đọc một trong các file này, cung cấp AGENTS.md làm tài liệu đầu vào. Không giả định mọi agent có cùng cơ chế tự nạp.

## Quy trình một nhiệm vụ
1. Đọc phạm vi, quyết định và phần kiến trúc liên quan.
2. Kiểm tra trạng thái hiện tại; nêu giả định quan trọng.
3. Thay đổi trong phạm vi đã được yêu cầu.
4. Chạy kiểm tra thích hợp; báo đúng bằng chứng.
5. Cập nhật [handoff](handoff-template.md) khi bàn giao công việc dài.

Tài liệu vai trò trong [roles.md](roles.md) là checklist trách nhiệm, không tự kích hoạt subagent.

Nguồn chính thức đã đối chiếu ngày 2026-10-25:
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference)
