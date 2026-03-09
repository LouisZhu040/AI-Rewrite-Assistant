"""
AI 改写助手 v5.1
========================================
依赖安装:
    pip install PyQt6 keyboard pyperclip requests pystray pillow pywin32

运行（需管理员权限）:
    python ai_rewrite.py
"""

import sys, json, time, ctypes, ctypes.wintypes, threading, winreg, os
import keyboard, pyperclip, requests
from PIL import Image, ImageDraw
import pystray

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QTextEdit, QSizePolicy,
    QGraphicsDropShadowEffect, QComboBox, QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, pyqtSignal, QObject, QThread,
    QRect, QByteArray, QParallelAnimationGroup
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontDatabase,
    QPainterPath, QBrush, QPen, QLinearGradient,
    QFontMetrics
)

os.environ["QT_LOGGING_RULES"] = "*.warning=false"

# ──────────────────────────────────────────
#  配置
# ──────────────────────────────────────────
OLLAMA_BASE = "http://localhost:11434"
HOTKEY      = "ctrl+shift+space"
MAX_TOKENS  = 256
TEMPERATURE = 0.7
STRICT_SUFFIX = "\nOnly output the rewritten text. Do not reply, explain, or add tags."

REWRITE_MODES = {
    "✨ 润色": {
        "zh": "你是专业写作助手。润色以下文本使其更流畅自然，保持原意。只输出结果，不要解释。",
        "en": "Polish the text to be more fluent and natural. Preserve meaning. Output only the result.",
    },
    "💼 正式": {
        "zh": "你是商务写作助手。将以下文本改为正式商务风格。只输出结果，不要解释。",
        "en": "Rewrite in formal business style. Output only the result.",
    },
    "✂️ 简洁": {
        "zh": "你是写作助手。压缩以下文本，去除冗余，保留核心。只输出结果，不要解释。",
        "en": "Compress the text, remove redundancy, keep core message. Output only the result.",
    },
    "😊 亲切": {
        "zh": "你是写作助手。将以下文本改为友好亲切的语气。只输出结果，不要解释。",
        "en": "Rewrite in a warm, friendly tone. Output only the result.",
    },
    "🔧 纠错": {
        "zh": "你是校对助手。修正以下文本的语法和表达错误，保持原意。只输出结果，不要解释。",
        "en": "Fix grammar and phrasing errors. Preserve meaning. Output only the result.",
    },
    "📧 收尾": {
        "zh": "你是邮件助手。为以下邮件补充一句礼貌收尾语。只输出收尾句，不要解释。",
        "en": "Write a polite closing sentence for this email. Output only the closing.",
    },
    "🌐 →英文": {
        "zh": "翻译为地道英文。只输出结果，不要解释。",
        "en": "Translate to natural English. Output only the result.",
        "force_lang": "en",
    },
    "🀄 →中文": {
        "zh": "翻译为流畅简体中文。只输出结果，不要解释。",
        "en": "Translate to fluent Simplified Chinese. Output only the result.",
        "force_lang": "zh",
    },
    "📝 扩写": {
        "zh": "你是专业写作助手。将以下文本扩写得更加丰富详细，补充细节、背景或论据，使内容更充实，保持原意和语气。只输出扩写结果，不要解释。",
        "en": "You are a professional writing assistant. Expand the following text with more detail, context, and supporting points while preserving the original meaning and tone. Output only the expanded text, no explanation.",
    },
}

# ──────────────────────────────────────────
#  字体：优先 Inter，fallback Segoe UI Variable
# ──────────────────────────────────────────
def load_font() -> str:
    for name in ["Inter", "Segoe UI Variable", "Segoe UI"]:
        if name in QFontDatabase.families():
            return name
    return "Arial"

# ──────────────────────────────────────────
#  工具
# ──────────────────────────────────────────
def is_dark_mode() -> bool:
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        return v == 0
    except:
        return False

def detect_lang(text: str) -> str:
    zh = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return "zh" if zh / max(len(text), 1) > 0.15 else "en"

def get_cursor_pos():
    pt = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

_model = ""
def get_model() -> str:
    global _model
    if _model: return _model
    try:
        r = requests.get(f"{OLLAMA_BASE}/v1/models", timeout=5)
        data = r.json().get("data", [])
        if data: _model = data[0]["id"]
    except: pass
    if not _model: _model = "local-model"
    print(f"[模型] {_model}")
    return _model

