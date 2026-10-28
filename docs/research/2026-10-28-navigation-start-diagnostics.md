# Chẩn đoán offline: lỗ coverage gần tâm gây kẹt đoạn đầu

Ngày: 2026-10-28. Thực thi [kế hoạch 0013](../plans/0013-navigation-start-diagnostics.md). Đây là chẩn đoán development bằng quan sát đã ghi; không có episode Webots mới hoặc kết quả điều hướng cải thiện.

## Kết luận có bằng chứng

Cả **5 trace reference được chọn** có cùng cơ chế gây kẹt: planner chấp nhận đi qua unknown với chi phí cao hơn, nhưng executor yêu cầu đoạn tới waypoint phải hoàn toàn thuộc free-grid. Ô đầu tiên vi phạm nằm hoàn toàn phía trong vòng gốc cảm biến 0.33 m và không chứa tâm drone ở bất kỳ acquisition nào. Các tia bắt đầu tại vòng đó rồi hướng ra ngoài, nên không thể đánh dấu ô này là free dù drone quay thêm. Grid chỉ tự retain ô chứa tâm, không nối phần giữa tâm và sensor origin.

Đó là deadlock giữa biểu diễn quan sát, lựa chọn đường và điều kiện thực thi. Không phải phát hiện vật cản tại chính ô từ chối, ngoài bản đồ hoặc range quá cũ trong năm trace này. Không suy từ đó rằng ô unknown an toàn để đi qua, hoặc toàn bộ failure validation có cùng nguyên nhân.

## Nguồn và kiểm tra tính toàn vẹn

- Runtime được phát lại: `0c75ce28f14b8ea881e8c0c7c9335aa4319030c5`.
- Raw development: `artifacts/v3-development-0c75ce2/`; 240 episode, 120 attempt hợp lệ. Công cụ review hiện có xác minh identity, complete membership, inventory, file hashes và raw audit toàn bộ study trước chẩn đoán.
- SHA-256 raw `result.json`: `78ff9c4406f1007dd5797d581f4e8042f9dbcf95e4c5652d4556258275fa2892`.
- Design digest: `968c59e193336c49a015a62f87bf6f0ac834c6131bdb348105b5fcd950ad1474`; runtime digest: `bcc938bb18acd9bd829f43e6f0f722f204a5c7702e5fa3b20c82b6171a080c3d`.
- [JSON bằng chứng](2026-10-28-navigation-start-diagnostics.json) giữ tool hash, cả bốn lock file hash, counters, ô/tọa độ/thời điểm từ chối đầu/cuối, kiểm tra hình học và sweep. Digest canonical của khóa và hash byte file khóa là hai đại lượng khác nhau.
- Raw chẩn đoán: `artifacts/navigation-start-diagnostics-0013/rejections.jsonl`; SHA-256 `2d5f4cfa75282324170d90b660e89d12d83456899de62fee30ff83ee483fe1f8`.

Mẫu chọn đúng năm trace trong [replay trước](2026-10-28-v3-public-replay.json), một trace mỗi case reference thất bại. Toàn development có **8 reference feasible failure episode thuộc 5 case**; lần này phân tích 5/8 episode, phủ 5/5 case thất bại reference. Không phải mẫu ngẫu nhiên, không là ước lượng tỷ lệ lỗi mới. Không phân tích candidate: acquisition log 64 ms không giữ đầy đủ pose trung gian 32 ms; không bịa nội suy.

## Tái hiện quyết định và ô gây từ chối

Mỗi trace có 5625 quyết định: 157 `initial_scan`, 5468 `scan_unknown_or_blocked`, **0 lệnh ngang khác 0**. Tất cả 5468 lần kiểm tra đoạn thất bại đều có lý do `unknown`; bỏ riêng yêu cầu free thì predicate hình học chấp nhận. Đây chỉ là đối chiếu predicate, không phải đề nghị bỏ điều kiện an toàn. Không có lần từ chối do blocked/outside trong mẫu.

