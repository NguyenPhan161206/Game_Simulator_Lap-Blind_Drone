# Development tools

- python3 tools/check_scaffold.py: cấu trúc, TOML, ràng buộc khai báo và link nội bộ.
- python3 tools/build_lab.py [--check]: tạo hoặc kiểm tra world/PROTO từ cấu hình v1.
- python3 tools/install_webots.py [--check]: tarball chính thức R2025a trong .local/; không dùng sudo.
- python3 tools/run_webots.py [--smoke | --navigation]: mở world, kiểm tra môi trường hoặc chạy paired navigation trên simulator thật; có timeout và output riêng. --policy/--case chọn lượt, --realtime để quan sát tự hành.
- python3 tools/report_webots_evidence.py artifacts/<run>: báo dữ liệu kiểm chứng nhỏ; ảnh observer là đầu ra, không vào controller.
- python3 tools/run_codex.py [--dry-run]: launcher Codex với cấu hình dự án.
- bash tools/git.sh status --short --branch: metadata Git của workspace managed hoặc repo thường.

Các công cụ không huấn luyện model hoặc sửa cấu hình agent toàn máy.
