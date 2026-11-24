# -*- coding: utf-8 -*-
"""
gothic_ime.py - Bộ gõ kiểu Unikey (Telex) + đổi font Unicode (Gothic/Fraktur và các kiểu khác)
Một file duy nhất: chương trình + hướng dẫn + bảng font + lưu ý.

=== CÁCH CHẠY (Windows, Python 3.8+, không cần cài thêm thư viện) ===
    python gothic_ime.py              chạy bộ gõ
    python gothic_ime.py --title      in tiêu đề cửa sổ đang focus 10 giây (để chỉnh GAME_TITLES)
    python gothic_ime.py --selftest   kiểm tra engine Telex (chạy được cả Linux/Mac)
Thoát Unikey/EVKey trước khi chạy, nếu không 2 bộ gõ xử lý chồng nhau.
Nếu game chạy quyền Administrator thì chạy chương trình bằng Admin.

=== PHÍM TẮT ===
    Ctrl + Shift   chuyển Tiếng Việt <-> English
    `  (backtick)  đổi font vòng tròn theo danh sách FONTS bên dưới
    Mặc định (ONLY_IN_GAME=True) chỉ hoạt động khi đang TRONG TRẬN (cửa sổ khớp GAME_TITLES),
    và chỉ biến đổi chữ sau khi bấm Enter mở chat, dừng khi Enter/Esc.
    Client, trình duyệt, app khác: chương trình không đụng vào phím nào.

=== DANH SÁCH FONT (điền tên vào FONTS) ===
    Tên             Ví dụ "minh"   Ghi chú
    fraktur         𝔪𝔦𝔫𝔥          Blackletter đúng nghĩa (kiểu đã thử qua được bộ lọc)
    bold_fraktur    𝖒𝖎𝖓𝖍          Đậm hơn Fraktur
    script          𝓂𝒾𝓃𝒽          Chữ viết tay; vài chữ nằm ở khối khác (e, g, o, B, E...)
    bold_script     𝓶𝓲𝓷𝓱          Chữ viết tay đậm
    double_struck   𝕞𝕚𝕟𝕙          Nét đôi; C H N P Q R Z nằm ở khối khác
    monospace       𝚖𝚒𝚗𝚑          Giống chữ máy đánh
    sans            𝗆𝗂𝗇𝗁          Sans-serif thường
    sans_bold       𝗺𝗶𝗻𝗵          Sans-serif đậm, dễ đọc nhất
    sans_italic     𝘮𝘪𝘯𝘩          Sans-serif nghiêng
    fullwidth       ｍｉｎｈ          Chữ rộng kiểu Nhật (dấu kết hợp dễ lệch)
    circled         ⓜⓘⓝⓗ          Chữ trong vòng tròn, khó đọc cả câu (dấu dễ lệch)
    small_caps      ᴍɪɴʜ          Thiếu q, x (giữ nguyên chữ thường)
    normal          minh          Font thường
"""
import os
import struct
import sys
import time
import unicodedata

# ============================ CẤU HÌNH ============================
# Tên hợp lệ: normal, fraktur, bold_fraktur, script, bold_script, double_struck, monospace,
#              sans, sans_bold, sans_italic, fullwidth, circled, small_caps
FONTS = ["normal", "script"]  # thứ tự khi bấm phím `
START_VIETNAMESE = True
START_FONT_INDEX = 0          # 0 = bắt đầu bằng font thường
MODERN_TONE = False           # False: òa, úy (mặc định Unikey) | True: oà, uý
BACKSPACE_MODE = "codepoint"  # "codepoint" | "utf16" | "grapheme"  (xem ghi chú cuối file)
D_STROKE = "̵"           # gạch ngang cho đ khi ở font Fraktur (Fraktur không có sẵn đ)
FONT_KEY_VK = 0xC0            # phím ` (VK_OEM_3)
BEEP = True                   # bíp báo khi đổi chế độ

