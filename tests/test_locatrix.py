import unittest
from locatrix import PositionEstimator, circular_blend, encode_packet, decode_packet

class LocatrixTests(unittest.TestCase):
    def test_circular_heading_blend_wraparound(self):
        value = circular_blend(359, 1, 0.5)
        self.assertTrue(value < 2 or value > 358)

    def test_step_moves_east_and_increases_uncertainty(self):
        estimator = PositionEstimator(13.0, 80.0)
        before = estimator.snapshot()
        after = estimator.step(1.0, 90.0)
        self.assertGreater(after.longitude, before["longitude"])
        self.assertEqual(after.steps, 1)
        self.assertGreater(after.uncertainty_m, before["uncertainty_m"])

    def test_invalid_coordinates_and_stride(self):
        with self.assertRaises(ValueError):
            PositionEstimator(100, 0)
        with self.assertRaises(ValueError):
            PositionEstimator(0, 0).step(0, 90)

    def test_packet_round_trip_and_checksum(self):
        original = {"latitude": 13.08, "longitude": 80.27, "steps": 8}
        packet = encode_packet(original)
        self.assertEqual(decode_packet(packet), original)
        packet["crc32"] = "00000000"
        with self.assertRaises(ValueError):
            decode_packet(packet)

if __name__ == "__main__":
    unittest.main()
