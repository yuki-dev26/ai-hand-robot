#!/usr/bin/env python3
"""利用可能なシリアルポートを一覧表示する。"""

from hand import list_ports


def main() -> None:
    ports = list_ports()
    if not ports:
        print("シリアルポートが見つかりません。")
        return

    print("利用可能なシリアルポート:")
    for device, desc in ports:
        print(f"  {device}")
        if desc:
            print(f"    ({desc})")


if __name__ == "__main__":
    main()