# Trong game, chỉ gõ tiếng Việt/đổi font KHI ĐANG MỞ Ô CHAT (Enter mở, Enter/Esc đóng),
# để không nuốt các phím Q W E R D F... khi đang chơi.
# Chỉ áp dụng cho các phần mềm có title như bên dưới:
GAME_TITLES = ["League of Legends (TM) Client"]
ONLY_IN_GAME = False   # True: chỉ bật bộ gõ khi cửa sổ đang mở khớp với GAME_TITLES. Client hoặc app khác thì bộ gõ không làm gì.
# ==================================================================

# ---------------------------- Bảng chữ Fraktur ----------------------------
def _build_font(lower0, upper0, holes):
    m = {}
    for i in range(26):
        for base, c in ((lower0, chr(97 + i)), (upper0, chr(65 + i))):
            m[c] = holes.get(c, chr(base + i))
    return m


def _from_string(lower26):  # small caps: chữ hoa dùng chung bản thường
    m = {}
    for i, ch in enumerate(lower26):
        m[chr(97 + i)] = ch
        m[chr(65 + i)] = ch
    return m


FONT_MAPS = {
    "fraktur":       _build_font(0x1D51E, 0x1D504, {"C": "\u212D", "H": "\u210C", "I": "\u2111", "R": "\u211C", "Z": "\u2128"}),
    "bold_fraktur":  _build_font(0x1D586, 0x1D56C, {}),
    "script":        _build_font(0x1D4B6, 0x1D49C, {"B": "\u212C", "E": "\u2130", "F": "\u2131", "H": "\u210B",
                                                    "I": "\u2110", "L": "\u2112", "M": "\u2133", "R": "\u211B",
                                                    "e": "\u212F", "g": "\u210A", "o": "\u2134"}),
    "bold_script":   _build_font(0x1D4EA, 0x1D4D0, {}),
    "double_struck": _build_font(0x1D552, 0x1D538, {"C": "\u2102", "H": "\u210D", "N": "\u2115", "P": "\u2119",
                                                    "Q": "\u211A", "R": "\u211D", "Z": "\u2124"}),
    "monospace":     _build_font(0x1D68A, 0x1D670, {}),
    "sans":          _build_font(0x1D5BA, 0x1D5A0, {}),
    "sans_bold":     _build_font(0x1D5EE, 0x1D5D4, {}),
    "sans_italic":   _build_font(0x1D622, 0x1D608, {}),
    "fullwidth":     _build_font(0xFF41, 0xFF21, {}),
    "circled":       _build_font(0x24D0, 0x24B6, {}),
    "small_caps":    _from_string("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘqʀꜱᴛᴜᴠᴡxʏᴢ"),
}

_bad = [f for f in FONTS if f != "normal" and f not in FONT_MAPS]
if _bad:
    raise SystemExit("FONTS có tên không hợp lệ: %s\nTên hợp lệ: normal, %s"
                     % (", ".join(_bad), ", ".join(FONT_MAPS)))

# ---------------------------- Engine Telex ----------------------------
TONE_KEYS = {"s": 1, "f": 2, "r": 3, "x": 4, "j": 5, "z": 0}
TONE_MARK = {1: "́", 2: "̀", 3: "̉", 4: "̃", 5: "̣"}
MOD_MARK = {"^": "̂", "(": "̆", "+": "̛"}  # mũ â ê ô | trăng ă | móc ơ ư
VOWELS = "aeiouy"


class Cell:
    __slots__ = ("c", "up", "mod", "from_w")

    def __init__(self, c, up, mod="", from_w=False):
        self.c, self.up, self.mod, self.from_w = c, up, mod, from_w


class Syl:
    def __init__(self):
        self.cells = []
        self.tone = 0
        self.dead = set()  # phím đã bị "hoàn tác" (vd: ass -> as), lần sau gõ chữ thường


def is_vowel(cells, i):
    c = cells[i]
    if c.c not in VOWELS:
        return False
    if i > 0:
        p = cells[i - 1]
        if c.c == "u" and p.c == "q":
            return False  # qu: u là phụ âm
        if c.c == "i" and p.c == "g" and i + 1 < len(cells) and cells[i + 1].c in VOWELS:
            return False  # gi + nguyên âm: i là phụ âm
    return True


