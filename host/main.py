
import os
import socket
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import torch
from PIL import Image, ImageDraw

from mnist_model import load_model

PL_HOST, PL_PORT = "127.0.0.1", 5000
PL_SCRIPT = "pl_node.py"
VERBOSE_LINK = False



class PLLink:
    def __init__(self, host=PL_HOST, port=PL_PORT, log=None, verbose=VERBOSE_LINK):
        self.sock = None
        self.verbose = verbose
        self.log = log or (lambda s: None)
        self.connect(host, port)

    def _vlog(self, msg):
        if self.verbose:
            self.log(msg)

    def connect(self, host=PL_HOST, port=PL_PORT):

        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            self.sock = s
            self._vlog(f"[LINK] 已连接 PL 节点 ({host}:{port})")
        except Exception as e:
            self.sock = None
            self._vlog(f"[LINK] 连接失败：{e}")

    @staticmethod
    def build_frame(cmd, data=b""):
        head = bytes([0xAA, 0x55, cmd, (len(data) >> 8) & 0xFF, len(data) & 0xFF])
        body = head + data
        chk = int(np.bitwise_xor.reduce(np.frombuffer(body, np.uint8)))
        return body + bytes([chk])

    @staticmethod
    def parse_frame(buf):
        while True:
            i = buf.find(b"\xAA\x55")
            if i < 0:
                buf.clear()
                return None
            if i:
                del buf[:i]
            if len(buf) < 5:
                return None
            ln = (buf[3] << 8) | buf[4]
            if ln > 4096:
                del buf[:2]
                continue
            if len(buf) < 6 + ln:
                return None
            frame = bytes(buf[:6 + ln])
            calc = int(np.bitwise_xor.reduce(np.frombuffer(frame[:-1], np.uint8)))
            if calc != frame[-1]:
                del buf[:2]
                continue
            del buf[:6 + ln]
            return frame[2], frame[5:5 + ln]

    def _wait(self, expect_cmd, timeout=2.0):
        if self.sock is None:
            return None
        buf = bytearray()
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                buf.extend(self.sock.recv(64))
            except socket.timeout:
                pass
            except Exception:
                break
            parsed = self.parse_frame(buf)
            if parsed and parsed[0] == expect_cmd:
                return parsed
        return None

    def handshake(self):
        if self.sock is None:
            return False
        try:
            self._vlog("[TX ] 握手请求 0x00")
            self.sock.sendall(self.build_frame(0x00))
        except Exception as e:
            self._vlog(f"[LINK] 发送失败：{e}")
            return False
        r = self._wait(0x80)
        if r:
            self._vlog(f"[RX ] PL 就绪 0x80 (ver={r[1][0]})")
            return True
        self._vlog("[RX ] 握手超时")
        return False

    def request(self, payload):
        if self.sock is None:
            return None
        try:
            self._vlog(f"[TX ] 推理请求 0x01 ({len(payload)} B)")
            self.sock.sendall(self.build_frame(0x01, payload))
        except Exception as e:
            self._vlog(f"[LINK] 发送失败：{e}")
            return None
        r = self._wait(0x81)
        if r:
            digit = int(r[1][0])
            self._vlog(f"[RX ] PL 推理结果 0x81 -> {digit}")
            return digit
        self._vlog("[RX ] 响应超时")
        return None


