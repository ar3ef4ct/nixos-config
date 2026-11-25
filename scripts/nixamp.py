#!/usr/bin/env python3
"""NixAMP: panel kontrol Apache + MariaDB untuk NixOS, bisa dipakai penuh lewat keyboard.

Hanya memakai PyQt6 dan standard library Python.
"""
import codecs
import html
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from string import Template

from PyQt6.QtCore import (QEasingCurve, QEvent, QModelIndex, QPoint, QPointF, QProcess,
                          QProcessEnvironment, QRect, QRectF, Qt, QTimer, QVariantAnimation, pyqtSignal)
from PyQt6.QtGui import (QColor, QFileSystemModel, QFont, QFontMetrics, QKeySequence, QPainter,
                         QShortcut, QTextCharFormat, QTextCursor)
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton, QSizePolicy, QSplitter, QStackedWidget,
    QTextEdit, QTreeView, QVBoxLayout, QWidget,
)

# ── Palet: biru es ala salju Nix, hanya satu aksen ───────────────────────────
P = dict(
    INK="#0f1522", PANEL="#151d2e", HOVER="#1c2740", LINE="#243049", LINE_HI="#34456a",
    TEXT="#e8eef9", MUTED="#7b8aa8", ACCENT="#7ebae4",
    OK="#5ee0a0", WARN="#f2c46b", DANGER="#ff7a8a",
)

QSS = Template("""
* { outline: none; }
QMainWindow, #root { background: $INK; }
QWidget { color: $TEXT; }
QLabel { background: transparent; }
#brand { font-size: 19pt; font-weight: 700; }
#svcname { font-size: 12pt; font-weight: 600; }
#muted { color: $MUTED; }
#section { color: $MUTED; font-weight: 600; }
#panel { background: $PANEL; border: 1px solid $LINE; border-radius: 14px; }
#divider { background: $LINE; }
#empty { border: 1px dashed $LINE_HI; border-radius: 14px; color: $MUTED; }

#keycap { background: $PANEL; border: 1px solid $LINE_HI; border-bottom: 2px solid $LINE_HI;
          border-radius: 5px; padding: 1px 7px; font-size: 8pt; font-weight: 700; }
#keycap[on="true"] { background: $ACCENT; border-color: $ACCENT; color: $INK; }

QPushButton { background: transparent; border: 1px solid $LINE; border-radius: 8px; padding: 8px 14px; }
QPushButton:hover { background: $HOVER; border-color: $LINE_HI; }
QPushButton:pressed { background: $LINE; }
QPushButton:disabled { color: $MUTED; background: transparent; }
QPushButton[kind="util"] { background: $PANEL; }
QPushButton[kind="util"]:hover { background: $HOVER; }
QPushButton[kind="start"] { color: $OK; background: rgba(94,224,160,0.10);
                            border-color: rgba(94,224,160,0.28); font-weight: 600; }
QPushButton[kind="start"]:hover { background: rgba(94,224,160,0.20); }
QPushButton[kind="stop"] { color: $DANGER; background: rgba(255,122,138,0.10);
                           border-color: rgba(255,122,138,0.28); font-weight: 600; }
QPushButton[kind="stop"]:hover { background: rgba(255,122,138,0.20); }
QPushButton[kind="active"] { color: $ACCENT; background: rgba(126,186,228,0.12);
                             border-color: rgba(126,186,228,0.40); font-weight: 600; }
QPushButton[kind="active"]:hover { background: rgba(126,186,228,0.22); }
QPushButton[kind]:focus { border: 1px solid $ACCENT; }

QLineEdit, QComboBox { background: $PANEL; border: 1px solid $LINE; border-radius: 8px;
                       padding: 8px 12px; selection-background-color: $LINE_HI; }
QLineEdit:focus, QComboBox:focus { border-color: $ACCENT; }
QComboBox QAbstractItemView { background: $PANEL; border: 1px solid $LINE; outline: 0;
                              selection-background-color: $HOVER; selection-color: $TEXT; }

QTextEdit, QListWidget, QTreeView { background: $PANEL; border: 1px solid $LINE; border-radius: 12px;
                                    padding: 6px; selection-background-color: $LINE_HI; }
QTextEdit { padding: 8px 10px; }
QTextEdit:focus, QListWidget:focus, QTreeView:focus { border-color: $ACCENT; }
QListWidget::item, QTreeView::item { padding: 5px 8px; border-radius: 6px; }
QListWidget::item:hover, QTreeView::item:hover { background: $HOVER; }
QListWidget::item:selected, QTreeView::item:selected { background: $LINE; color: $TEXT; }
QHeaderView { background: transparent; border: none; }
QHeaderView::section { background: transparent; color: $MUTED; border: none; padding: 4px 8px;
                       font-weight: 600; }
QScrollBar:vertical, QScrollBar:horizontal { background: transparent; width: 8px; height: 8px; margin: 2px; }
QScrollBar::handle { background: $LINE_HI; border-radius: 3px; min-height: 28px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QSplitter::handle:vertical { height: 12px; background: transparent; }
QSplitter::handle:horizontal { width: 12px; background: transparent; }
""").substitute(P)

# state systemd -> (label, warna, berdenyut)
STATE = {
    "active": ("Berjalan", "OK", True),
    "activating": ("Memulai", "WARN", True),
    "deactivating": ("Menghentikan", "WARN", True),
    "failed": ("Gagal", "DANGER", False),
    "inactive": ("Berhenti", "MUTED", False),
}
PAGE_EMPTY, PAGE_TEXT, PAGE_CONFIG, PAGE_EXPLORER, PAGE_SHELL = range(5)

HOME = str(Path.home())
CONFIG_DIR = Path.home() / ".config" / "nixamp"
CUSTOM_PATHS = CONFIG_DIR / "custom_paths.json"
FOLDERS_FILE = CONFIG_DIR / "folders.json"
COMMANDS_FILE = CONFIG_DIR / "commands.json"

DEFAULT_FOLDERS = [HOME, "/var/www/localhost", "/mnt/data/Kuliah", "/etc/nixos"]
DEFAULT_COMMANDS = [
    {"label": "apache", "cmd": "systemctl status httpd --no-pager"},
    {"label": "mariadb", "cmd": "systemctl status mysql --no-pager"},
    {"label": "disk", "cmd": "df -h"},
]

SHELL_BIN = shutil.which("bash") or "/bin/sh"
SETSID = shutil.which("setsid")  # supaya Ctrl+C bisa menghentikan seluruh proses anak
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")
ADD_RE = re.compile(r'^add\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s+(.+)$', re.I | re.S)
RM_RE = re.compile(r"^(?:rm|del)\s+(.+)$", re.I)
MANAGE_RE = re.compile(r"^(add|rm|del)(\s|$)", re.I)

