# Môi trường có seed và protocol đánh giá v1

Mục tiêu: hoàn thiện môi trường/đánh giá trước huấn luyện, mở rộng các trường hợp khó và kiểm tra toàn bộ luồng thực nghiệm. [Kế hoạch](plans/0004-seeded-environments.md) ghi trạng thái kiểm chứng; test Python không thay chạy Webots.

Đã kiểm chứng đủ 48 lượt trên Webots CI: [báo cáo và bằng chứng](research/2026-10-26-seeded-environments.md). Giai đoạn pipeline hoàn thành; giữ nguyên ba reactive collision ở U và đánh dấu test v1 đã exposed.

## Bộ tình huống

[scenario_suite_v1.toml](../configs/scenario_suite_v1.toml) định nghĩa empty, single_block, staggered_blocks, narrow_gap, u_trap và blocked_goal. Generator dùng SHA256 của family/seed/tên tham số, làm tròn tọa độ/kích thước để tái lập. [Manifest](../configs/scenarios/seeded_v1.json) chứa geometry và chứng cứ kiểm tra.

| Split | Seed | Case | Mục đích |
|---|---|---:|---|
| train_reserved | 11001, 11002 | 12 | Dành sẵn, chưa train/chạy đánh giá |
| development | 21001, 21002 | 12 | Kiểm tra tích hợp và thất bại |
| validation | 31001 | 6 | Đánh giá theo protocol khóa, không tune trong đợt này |
| test | 41001 | 6 | Đọc sau khi khóa baseline; không tune rồi gọi lại là unseen |

Seed và fingerprint start/goal/obstacles không trùng giữa split. Cùng family giữa split là biến thể trong cùng miền, chưa phải generalization sang loại môi trường mới. Seed/manifest công khai; độc lập được giữ bằng quy trình/checksum, không phải bí mật dữ liệu.

Thay đổi kích thước/độ lệch vật cản, start/goal, tịnh tiến/phản chiếu/quay world theo bội 90 độ và yaw ban đầu liên tục. Giữ world 20×20 m, độ cao 1.5 m. Narrow gap rộng 1.4–1.8 m. Chữ U có lối thoát ngược hướng đích ban đầu. Ba Solid sẵn có được thay render geometry và boundingObject đồng thời trước lượt.

## Khả thi và quyền dữ liệu

Grid 0.25 m tìm đường tám hướng trên inflated AABB. Bán kính hull bảo thủ bằng nửa đường chéo 3D hộp thân cộng 0.12 m. Mỗi đoạn, kể cả đường chéo và đoạn nén line-of-sight, được kiểm tra giao cắt. Witness chứng minh có đường ngang ở 1.5 m cho hull bảo thủ; không chứng minh thực thi động lực học hoặc tối ưu đường.

Không tìm được đường thì dừng sinh case, không tự gắn nhãn vô nghiệm. Negative control phải có goal nằm trong Solid thực. Manifest/witness/labels chỉ dành world/evaluation/observer. Drone nhận goal_m/policy, không nhận split, case ID, seed, geometry, nhãn khả thi hoặc witness.

## Khóa và tái hiện

```bash
make check
python3 tools/run_webots.py --navigation --suite seeded --split development --output artifacts/seeded-development
python3 tools/run_webots.py --navigation --suite seeded --split validation --output artifacts/seeded-validation
python3 tools/run_webots.py --navigation --suite seeded --split test --output artifacts/seeded-test
python3 tools/check_study.py artifacts/seeded-development/result.json artifacts/seeded-validation/result.json artifacts/seeded-test/result.json
```

Cần Webots R2025a; headless thêm xvfb-run -a và --software-rendering. --case <manifest-id> --policy reactive --realtime cho phép xem một lượt; đó là partial report, không thay cả split. Dùng thư mục output mới cho mỗi lần chạy; các tên trên dành lần chạy đầu.

tools/build_scenarios.py tạo manifest; --freeze tạo lock lần đầu và từ chối ghi đè. --check kiểm tra manifest và checksum file runtime/config. File đã khóa thay đổi cần protocol version mới và quy tắc test mới; không sửa lock để che thay đổi sau khi đọc test. Checksum ghi nhận phiên bản, không chống chủ repo sửa file.

Baseline giữ nguyên từ 555f59f. Radius 0.5 m, stop speed 0.18 m/s, dwell 1 s, deadline 75 s, warmup 2 s. Scoring từng 16 ms; collision/bounds ưu tiên success. Hai policy chạy cùng geometry/start/yaw, một lần mỗi case: 48 lượt. Seed môi trường không phải seed huấn luyện hoặc nhiễu cảm biến.

Summary giữ mọi outcome, tách split/family/feasibility và ghi rõ success-only metrics. Gate pipeline: đủ lượt, ca trống đạt, direct single_block collision, ca âm không success; không đòi reactive hoàn thành mọi family. check_study.py từ chối thiếu/trùng/khác manifest/protocol/source hoặc summary bỏ failure.

Output có result.json, cases.json, manifest.json, telemetry.jsonl, trajectories.json và ảnh observer. Trace ground truth lấy thưa chỉ để phân tích, không đưa vào drone/thay scoring. File lớn giữ ở artifacts/; chỉ evidence nhỏ đã xem mới lưu vào docs/research.

## Giới hạn

Điều hướng ngang, cảm biến/định vị/actuator lý tưởng v1, không mô phỏng rotor collision/radar vật lý. Chưa thử môi trường đa tầng hoặc giảm cảm biến. Test một seed/family không đủ suy rộng tỷ lệ chất lượng. Sau lần đọc này, test v1 là tập đã exposed cho thay đổi thuật toán tương lai; cần test mới trước báo cáo chất lượng tiếp theo.
