from __future__ import annotations

import signal
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from demo.idle import install_signal_handlers
from hand.ports import find_servo_port


class IdleSignalTests(unittest.TestCase):
    @patch("demo.idle.signal.signal")
    def test_sigterm_is_converted_to_keyboard_interrupt(self, signal_mock) -> None:
        install_signal_handlers()

        registered_signal, handler = signal_mock.call_args.args
        self.assertEqual(registered_signal, signal.SIGTERM)
        with self.assertRaises(KeyboardInterrupt):
            handler(signal.SIGTERM, None)


class ServoPortTests(unittest.TestCase):
    @patch("hand.ports.serial.tools.list_ports.comports")
    def test_rejects_ambiguous_ports(self, comports_mock) -> None:
        comports_mock.return_value = [
            SimpleNamespace(device="/dev/cu.Bluetooth-Incoming-Port", description="n/a"),
            SimpleNamespace(device="/dev/cu.Headphones", description="n/a"),
        ]

        with self.assertRaisesRegex(RuntimeError, "--port"):
            find_servo_port()

    @patch("hand.ports.serial.tools.list_ports.comports")
    def test_selects_recognized_usb_serial_port(self, comports_mock) -> None:
        comports_mock.return_value = [
            SimpleNamespace(device="/dev/cu.Bluetooth-Incoming-Port", description="n/a"),
            SimpleNamespace(device="/dev/cu.usbserial-1234", description="USB Serial"),
        ]

        self.assertEqual(find_servo_port(), "/dev/cu.usbserial-1234")


if __name__ == "__main__":
    unittest.main()
