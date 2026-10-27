# Hoàn tất mốc 6 — đăng ký thiết kế nghiên cứu range cadence v3

Ngày: 2026-10-27. Source công cụ/thiết kế được kiểm chứng: `761318df1293c195347f486b0d228f88af10fae1`; commit tài liệu bàn giao sau source này giữ nguyên các file đã khóa. [Bằng chứng máy đọc](2026-10-27-research-protocol-v3.json).

## Kết quả trong phạm vi mốc

EXP-01–12 có câu trả lời được ghi trước evaluation: [kế hoạch chi tiết](../plans/0010-research-protocol-v3.md), [ADR 0006](../decisions/0006-range-cadence-protocol-v3.md), [protocol](../protocols/range-cadence-v3.md), [config](../../configs/experiments/range_cadence_v3.toml), [nguồn chính/đóng góp](2026-10-27-range-cadence-related-work.md), [exposure](../../configs/scenarios/exposure_v3.json).

Câu hỏi chính: tăng chu kỳ acquisition 10 range từ 32 lên 64 ms trên mapped cố định có giảm ít nhất 50% rate range mà vẫn đạt ngưỡng nhiệm vụ/tài nguyên hay không? Chỉ một candidate chọn trước; chưa chọn ML/framework. Success quan sát ít nhất 95% cho cả hai arm, adverse-pair exact upper bound một phía 95% không quá 5%, không collision/bounds, giới hạn path/time và tài nguyên được đặc tả. Các con số này là tiêu chí nghiên cứu do agent xác lập trong nhiệm vụ được giao, không phải kết quả đạt hoặc cam kết sản phẩm.

Đã thực sự sinh đầy đủ 480 case và chứng chỉ trong `artifacts/research-v3-fixtures/{train,development,validation,test}.json`; các file này bị Git ignore. Index được review/commit chỉ có metadata/hashes/certificate kind, không có tọa độ hoặc witness. Không đưa fixtures vào policy.

| Split | Feasible | Negative | Tổng |
|---|---:|---:|---:|
| train dự trữ | 50 | 10 | 60 |
| development | 50 | 10 | 60 |
| validation | 100 | 20 | 120 |
| test | 200 | 40 | 240 |

Tổng 400 feasible có witness ngang với hull margin; 80 negative có goal trong solid. Kiểm geometry hash và canonical task fingerprint không trùng giữa mọi case/split và v1/v2, kể cả scene tương đương do tịnh tiến/quay 90°/đối xứng. Không bỏ/reseed case sau failure. Cùng family/generator nên không tuyên bố OOD; public seed/generator không là bí mật test. Chưa xem outcome hoặc trajectory v3.

## Kiểm tra thực sự đã chạy

- `python3 tools/build_research_v3.py`: sinh fixture đủ bốn split; lần freeze và check tiếp theo tái lập cùng commitments.
- `make check`: scaffold, lab builder, v1 scenario, v2 manifest/lock, v3 generation/design lock và **92 unit tests đều đạt**. Mười test mới kiểm counts/splits, equivalent geometry/seed duplicates, drift controls/encoding, exposure genesis/schema, exact bound, lock mismatch và CLI từ chối overwrite/evaluation.
- `--freeze` khi lock tồn tại và `--evaluate` đều exit khác 0 theo kỳ vọng; unit test kiểm file lock không đổi. Không có skip giả hoặc launcher v3 giả.
- [GitHub Actions 40446508423](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40446508423): **success** ở đúng source trên; job `121998969583`, bước `Run make check` đạt; log xác nhận 92 tests. CI dùng Python 3.12, không chạy Webots v3.
- Kiểm staged diff/whitespace và tree GitHub khớp local trước publish; fixtures/raw logs không được stage. Khóa v1/v2 giữ nguyên byte.

Design hash: `968c59e193336c49a015a62f87bf6f0ac834c6131bdb348105b5fcd950ad1474`. V1: `96872282fc7df5029453ed684d0e73e9305137c3d6907736869b2e04bf64b90f`; v2: `0825b3b219fbf6a7f939b3076b79b1c82888c02d71a8ffea36d2e7d5bde1e395`.

Minh họa thống kê được unit test xác minh: giả sử 0 adverse/200 independent feasible cases thì upper bound ≈1.4867%; 4/200 thì ≈4.5180%. Đây là số từ công thức, **không là outcome nghiên cứu** và không bảo đảm power.

## Mốc tiếp theo và giới hạn

Qua gate **thiết kế**, chưa qua gate **evaluation**. Runtime v3 còn thiếu: adapter đặt acquisition period thật, timestamp/pose đúng lúc đo, accounting bốn tầng dữ liệu, evaluator/aggregator/retry runner, kiểm chứng Webots development và runtime dependency/source lock. Runtime lock phải tham chiếu design lock; không đổi lock thiết kế để cập nhật implementation.

[Checklist mục tiêu phát sinh](../../CHECKLIST_MUC_TIEU_NGHIEN_CUU.md) ghi rõ các mục này với lý do/tiêu chí/bằng chứng còn thiếu. [Checklist tổng](../../CHECKLIST_DU_AN.md) đóng EXP trong đúng phạm vi đặc tả và giữ DATA/ML/runtime objectives mở. Không có chuyến bay v3, kết quả giảm acquisition, learned policy, privacy guarantee hoặc bằng chứng phần cứng mới. Nghiệm thu desktop v1/v2 tại source `39c34af` vẫn là bằng chứng lịch sử riêng.
