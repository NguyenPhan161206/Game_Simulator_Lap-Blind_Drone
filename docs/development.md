# Phát triển và kiểm tra

## Milestone hiện tại

Bản thử Webots v1 có world primitive, điều khiển thủ công, cảm biến và smoke runner. Mốc kế tiếp là [navigation baseline và evaluator](navigation-v1.md), với [kế hoạch từng bước](plans/0003-navigation-baseline.md). Python 3.11+ đủ cho các kiểm tra core; chưa cần pip install. Webots là dependency riêng khi chạy simulator. Huấn luyện model chưa thuộc mốc này.

Mốc hiện tại mở rộng sang [môi trường có seed và protocol khóa](seeded-environments-v1.md). make check kiểm tra cả manifest/checksum. Các case test đã đọc không được dùng để tune rồi báo lại là unseen. [Quy tắc Git](../AGENTS.md#standing-git-authorization-for-this-workspace) cho phép tự commit/push theo milestone, với kiểm tra phù hợp và bảo toàn thay đổi khác.

[Giai đoạn v2](navigation-v2.md) đã kiểm chứng observation grid/guard/planner với lock riêng, 64 unit test và 108 lượt chính thức. make check kiểm tra cả v1/v2; launcher mới là tools/run_navigation_v2.py. Sau exposure không sửa runtime/config đã khóa để tune rồi dùng lại cùng test như unseen.

```bash
python3 tools/check_scaffold.py
python3 tools/build_lab.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/run_codex.py --dry-run
```

## Cấu hình agent

Đọc [agents/README.md](../agents/README.md). Cấu hình portable dùng launcher; chạy trực tiếp Codex vẫn nhận root AGENTS.md. Model, tài khoản, quyền và trust do môi trường/người dùng quản lý.

## Git trong workspace managed

Checkout bình thường dùng Git như thường lệ. Trong phiên AI_Lap hiện tại, .git do môi trường quản lý và đặt chỉ đọc; nó có thể xuất hiện dưới dạng metadata khởi tạo rỗng. Không sửa quyền hoặc xóa nó.

[tools/git.sh](../tools/git.sh) ưu tiên metadata cục bộ đã khởi tạo trong .local/git; nếu không có thì dùng repo chuẩn. Cách này giữ đúng lịch sử của workspace khi môi trường managed tạo thêm .git rỗng/chỉ đọc. Lệnh helper không tự khởi tạo hoặc thay thế repository.

```bash
bash tools/git.sh status --short --branch
bash tools/git.sh diff --check
```

Khi clone repo từ GitHub vào thư mục thông thường, helper tự dùng .git bình thường. .local/ không được push.

## Bước triển khai tiếp theo

Theo [kế hoạch thực hiện](plans/0002-webots-minimal-lab.md) và [hướng dẫn lab v1](lab-v1.md). Các mốc sau vẫn giữ thứ tự:

1. Chốt đặc tả môi trường tối thiểu và các tham số còn mở.
2. Chọn phiên bản Webots/asset, ghi provenance.
3. Tạo world và điều khiển thủ công; kiểm tra va chạm.
4. Kiểm tra đầu ra cảm biến và ranh giới quan sát.
5. Thêm baseline và đánh giá nhiệm vụ.
6. Chỉ sau đó tích hợp huấn luyện.

## Trạng thái kiểm chứng

CI scaffold kiểm tra cấu trúc, TOML và các bất biến khai báo. Workflow Webots riêng cài R2025a, chạy world thực trên Xvfb và lưu bằng chứng. Các kiểm tra này chưa chứng minh độ chính xác so với phần cứng thật hoặc chất lượng AI. GUI/keyboard local và simulator CI được báo riêng.