def last_vowel(cells):
    j = len(cells) - 1
    while j >= 0 and not is_vowel(cells, j):
        j -= 1
    return j if j >= 0 else None


def vowel_run(cells, j):
    run = [j]
    k = j - 1
    while k >= 0 and is_vowel(cells, k):
        run.insert(0, k)
        k -= 1
    return run


def tone_index(cells):
    j = last_vowel(cells)
    if j is None:
        return None
    run = vowel_run(cells, j)
    mods = [i for i in run if cells[i].mod in ("^", "(", "+")]
    if mods:
        return mods[-1]
    if len(run) == 1:
        return run[0]
    if len(run) == 2:
        if run[-1] < len(cells) - 1:  # có phụ âm cuối
            return run[1]
        if MODERN_TONE and cells[run[0]].c + cells[run[1]].c in ("oa", "oe", "uy"):
            return run[1]
        return run[0]
    return run[1]


def _key_w(st, up):
    cells = st.cells
    lit = lambda: cells.append(Cell("w", up))
    if "w" in st.dead:
        return lit()
    j = last_vowel(cells)
    if j is None:  # w đứng một mình -> ư
        cells.append(Cell("u", up, "+", from_w=True))
        return
    if cells[-1].from_w and j == len(cells) - 1:  # ww -> w
        cells[-1] = Cell("w", cells[-1].up)
        st.dead.add("w")
        return
    run = vowel_run(cells, j)
    for k in run:  # uo -> ươ
        if k + 1 in run and cells[k].c == "u" and cells[k + 1].c == "o":
            a, b = cells[k], cells[k + 1]
            if a.mod == "+" and b.mod == "+":
                a.mod = b.mod = ""
                st.dead.add("w")
                return lit()
            a.mod = b.mod = "+"
            return
    if cells[j].c == "a" and j - 1 in run and cells[j - 1].c == "u":  # ua -> ưa
        u = cells[j - 1]
        if u.mod == "+":
            u.mod = ""
            st.dead.add("w")
            return lit()
        u.mod = "+"
        return
    tgt = None
    if cells[j].c in "aou":
        tgt = j
    else:  # oi / ui / ... : áp w cho o hoặc u trong cụm nguyên âm
        for k in reversed(run):
            if cells[k].c in "ou":
                tgt = k
                break
    if tgt is None:
        return lit()
    t = cells[tgt]
    if t.c == "a":
        if t.mod in ("", "^"):
            t.mod = "("
        else:
            t.mod = ""
            st.dead.add("w")
            lit()
    else:
        if t.mod in ("", "^"):
            t.mod = "+"
        else:
            t.mod = ""
            st.dead.add("w")
            lit()


def feed(st, c, up):
    cells = st.cells
    lit = lambda: cells.append(Cell(c, up))

    if c in TONE_KEYS:  # dấu thanh
        if c in st.dead or not any(is_vowel(cells, i) for i in range(len(cells))):
            return lit()
        t = TONE_KEYS[c]
        if t == 0:
            if st.tone:
                st.tone = 0
            else:
                lit()
        elif st.tone == t:  # gõ lại cùng phím -> hoàn tác, ra chữ thường
            st.tone = 0
            st.dead.add(c)
            lit()
        else:
            st.tone = t
        return

    if c == "d":  # dd -> đ
        if cells and cells[-1].c == "d" and "d" not in st.dead:
            if cells[-1].mod == "":
                cells[-1].mod = "-"
                return
            if cells[-1].mod == "-":
                cells[-1].mod = ""
                st.dead.add("d")
                return lit()
        return lit()

    if c in "aeo" and c not in st.dead:  # aa ee oo -> â ê ô
        j = last_vowel(cells)
        if j is not None and cells[j].c == c:
            m = cells[j].mod
            if m in ("", "("):
                cells[j].mod = "^"
                return
            if m == "^":
                cells[j].mod = ""
                st.dead.add(c)
                return lit()
        return lit()

    if c == "w":
        return _key_w(st, up)

    lit()