def fetch_models() -> list:
    try:
        r = requests.get(f"{OLLAMA_BASE}/v1/models", timeout=5)
        return [m["id"] for m in r.json().get("data", [])]
    except: return [get_model()]

def set_model(n: str):
    global _model; _model = n

# ──────────────────────────────────────────
#  配色：极简磨砂质感
# ──────────────────────────────────────────
def make_colors(dark: bool) -> dict:
    if dark:
        return {
            "win_bg":      QColor(22, 22, 26, 215),
            "border":      QColor(255, 255, 255, 18),
            "pill_bg":     QColor(255, 255, 255, 10),
            "pill_hover":  QColor(255, 255, 255, 20),
            "pill_active": QColor(99, 102, 241),        # indigo
            "accent":      QColor(99, 102, 241),
            "accent2":     QColor(139, 92, 246),        # violet
            "text":        QColor(250, 250, 252),
            "text2":       QColor(160, 160, 175),
            "divider":     QColor(255, 255, 255, 12),
            "panel_orig":  QColor(255, 255, 255, 6),
            "panel_res":   QColor(99, 102, 241, 18),
            "orig_fg":     QColor(210, 210, 225),
            "res_fg":      QColor(230, 230, 255),
            "btn_cancel":  QColor(255, 255, 255, 12),
            "btn_confirm": QColor(99, 102, 241),
            "shadow":      QColor(0, 0, 0, 140),
            "acrylic":     0xD8161618,
            "green":       QColor(52, 211, 153),
            "red":         QColor(248, 113, 113),
        }
    else:
        return {
            "win_bg":      QColor(252, 252, 255, 218),
            "border":      QColor(0, 0, 0, 14),
            "pill_bg":     QColor(0, 0, 0, 7),
            "pill_hover":  QColor(99, 102, 241, 18),
            "pill_active": QColor(99, 102, 241),
            "accent":      QColor(79, 70, 229),
            "accent2":     QColor(124, 58, 237),
            "text":        QColor(15, 15, 20),
            "text2":       QColor(100, 100, 120),
            "divider":     QColor(0, 0, 0, 10),
            "panel_orig":  QColor(0, 0, 0, 5),
            "panel_res":   QColor(99, 102, 241, 12),
            "orig_fg":     QColor(40, 40, 60),
            "res_fg":      QColor(55, 48, 163),
            "btn_cancel":  QColor(0, 0, 0, 8),
            "btn_confirm": QColor(79, 70, 229),
            "shadow":      QColor(0, 0, 0, 55),
            "acrylic":     0xDEFCFCFF,
            "green":       QColor(16, 185, 129),
            "red":         QColor(239, 68, 68),
        }

# ──────────────────────────────────────────
#  Acrylic 毛玻璃 + 圆角
# ──────────────────────────────────────────
def apply_acrylic(hwnd: int, color: int):
    try:
        class ACCENT(ctypes.Structure):
            _fields_ = [("State",ctypes.c_int),("Flags",ctypes.c_int),
                        ("Color",ctypes.c_int),("AnimId",ctypes.c_int)]
        class WINATTR(ctypes.Structure):
            _fields_ = [("Attr",ctypes.c_int),("pData",ctypes.c_void_p),
                        ("Size",ctypes.c_ulong)]
        a = ACCENT(); a.State = 4; a.Color = color
        d = WINATTR(); d.Attr = 19
        d.pData = ctypes.cast(ctypes.byref(a), ctypes.c_void_p)
        d.Size  = ctypes.sizeof(a)
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(d))
    except: pass
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)
    except: pass

# ──────────────────────────────────────────
#  流式 Worker
# ──────────────────────────────────────────
class Sig(QObject):
    chunk = pyqtSignal(str)
    done  = pyqtSignal()
    error = pyqtSignal(str)

