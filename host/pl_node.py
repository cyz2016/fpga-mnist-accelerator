
import socket
import time

import numpy as np
import torch

from mnist_model import load_model

HOST, PORT = "127.0.0.1", 5000
MODEL_PATH = "model.pth"
SIM_LATENCY = 0.028


def build_frame(cmd, data=b""):

    head = bytes([0xAA, 0x55, cmd, (len(data) >> 8) & 0xFF, len(data) & 0xFF])
    body = head + data
    chk = int(np.bitwise_xor.reduce(np.frombuffer(body, np.uint8)))
    return body + bytes([chk])


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


def handle(conn):

    conn.sendall(build_frame(0x80, bytes([0x01])))
    print("[PL] 已发送就绪帧 0x80")

    buf = bytearray()
    while True:
        try:
            chunk = conn.recv(512)
        except Exception:
            break
        if not chunk:
            continue
        buf.extend(chunk)
        parsed = parse_frame(buf)
        if parsed is None:
            continue
        cmd, data = parsed
        if cmd == 0x00:
            conn.sendall(build_frame(0x80, bytes([0x01])))
            print("[PL] 握手完成 -> 0x80")
        elif cmd == 0x01 and len(data) == 784:
            arr = np.frombuffer(data, np.uint8).reshape(28, 28).astype(np.float32) / 255.0
            x = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
            with torch.no_grad():
                digit = int(model(x).argmax(1).item())
            time.sleep(SIM_LATENCY)
            conn.sendall(build_frame(0x81, bytes([digit])))
            print(f"[PL] 推理完成 -> {digit}")
        else:
            print(f"[PL] 未知帧 cmd=0x{cmd:02X} len={len(data)}")


def main():
    global model
    model = load_model(MODEL_PATH)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(5)
    print(f"[PL] 节点就绪，监听 {HOST}:{PORT}")

    while True:                      
        conn, addr = srv.accept()
        print(f"[PL] 上位机已连接：{addr}")
        try:
            handle(conn)
        except Exception as e:
            print(f"[PL] 连接异常：{e}")
        finally:
            conn.close()
            print("[PL] 连接断开，等待下一次连接")


if __name__ == "__main__":
    main()