def start_pl_node(log):

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), PL_SCRIPT)
    if not os.path.exists(path):
        return None
    try:
        proc = subprocess.Popen([sys.executable, path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    except Exception:
        return None
    for _ in range(50):                      # 最多等 10 秒
        try:
            probe = socket.create_connection((PL_HOST, PL_PORT), timeout=0.5)
            probe.close()
            return proc
        except Exception:
            time.sleep(0.2)
    return proc


def preprocess(pil_img):
    img = pil_img.convert("L").resize((28, 28), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)

    ys, xs = np.nonzero(arr < 200)
    if len(xs) > 0:
        cx, cy = xs.mean(), ys.mean()
        sx, sy = int(round(13.5 - cx)), int(round(13.5 - cy))
        arr = np.roll(np.roll(arr, sy, axis=0), sx, axis=1)

    arr = 255.0 - arr
    arr = np.clip(arr, 0, 255) / 255.0
    return arr


def pil_to_payload(arr):

    return (arr * 255.0).astype(np.uint8).tobytes()



class App:
    CANVAS = 280
    PEN = 24

    def __init__(self, root, model):
        self.model = model
        self.strokes, self.cur = [], []

        root.title("Zynq MNIST 加速器 · 上位机")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=self.CANVAS, height=self.CANVAS,
                                bg="white", highlightthickness=1)
        self.canvas.grid(row=0, column=0, padx=10, pady=10)
        self.canvas.bind("<B1-Motion>", self.on_draw)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        right = ttk.Frame(root)
        right.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self.result = ttk.Label(right, text="等待识别…", font=("微软雅黑", 26, "bold"))
        self.result.grid(row=0, column=0, pady=6)

        for i, txt in enumerate(["识别", "清空", "重连", "保存截图"]):
            ttk.Button(right, text=txt,
                       command=[self.recognize, self.clear,
                                self.reconnect, self.save][i]).grid(
                row=1 + i, column=0, pady=4, sticky="ew")

        self.logbox = tk.Text(right, width=42, height=12, font=("Consolas", 9))
        self.logbox.grid(row=5, column=0, pady=6)

        self.pl_proc = start_pl_node(self.log)
        self.link = PLLink(log=self.log)
        self.link_ok = self.link.handshake()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- 绘图 ----------
    def on_draw(self, e):
        if self.cur:
            self.canvas.create_line(self.cur[-1][0], self.cur[-1][1], e.x, e.y,
                                    width=self.PEN, capstyle="round", smooth=True)
        self.cur.append((e.x, e.y))

    def on_release(self, _):
        if len(self.cur) > 1:
            self.strokes.append(self.cur)
        self.cur = []

    def clear(self):
        self.canvas.delete("all")
        self.strokes, self.cur = [], []
        self.result.config(text="等待识别…")

    def render(self):
        img = Image.new("L", (self.CANVAS, self.CANVAS), 255)
        d = ImageDraw.Draw(img)
        for pts in self.strokes:
            if len(pts) > 1:
                d.line(pts, fill=0, width=self.PEN, joint="curve")
        return img

    def save(self):
        if not self.strokes:
            messagebox.showinfo("提示", "画布为空")
            return
        self.render().save("snapshot.png")
        self.log("[SAVE] 已保存 snapshot.png")

    def reconnect(self):
        if self.pl_proc is None or self.pl_proc.poll() is not None:
            self.pl_proc = start_pl_node(self.log)
        self.link.connect()
        self.link_ok = self.link.handshake()
        self.log(f"[LINK] 重连结果：{'成功' if self.link_ok else '失败'}")

    def on_close(self):
        if self.pl_proc is not None and self.pl_proc.poll() is None:
            self.pl_proc.terminate()
        self.root.destroy()

    # ---------- 识别 ----------
    def recognize(self):
        if not self.strokes:
            messagebox.showinfo("提示", "请先写一个数字")
            return

        arr = preprocess(self.render())
        payload = pil_to_payload(arr)

        digit = self.link.request(payload) if self.link_ok else None
        if digit is None:                      # PL 不可用时本机兜底
            x = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
            with torch.no_grad():
                digit = int(self.model(x).argmax(1).item())

        self.result.config(text=f"识别结果：{digit}")
        self.log(f"[RESULT] digit={digit}")

    def log(self, msg):
        self.logbox.insert("end", f"{time.strftime('%H:%M:%S')} {msg}\n")
        self.logbox.see("end")


def main():
    model = load_model("model.pth")
    print("模型加载成功，层名：", [n for n, _ in model.named_parameters()])
    root = tk.Tk()
    App(root, model)
    root.mainloop()


if __name__ == "__main__":
    main()