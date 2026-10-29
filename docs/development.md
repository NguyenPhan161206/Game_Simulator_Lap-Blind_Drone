# Phát triển và kiểm tra

## Trạng thái hiện tại — 2026-10-30

Đang ở mốc 7A, đã hoàn tất [A/A khởi tạo 0019](research/2026-10-30-initialization-aa.md): source `97be9a0`, CI 40911479243, 189 tests và 96 episode/72 process. 36/36 so sánh cold đạt precision gate, raw review local trên worktree sạch khớp CI. Đây là preflight, chưa là quality gate retention/held-out. V4 và DATA-03/04 giữ kết quả development lịch sử; chưa ML hoặc phần cứng.

Đợt [0017](plans/0017-maintenance-and-retention-audit.md) đã hoàn tất củng cố/đối chiếu log; bước A/A B của [0018](plans/0018-retention-study-proposal.md) đã thực thi riêng theo [0019](plans/0019-initialization-aa-development.md). Bước C–F vẫn cần thiết kế retention mới: cold-isolated cho cả hai arm, v4 full-history làm đối chứng, accounting/budget công bằng và một candidate/ngưỡng đăng ký trước chạy. Không suy quyền mở held-out từ việc preflight đạt.

V3 đã đóng với validation âm 87/100 mỗi arm, dưới ngưỡng 95%; giữ test chưa mở. Không chạy lại validation/test, sửa frozen runtime hoặc tái sinh lock để cải thiện outcome. V1/v2 validation/test đã exposed; nghiên cứu tiếp dùng version/protocol và split mới.

## Kiểm tra source

Python 3.11+ đủ cho core checks, không cần Webots hoặc ML:

```bash
make check
python3 tools/run_codex.py --dry-run
bash tools/git.sh diff --check
```

`make check` kiểm scaffold, TOML/link source, generated assets, bốn khóa v1/v2/v3 và toàn bộ unit tests. Đây không phải bay simulator, thử GUI hoặc bằng chứng hardware.

Scaffold checker bỏ phần sinh trong ba thư mục root artifacts/data/models, vẫn kiểm README của mỗi thư mục. File export `codex-session-*.md` tại root được giữ local/ignored và không được diễn giải là tài liệu source. Source/tài liệu mới chưa tracked vẫn được kiểm; thư mục tên artifacts bên trong docs không bị bỏ. Không dùng cơ chế này để che lỗi source hoặc nới kiểm tra khóa.

Hash khóa tính theo byte: thiếu ký tự xuống dòng cuối file cấu hình cũng khiến mismatch. Phục hồi đúng bản đã khóa khi có khác biệt định dạng ngoài ý muốn; không chạy `--freeze` để cập nhật khóa. [Báo cáo 0017](research/2026-10-29-retention-failure-audit.md) ghi lỗi checkout và cách khôi phục.

Webots là dependency riêng. Runtime/lab changes cần simulator checks theo [AGENTS.md](../AGENTS.md); thiếu executable phải báo lỗi. Công việc tooling/tài liệu/offline ở 0017 không thay runtime và không chạy thêm Webots.

## Git trong workspace managed

Đọc [quyền Git thường trực](../AGENTS.md#standing-git-authorization-for-this-workspace). Normal Git có thể nhìn thấy metadata .git rỗng/chỉ đọc do môi trường quản lý. Không đổi quyền hoặc xóa nó.

[tools/git.sh](../tools/git.sh) dùng .local/git nếu có, nếu không dùng repository chuẩn; helper không tự khởi tạo/thay thế repo:

```bash
bash tools/git.sh status --short --branch
bash tools/git.sh diff --check
```

Kiểm tra status/diff, collector flock và remote trước sửa/commit/push; stage explicit task-owned paths, giữ công việc khác. Dùng Git/SSH khi có thể; nếu lỗi sandbox/network, xin escalation theo môi trường. Connector GitHub là kênh thay thế được cho phép khi phù hợp; kiểm khớp tree/commit, không đổi remote hoặc force-push. Feature push không đồng nghĩa đã tích hợp main; main chỉ cập nhật sau gates và remote read mới.

## Lịch sử và hướng dẫn tái hiện

Các kế hoạch 0002–0016 ghi phạm vi và trạng thái lúc thực thi. Các bước “tiếp theo/chưa có GUI” trong mốc cũ không thay thế trạng thái hiện tại ở đầu tài liệu này.

| Mốc hoàn tất | Nguồn / giới hạn |
|---|---|
| Webots v1, baseline/evaluator | [Lab](research/2026-10-25-webots-v1-smoke.md), [navigation v1](research/2026-10-26-navigation-v1.md); simulator CI, không phải phần cứng |
| Seeded v1 và observed navigation v2 | [Seeded](research/2026-10-26-seeded-environments.md), [v2](research/2026-10-26-navigation-v2.md); các test đã exposed |
| Desktop/manual và mapped | [Nghiệm thu cuối](research/2026-10-27-local-acceptance-complete.md), runtime `39c34af`; LOC-01–09 đạt, không hard realtime |
| Thiết kế/runtime v3 | [Thiết kế](research/2026-10-27-research-protocol-v3.md), [development](research/2026-10-28-cadence-v3-development.md); design lock riêng runtime lock |
| Validation v3 | [480 episode/127 tests](research/2026-10-28-cadence-v3-validation.md), source `0c5f598`; kết luận âm, test đóng |
| Chẩn đoán/GOAL-23 v4 | [Offline](research/2026-10-28-navigation-start-diagnostics.md), [v4](research/2026-10-28-observed-detour-v4.md); development, không held-out |
| A/A initialization | [0019/source/CI/raw review](research/2026-10-30-initialization-aa.md); 12 exposed cases, chưa retention treatment |
| DATA-03/04 | [Occupied-only](research/2026-10-29-data03-occupied-only.md), [TTL](research/2026-10-29-data04-hit-ttl.md); development đã exposed |

[Runtime v3](runtime-v3.md), [local acceptance](local-acceptance.md), [cây phiên bản](version-history.md), [tooling](../tools/README.md) và [hai checklist](../CHECKLIST_DU_AN.md) giữ lệnh và nguồn chi tiết. Collector local dùng `python3 tools/local_session.py accept`; nghiệm thu bàn phím/quan sát vẫn là bằng chứng riêng của người thao tác, không tự điền phiếu hoặc sao chép giữa các run.

## Cấu hình agent

Đọc [agents/README.md](../agents/README.md). Root AGENTS.md là nguồn chung; launcher cấu hình portable không thay model, quyền, trust hoặc tài khoản toàn máy. [Mục tiêu nghiên cứu](../CHECKLIST_MUC_TIEU_NGHIEN_CUU.md) phân biệt hoàn tất phép thử với đạt giả thuyết và phần test không đủ điều kiện thực hiện.
