import copy
import unittest
from types import SimpleNamespace

from opendbc.can import CANPacker, CANParser
from opendbc.car.hyundai.hyundaicanfd import create_daw_suppression, hkg_can_fd_checksum


DBC = "hyundai_canfd_generated"
MSG_NAME = "FR_CMR_01_10ms"
MSG_ADDR = 0x11A
WARNING_FRAME = bytes.fromhex("24a8ec05000a080b0000000000000100")


class TestDawSuppression(unittest.TestCase):
  def test_captured_warning_frame_is_rebuilt_losslessly(self):
    parser = CANParser(DBC, [(MSG_NAME, 0)], 1)
    parser.update([0, [(MSG_ADDR, WARNING_FRAME, 1)]])
    stock_values = copy.deepcopy(parser.vl[MSG_NAME])

    address, dat, bus = create_daw_suppression(CANPacker(DBC), SimpleNamespace(ECAN=1), stock_values)

    self.assertEqual(address, MSG_ADDR)
    self.assertEqual(bus, 1)
    self.assertEqual(len(dat), len(WARNING_FRAME))
    self.assertEqual(dat[2], (WARNING_FRAME[2] + 1) & 0xFF)
    self.assertEqual(dat[3:6], WARNING_FRAME[3:6])
    self.assertEqual(dat[6] & 0x7F, WARNING_FRAME[6] & 0x7F)
    self.assertEqual(dat[7] & 0xC0, WARNING_FRAME[7] & 0xC0)
    self.assertEqual(dat[8:], WARNING_FRAME[8:])
    self.assertEqual(int.from_bytes(dat[:2], "little"), hkg_can_fd_checksum(address, None, bytearray(dat)))

    parser.update([0, [(address, dat, bus)]])
    self.assertEqual(parser.vl[MSG_NAME]["FR_CMR_AlvCnt1Val"], (int(stock_values["FR_CMR_AlvCnt1Val"]) + 1) & 0xFF)
    self.assertEqual(parser.vl[MSG_NAME]["DAW_SysSta"], 1)
    self.assertEqual(parser.vl[MSG_NAME]["DAW_WrnMsgSta"], 0)