class StreamWorker(QThread):
    def __init__(self, prompt, text, stop):
        super().__init__()
        self.prompt = prompt; self.text = text; self.stop = stop
        self.sig = Sig()

    def run(self):
        payload = {
            "model": get_model(),
            "messages": [
                {"role":"system","content": self.prompt + STRICT_SUFFIX},
                {"role":"user",  "content": f"Rewrite this text:\n{self.text}"},
            ],
            "max_tokens": 512 if "扩写" in self.prompt else MAX_TOKENS,
            "temperature": TEMPERATURE, "stream": True,
        }
        try:
            with requests.post(f"{OLLAMA_BASE}/v1/chat/completions",
                               json=payload, stream=True, timeout=60) as r:
                r.raise_for_status()
                for raw in r.iter_lines():
                    if self.stop.is_set(): r.close(); return
                    if not raw: continue
                    line = raw.decode()
                    if not line.startswith("data: "): continue
                    s = line[6:]
                    if s.strip() == "[DONE]": break
                    try:
                        d = json.loads(s)["choices"][0]["delta"].get("content","")
                        if d: self.sig.chunk.emit(d)
                    except: continue
            if not self.stop.is_set(): self.sig.done.emit()
        except Exception as e:
            if not self.stop.is_set(): self.sig.error.emit(str(e))

# ──────────────────────────────────────────
#  圆角磨砂基窗口
# ──────────────────────────────────────────
class GlassBase(QWidget):
    R = 16
    def __init__(self, C):
        super().__init__()
        self.C = C
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(40)
        sh.setOffset(0, 12)
        sh.setColor(C["shadow"])
        self.setGraphicsEffect(sh)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width()-2, self.height()-2, self.R, self.R)
        p.fillPath(path, self.C["win_bg"])
        p.setPen(QPen(self.C["border"], 1))
        p.drawPath(path)

# ──────────────────────────────────────────
#  滑入 / 滑出动画
# ──────────────────────────────────────────
SLIDE_DIST = 14   # px

def animate_in(widget: QWidget):
    """从下方 SLIDE_DIST px 处滑入 + 淡入"""
    geo = widget.geometry()
    start_pos = QPoint(geo.x(), geo.y() + SLIDE_DIST)
    end_pos   = QPoint(geo.x(), geo.y())

    widget.setWindowOpacity(0)
    widget.show()

    pos_anim = QPropertyAnimation(widget, b"pos", widget)
    pos_anim.setDuration(260)
    pos_anim.setStartValue(start_pos)
    pos_anim.setEndValue(end_pos)
    pos_anim.setEasingCurve(QEasingCurve.Type.OutExpo)

    op_anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    op_anim.setDuration(220)
    op_anim.setStartValue(0.0)
    op_anim.setEndValue(1.0)
    op_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    grp = QParallelAnimationGroup(widget)
    grp.addAnimation(pos_anim)
    grp.addAnimation(op_anim)
    grp.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._anim_in = grp

def animate_out(widget: QWidget, callback=None):
    """滑出 + 淡出"""
    geo = widget.geometry()
    end_pos = QPoint(geo.x(), geo.y() + SLIDE_DIST)

    pos_anim = QPropertyAnimation(widget, b"pos", widget)
    pos_anim.setDuration(180)
    pos_anim.setStartValue(QPoint(geo.x(), geo.y()))
    pos_anim.setEndValue(end_pos)
    pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)

    op_anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    op_anim.setDuration(160)
    op_anim.setStartValue(widget.windowOpacity())
    op_anim.setEndValue(0.0)
    op_anim.setEasingCurve(QEasingCurve.Type.InCubic)

    grp = QParallelAnimationGroup(widget)
    grp.addAnimation(pos_anim)
    grp.addAnimation(op_anim)
    def _fin():
        widget.close()
        if callback: callback()
    grp.finished.connect(_fin)
    grp.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._anim_out = grp

# ──────────────────────────────────────────
#  Pill 模式按钮
# ──────────────────────────────────────────
class PillBtn(QPushButton):
    def __init__(self, text, C, font_family, parent=None):
        super().__init__(text, parent)
        self.C = C; self._h = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        f = QFont(font_family, 8)
        f.setWeight(QFont.Weight.Medium)
        self.setFont(f)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # 按下动画
        self._scale = 1.0

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = self.C["pill_hover"] if self._h else self.C["pill_bg"]
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        p.fillPath(path, bg)
        p.setPen(self.C["text"] if not self._h else self.C["accent"])
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

    def enterEvent(self, e): self._h = True;  self.update()
    def leaveEvent(self, e): self._h = False; self.update()