def cell_text(cell, tone_mark, font):
    b = cell.c.upper() if cell.up else cell.c
    if font == "normal":
        if cell.c == "d" and cell.mod == "-":
            return "Đ" if cell.up else "đ"
        return unicodedata.normalize("NFC", b + MOD_MARK.get(cell.mod, "") + tone_mark)
    s = FONT_MAPS[font][b]
    if cell.c == "d" and cell.mod == "-":
        s += D_STROKE
    return s + MOD_MARK.get(cell.mod, "") + tone_mark


def render(keys, vn, font):
    """keys: list[(chữ thường, is_upper)] của từ đang gõ -> chuỗi hiển thị."""
    st = Syl()
    for c, up in keys:
        if vn:
            feed(st, c, up)
        else:
            st.cells.append(Cell(c, up))
    ti = tone_index(st.cells) if st.tone else None
    return "".join(
        cell_text(cell, TONE_MARK[st.tone] if i == ti else "", font)
        for i, cell in enumerate(st.cells)
    )


def diff(old, new):
    """Trả về (số lần backspace, chuỗi cần gõ thêm)."""
    a, b = list(old), list(new)
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    if BACKSPACE_MODE == "grapheme":
        while i > 0 and ((i < len(a) and unicodedata.combining(a[i])) or
                         (i < len(b) and unicodedata.combining(b[i]))):
            i -= 1
    removed = a[i:]
    if BACKSPACE_MODE == "utf16":
        bs = sum(2 if ord(ch) > 0xFFFF else 1 for ch in removed)
    elif BACKSPACE_MODE == "grapheme":
        bs = sum(1 for ch in removed if not unicodedata.combining(ch))
    else:
        bs = len(removed)
    return bs, "".join(b[i:])


class IME:
    def __init__(self):
        self.vn = START_VIETNAMESE
        self.font_i = START_FONT_INDEX % len(FONTS)
        self.raw = []
        self.sent = ""
        self.chat_open = False

    @property
    def font(self):
        return FONTS[self.font_i]

    def active(self):
        return self.vn or self.font != "normal"

    def reset(self):
        self.raw = []
        self.sent = ""

    def toggle_vn(self):
        self.vn = not self.vn
        self.reset()

    def next_font(self):
        self.font_i = (self.font_i + 1) % len(FONTS)
        self.reset()

    def _update(self):
        new = render(self.raw, self.vn, self.font)
        bs, text = diff(self.sent, new)
        self.sent = new
        return bs, text

    def push(self, c, up):
        self.raw.append((c, up))
        return self._update()

    def pop(self):
        self.raw.pop()
        return self._update()


