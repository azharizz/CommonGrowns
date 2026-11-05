import unittest

from commongrown.switch import message_event, safe_url, chunks


class SwitchTests(unittest.TestCase):
    def test_only_authenticated_message_event_shape_is_routed(self):
        frame = {"event": "message", "id": 12, "data": {"type": "message", "sequence": 12,
                 "room_id": "room", "payload": {"sender": "user-id", "addressed": True,
                 "body": "hello", "message_id": "m1"}}}
        self.assertEqual(message_event(frame)["payload"]["sender"], "user-id")
        self.assertIsNone(message_event({"event": "command", "data": {}}))
        # Unaddressed messages are routed too: the worker uses them as listen-mode evidence only.
        self.assertIsNotNone(message_event({"event": "message", "data": {"payload": {"addressed": False}}}))
        self.assertIsNone(message_event({"event": "message", "data": {}}))

    def test_remote_server_requires_tls(self):
        self.assertEqual(safe_url("https://switch.example.com/"), "https://switch.example.com")
        self.assertEqual(safe_url("http://127.0.0.1:8080"), "http://127.0.0.1:8080")
        for value in ("http://remote.example.com", "https://user:password@example.com", "file:///secret"):
            with self.assertRaises(ValueError):
                safe_url(value)

    def test_message_chunks_stay_below_telegram_limit(self):
        parts = chunks({"reply": "a" * 8000})
        self.assertTrue(all(len(p) <= 3500 for p in parts))
        self.assertEqual("".join(parts), "a" * 8000)