# ──────────────────────────────────────────
#  主悬浮窗
# ──────────────────────────────────────────
class FloatingBar(GlassBase):
    W  = 540
    H1 = 52
    H2 = 320

    def __init__(self, selected, cx, cy, dark, font_family):
        C = make_colors(dark)
        super().__init__(C)
        self.dark     = dark
        self.selected = selected.strip()
        self.lang     = detect_lang(self.selected)
        self.result   = ""
        self._stop    = threading.Event()
        self._worker  = None
        self.FF       = font_family
        self._closing = False

        self._calc_pos(cx, cy, self.H1)
        self._build_bar()
        animate_in(self)
        QTimer.singleShot(80, self._apply_fx)

    def _apply_fx(self):
        hwnd = int(self.winId())
        apply_acrylic(hwnd, self.C["acrylic"])

    def _calc_pos(self, cx, cy, h):
        sc = QApplication.primaryScreen().availableGeometry()
        x  = max(sc.x()+16, min(cx - self.W//2, sc.right() - self.W - 16))
        y  = cy + 20
        if y + h > sc.bottom() - 16: y = cy - h - 20
        y  = max(sc.y()+16, y)
        self.setGeometry(x, y, self.W, h)
        self._base_cx = cx; self._base_cy = cy

    # ── helpers ──
    def _font(self, size=9, weight=QFont.Weight.Normal):
        f = QFont(self.FF, size); f.setWeight(weight); return f

    def _lbl(self, text, size=9, weight=QFont.Weight.Normal, color=None):
        l = QLabel(text)
        l.setFont(self._font(size, weight))
        c = color or self.C["text"]
        l.setStyleSheet(f"color:rgba({c.red()},{c.green()},{c.blue()},{c.alpha()});background:transparent;")
        return l

    def _hdiv(self):
        f = QFrame(); f.setFixedHeight(1)
        c = self.C["divider"]
        f.setStyleSheet(f"background:rgba({c.red()},{c.green()},{c.blue()},{c.alpha()});border:none;")
        return f

    def _vdiv(self):
        f = QFrame(); f.setFixedWidth(1)
        c = self.C["divider"]
        f.setStyleSheet(f"background:rgba({c.red()},{c.green()},{c.blue()},{c.alpha()});border:none;")
        return f

    def _clear_layout(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            QWidget().setLayout(old)

    # ─── 阶段1：按钮条 ───
    def _build_bar(self):
        self._clear_layout()
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(4)

        # 模型下拉
        combo = QComboBox()
        combo.addItems(fetch_models())
        combo.setCurrentText(get_model())
        combo.setFont(self._font(7))
        combo.setFixedHeight(28)
        c = self.C
        combo.setStyleSheet(f"""
            QComboBox {{
                background: rgba({c['pill_bg'].red()},{c['pill_bg'].green()},{c['pill_bg'].blue()},60);
                color: rgba({c['text2'].red()},{c['text2'].green()},{c['text2'].blue()},255);
                border: 1px solid rgba({c['border'].red()},{c['border'].green()},{c['border'].blue()},255);
                border-radius: 7px; padding: 0 8px; min-width: 80px;
            }}
            QComboBox::drop-down {{ border:none; width:18px; }}
            QComboBox QAbstractItemView {{
                background: rgba({c['win_bg'].red()},{c['win_bg'].green()},{c['win_bg'].blue()},240);
                color: rgba({c['text'].red()},{c['text'].green()},{c['text'].blue()},255);
                border: 1px solid rgba({c['border'].red()},{c['border'].green()},{c['border'].blue()},80);
                border-radius: 8px; padding: 4px;
                selection-background-color: rgba({c['accent'].red()},{c['accent'].green()},{c['accent'].blue()},160);
            }}
        """)
        combo.currentTextChanged.connect(set_model)
        row.addWidget(combo)
        row.addWidget(self._vdiv())

        for mode in REWRITE_MODES:
            btn = PillBtn(mode, self.C, self.FF)
            btn.clicked.connect(lambda _, m=mode: self._trigger(m))
            row.addWidget(btn)

        self.setLayout(row)

    # ─── 阶段2：对比视图 ───
    def _trigger(self, mode):
        self._stop.set()
        self._stop = threading.Event()
        self.result = ""

        cfg        = REWRITE_MODES[mode]
        lang       = cfg.get("force_lang", self.lang)
        sys_prompt = cfg[lang]

        # 展开动画
        self._expand_animated(self.H2, lambda: self._build_compare(mode, sys_prompt))

    def _expand_animated(self, target_h, callback):
        sc       = QApplication.primaryScreen().availableGeometry()
        start_h  = self.height()
        steps, i = 14, [0]
        ease     = QEasingCurve(QEasingCurve.Type.OutExpo)

        def _step():
            i[0] += 1
            t  = i[0] / steps
            et = ease.valueForProgress(t)
            nh = int(start_h + (target_h - start_h) * et)
            g  = self.geometry()
            nx = max(sc.x()+16, min(g.x(), sc.right()-self.W-16))
            ny = g.y()
            if ny + nh > sc.bottom() - 16: ny = sc.bottom() - nh - 16
            ny = max(sc.y()+16, ny)
            self.setGeometry(nx, ny, self.W, nh)
            if i[0] < steps:
                QTimer.singleShot(10, _step)
            else:
                callback()

        QTimer.singleShot(10, _step)

    def _build_compare(self, mode, sys_prompt):
        self._clear_layout()
        C = self.C

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # ── 顶部：模式标题 + 状态 ──
        top = QHBoxLayout(); top.setSpacing(8)
        # 模式徽章
        badge = QLabel(mode)
        badge.setFont(self._font(9, QFont.Weight.DemiBold))
        ac = C["accent"]
        badge.setStyleSheet(f"""
            color: rgba({ac.red()},{ac.green()},{ac.blue()},255);
            background: rgba({ac.red()},{ac.green()},{ac.blue()},18);
            border-radius: 6px; padding: 2px 8px;
        """)
        top.addWidget(badge)
        top.addStretch()
        self._status = self._lbl("生成中…", 8, color=C["text2"])
        top.addWidget(self._status)
        root.addLayout(top)
        root.addWidget(self._hdiv())

        # ── 双栏 ──
        cols = QHBoxLayout(); cols.setSpacing(10)

        def panel(title, bg: QColor, fg: QColor):
            box = QVBoxLayout(); box.setSpacing(5)
            box.addWidget(self._lbl(title, 7, QFont.Weight.Medium, C["text2"]))
            te = QTextEdit()
            te.setFont(self._font(10))
            te.setReadOnly(True)
            te.setFrameShape(QFrame.Shape.NoFrame)
            te.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            te.setStyleSheet(f"""
                QTextEdit {{
                    background: rgba({bg.red()},{bg.green()},{bg.blue()},{bg.alpha()});
                    color: rgba({fg.red()},{fg.green()},{fg.blue()},255);
                    border-radius: 10px; padding: 10px;
                    border: 1px solid rgba({C['border'].red()},{C['border'].green()},{C['border'].blue()},255);
                    line-height: 1.5;
                }}
                QScrollBar {{ width:0; height:0; }}
            """)
            box.addWidget(te)
            return box, te

        orig_col, orig_te = panel("原文", C["panel_orig"], C["orig_fg"])
        orig_te.setText(self.selected)

        res_col, self._res_te = panel("改写结果", C["panel_res"], C["res_fg"])

        cols.addLayout(orig_col)
        cols.addWidget(self._vdiv())
        cols.addLayout(res_col)
        root.addLayout(cols)
        root.addWidget(self._hdiv())

        # ── 底部操作 ──
        bot = QHBoxLayout(); bot.setSpacing(8)
        hint = self._lbl("↵ 替换   Esc 取消", 8, color=C["text2"])
        bot.addWidget(hint)
        bot.addStretch()

        # 取消按钮
        cb = C["btn_cancel"]
        cancel = QPushButton("取消")
        cancel.setFont(self._font(9))
        cancel.setFixedSize(70, 32)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: rgba({cb.red()},{cb.green()},{cb.blue()},{cb.alpha()});
                color: rgba({C['text'].red()},{C['text'].green()},{C['text'].blue()},200);
                border-radius: 9px; border: 1px solid rgba({C['border'].red()},{C['border'].green()},{C['border'].blue()},255);
            }}
            QPushButton:hover {{
                background: rgba({cb.red()},{cb.green()},{cb.blue()},{min(cb.alpha()+20,255)});
            }}
        """)
        cancel.clicked.connect(self._cancel)

        # 确认按钮（渐变）
        ac = C["btn_confirm"]; ac2 = C["accent2"]
        confirm = QPushButton("替换")
        confirm.setFont(self._font(9, QFont.Weight.DemiBold))
        confirm.setFixedSize(70, 32)
        confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba({ac.red()},{ac.green()},{ac.blue()},255),
                    stop:1 rgba({ac2.red()},{ac2.green()},{ac2.blue()},255));
                color: white; border-radius: 9px; border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        confirm.clicked.connect(self._confirm)

        bot.addWidget(cancel)
        bot.addWidget(confirm)
        root.addLayout(bot)
        self.setLayout(root)

        # 启动流式
        self._worker = StreamWorker(sys_prompt, self.selected, self._stop)
        self._worker.sig.chunk.connect(self._on_chunk)
        self._worker.sig.done.connect(self._on_done)
        self._worker.sig.error.connect(self._on_error)
        self._worker.start()

    def _on_chunk(self, text):
        self.result += text
        cur = self._res_te.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        self._res_te.setTextCursor(cur)
        self._res_te.insertPlainText(text)

    def _on_done(self):
        g = self.C["green"]
        self._status.setText("✓ 完成")
        self._status.setStyleSheet(
            f"color:rgba({g.red()},{g.green()},{g.blue()},255);background:transparent;")

    def _on_error(self, msg):
        r = self.C["red"]
        self._status.setText(f"⚠ {msg}")
        self._status.setStyleSheet(
            f"color:rgba({r.red()},{r.green()},{r.blue()},255);background:transparent;")

    def _confirm(self):
        if not self.result or self._closing: return
        self._closing = True
        self._stop.set()
        txt = self.result
        animate_out(self, lambda: self._paste(txt))

    def _cancel(self):
        if self._closing: return
        self._closing = True
        self._stop.set()
        animate_out(self)

    def _paste(self, txt):
        pyperclip.copy(txt)
        time.sleep(0.12)
        keyboard.send("ctrl+v")

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Return:   self._confirm()
        elif e.key() == Qt.Key.Key_Escape: self._cancel()

    def focusOutEvent(self, e):
        QTimer.singleShot(200, self._check_focus)

    def _check_focus(self):
        if not self._closing and not self.isActiveWindow():
            self._cancel()

# ──────────────────────────────────────────
#  单例
# ──────────────────────────────────────────
_cur = None; _lock = threading.Lock()

def close_current():
    global _cur
    with _lock:
        if _cur:
            try: _cur._stop.set(); _cur.close()
            except: pass
            _cur = None

def show_window(sel, cx, cy):
    global _cur
    close_current()
    dark = is_dark_mode()
    win  = FloatingBar(sel, cx, cy, dark, _FF)
    with _lock: _cur = win

# ──────────────────────────────────────────
#  热键桥
# ──────────────────────────────────────────
class Bridge(QObject):
    triggered = pyqtSignal(str, int, int)

bridge = Bridge()

def on_hotkey():
    close_current()
    cx, cy = get_cursor_pos()
    try:    old = pyperclip.paste()
    except: old = ""
    keyboard.send("ctrl+c")
    time.sleep(0.18)
    try:    sel = pyperclip.paste()
    except: sel = ""
    try:
        if old: pyperclip.copy(old)
    except: pass
    bridge.triggered.emit(sel if sel != old else "", cx, cy)

# ──────────────────────────────────────────
#  托盘
# ──────────────────────────────────────────
def _tray_icon():
    img  = Image.new("RGBA",(64,64),(0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4,4,60,60], fill="#6366F1")
    draw.text((20,14),"✦",fill="#FFFFFF")
    return img

def run_tray():
    def quit_(i,_): i.stop(); keyboard.unhook_all(); sys.exit(0)
    pystray.Icon("ai_rewrite",_tray_icon(),"AI 改写助手",
        menu=pystray.Menu(
            pystray.MenuItem("AI 改写助手 v5.1",lambda i,_:None,enabled=False),
            pystray.MenuItem(f"热键：{HOTKEY.upper()}",lambda i,_:None,enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出",quit_),
        )).run()

# ──────────────────────────────────────────
#  入口
# ──────────────────────────────────────────
_FF = "Arial"

def main():
    global _FF
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    _FF = load_font()

    bridge.triggered.connect(lambda t,x,y: show_window(t,x,y))
    threading.Thread(target=get_model, daemon=True).start()
    keyboard.add_hotkey(HOTKEY, on_hotkey, suppress=True)
    threading.Thread(target=run_tray, daemon=True).start()

    print(f"  ✦ AI 改写助手 v5.1  |  字体：{_FF}  |  {'深色' if is_dark_mode() else '亮色'}模式")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()