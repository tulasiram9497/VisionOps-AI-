from __future__ import annotations

from ultralytics import YOLO


def main() -> None:
    model = YOLO("yolo11n.pt")
    model.fuse()
    print(f"Downloaded and initialized {model.ckpt_path or 'yolo11n.pt'}")


if __name__ == "__main__":
    main()