# Helper admin: dijalankan SEKALI lewat pkexec (satu kali password) dan hidup selama aplikasi terbuka.
# Ia membaca perintah dari stdin dan hanya menerima start/stop untuk unit yang ada di daftar putih.
SYSTEMCTL = shutil.which("systemctl")
SH_BIN = shutil.which("sh") or "/bin/sh"
UNIT_RE = re.compile(r"^[A-Za-z0-9_.@-]+$")
HELPER_SCRIPT = r"""echo READY
while IFS=' ' read -r action unit; do
  case "$action:$unit" in
    @ALLOWED@)
      out=$("$1" "$action" "$unit" 2>&1); rc=$?
      [ -z "$out" ] || printf '%s\n' "$out"
      printf '__DONE__ %s\n' "$rc" ;;
    *) printf '__DONE__ 126\n' ;;
  esac
done
"""


# ── Helper ───────────────────────────────────────────────────────────────────
def restyle(w):
    w.style().unpolish(w)
    w.style().polish(w)


def keep_space(w):
    sp = w.sizePolicy()
    sp.setRetainSizeWhenHidden(True)
    w.setSizePolicy(sp)
    return w


def short(path):
    return "~" + path[len(HOME):] if path == HOME or path.startswith(HOME + os.sep) else path


def run(args, timeout=5):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"Error: {e}"


