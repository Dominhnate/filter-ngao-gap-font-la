Filter chat của "nhà phát hành chữ V" chặn rất nhiều từ vô chi như "còn", "đi", "ngủ"... Thôi thì gõ bằng font khác: 𝒹̵𝒾 𝓃ℊ𝓊̉ 𝒸𝒽𝓊̛𝒶?.

Bộ gõ tiếng Việt (Telex, như Unikey) cho Windows, có đổi font chữ khi gõ.

## Cách dùng

1. Cài Python từ [python.org](https://www.python.org/downloads/). Khi cài, tick ô **Add Python to PATH**.
2. Tải file `fontgo.py` về.
3. **Tắt Unikey/EVKey** nếu đang chạy.
4. Nhấn chuột phải vào file → mở bằng Python, hoặc mở Command Prompt và gõ: `python fontgo.py`
5. Giữ cửa sổ đó mở khi chơi.

Game nào chạy bằng quyền Administrator thì chạy `fontgo.py` bằng quyền Administrator.

## Phím tắt

| Phím | Làm gì |
|---|---|
| `Ctrl + Shift` | Đổi Tiếng Việt ↔ English |
| `` ` `` (phím dưới Esc) | Đổi font |
| `Enter` | Mở chat trong trận, bắt đầu gõ font |
| `Enter` hoặc `Esc` | Đóng chat |

Đổi chế độ sẽ có tiếng bíp.

## Gõ tiếng Việt

Gõ Telex như Unikey: `tieengs` → tiếng, `nguoiwf` → người, `dduowcj` → được.

## Các font

| Tên | Ví dụ |
|---|---|
| fraktur | 𝔪𝔦𝔫𝔥 |
| bold_fraktur | 𝖒𝖎𝖓𝖍 |
| script | 𝓂𝒾𝓃𝒽 |
| double_struck | 𝕞𝕚𝕟𝕙 |

Còn nhiều font khác (monospace, sans, circled...). Muốn đổi danh sách font thì mở `fontgo.py` bằng Notepad, sửa dòng `FONTS = [...]` ở đầu file, danh sách tên đầy đủ nằm ngay trong file.

## Bị lỗi?

- **Không gõ được gì trong game:** nhớ bấm Enter mở chat trước. Nếu vẫn không được, chạy `python fontgo.py --title`, click vào game, xem tiêu đề cửa sổ, rồi sửa dòng `GAME_TITLES` trong file cho khớp.
- **Chữ bị thừa hoặc thiếu khi bỏ dấu:** sửa dòng `BACKSPACE_MODE` thành `"utf16"` hoặc `"grapheme"`.
- **Hiện ô vuông:** font đó game không hiển thị được, đổi font khác.
- **Gõ ra ký tự lạ:** tắt Unikey/EVKey.

## Lưu ý

- Chỉ chạy trên Windows, chỉ có Telex (chưa có VNI).
- Nếu sau này lọc cả chữ font lạ thì cách này hết tác dụng.
- Tự chịu rủi ro khi dùng. Chương trình không tự động hoá thao tác chơi game, nhưng không ai đảm bảo được phản ứng của hệ thống chống gian lận.
