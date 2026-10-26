# Development tools

- python3 tools/check_scaffold.py: cấu trúc, TOML, ràng buộc khai báo và link nội bộ.
- python3 tools/build_lab.py [--check]: tạo hoặc kiểm tra world/PROTO từ cấu hình v1.
- python3 tools/build_scenarios.py [--check | --freeze]: sinh manifest có chứng cứ hình học hoặc xác minh khóa; từ chối thay lock đã có.
- python3 tools/check_study.py <dev-result> <validation-result> <test-result>: kiểm tra đủ lượt paired/split/provenance, không bỏ thất bại.
- python3 tools/install_webots.py [--check]: tarball chính thức R2025a trong .local/; không dùng sudo.
- python3 tools/run_webots.py [--smoke | --navigation]: mở world, kiểm tra môi trường hoặc chạy paired navigation trên simulator thật; có timeout và output riêng. --policy/--case chọn lượt, --realtime để quan sát tự hành.
- python3 tools/report_webots_evidence.py artifacts/<run>: báo dữ liệu kiểm chứng nhỏ; ảnh observer là đầu ra, không vào controller.
- python3 tools/run_codex.py [--dry-run]: launcher Codex với cấu hình dự án.
- bash tools/git.sh status --short --branch: metadata Git của workspace managed hoặc repo thường.

Các công cụ không huấn luyện model hoặc sửa cấu hình agent toàn máy.

V2 độc lập: build_navigation_v2.py [--check | --freeze] tạo/check world/manifest/lock; run_navigation_v2.py chạy development/frozen splits; check_navigation_v2.py kiểm tra ba result đủ 108 lượt; report_navigation_v2.py đưa evidence nhỏ và failure snapshot ra CI log. --realtime để xem, --no-rendering để đánh giá số không xuất ảnh. [Chi tiết](../docs/navigation-v2.md).

Seed suite: python3 tools/run_webots.py --navigation --suite seeded --split development (hoặc validation/test). [Protocol và giới hạn](../docs/seeded-environments-v1.md).