| Case development | Repeat | Ô đầu tiên vi phạm | Khoảng cách mẫu vi phạm từ pose (m) | Góc ô xa nhất so với pose, toàn trace (m) |
|---|---:|---|---:|---:|
| empty-s3200020 | 0 | (1, 17) | 0.057636 | 0.325903 |
| empty-s3200034 | 0 | (1, -20) | 0.057994 | 0.327511 |
| empty-s3200041 | 0 | (1, -17) | 0.071473 | 0.314068 |
| narrow_gap-s3200004 | 0 | (-1, 20) | 0.068292 | 0.321944 |
| narrow_gap-s3200029 | 1 | (-2, -24) | 0.062361 | 0.313941 |

Mỗi ô vẫn unknown và không blocked khi kết thúc. Với **2813 acquisition được policy sử dụng mỗi trace**, mọi góc của ô đều gần pose hơn mọi horizontal sensor origin; số lần center-retain vào ô bằng 0. Tính cả roll/pitch thực đo: projected origin nhỏ nhất ≥0.329995 m. Phép chứng minh dùng vị trí/attitude tại acquisition cho từng mẫu, không giả định drone đứng im tuyệt đối.

Ví dụ `empty-s3200020`: pose đầu bị từ chối `(0.367485, 4.547746)`; waypoint `(0.375, 4.375)`. Segment check lấy 4 điểm (3 đoạn), điểm vi phạm đầu `(0.369990, 4.490164)` rơi vào ô `(1,17)`. Grid 0.25 m đặt biên ô đó tại x=[0.25,0.50], y=[4.25,4.50]. Cả hình chữ nhật nằm trong vòng sensor origin, nên quay yaw không thể phủ nó bằng các tia hướng ra ngoài.

Thời điểm từ chối đầu là 2.512 s sau quyết định policy đầu tiên ở cả năm trace, ngay sau scan 2.5 s. Timestamp tuyệt đối của repeat 1 khác repeat 0 do đồng hồ simulator tiếp tục chạy; không lấy timestamp tuyệt đối làm elapsed nhiệm vụ.

Các counter tất định replay khớp **toàn bộ counter gốc trừ CPU** ở từng episode: decisions, samples, map/free/occupied/blocked, guard/scan, plans và budget. Mọi lời gọi segment predicate được so kết quả với hàm gốc; wrapper trả nguyên kết quả gốc, không sửa grid/target/command. Log gốc không lưu command từng tick, nên không tuyên bố đã đối chiếu command từng tick với simulator. CPU lúc replay không dùng làm CPU runtime mới.

## Phân biệt sensor origin, cell alignment và pose

1. **Sensor origin:** rays chỉ ghi free từ origin ra ngoài; ô tâm được retain riêng. Bán kính 0.33 m lớn hơn cell 0.25 m tạo khả năng có ô kề nằm trọn trong khoảng không được ray cập nhật.
2. **Cell alignment:** grid dùng `floor(x/0.25), floor(y/0.25)` theo world origin, không đặt cell quanh vị trí khởi hành. Vị trí khởi hành khác nhau trong cell làm thay đổi ô nào nằm trong vòng trống. Vì vậy lỗi xuất hiện ở một số reset pose mà không phải mọi case.
3. **Current/acquisition pose:** khoảng cách ngang giữa hai pose bằng 0 trong từng quyết định reference này; tuổi range tối đa khoảng 16 ms, thấp hơn 120 ms. Các counter không báo invalid/stale. Drift ngang ba empty <2e-14 m; hai narrow_gap lần lượt khoảng 0.015506 m và 0.000111 m. Dù có drift, điều kiện ô nằm trong vòng origin vẫn đúng ở mọi acquisition. Bằng chứng không ủng hộ việc dùng sai acquisition pose làm nguyên nhân của năm trace này. Chưa khảo sát lỗi reset thiết bị hoặc drift phần cứng nói chung.

Sweep tổng hợp giữ nguyên grid/cell, tám hướng ray và toàn bộ mã update/check; chỉ thay origin giữa 0.33 m và 0 m trong phép thử biểu diễn. Dùng 9×9 offset `[0.025, …, 0.225]` m trong một cell, 64 yaw đủ vòng; tám ray no-return lý tưởng giới hạn tổng hợp 1 m, không hit, không dùng obstacle/world. Không chạy navigator/physics hoặc hợp thức hóa sensor 1 m thành cấu hình runtime.

