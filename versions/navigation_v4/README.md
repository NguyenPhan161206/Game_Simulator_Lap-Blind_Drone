# Navigation v4 development

Package riêng ngoài src/ để giữ nguyên bốn khóa v1/v2/v3. Python path khi chạy gồm `src/` và `versions/navigation_v4/`. Chỉ dùng shared core đã khóa; không đặt source generated hoặc log vào package này.

Được triển khai theo [ADR 0007](../../docs/decisions/0007-observed-detour-v4.md) và [kế hoạch 0014](../../docs/plans/0014-observed-detour-v4.md). Đây là development, chưa có validation/test v4. CLI từ chối held-out.

Adapter v4 được dẫn xuất từ adapter v3 cùng repository tại `0c75ce28f14b8ea881e8c0c7c9335aa4319030c5`, không phải code bên thứ ba. Phần acquisition/evaluation chung vẫn import từ bản đã khóa; khác biệt gồm policy selection, trace command và fixture/inventory development riêng.

## Kiểm tra và chạy

```bash
python3 tools/build_navigation_v4.py
make check
# Chạy trên CI/Xvfb; không dùng DISPLAY của desktop người dùng:
xvfb-run -a python3 tools/run_navigation_v4.py --output artifacts/v4-development-new
python3 tools/review_navigation_v4.py artifacts/v4-development-new \
  --expected-source <FULL_SOURCE_SHA> --output artifacts/v4-review-new.json
```

Suite có 88 case: 60 regression v3 development đã exposed, 16 empty offset/yaw, 4 near-wall, 4 narrow-gap, 4 negative. 74 feasible và 14 negative; 2 arm × 2 repeat = 352 episode. Fixture đầy đủ ignored; index case hashes được commit. Không gọi đây là unseen hoặc validation. Cả reference và candidate cùng range/pose 32 ms, control 16 ms.

Review kiểm lại acquisition/binary/physics, hashes và mọi target/lệnh ngang candidate từ grid tái dựng bằng public observations. Clearance world dùng ở evaluator hậu kiểm trên polyline 16 ms, không vào controller; không là quỹ đạo liên tục thật hoặc bảo đảm vật lý. CPU/RSS báo riêng; mô phỏng có thể chờ controller.
