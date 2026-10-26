# Collector nghiệm thu tuần tự — kiểm chứng công cụ

Ngày 2026-10-26. Source kiểm chứng: **ea1329520137487b11491304f1f5b421b9f6d1d5**. [CI 40290684935](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40290684935), job 121464759216, success; artifact 12636202161. [JSON evidence](2026-10-26-sequential-acceptance.json) trích đúng log của source này, có metadata/hash artifact. Kế hoạch được push trước ở b46dc5d.

## Thay đổi và kiểm tra

- Lệnh accept chạy manual và mapped tuần tự, dừng khi bước trước thiếu bằng chứng. audit-batch kiểm tra lại raw files, source/protocol/helper, thứ tự thời gian và phiếu; không tự sửa checklist.
- Khóa OS ngăn hai collector trong workspace chạy chồng nhau, giữ khóa cả lúc hỏi phiếu. File khóa cũ không gây khóa vĩnh viễn; các cửa sổ Webots mở ngoài launcher không được kiểm soát bởi cơ chế này.
- Phiếu có lựa chọn rõ về độ phản hồi và pause/đổi tốc độ; Enter ghi chưa quan sát/không rõ. Tạo phiếu bằng thao tác exclusive để bảo toàn bản đã có. Ghi nhận trễ nhiều vẫn là thông tin hiệu năng hợp lệ, không được đổi thành “mượt”.
- 82 unit test đạt. Có kiểm tra khóa giữa hai process, giải phóng sau exception, thiếu/mâu thuẫn phiếu, source dirty/khác nhau, lượt chồng thời gian, pause và non-interactive accept. Fixture unit chỉ kiểm tra logic gate, không là thao tác GUI.
- CI Webots thật/Xvfb: mapped success; manual ghi 204 packet, không dòng lỗi và dừng theo timeout. Trong khi manual giữ khóa, mapped thứ hai bị từ chối với exit 2 trước khi tạo thư mục output. Phiếu người thao tác vẫn vắng trong CI, không có tự điền câu trả lời.

Hai lock v1/v2 giữ nguyên. Các thay đổi nằm ở collector/test/CI/docs; runtime điều hướng, world và controller đã khóa không đổi. CI này kiểm chứng collector thực; chưa chạy trọn luồng accept với một người thao tác desktop.

## Thực hiện trên laptop

Đóng các cửa sổ Webots cũ rồi chạy từ terminal desktop tại AI_Lap:

```bash
python3 tools/local_session.py accept
```

Trong manual, chọn vùng 3D, giữ từng phím khoảng 0.5–1 giây, quan sát, thử SPACE/thả phím và R sau khi đã di chuyển. Đóng Webots bằng nút đóng rồi trả lời phiếu trong terminal. Khi manual đủ bằng chứng, mapped tự mở để quan sát đến lúc kết thúc và điền phiếu tương ứng. Xem [hướng dẫn đầy đủ](../local-acceptance.md).

Gửi đường dẫn Acceptance batch để review. **LOC-05/06/09 vẫn mở**: chưa có lượt accept mới của người dùng tại lúc bàn giao công cụ. ready_for_review=true chỉ nói rằng dữ liệu/phiếu đã đủ theo gate; việc đóng LOC vẫn cần đọc bằng chứng và giữ các giới hạn về timestep, input latency và realtime.
