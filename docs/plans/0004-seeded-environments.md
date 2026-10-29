# Kế hoạch 0004 — hoàn thiện môi trường và đánh giá trước huấn luyện

**Trạng thái hiện tại:** Hoàn tất seeded protocol v1; validation/test đã exposed. [Bằng chứng](../research/2026-10-26-seeded-environments.md). Các bước và giới hạn lúc thực thi bên dưới là lịch sử, không là việc đang chờ chạy lại.

Ngày: 2026-10-26. Yêu cầu: lập kế hoạch chi tiết rồi thực hiện trọn giai đoạn tiếp theo sau baseline v1.

## Đầu ra và điều kiện hoàn thành

Giai đoạn này hoàn thành khi có bộ sinh tái lập theo seed, chứng cứ hình học cho các ca khả thi, tập tách biệt, protocol được khóa trước khi đọc kết quả, runner Webots thực, thống kê mọi outcome và báo cáo giới hạn. Không yêu cầu baseline đạt 100%; không điều chỉnh thuật toán theo kết quả test. Chưa huấn luyện hoặc giảm cảm biến; không mở rộng logistics/hardware.

Sáu family: empty, single_block, staggered_blocks, narrow_gap, u_trap, blocked_goal. Năm family đầu phải có đường ngang kiểm chứng với hull bảo thủ; blocked_goal là đối chứng âm có đích nằm trong solid. Ngõ cụt chữ U vẫn có lối thoát, không được gắn nhãn bất khả thi chỉ vì baseline mắc kẹt.

Đa dạng hóa kích thước/độ lệch vật cản, vị trí start/goal, tịnh tiến/phản chiếu/quay world theo bội 90 độ và yaw ban đầu liên tục. Giữ độ cao đích 1.5 m, cảm biến/động lực học lý tưởng v1. Các số dưới đây là protocol kỹ thuật v1, không phải ngưỡng chất lượng cho mọi nhiệm vụ giao hàng.

## Các bước theo thứ tự

| Bước | Việc thực hiện | Điều kiện qua bước |
|---|---|---|
| 1 | Audit Git, kiến trúc, protocol cũ, thiết bị và simulator | Worktree sạch; bảo toàn lịch sử; xác minh đường chạy local/CI |
| 2 | Ghi kế hoạch và protocol | Định nghĩa family/split/seeds/timeout/metrics và cách xử lý thất bại trước chạy |
| 3 | Sinh case tái lập và kiểm định hình học | Geometry/collision/sensing nhất quán; start/goal an toàn; witness route có đoạn không cắt inflated AABB; ca âm có chứng cứ đích trong solid |
| 4 | Tách tập và khóa | train_reserved: 2 seed/family; development: 2; validation: 1; test: 1. Tổng 36 case, seed và geometry fingerprint không trùng; khóa manifest, code baseline/runtime/evaluator và tham số trước Webots test |
| 5 | Tích hợp runner và supervisor | 48 lượt paired trên 24 case thuộc dev/validation/test; 12 case train_reserved chỉ sinh, không chạy huấn luyện; yaw, geometry và reset được áp dụng trước lượt, không teleport/route leak trong lượt |
| 6 | Test logic/hợp đồng + regression | Kiểm tra tái lập, chia tập, invalid geometry, route/corner crossing, tamper lock, kết quả summary; legacy smoke/navigation vẫn đạt |
| 7 | Chạy thật dev → validation → test với baseline đã khóa | Mỗi lượt có manifest hash, commit, policy, family/seed, outcome; mọi failure được giữ. Nếu sửa infrastructure sau exposure phải ghi rõ, không gọi lại dữ liệu đó là test mới |
| 8 | Rà soát và bàn giao | Đọc kết quả theo split/family, xem ảnh/trace khi có; tài liệu tái hiện, giới hạn, quyết định readiness; đồng bộ Git không force/overwrite |

## Protocol dự kiến khóa trước lần chạy đầu

- Seed ranges: train_reserved 11001/11002; development 21001/21002; validation 31001; test 41001. Family là một phần khóa RNG để các family không tái dùng cùng random stream.
- Tham số navigation giữ nguyên v1; không tune trên validation/test trong giai đoạn này. File lock ghi SHA256 code/config/manifest. Chạy test yêu cầu khóa hợp lệ, không có cờ bỏ qua.
- Hai policy direct/reactive chạy cùng case, cùng pose/yaw ban đầu, reset và warmup 2 s. Mỗi cặp chạy một lần; nhiều seed môi trường không phải nhiều seed huấn luyện.
- Scoring giữ radius 0.5 m, stop speed 0.18 m/s, dwell 1 s; timeout 75 s cho seed suite, physics 16 ms. Collision/bounds ưu tiên thành công; không chấm success sau deadline.
- Báo mọi outcome, tỷ lệ thành công theo split/family, thống kê chỉ trên success có nhãn rõ; ca âm tách riêng. Không coi grid witness là đường tối ưu hoặc năng lực của drone.
- Chứng minh khả thi chỉ trong lát ngang cố định, hull bảo thủ hình tròn bao hộp thân + margin 0.12 m; chưa bảo đảm động lực học/rotor hoặc giải pháp 3D.
- Gate hoàn thành là pipeline đúng: đủ paired episodes; thông tin đặc quyền không vào mission; ca trống hoàn thành; ca âm không bị chấm success; direct single_block được chấm collision. Các family khó có thể thất bại và vẫn phải báo. Không đặt ngưỡng thành công cho reactive sau khi thấy số liệu.

## Tiến độ

- [x] Bước 1: main 555f59f, worktree sạch; GitHub connector đọc được remote đúng SHA. Local không có Webots; kiểm chứng simulator qua CI như mốc trước.
- [x] Bước 2: kế hoạch được ghi trước triển khai.
- [x] Bước 3: sinh đủ 36 case, mọi ca khả thi có witness đã kiểm tra đoạn; ca âm có đích trong solid. Không đưa witness vào controller.
- [x] Bước 4: split/seed/geometry không trùng; đã khóa trước lần chạy Webots seeded đầu tiên. Protocol SHA256 96872282fc7df5029453ed684d0e73e9305137c3d6907736869b2e04bf64b90f. Baseline không thay đổi.
- [x] Bước 5: runner/supervisor áp dụng fixture/yaw/reset; chạy đủ 48 lượt paired thật, không teleport/route leak trong lượt.
- [x] Bước 6: 42 unit test đạt; 12 smoke checks và tám lượt diagnostic cũ đạt trên Webots CI.
- [x] Bước 7: CI 40251251346 success, cùng runtime 373b002 và protocol/manifest cả ba split; không tune. Reactive dev 8/10, validation 4/5, test 5/5 ca khả thi; giữ ba U collision và mọi ca âm.
- [x] Bước 8: đã xem ba ảnh U và sáu trace review; lưu [báo cáo đầy đủ/JSON](../research/2026-10-26-seeded-environments.md), hướng dẫn tái hiện và quy tắc test exposure. Bàn giao theo standing Git policy của workspace.

Kết luận: giai đoạn môi trường/đánh giá trước huấn luyện hoàn thành trên CI. Baseline chưa đủ vững ở U; narrow_gap success không chứng minh đi xuyên khe. Chưa train, giảm cảm biến hoặc chạy GUI local. Không thay code/config đã khóa sau khi thấy test.
