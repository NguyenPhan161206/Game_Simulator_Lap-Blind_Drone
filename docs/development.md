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

[Cây phiên bản và nguồn kiểm chứng](version-history.md) ghi các mốc đã xuất bản. Nhánh feat/local-acceptance có CI kiểm tra collector bằng Webots thật dưới Xvfb, tách khỏi xác nhận GUI/bàn phím laptop. [Kế hoạch tích hợp](plans/0007-github-integration.md) yêu cầu kiểm tra từng mốc rồi commit/push; chỉ fast-forward main khi gate phù hợp đạt. Các nhánh lịch sử được giữ, không force-push hoặc xóa để làm graph trông gọn hơn.

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

## Bước hiện tại sau nghiệm thu local

Mốc 6 đã hoàn tất [thiết kế cadence v3](protocols/range-cadence-v3.md), [92 unit tests/CI](research/2026-10-27-research-protocol-v3.md). Chạy `make check` để kiểm scaffold, v1/v2, 480 case mới/khóa thiết kế và tests; không cần Webots hoặc ML. `python3 tools/build_research_v3.py` tái sinh fixture đầy đủ vào artifacts ignored, không cấp chúng cho navigation. Không chạy lại `--freeze` để cập nhật thiết kế.

Tiếp theo triển khai adapter acquisition 32/64 ms, kế toán dữ liệu và runner/evaluator version mới, chỉ kiểm chứng trên development; giữ [mục tiêu phát sinh](../CHECKLIST_MUC_TIEU_NGHIEN_CUU.md) mở tới khi có runtime evidence. Sau đó tạo runtime lock riêng trước validation/test. Chưa huấn luyện hoặc thực thi đánh giá v3; v1/v2 runtime và test exposure được giữ nguyên. Các mục mốc kế tiếp trong phần đầu tài liệu là lịch sử nền tảng, không thay thứ tự này.

## Bàn giao 7A — 2026-10-28

[Runtime v3](runtime-v3.md) đã triển khai/khóa tại source `0c75ce2`; [local/CI development](research/2026-10-28-cadence-v3-development.md) mỗi nơi có 240 lượt, rate giảm 50% nhưng success reference 45/50, candidate 46/50. `make check` kiểm runtime lock riêng; CI checkout đủ history để đối chiếu implementation commit. Validation/test chưa chạy, chưa kết luận giữ chất lượng hoặc ML. Phần “tiếp theo triển khai” phía trên ghi trạng thái mốc 6, nay được thay bằng bàn giao này.

## Bàn giao validation v3 — 2026-10-28

[Validation duy nhất](research/2026-10-28-cadence-v3-validation.md) tại source `0c5f598` đã qua 127 tests và 480 lượt CI, local review raw khớp. Success 87/100 mỗi arm không đạt 95%; theo protocol dừng ở kết quả âm, giữ test chưa chạy. Hai lock v3 và legacy v1/v2 không đổi. Không sửa thuật toán v3 hoặc tiếp tục test khi gate chưa đạt; GOAL-22 là đề xuất cho nghiên cứu version mới.

## Thực thi DATA-03 — occupied-only persistent map

Thiết kế/kế hoạch hiện hành ở [ADR 0008](decisions/0008-data03-occupied-only.md) và [plan 0015](plans/0015-data03-occupied-only.md). `make data03` dựng world riêng từ 88 case development đã lộ của v4; Webots cần chạy trong CI/Xvfb. Candidate giữ free evidence tới acquisition tiếp theo, giữ occupied hits trong episode và dừng nếu lối không còn được quan sát. Chưa có runtime outcome; DATA-03 checklist vẫn mở cho tới khi raw evidence được review.