| Origin trong phép kiểm tra | Vị trí có ít nhất một segment tới tâm ô kề bị từ chối | Phân bố số hướng bị từ chối |
|---|---:|---|
| 0.33 m hiện hành | 32/81 | 49 vị trí: 0; 8 vị trí: 2; 24 vị trí: 3 |
| 0 m, control chẩn đoán | 0/81 | 81 vị trí: 0 |

Sweep tách được tác động origin/cell alignment ngay cả khi không có vật cản hoặc sai timestamp. **32/81 không phải tỷ lệ thất bại chuyến bay.** Origin=0 không phải đề nghị chuyển sensor vào thân drone: self-occlusion, hình học thân và tính đúng của phép đo cần thiết kế riêng.

## Trạng thái từng bước trong kế hoạch

1. Đã đối chiếu checkout ban đầu sạch, local acceptance không giữ flock, source/inventory và bốn khóa hợp lệ.
2. Đã khoanh đúng năm trace development và báo đầy đủ mẫu số failure.
3. Đã thêm công cụ offline trong tools/, không thêm hoặc sửa Python trong src/ đã khóa.
4. Đã xác định ô đầu vi phạm, lý do, thời điểm, pose và đối chiếu predicate/counters.
5. Đã kiểm tra toàn bộ acquisition cho từng ô và sweep origin/offset tổng hợp.
6. `make check` đạt: scaffold, lab, seeded v1, navigation v2, design/runtime v3 và **141 unit tests**, gồm 14 test chẩn đoán mới. Log local `artifacts/navigation-start-diagnostics-0013/checks.log`. Không mở Webots mới.
7. Đã lưu JSON/báo cáo, cập nhật checklist và hướng dẫn. Source commit/push/CI được báo trong bàn giao Git; không dùng kiểm tra code để tuyên bố đã sửa chất lượng bay.

Lệnh tái lập khi còn raw development và fixture đã cam kết (output phải mới):

```bash
python3 tools/diagnose_navigation_start.py artifacts/v3-development-0c75ce2 \
  --expected-source 0c75ce28f14b8ea881e8c0c7c9335aa4319030c5 \
  --output artifacts/navigation-start-diagnostics-reproduction
make check
```

## Bước cải thiện tiếp theo — đề xuất, chưa triển khai

Ưu tiên một phiên bản điều hướng mới phân biệt **đường thăm dò qua unknown** với **đoạn thực sự thực thi được từ pose hiện tại**. Thử tìm nhánh đi vòng qua các ô đã quan sát free, thay vì liên tục chọn cùng waypoint xuyên qua ô chưa thể quan sát. Không tự tô vòng blind thành free hoặc bỏ free-check. Trước khi chọn bản sửa, đo có tồn tại lối thay thế từ free-grid và kiểm tra swept clearance; chẩn đoán này chưa chứng minh giải pháp cụ thể sẽ thành công.

Giữ cadence reference 32 ms để tách sửa navigation khỏi giảm dữ liệu. Bộ development cần empty theo offset/yaw/biên cell, gần tường/vật cản, narrow gap và negative controls; báo cả timeout/collision/bounds, thời gian và CPU/RAM. Năm case cũ chỉ là regression đã exposed. Sau development mới đăng ký protocol, khóa source và tạo validation/test mới để đánh giá chất lượng.

Lưu ý tổ chức mã: inventory v3 ghim **mọi src/**/*.py**. Thêm module v4 vào src/ hiện tại cũng làm verify_runtime v3 không còn hợp lệ; cần thiết kế version/checkout và inventory riêng trước khi triển khai, giữ nguyên source/locks v3 để tái lập. Không tái sinh khóa v3 nhằm hợp thức hóa mã mới. Validation v3 vẫn là kết luận âm 87/100; test v3 vẫn chưa mở. Không có ML/radar/hardware trong bước này.