# ---------------------------- Lớp Windows ----------------------------
def run_windows():
    import ctypes
    import threading
    from ctypes import wintypes

    import winsound

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    ULONG_PTR = ctypes.c_size_t
    LRESULT = ctypes.c_ssize_t
    HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    MAGIC = 0x474F5448  # đánh dấu input do chương trình này tạo ra

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                    ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

    class _U(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _U)]

    user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD)
    user32.SetWindowsHookExW.restype = wintypes.HHOOK
    user32.CallNextHookEx.argtypes = (wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    user32.CallNextHookEx.restype = LRESULT
    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
    user32.GetAsyncKeyState.restype = ctypes.c_short
    user32.GetKeyState.argtypes = (ctypes.c_int,)
    user32.GetKeyState.restype = ctypes.c_short
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE

    title_buf = ctypes.create_unicode_buffer(256)

    def fg_title():
        h = user32.GetForegroundWindow()
        if not h:
            return ""
        user32.GetWindowTextW(h, title_buf, 256)
        return title_buf.value

    def _ki(vk, scan, flags):
        i = INPUT()
        i.type = 1  # INPUT_KEYBOARD
        i.ki = KEYBDINPUT(vk, scan, flags, 0, MAGIC)
        return i

    def send(bs, text):
        ev = []
        for _ in range(bs):
            ev.append(_ki(0x08, 0x0E, 0))
            ev.append(_ki(0x08, 0x0E, 0x0002))
        for ch in text:
            b = ch.encode("utf-16-le")
            for unit in struct.unpack("<%dH" % (len(b) // 2), b):
                ev.append(_ki(0, unit, 0x0004))           # KEYEVENTF_UNICODE
                ev.append(_ki(0, unit, 0x0004 | 0x0002))  # | KEYUP
        if ev:
            arr = (INPUT * len(ev))(*ev)
            user32.SendInput(len(ev), arr, ctypes.sizeof(INPUT))

    def beep(freq):
        if BEEP:
            threading.Thread(target=winsound.Beep, args=(freq, 60), daemon=True).start()

    ime = IME()

    def announce(freq):
        print("  Ngôn ngữ: %-10s | Font: %s" % ("Tiếng Việt" if ime.vn else "English", ime.font),
              flush=True)
        beep(freq)

    CTRL = {0xA2, 0xA3, 0x11}
    SHIFT = {0xA0, 0xA1, 0x10}
    ALT = {0xA4, 0xA5, 0x12}
    WIN = {0x5B, 0x5C}
    MODS = CTRL | SHIFT | ALT | WIN | {0x14}
    swallowed = set()
    pending = [False]  # đang chờ nhả Ctrl+Shift để đổi ngôn ngữ

    def phys(vk):
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)

    def in_game_now():
        title = fg_title().lower()
        return any(t.lower() in title for t in GAME_TITLES)

    def handle_mod(vk, down):
        if ONLY_IN_GAME and not in_game_now():
            pending[0] = False
            return False
        if vk in CTRL or vk in SHIFT:
            if down:
                other = 0x10 if vk in CTRL else 0x11
                pending[0] = phys(other) and not phys(0x12)
            elif pending[0]:
                pending[0] = False
                ime.toggle_vn()
                announce(880 if ime.vn else 440)
        elif down:
            pending[0] = False
        return False

    def handle_down(vk):
        in_game = in_game_now()
        if not in_game:
            ime.chat_open = False
            if ONLY_IN_GAME:  # ngoài trận (client, trình duyệt...): không đụng vào phím nào
                ime.reset()
                return False
        shift = phys(0x10)
        if phys(0x11) or phys(0x12) or phys(0x5B) or phys(0x5C):
            ime.reset()
            return False
        if vk == FONT_KEY_VK and not shift:
            if vk not in swallowed:  # bỏ qua auto-repeat
                ime.next_font()
                announce(1320 if ime.font != "normal" else 330)
            return True
        if vk == 0x0D:  # Enter
            ime.reset()
            if in_game:
                ime.chat_open = not ime.chat_open
            return False
        if vk == 0x1B:  # Esc
            ime.reset()
            ime.chat_open = False
            return False
        if (in_game and not ime.chat_open) or not ime.active():
            ime.reset()
            return False
        if 0x41 <= vk <= 0x5A:
            up = shift != bool(user32.GetKeyState(0x14) & 1)
            send(*ime.push(chr(vk + 32), up))
            return True
        if vk == 0x08 and ime.raw:
            send(*ime.pop())
            return True
        ime.reset()
        return False

    def handle(vk, down):
        if vk in MODS:
            return handle_mod(vk, down)
        if not down:
            if vk in swallowed:
                swallowed.discard(vk)
                return True
            return False
        pending[0] = False
        sw = handle_down(vk)
        if sw:
            swallowed.add(vk)
        else:
            swallowed.discard(vk)
        return sw

    def kb_proc(nCode, wParam, lParam):
        if nCode == 0:
            try:
                kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if kb.dwExtraInfo != MAGIC and kb.vkCode != 0xE7:
                    if handle(kb.vkCode, wParam in (0x100, 0x104)):
                        return 1
            except Exception:
                import traceback
                traceback.print_exc()
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def mouse_proc(nCode, wParam, lParam):
        if nCode == 0 and wParam in (0x201, 0x204, 0x207):  # click -> hết từ đang gõ
            ime.reset()
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    kb_cb, ms_cb = HOOKPROC(kb_proc), HOOKPROC(mouse_proc)
    hmod = kernel32.GetModuleHandleW(None)
    h1 = user32.SetWindowsHookExW(13, kb_cb, hmod, 0)
    h2 = user32.SetWindowsHookExW(14, ms_cb, hmod, 0)
    if not h1:
        print("Không cài được hook bàn phím, lỗi:", ctypes.get_last_error())
        return

    print("Gothic IME đang chạy. Ctrl+Shift: Anh/Việt | `: đổi font | Ctrl+C trong cửa sổ này: thoát")
    announce(880 if ime.vn else 440)

    msg = wintypes.MSG()
    try:
        while True:
            user32.MsgWaitForMultipleObjects(0, None, False, 100, 0x04FF)
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(h1)
        if h2:
            user32.UnhookWindowsHookEx(h2)


# ---------------------------- Self test ----------------------------
def selftest():
    cases = [
        ("tieengs", "tiếng"), ("Vieetj", "Việt"), ("nguoiwf", "người"), ("nguwowif", "người"),
        ("dduowcj", "được"), ("thuowng", "thương"), ("mowis", "mới"), ("chuyeenr", "chuyển"),
        ("hoaf", "hòa"), ("quas", "quá"), ("giaf", "già"), ("giuwx", "giữ"), ("ass", "as"),
        ("aaa", "aa"), ("ww", "w"), ("w", "ư"), ("muaw", "mưa"), ("khoong", "không"),
        ("chowi", "chơi"), ("minhf", "mình"), ("DDuowcj", "Được"), ("Hoaf", "Hòa"),
        ("tooi", "tôi"), ("ddi", "đi"), ("ddd", "dd"), ("anhs", "ánh"), ("quyeenf", "quyền"),
        ("giaos", "giáo"), ("muoons", "muốn"), ("duwowcj", "dược"), ("awn", "ăn"), ("Awn", "Ăn"),
        ("toans", "toán"), ("mieeng", "miêng"),
        ("minh", "minh"), ("chowi", "chơi"), ("choiw", "chơi"), ("asss", "ass"),
    ]
    bad = 0
    for raw, exp in cases:
        got = render([(c.lower(), c.isupper()) for c in raw], True, "normal")
        ok = got == exp
        bad += not ok
        print("%s %-10s -> %-8s %s" % ("OK " if ok else "BAD", raw, got, "" if ok else "(mong đợi %s)" % exp))
    print("\nFraktur  :", render([(c, False) for c in "minh"], True, "fraktur"),
          render([(c, False) for c in "chowi"], True, "fraktur"),
          render([(c, False) for c in "khoong"], True, "fraktur"))
    print("Bold     :", render([(c, False) for c in "minh"], True, "bold_fraktur"),
          render([(c.lower(), c.isupper()) for c in "Dduowcj"], True, "bold_fraktur"))
    print("EN+Fraktur:", render([(c, False) for c in "minh"], False, "fraktur"))
    print("\n%d lỗi" % bad)
    return bad


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(1 if selftest() else 0)
    if os.name != "nt":
        print("Chương trình này chỉ chạy trên Windows (dùng --selftest để kiểm tra engine).")
        sys.exit(1)
    if "--title" in sys.argv:
        import ctypes
        u = ctypes.windll.user32
        buf = ctypes.create_unicode_buffer(256)
        print("Trong 10 giây, click vào cửa sổ game để xem tiêu đề:")
        for _ in range(10):
            time.sleep(1)
            u.GetWindowTextW(u.GetForegroundWindow(), buf, 256)
            print(repr(buf.value))
        sys.exit(0)
    run_windows()

# Ghi chú BACKSPACE_MODE: khi đổi từ (vd "mi" + "f" -> "mì") chương trình xoá chữ cũ rồi gõ lại.
# Chữ Fraktur nằm ngoài BMP (2 đơn vị UTF-16) và dấu thanh là ký tự kết hợp, nên mỗi game
# xoá lùi theo một kiểu khác nhau. Nếu thấy gõ ra chữ bị lỗi/thừa/thiếu:
#   "codepoint": 1 backspace = 1 code point (mặc định, đúng với đa số ô nhập)
#   "utf16"    : 1 backspace = 1 đơn vị UTF-16 (nếu game xoá nửa ký tự)
#   "grapheme" : 1 backspace = xoá cả chữ + dấu kết hợp (nếu game xoá cả cụm)