def unit_status(unit):
    try:
        out = subprocess.run(["systemctl", "show", unit, "-p", "ActiveState", "-p", "MainPID"],
                             capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", "0"
    d = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    return d.get("ActiveState", "unknown"), d.get("MainPID", "0")


def load_list(path, default=()):
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
    except (OSError, ValueError):
        pass
    return list(default)


def save_list(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def pair(key, text):
    """Keycap + label kecil; dipakai untuk petunjuk tombol."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    cap, lab = Keycap(key), QLabel(text)
    lab.setObjectName("muted")
    lay.addWidget(cap)
    lay.addWidget(lab)
    return w, cap


# ── Widget kecil ─────────────────────────────────────────────────────────────
class Keycap(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setObjectName("keycap")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("on", False)

    def set_on(self, on):
        self.setProperty("on", on)
        restyle(self)


class KeyButton(QPushButton):
    """Tombol dengan badge keycap yang muncul (fade) saat mode petunjuk aktif."""

    def __init__(self, text, kind="ghost", min_w=116):
        super().__init__(text)
        self.key, self.hint_opacity = "", 0.0
        self.setProperty("kind", kind)
        self.setMinimumWidth(min_w)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # fokus lewat Tab, bukan klik mouse
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_kind(self, kind):
        if self.property("kind") != kind:
            self.setProperty("kind", kind)
            restyle(self)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if not self.key or self.hint_opacity < 0.02:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self.hint_opacity)
        f = QFont(self.font())
        f.setPointSizeF(7.5)
        f.setBold(True)
        p.setFont(f)
        w = max(18, QFontMetrics(f).horizontalAdvance(self.key) + 10)
        r = QRectF(self.width() - w - 8, (self.height() - 18) / 2, w, 18)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(P["ACCENT"]))
        p.drawRoundedRect(r, 5, 5)
        p.setPen(QColor(P["INK"]))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.key)
        p.end()


class HistoryInput(QLineEdit):
    """Input shell: panah atas/bawah menelusuri riwayat, Tab mengganti layar shell / shortcut."""
    tab = pyqtSignal()

    def __init__(self, history):
        super().__init__()
        self.history, self.pos, self.use_history = history, len(history), True

    def event(self, ev):
        if ev.type() == QEvent.Type.KeyPress and ev.key() == Qt.Key.Key_Tab:
            self.tab.emit()
            return True
        return super().event(ev)

    def keyPressEvent(self, ev):
        k = ev.key()
        if k in (Qt.Key.Key_Up, Qt.Key.Key_Down) and self.use_history and self.history:
            step = -1 if k == Qt.Key.Key_Up else 1
            self.pos = max(0, min(len(self.history), self.pos + step))
            self.setText(self.history[self.pos] if self.pos < len(self.history) else "")
            return
        super().keyPressEvent(ev)


class StatusDot(QWidget):
    """Titik status; berdenyut pelan hanya saat layanan aktif / sedang berubah."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(20, 20)
        self.color, self.pulse, self.t = QColor(P["MUTED"]), False, 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setDuration(1800)
        self.anim.setLoopCount(-1)
        self.anim.valueChanged.connect(self._tick)

    def _tick(self, v):
        self.t = float(v)
        self.update()

    def set_state(self, color, pulse):
        self.color, self.pulse = QColor(color), pulse
        if pulse and self.anim.state() != self.anim.State.Running:
            self.anim.start()
        elif not pulse:
            self.anim.stop()
            self.t = 0.0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        c = QPointF(self.width() / 2, self.height() / 2)
        if self.pulse:
            halo = QColor(self.color)
            halo.setAlphaF(0.40 * (1 - self.t))
            p.setBrush(halo)
            r = 4.5 + 5.5 * self.t
            p.drawEllipse(c, r, r)
        p.setBrush(self.color)
        p.drawEllipse(c, 4.5, 4.5)
        p.end()


@dataclass
class Service:
    unit: str
    name: str
    ports: str
    keys: tuple          # toggle, admin, config, logs
    admin_url: str
    paths: tuple
    state: str = ""
    row: object = None


class ServiceRow(QWidget):
    def __init__(self, svc):
        super().__init__()
        self.svc, self.busy = svc, False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 14, 14)
        lay.setSpacing(10)

        self.dot = StatusDot()
        name = QLabel(svc.name)
        name.setObjectName("svcname")
        self.status, self.detail = QLabel(), QLabel()
        self.detail.setObjectName("muted")
        sub = QHBoxLayout()
        sub.setSpacing(14)
        sub.addWidget(self.status)
        sub.addWidget(self.detail)
        sub.addStretch()
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(name)
        col.addLayout(sub)

        lay.addWidget(self.dot)
        lay.addSpacing(4)
        lay.addLayout(col, 1)
        self.toggle = KeyButton("Start", "start")
        self.admin, self.config, self.logs = KeyButton("Admin"), KeyButton("Config"), KeyButton("Logs")
        for b in (self.toggle, self.admin, self.config, self.logs):
            lay.addWidget(b)
        self.set_state("inactive", "0")

    def _paint_toggle(self, state):
        running = state == "active"
        self.toggle.setText("Stop" if running else "Start")
        self.toggle.set_kind("stop" if running else "start")

    def set_state(self, state, pid):
        label, color, pulse = STATE.get(state, (state, "MUTED", False))
        self.dot.set_state(P[color], pulse)
        self.status.setText(label)
        self.status.setStyleSheet(f"color: {P[color]}; font-weight: 600;")
        parts = [f"PID {pid}"] if state == "active" and pid != "0" else []
        self.detail.setText("     ".join(parts + [f"port {self.svc.ports}"]))
        if not self.busy:
            self._paint_toggle(state)

    def set_busy(self, busy):
        self.busy = busy
        self.toggle.setEnabled(not busy)
        if busy:
            self.toggle.setText("…")
        else:
            self._paint_toggle(self.svc.state)


# ── Jendela utama ────────────────────────────────────────────────────────────
class NixAMP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NixAMP")
        self.resize(940, 800)
        self.setMinimumSize(820, 660)

        self.hints_on, self.level = False, 0.0
        self.keymap, self.chips = {}, []
        self._last_nav = None
        self.ctx = {PAGE_CONFIG: {}, PAGE_EXPLORER: {}, PAGE_SHELL: {}}  # tombol khusus per halaman

        self.mono = QFont()
        self.mono.setFamilies(["JetBrains Mono", "Fira Code", "Noto Sans Mono", "monospace"])
        self.mono.setPointSize(9)

        # shell
        fd, self.sh_cwd_file = tempfile.mkstemp(prefix="nixamp-cwd-")
        os.close(fd)
        self.sh_cwd, self.sh_proc, self.sh_stopping = HOME, None, False
        self.sh_mode, self.sh_history, self._sh_bol = False, [], True
        self.helper, self.helper_ready, self._hbuf, self._closing = None, False, "", False
        self._jobs, self._job, self._job_out = [], None, []
        self.commands = [c for c in load_list(COMMANDS_FILE, DEFAULT_COMMANDS)
                         if isinstance(c, dict) and c.get("cmd")]
        # explorer
        existing = [d for d in DEFAULT_FOLDERS if os.path.isdir(d)]
        self.folders = [p for p in load_list(FOLDERS_FILE, existing) if isinstance(p, str)]
        self.ex_path, self._ex_select, self._ex_pending = "", None, False

        self.services = [
            Service("httpd", "Apache", "80, 443", ("1", "q", "w", "e"), "http://localhost",
                    ("/var/www/localhost", "/mnt/data/Kuliah/", "/etc/nixos/configuration.nix")),
            Service("mysql", "MariaDB", "3306", ("2", "a", "s", "d"), "http://localhost/phpmyadmin",
                    ("/var/lib/mysql", "/etc/nixos/configuration.nix")),
        ]

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(26, 22, 26, 18)
        lay.setSpacing(14)

        lay.addLayout(self._build_header())
        lay.addWidget(self._build_services())
        lay.addLayout(self._build_utils())

        split = QSplitter(Qt.Orientation.Vertical)
        split.setChildrenCollapsible(False)
        split.addWidget(self._build_workspace())
        split.addWidget(self._build_activity())
        split.setStretchFactor(0, 4)
        split.setStretchFactor(1, 1)
        split.setSizes([520, 110])
        lay.addWidget(split, 1)
        # widget non-tombol yang bisa dituju navigasi hjkl
        self.nav_widgets = [self.tree, self.ex_list, self.combo, self.text, self.sh_out, self.sc_view]

        self.hint_anim = QVariantAnimation(self)
        self.hint_anim.setDuration(140)
        self.hint_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hint_anim.valueChanged.connect(self._set_level)

        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        QApplication.instance().installEventFilter(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

        self._sync_chrome()
        self.log("NixAMP siap. Tekan F untuk melihat tombol pintas.")
        self.sh_write("Tab membuka daftar shortcut. Ctrl+C menghentikan perintah.\n", P["MUTED"])
        self.refresh()
        QTimer.singleShot(600, self.start_helper)  # minta password admin sekali, setelah jendela tampil

    # ---- UI ----
    def _build_header(self):
        row = QHBoxLayout()
        brand, sub = QLabel("NixAMP"), QLabel("Apache dan MariaDB untuk NixOS")
        brand.setObjectName("brand")
        sub.setObjectName("muted")
        box = QVBoxLayout()
        box.setSpacing(0)
        box.addWidget(brand)
        box.addWidget(sub)
        hint, self.f_cap = pair("F", "Tombol pintas")
        nav_hint, _ = pair("hjkl", "Navigasi")
        self.chips.append(keep_space(nav_hint))
        row.addLayout(box)
        row.addStretch()
        row.addWidget(nav_hint, 0, Qt.AlignmentFlag.AlignTop)
        row.addSpacing(18)
        row.addWidget(hint, 0, Qt.AlignmentFlag.AlignTop)
        return row

    def _build_services(self):
        panel = QFrame()
        panel.setObjectName("panel")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)
        for i, s in enumerate(self.services):
            if i:
                line = QFrame()
                line.setObjectName("divider")
                line.setFixedHeight(1)
                pl.addWidget(line)
            s.row = r = ServiceRow(s)
            pl.addWidget(r)
            r.toggle.clicked.connect(lambda _=False, s=s: self.toggle_service(s))
            r.admin.clicked.connect(lambda _=False, s=s: self.open_admin(s))
            r.config.clicked.connect(lambda _=False, s=s: self.show_config(s))
            r.logs.clicked.connect(lambda _=False, s=s: self.show_logs(s))
            for key, b in zip(s.keys, (r.toggle, r.admin, r.config, r.logs)):
                self.bind(key, b)
        return panel

    def _build_utils(self):
        row = QHBoxLayout()
        row.setSpacing(8)
        items = (("Netstat", "z", self.util_netstat), ("Shell", "x", self.show_shell),
                 ("Explorer", "c", self.show_explorer))
        for label, key, fn in items:
            b = KeyButton(label, "util")
            b.clicked.connect(fn)
            self.bind(key, b)
            row.addWidget(b)
        quit_btn = self.quit_btn = KeyButton("Quit", "util")
        quit_btn.key = "Ctrl+Q"
        quit_btn.clicked.connect(self.close)
        row.addWidget(quit_btn)
        for i in range(row.count()):
            row.itemAt(i).widget().setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return row

    def _build_workspace(self):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        head = QHBoxLayout()
        self.ws_title = QLabel("Workspace")
        self.ws_title.setObjectName("section")
        self.esc_hint, _ = pair("Esc", "Tutup")
        keep_space(self.esc_hint)
        head.addWidget(self.ws_title)
        head.addStretch()
        head.addWidget(self.esc_hint)
        lay.addLayout(head)

        self.stack = QStackedWidget()
        empty = QLabel(
            f"<p style='font-size:12pt; color:{P['TEXT']}'>Belum ada yang dibuka</p>"
            "<p>Pilih Admin, Config, atau Logs pada sebuah layanan,<br>"
            "atau buka Shell dan Explorer dari baris di atas.<br>"
            "Tekan <b>F</b> untuk melihat tombol pintasnya, <b>h j k l</b> untuk berpindah.</p>")
        empty.setObjectName("empty")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(self.mono)
        self.text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        for page in (empty, self.text, self._build_config_page(),
                     self._build_explorer_page(), self._build_shell_page()):
            self.stack.addWidget(page)  # urutan harus sama dengan PAGE_*
        lay.addWidget(self.stack, 1)
        return box

    def _build_config_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.combo = QComboBox()
        self.btn_kwrite, self.btn_dolphin = KeyButton("KWrite"), KeyButton("Dolphin")
        self.btn_kwrite.setToolTip("Buka dengan KWrite (Enter atau O)")
        self.btn_dolphin.setToolTip("Buka folder dengan Dolphin")
        self.btn_kwrite.clicked.connect(self.open_kwrite)
        self.btn_dolphin.clicked.connect(self.open_dolphin)
        self.bind("o", self.btn_kwrite, PAGE_CONFIG)
        self.bind("b", self.btn_dolphin, PAGE_CONFIG)
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(self.combo, 1)
        row1.addWidget(self.btn_kwrite)
        row1.addWidget(self.btn_dolphin)

        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Tambah path kustom, lalu tekan Enter")
        self.txt_path.returnPressed.connect(self.add_path)
        slash = keep_space(Keycap("/"))
        self.chips.append(slash)
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(self.txt_path, 1)
        row2.addWidget(slash, 0, Qt.AlignmentFlag.AlignVCenter)

        lay.addLayout(row1)
        lay.addLayout(row2)
        lay.addStretch()
        return page

    def _build_explorer_page(self):
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)

        # kiri: pintasan folder
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(8)
        title = QLabel("Pintasan")
        title.setObjectName("section")
        self.ex_list = QListWidget()
        self.ex_list.setToolTip("Enter membuka folder, Delete menghapus pintasan")
        self.ex_list.itemClicked.connect(self._ex_pick_item)
        self.ex_list.itemActivated.connect(self._ex_pick_item)
        btn_add = KeyButton("Tambah", "util")
        btn_add.setToolTip("Pilih folder untuk dijadikan pintasan")
        btn_add.clicked.connect(self.explorer_add_dialog)
        self.bind("n", btn_add, PAGE_EXPLORER)
        ll.addWidget(title)
        ll.addWidget(self.ex_list, 1)
        ll.addWidget(btn_add)
        left.setMinimumWidth(190)
        left.setMaximumWidth(250)

        # kanan: explorer
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.addr = QLineEdit()
        self.addr.setPlaceholderText("Ketik path folder, lalu Enter")
        self.addr.returnPressed.connect(lambda: self.explorer_go(self.addr.text()))
        slash = keep_space(Keycap("/"))
        self.chips.append(slash)
        bar.addWidget(self.addr, 1)
        bar.addWidget(slash)
        for label, key, fn, tip in (
                ("Pin", "p", self.explorer_pin, "Jadikan folder ini pintasan"),
                ("Shell", "t", self.explorer_shell_here, "Buka Shell di folder ini"),
                ("Dolphin", "b", lambda: self.launch(["dolphin", self.ex_path or HOME],
                                                      "Membuka folder di Dolphin"),
                 "Buka folder ini di Dolphin (salin, ganti nama, hapus)")):
            b = KeyButton(label, min_w=108)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            self.bind(key, b, PAGE_EXPLORER)
            bar.addWidget(b)
        rl.addLayout(bar)

        self.fs = QFileSystemModel(self)
        self.fs.setOption(QFileSystemModel.Option.DontUseCustomDirectoryIcons)
        self.fs.setReadOnly(True)
        self.fs.directoryLoaded.connect(self._ex_loaded)
        self.tree = QTreeView()
        self.tree.setModel(self.fs)
        self.tree.setRootIsDecorated(False)
        self.tree.setItemsExpandable(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree.hideColumn(2)
        hdr = self.tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.activated.connect(self._ex_activated)
        rl.addWidget(self.tree, 1)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        split.setSizes([210, 700])
        self._refresh_folders()
        return split

    def _build_shell_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(10)
        self.sh_cwd_label, self.sh_status = QLabel(), QLabel()
        self.sh_cwd_label.setObjectName("muted")
        self.sh_status.setStyleSheet(f"color: {P['WARN']}; font-weight: 600;")
        self.btn_mode, self.btn_konsole = KeyButton("Shortcut", min_w=136), KeyButton("Konsole")
        self.btn_mode.setToolTip("Daftar shortcut perintah (Tab saat mengetik)")
        self.btn_konsole.setToolTip("Buka Konsole di folder ini (untuk program interaktif)")
        self.btn_mode.clicked.connect(lambda: self.set_sh_mode(not self.sh_mode))
        self.btn_konsole.clicked.connect(self.open_konsole)
        self.bind("m", self.btn_mode, PAGE_SHELL)
        self.bind("t", self.btn_konsole, PAGE_SHELL)
        head.addWidget(self.sh_cwd_label)
        head.addWidget(self.sh_status)
        head.addStretch()
        head.addWidget(self.btn_mode)
        head.addWidget(self.btn_konsole)
        lay.addLayout(head)

        # layar: output shell, atau daftar shortcut
        self.sh_out, self.sc_view = QTextEdit(), QTextEdit()
        for view in (self.sh_out, self.sc_view):
            view.setReadOnly(True)
            view.setFont(self.mono)
            view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.sh_out.document().setMaximumBlockCount(3000)
        self.sh_stack = QStackedWidget()
        self.sh_stack.addWidget(self.sh_out)
        self.sh_stack.addWidget(self.sc_view)
        lay.addWidget(self.sh_stack, 1)

        # input yang sama untuk kedua mode
        self.sh_prompt = QLabel("❯")
        self.sh_prompt.setStyleSheet(f"color: {P['ACCENT']}; font-weight: 700;")
        self.sh_input = HistoryInput(self.sh_history)
        self.sh_input.setFont(self.mono)
        self.sh_input.returnPressed.connect(self._sh_submit)
        self.sh_input.textChanged.connect(self._sh_text_changed)
        self.sh_input.tab.connect(lambda: self.set_sh_mode(not self.sh_mode))
        slash = keep_space(Keycap("/"))
        self.chips.append(slash)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.sh_prompt)
        row.addWidget(self.sh_input, 1)
        row.addWidget(slash)
        lay.addLayout(row)
        self.set_sh_mode(False)
        return page

    def _build_activity(self):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        title = QLabel("Aktivitas")
        title.setObjectName("section")
        self.sys_log = QTextEdit()
        self.sys_log.setReadOnly(True)
        self.sys_log.document().setMaximumBlockCount(300)
        lay.addWidget(title)
        lay.addWidget(self.sys_log, 1)
        return box

    # ---- Keyboard ----
    def bind(self, key, btn, page=None):
        btn.key = key.upper()
        (self.ctx[page] if page is not None else self.keymap)[key] = btn

    def eventFilter(self, obj, ev):
        if ev.type() != QEvent.Type.KeyPress or not self.isActiveWindow():
            return False
        if QApplication.activePopupWidget() is not None:  # dropdown / menu terbuka
            return False
        fw, key, mods = QApplication.focusWidget(), ev.key(), ev.modifiers()
        page = self.stack.currentIndex()

        if (key == Qt.Key.Key_C and mods == Qt.KeyboardModifier.ControlModifier
                and self.sh_proc is not None and not self.sh_out.textCursor().hasSelection()):
            self.stop_cmd()
            return True
        if key == Qt.Key.Key_Escape:
            if isinstance(fw, QLineEdit):
                fw.clearFocus()
            else:
                in_grid = fw in self.keymap.values() or fw is self.quit_btn
                if fw is not None and not in_grid:
                    fw.clearFocus()  # fokus di dalam panel: lepas, tombol utama tetap fokus
                self.show_page(PAGE_EMPTY)
            return True
        if isinstance(fw, QLineEdit):  # sedang mengetik: jangan curi huruf
            return False
        vim = {Qt.Key.Key_H: "h", Qt.Key.Key_J: "j", Qt.Key.Key_K: "k", Qt.Key.Key_L: "l"}
        if mods == Qt.KeyboardModifier.ControlModifier and key in vim:
            self._vim(vim[key], fw, page, True, ev.isAutoRepeat())  # Ctrl+hjkl: pindah panel
            return True
        if mods not in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.KeypadModifier):
            return False

        if key == Qt.Key.Key_Delete:
            if fw is self.ex_list:
                self.explorer_unpin()
                return True
        if page == PAGE_EXPLORER:
            if key == Qt.Key.Key_Backspace:
                self.explorer_up()
                return True
            if key == Qt.Key.Key_Left and fw is self.tree:
                self.ex_list.setFocus()
                return True
            if key == Qt.Key.Key_Right and fw is self.ex_list:
                self.tree.setFocus()
                return True

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if isinstance(fw, QPushButton):
                fw.animateClick()
                return True
            if page == PAGE_CONFIG and isinstance(fw, QComboBox):
                self.btn_kwrite.animateClick()
                return True
            return False

        k = ev.text().lower()
        if not k:
            return False
        repeat = ev.isAutoRepeat()  # tahan tombol tidak boleh memicu aksi berulang
        if k == "f":
            if not repeat:
                self.toggle_hints()
            return True
        if k in ("h", "j", "k", "l"):
            self._vim(k, fw, page, False, repeat)
            return True
        if k == "/":
            if not repeat and self._page_key(page):
                return True
            return repeat

        btn = self.ctx.get(page, {}).get(k) or self.keymap.get(k)
        if btn is None:
            return False
        if not repeat:
            btn.animateClick()
        return True

    def _page_key(self, page):
        """Tombol '/' memfokuskan kolom input pada halaman yang punya."""
        target = {PAGE_CONFIG: self.txt_path, PAGE_EXPLORER: self.addr, PAGE_SHELL: self.sh_input}.get(page)
        if target is None:
            return False
        target.setFocus()
        if page == PAGE_EXPLORER:
            target.selectAll()
        return True

    # ---- Navigasi gaya vim ----
    def _vim(self, d, fw, page, ctrl, repeat):
        """h/j/k/l mengikuti widget yang sedang fokus; Ctrl+hjkl selalu memindah fokus antar panel."""
        if ctrl:
            self._spatial(fw, d)
        elif fw is self.tree:
            if d in "jk":
                self._step_view(self.tree, 1 if d == "j" else -1)
            elif not repeat:
                if d == "h":
                    self.explorer_up()
                elif self.tree.currentIndex().isValid():
                    self._ex_activated(self.tree.currentIndex())
        elif fw is self.ex_list:
            if d in "jk":
                self._step_view(self.ex_list, 1 if d == "j" else -1)
            elif d == "l" and not repeat and self.ex_list.currentItem():
                self._ex_pick_item(self.ex_list.currentItem())
        elif isinstance(fw, QComboBox) and d in "jk":
            i = fw.currentIndex() + (1 if d == "j" else -1)
            if 0 <= i < fw.count():
                fw.setCurrentIndex(i)
        elif isinstance(fw, QTextEdit) and fw.isReadOnly():
            self._scroll(fw, d)
        elif fw is None and page in (PAGE_TEXT, PAGE_SHELL):
            self._scroll(self.text if page == PAGE_TEXT else self.sh_stack.currentWidget(), d)
        else:
            self._spatial(fw, d)

    def _step_view(self, view, delta):
        if isinstance(view, QListWidget):
            if view.count():
                view.setCurrentRow(max(0, min(view.count() - 1, view.currentRow() + delta)))
            return
        root, cur = view.rootIndex(), view.currentIndex()
        row = max(0, (cur.row() if cur.isValid() else -delta) + delta)
        idx = view.model().index(row, 0, root)
        if idx.isValid():
            view.setCurrentIndex(idx)
            view.scrollTo(idx)

    @staticmethod
    def _scroll(te, d):
        bar = te.verticalScrollBar() if d in "jk" else te.horizontalScrollBar()
        bar.setValue(bar.value() + bar.singleStep() * 2 * (1 if d in "jl" else -1))

    def _spatial(self, fw, d):
        """Pindah fokus ke tombol / panel terdekat pada arah h, j, k, atau l."""
        targets = [w for w in self.findChildren(KeyButton) + self.nav_widgets
                   if w.isVisible() and w.isEnabled()]

        def rect(w):
            return QRect(w.mapToGlobal(QPoint(0, 0)), w.size())

        if fw not in targets:
            start = self._last_nav if self._last_nav in targets else self.services[0].row.toggle
            start.setFocus(Qt.FocusReason.OtherFocusReason)
            self._last_nav = start
            return
        f, best, best_score = rect(fw), None, None
        for w in targets:
            if w is fw:
                continue
            c = rect(w)
            if d in "hl":
                ok = c.center().x() > f.center().x() if d == "l" else c.center().x() < f.center().x()
                main = max(0, c.left() - f.right()) if d == "l" else max(0, f.left() - c.right())
                perp = max(0, c.top() - f.bottom(), f.top() - c.bottom())
                off = abs(c.center().y() - f.center().y())
            else:
                ok = c.center().y() > f.center().y() if d == "j" else c.center().y() < f.center().y()
                main = max(0, c.top() - f.bottom()) if d == "j" else max(0, f.top() - c.bottom())
                perp = max(0, c.left() - f.right(), f.left() - c.right())
                off = abs(c.center().x() - f.center().x())
            if ok:
                score = (perp > 0, main, perp, off)  # utamakan yang sejajar, lalu yang terdekat
                if best_score is None or score < best_score:
                    best, best_score = w, score
        if best is not None:
            best.setFocus(Qt.FocusReason.OtherFocusReason)
            self._last_nav = best

    def toggle_hints(self):
        self.hints_on = not self.hints_on
        self.f_cap.set_on(self.hints_on)
        self._sync_chrome()
        self.hint_anim.stop()
        self.hint_anim.setStartValue(self.level)
        self.hint_anim.setEndValue(1.0 if self.hints_on else 0.0)
        self.hint_anim.start()

    def _set_level(self, v):
        self.level = float(v)
        for b in self.findChildren(KeyButton):
            b.hint_opacity = self.level
            b.update()

    def _sync_chrome(self):
        self.esc_hint.setVisible(self.hints_on and self.stack.currentIndex() != PAGE_EMPTY)
        for c in self.chips:
            c.setVisible(self.hints_on)

    def show_page(self, idx, title="Workspace"):
        self.stack.setCurrentIndex(idx)
        self.ws_title.setText(title)
        self._sync_chrome()

    # ---- Log ----
    def log(self, msg, level="info"):
        color = {"ok": P["OK"], "err": P["DANGER"]}.get(level, P["TEXT"])
        self.sys_log.append(
            f'<span style="color:{P["MUTED"]}">{time.strftime("%H:%M:%S")}</span>&nbsp;&nbsp;'
            f'<span style="color:{color}">{html.escape(msg)}</span>')

    def launch(self, args, msg):
        try:
            subprocess.Popen(args, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log(msg)
        except OSError:
            self.log(f"'{args[0]}' tidak ditemukan di PATH.", "err")

    # ---- Layanan ----
    def refresh(self):
        for s in self.services:
            state, pid = unit_status(s.unit)
            if s.state and s.state != state:
                old, new = STATE.get(s.state, (s.state,))[0], STATE.get(state, (state,))[0]
                self.log(f"{s.name}: {old} → {new}", "ok" if state == "active" else
                         "err" if state == "failed" else "info")
            s.state = state
            s.row.set_state(state, pid)

    def toggle_service(self, s):
        if s.row.busy:
            return
        action = "stop" if s.state == "active" else "start"
        s.row.set_busy(True)
        self._jobs.append((s, action))
        self.log(f"{action.capitalize()} {s.name}…")
        if self.helper is None and not self.start_helper():
            self._fail_jobs()
            return
        self._pump()

    # ---- Helper admin: password cukup sekali ----
    def start_helper(self):
        if self.helper is not None:
            return True
        if not SYSTEMCTL:
            self.log("systemctl tidak ditemukan di PATH.", "err")
            return False
        allowed = "|".join(f"{a}:{s.unit}" for s in self.services
                           for a in ("start", "stop") if UNIT_RE.match(s.unit))
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        p.readyRead.connect(self._helper_read)
        p.finished.connect(lambda code, _st, p=p: self._helper_exit(p, code))
        p.errorOccurred.connect(
            lambda err, p=p: self._helper_exit(p, 127) if err == QProcess.ProcessError.FailedToStart else None)
        self.helper, self.helper_ready, self._hbuf = p, False, ""
        self.log("Meminta akses admin sekali untuk start/stop layanan…")
        p.start("pkexec", [SH_BIN, "-c", HELPER_SCRIPT.replace("@ALLOWED@", allowed),
                           "nixamp-helper", SYSTEMCTL])
        return True

    def _helper_read(self):
        if self.helper is None:
            return
        self._hbuf += bytes(self.helper.readAll()).decode(errors="replace")
        *lines, self._hbuf = self._hbuf.split("\n")
        for line in lines:
            if line == "READY":
                self.helper_ready = True
                self.log("Akses admin aktif selama aplikasi terbuka.", "ok")
                self._pump()
            elif line.startswith("__DONE__ "):
                rc = line.split()[1]
                self._job_done(int(rc) if rc.isdigit() else 1)
            elif self._job is not None:
                self._job_out.append(line)

    def _pump(self):
        if not self.helper_ready or self._job is not None or not self._jobs:
            return
        s, action = self._jobs.pop(0)
        self._job, self._job_out = (s, action), []
        self.helper.write(f"{action} {s.unit}\n".encode())

    def _job_done(self, rc):
        if self._job is None:
            return
        s, action = self._job
        self._job = None
        s.row.set_busy(False)
        if rc != 0:
            self.log(f"Gagal {action} {s.name} (kode {rc}). {' '.join(self._job_out)}".strip(), "err")
        self.refresh()
        self._pump()

    def _fail_jobs(self):
        for s, _ in ([self._job] if self._job else []) + self._jobs:
            s.row.set_busy(False)
        self._job, self._jobs = None, []

    def _helper_exit(self, p, code):
        if self.helper is not p:
            return
        was_ready = self.helper_ready
        self.helper, self.helper_ready = None, False
        p.deleteLater()
        self._fail_jobs()
        if self._closing:
            return
        if code in (126, 127) and not was_ready:
            self.log("Otorisasi dibatalkan. Akan diminta lagi saat kamu menekan Start atau Stop.")
        elif code != 0:
            self.log(f"Helper admin berhenti (kode {code}).", "err")

    def open_admin(self, s):
        self.launch(["xdg-open", s.admin_url], f"Membuka {s.admin_url}")

    def show_logs(self, s):
        out = run(["journalctl", "-u", s.unit, "-n", "120", "--no-pager"])
        self.show_text(f"Log {s.unit}", out or "Tidak ada log ditemukan.")

    def show_text(self, title, content):
        self.text.setPlainText(content)
        self.text.moveCursor(QTextCursor.MoveOperation.End)
        self.show_page(PAGE_TEXT, title)
        self.text.setFocus()  # PgUp / PgDn langsung bisa scroll

    # ---- Config ----
    def show_config(self, s):
        self.combo.clear()
        custom = [p for p in load_list(CUSTOM_PATHS) if isinstance(p, str)]
        self.combo.addItems(list(dict.fromkeys(list(s.paths) + custom)))
        self.show_page(PAGE_CONFIG, f"Config {s.name}")
        self.combo.setFocus()  # panah atas/bawah memilih target

    def add_path(self):
        path = os.path.expanduser(self.txt_path.text().strip())
        if not path:
            return
        if not os.path.exists(path):
            self.log(f"Path tidak ditemukan: {path}", "err")
            return
        if self.combo.findText(path) < 0:
            self.combo.addItem(path)
        self.combo.setCurrentIndex(self.combo.findText(path))
        saved = [p for p in load_list(CUSTOM_PATHS) if isinstance(p, str)]
        if path not in saved:
            save_list(CUSTOM_PATHS, saved + [path])
        self.txt_path.clear()
        self.combo.setFocus()
        self.log(f"Path kustom disimpan: {path}", "ok")

    def open_kwrite(self):
        target = self.combo.currentText()
        if target:
            self.launch(["kwrite", target], f"Membuka {target} di KWrite")

    def open_dolphin(self):
        target = self.combo.currentText()
        if target:
            folder = target if os.path.isdir(target) else os.path.dirname(target)
            self.launch(["dolphin", folder], f"Membuka {folder} di Dolphin")

    def util_netstat(self):
        self.show_text("Port aktif (ss -tulpn)", run(["ss", "-tulpn"]))
        self.log("Menampilkan port jaringan yang aktif.")

    # ---- Explorer ----
    def show_explorer(self):
        self.show_page(PAGE_EXPLORER, "Explorer")
        if not self.ex_path:
            start = "/var/www/localhost" if os.path.isdir("/var/www/localhost") else HOME
            self.explorer_go(start)
        else:
            self.tree.setFocus()

    def explorer_go(self, path, select=None):
        path = os.path.abspath(os.path.expanduser(str(path).strip()))
        if not os.path.isdir(path):
            self.log(f"Folder tidak ditemukan: {path}", "err")
            return
        self.ex_path, self._ex_select, self._ex_pending = path, select, True
        self.tree.setRootIndex(self.fs.setRootPath(path))
        self.addr.setText(path)
        self.tree.setFocus()
        self._ex_loaded(path)

    def _ex_loaded(self, loaded):
        """Pilih baris pertama (atau folder asal saat naik) setelah isi folder selesai dimuat."""
        if not self._ex_pending or os.path.abspath(loaded) != self.ex_path:
            return
        idx = QModelIndex()
        for name in (self._ex_select, self._first_entry(self.ex_path)):
            if name:
                idx = self.fs.index(os.path.join(self.ex_path, name))
                if idx.isValid():
                    break
        if idx.isValid():
            self._ex_pending = False
            self.tree.setCurrentIndex(idx)
            self.tree.scrollTo(idx)

    @staticmethod
    def _first_entry(path):
        """Entri pertama menurut urutan tampilan (folder dulu, tanpa file tersembunyi)."""
        try:
            entries = [e for e in os.scandir(path) if not e.name.startswith(".")]
        except OSError:
            return None
        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
        return entries[0].name if entries else None

    def _ex_activated(self, idx):
        path = self.fs.filePath(idx)
        if self.fs.isDir(idx):
            self.explorer_go(path)
        else:
            self.launch(["xdg-open", path], f"Membuka {os.path.basename(path)}")

    def explorer_up(self):
        parent = os.path.dirname(self.ex_path)
        if self.ex_path and parent != self.ex_path:
            self.explorer_go(parent, select=os.path.basename(self.ex_path))

    def _ex_pick_item(self, item):
        self.explorer_go(item.data(Qt.ItemDataRole.UserRole))

    def _refresh_folders(self, keep_row=-1):
        self.ex_list.clear()
        for p in self.folders:
            item = QListWidgetItem("Home" if p == HOME else (os.path.basename(p) or p))
            item.setData(Qt.ItemDataRole.UserRole, p)
            item.setToolTip(p)
            self.ex_list.addItem(item)
        if keep_row >= 0 and self.ex_list.count():
            self.ex_list.setCurrentRow(min(keep_row, self.ex_list.count() - 1))

    def add_folder(self, path):
        path = os.path.normpath(os.path.expanduser(path))
        if not os.path.isdir(path):
            self.log(f"Folder tidak ditemukan: {path}", "err")
        elif path in self.folders:
            self.log(f"Sudah ada di pintasan: {path}")
        else:
            self.folders.append(path)
            save_list(FOLDERS_FILE, self.folders)
            self._refresh_folders(len(self.folders) - 1)
            self.log(f"Pintasan ditambahkan: {path}", "ok")

    def explorer_pin(self):
        if self.ex_path:
            self.add_folder(self.ex_path)

    def explorer_add_dialog(self):
        d = QFileDialog.getExistingDirectory(self, "Pilih folder pintasan", self.ex_path or HOME)
        if d:
            self.add_folder(d)

    def explorer_unpin(self):
        row = self.ex_list.currentRow()
        if row >= 0:
            path = self.folders.pop(row)
            save_list(FOLDERS_FILE, self.folders)
            self._refresh_folders(row)
            self.log(f"Pintasan dihapus: {path}")

    def explorer_shell_here(self):
        if self.ex_path:
            self.sh_cwd = self.ex_path
        self.show_shell()

    # ---- Shell ----
    def show_shell(self):
        self._sh_labels()
        self.show_page(PAGE_SHELL, "Shell")
        self.sh_input.setFocus()

    def set_sh_mode(self, on):
        """Layar shell (output) atau layar shortcut (daftar); input di bawah sama."""
        self.sh_mode = on
        self.sh_stack.setCurrentIndex(1 if on else 0)
        self.sh_prompt.setText("≡" if on else "❯")
        self.sh_input.use_history = not on
        self.sh_input.setPlaceholderText(
            "Ketik nomor atau nama, lalu Enter. Tab kembali ke shell" if on
            else "Ketik perintah, lalu Enter. Tab untuk daftar shortcut")
        self.btn_mode.set_kind("active" if on else "ghost")
        self.sh_input.clear()
        if on:
            self.sc_render()
        self.sh_input.setFocus()

    def _sh_labels(self):
        self.sh_cwd_label.setText(short(self.sh_cwd))
        self.sh_status.setText("Berjalan, Ctrl+C untuk berhenti" if self.sh_proc is not None else "")

    def sh_write(self, text, color=None):
        if not text:
            return
        cur = self.sh_out.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color or P["TEXT"]))
        cur.insertText(text, fmt)
        self.sh_out.setTextCursor(cur)
        self.sh_out.ensureCursorVisible()
        self._sh_bol = text.endswith("\n")

    def _sh_submit(self):
        text = self.sh_input.text().strip()
        self.sh_input.clear()
        self.sc_exec(text) if self.sh_mode else self.run_shell(text)

    def run_shell(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return
        if cmd in ("clear", "cls"):
            self.sh_out.clear()
            return
        if self.sh_proc is not None:
            self.log("Masih ada perintah berjalan. Tekan Ctrl+C untuk menghentikannya.", "err")
            return
        if cmd in self.sh_history:
            self.sh_history.remove(cmd)
        self.sh_history.append(cmd)
        self.sh_input.pos = len(self.sh_history)

        if not self._sh_bol:
            self.sh_write("\n")
        self.sh_write(f"{short(self.sh_cwd)} ❯ ", P["MUTED"])
        self.sh_write(cmd + "\n", P["ACCENT"])

        env = QProcessEnvironment.systemEnvironment()
        env.insert("TERM", "dumb")
        env.insert("NIXAMP_CWD", self.sh_cwd_file)
        # perintah dijalankan apa adanya; direktori akhir disimpan agar `cd` tetap berlaku
        script = f'{cmd}\n__rc=$?; pwd > "$NIXAMP_CWD"; exit $__rc'
        prog, args = (SETSID, ["-w", SHELL_BIN, "-c", script]) if SETSID else (SHELL_BIN, ["-c", script])

        p = QProcess(self)
        p.setProcessEnvironment(env)
        p.setWorkingDirectory(self.sh_cwd)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        dec = codecs.getincrementaldecoder("utf-8")("replace")
        p.readyRead.connect(lambda p=p, d=dec: self._sh_read(p, d))
        p.finished.connect(lambda code, _st, p=p, d=dec: self._sh_done(p, d, code))
        p.errorOccurred.connect(lambda err, p=p: self._sh_start_failed(p, err))
        self.sh_proc, self.sh_stopping = p, False
        self._sh_labels()
        p.start(prog, args)
        p.closeWriteChannel()  # program yang membaca stdin langsung dapat EOF

    @staticmethod
    def _clean(text):
        return ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")

    def _sh_read(self, p, dec):
        self.sh_write(self._clean(dec.decode(bytes(p.readAll()))))

    def _sh_start_failed(self, p, err):
        if err != QProcess.ProcessError.FailedToStart:
            return
        self.sh_write(f"Tidak bisa menjalankan shell ({SHELL_BIN}).\n", P["DANGER"])
        self.sh_proc = None
        p.deleteLater()
        self._sh_labels()

    def _sh_done(self, p, dec, code):
        self.sh_write(self._clean(dec.decode(bytes(p.readAll()), final=True)))
        self.sh_proc = None
        p.deleteLater()
        try:
            new = Path(self.sh_cwd_file).read_text().strip()
            if new and os.path.isdir(new):
                self.sh_cwd = new
            Path(self.sh_cwd_file).write_text("")
        except OSError:
            pass
        if not self._sh_bol:
            self.sh_write("\n")
        if self.sh_stopping:
            self.sh_write("[dihentikan]\n", P["WARN"])
        elif code != 0:
            self.sh_write(f"[kode keluar {code}]\n", P["DANGER"])
        self._sh_labels()

    def _kill_group(self, sig):
        p = self.sh_proc
        if p is None:
            return
        pid = int(p.processId())
        try:
            if SETSID and pid > 1:
                os.killpg(pid, sig)
            else:
                p.terminate() if sig == signal.SIGTERM else p.kill()
        except OSError:
            p.kill()

    def stop_cmd(self):
        p = self.sh_proc
        if p is None:
            return
        self.sh_stopping = True
        self._kill_group(signal.SIGTERM)
        QTimer.singleShot(1500, lambda: self.sh_proc is p and self._kill_group(signal.SIGKILL))

    def open_konsole(self):
        self.launch(["konsole", "--workdir", self.sh_cwd], f"Membuka Konsole di {short(self.sh_cwd)}")

    # ---- Shortcut mode ----
    def _sh_text_changed(self, text):
        if self.sh_mode:
            self.sc_render(text)

    def _sc_find(self, q):
        """Cari shortcut berdasarkan nomor, atau nama (persis, awalan, lalu sebagian)."""
        q = q.strip().lower()
        if q.isdigit():
            return [int(q) - 1] if 1 <= int(q) <= len(self.commands) else []
        names = [(c.get("label") or "").lower() for c in self.commands]
        for hit in ([i for i, n in enumerate(names) if n == q],
                    [i for i, n in enumerate(names) if n.startswith(q)],
                    [i for i, n in enumerate(names) if q in n]):
            if hit:
                return hit
        return []

    def sc_render(self, query="", msg="", level="info"):
        """Gambar daftar shortcut sebagai tabel (kolom tetap rapi di font apa pun)."""
        q = query.strip()
        managing = bool(MANAGE_RE.match(q))
        hits = self._sc_find(q) if q and not managing else []
        esc, muted = html.escape, P["MUTED"]
        rows = []
        for i, c in enumerate(self.commands):
            if q and not managing and i not in hits:
                continue
            # baris yang akan dijalankan oleh Enter diberi latar
            bg = f' style="background-color:{P["LINE"]}"' if q and not managing and len(hits) == 1 else ""
            rows.append(
                f'<tr><td{bg} align="right"><span style="color:{P["ACCENT"]}; font-weight:700">{i + 1}</span></td>'
                f'<td{bg}>&nbsp;&nbsp;{esc(c.get("label") or "-")}&nbsp;&nbsp;&nbsp;&nbsp;</td>'
                f'<td{bg}><span style="color:{muted}">{esc(c["cmd"])}</span></td></tr>')
        note = ""
        if not self.commands:
            note = "Belum ada shortcut. Contoh: add disk df -h"
        elif q and not managing and not hits:
            note = "Tidak ada yang cocok."
        table = f'<table cellspacing="0" cellpadding="3" style="margin-left:6px">{"".join(rows)}</table>' if rows else ""
        help_rows = (f'<tr><td><span style="color:{muted}">add nama perintah</span></td>'
                     f'<td><span style="color:{muted}">&nbsp;&nbsp;tambah shortcut</span></td></tr>'
                     f'<tr><td><span style="color:{muted}">rm nomor</span></td>'
                     f'<td><span style="color:{muted}">&nbsp;&nbsp;hapus shortcut</span></td></tr>')
        out = table
        if note:
            out += f'<p style="color:{muted}; margin-left:9px">{esc(note)}</p>'
        out += (f'<p style="color:{muted}; margin-left:9px; margin-top:14px">Ketik nomor atau nama, lalu Enter.</p>'
                f'<table cellspacing="0" cellpadding="1" style="margin-left:6px">{help_rows}</table>')
        if msg:
            color = {"ok": P["OK"], "err": P["DANGER"]}.get(level, P["TEXT"])
            out += f'<p style="color:{color}; margin-left:9px; margin-top:12px">{esc(msg)}</p>'
        self.sc_view.setHtml(out)

    def sc_exec(self, text):
        if not text:
            return
        m = ADD_RE.match(text)
        if m:
            name, cmd = m.group(1) or m.group(2) or m.group(3), m.group(4).strip()
            if name.isdigit():
                return self.sc_render(msg="Nama tidak boleh berupa angka.", level="err")
            if any((c.get("label") or "").lower() == name.lower() for c in self.commands):
                return self.sc_render(msg=f"Nama '{name}' sudah dipakai.", level="err")
            self.commands.append({"label": name, "cmd": cmd})
            save_list(COMMANDS_FILE, self.commands)
            self.log(f"Shortcut ditambahkan: {name}", "ok")
            return self.sc_render(msg=f"Ditambahkan sebagai nomor {len(self.commands)}.", level="ok")
        if re.match(r"^add(\s|$)", text, re.I):
            return self.sc_render(msg="Format: add nama perintah", level="err")
        m = RM_RE.match(text)
        if m:
            hits = self._sc_find(m.group(1))
            if len(hits) != 1:
                return self.sc_render(
                    msg="Tidak ditemukan." if not hits else "Lebih dari satu yang cocok, pakai nomor.", level="err")
            c = self.commands.pop(hits[0])
            save_list(COMMANDS_FILE, self.commands)
            self.log(f"Shortcut dihapus: {c.get('label') or c['cmd']}")
            return self.sc_render(msg="Dihapus.", level="ok")
        hits = self._sc_find(text)
        if len(hits) != 1:
            if not hits:
                return self.sc_render(msg=f"Tidak ada shortcut '{text}'.", level="err")
            names = ", ".join(f"{i + 1} {self.commands[i].get('label') or '-'}" for i in hits)
            return self.sc_render(msg=f"Ambigu: {names}. Ketik lebih lengkap atau pakai nomor.", level="err")
        if self.sh_proc is not None:
            return self.sc_render(msg="Masih ada perintah berjalan. Ctrl+C untuk menghentikan.", level="err")
        cmd = self.commands[hits[0]]["cmd"]
        self.set_sh_mode(False)  # kembali ke layar shell agar output terlihat
        self.run_shell(cmd)

    def closeEvent(self, ev):
        self._closing = True
        if self.helper is not None:  # stdin ditutup -> helper admin berhenti sendiri
            self.helper.closeWriteChannel()
            self.helper.waitForFinished(800)
        self._kill_group(signal.SIGKILL)
        try:
            os.remove(self.sh_cwd_file)
        except OSError:
            pass
        super().closeEvent(ev)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont()
    font.setFamilies(["Inter", "Noto Sans", "Cantarell", "DejaVu Sans"])
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet(QSS)
    window = NixAMP()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
