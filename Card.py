class Card:
    numb_lookup = {
        "9": "0",
        "8": "9",
        "7": "8",
        "6": "7",
    }

    def __init__(self, value, suit):
        self.suit = suit
        self.value = value
        self.id = value + suit

    def __str__(self):
        return self.id

    def is_face(self):
        return self.value == "F"

    def is_number(self):
        return not self.value == "F"

    def is_red(self):
        return self.suit == "R"


class CardBitmap:
    """12x12 pixels for one card"""

    NUM6 = [
        0xFE417F,  # 333200001333 333210011333
        0xF4001F,  # 331000000033 331000000133
        0xE01907,  # 320001200013 320001210013
        0xD07E03,  # 310013320003 310013320003
        0xC069BF,  # 300012212333 300023222333
        0xC0400B,  # 300000000023 300010000023
        0xC01403,  # 300001100003 300001100003
        0xC07E02,  # 300013320002 300013320002
        0xC0BF02,  # 300013330001 300023330002
        0xD07E02,  # 310003320002 310013320002
        0xE00003,  # 320000000003 330000100013
        0xF8001F,  # 332000000133 332000000133
    ]

    NUM7 = [
        0xC00002,  # 300000000002 300000000002
        0xC00002,  # 300000000002 300000000002
        0xC00007,  # 300000000013 300000000013
        0xFFF40F,  # 333333100033 333333200133
        0xFFE02F,  # 333332000233 333332000233
        0xFFC07F,  # 333330001333 333331001333
        0xFF80BF,  # 333320002333 333320002333
        0xFF00FF,  # 333300003333 333310013333
        0xFE02FF,  # 333200023333 333200023333
        0xFD02FF,  # 333100023333 333100023333
        0xFC03FF,  # 333000033333 333100033333
        0xFC03FF,  # 333000033333 333000033333
    ]

    NUM8 = [
        0xFD01BF,  # 333100002333 333210012333
        0xF4001F,  # 330000000133 331000000133
        0xD0240B,  # 310002100023 320002200023
        0xD07D07,  # 310013310013 310023320013
        0xD07D07,  # 310013310013 320013310023
        0xF5002F,  # 330000000133 331000000133
        0xF5002F,  # 331000000133 331000000133
        0xD02807,  # 310002200013 310012210013
        0xC07D03,  # 300013310003 300023320003
        0xC07D03,  # 300013310003 300013310003
        0xD00007,  # 310000000013 310000000013
        0xF4001F,  # 331000000133 331000000133
    ]

    NUM9 = [
        0xF900BF,  # 332100002333 332110012333
        0xE0001F,  # 320000000133 320000000133
        0xC0240B,  # 300002100023 300012200023
        0x80FD03,  # 200033310003 200033310013
        0x80FE03,  # 100033310003 200033320003
        0x807803,  # 200013200003 200013210003
        0xD00003,  # 310000000003 310000000003
        0xF80503,  # 332000110003 332100110003
        0xD5FD03,  # 311133310003 322233320013
        0xC07C07,  # 300013300013 310013310013
        0xE0000F,  # 320000000033 320000000033
        0xF4002F,  # 331000000233 332000001233
    ]

    NUM10 = [
        0xFFA0BF,  # 333322002333 333332003333
        0xF900BF,  # 332100002333 332110013333
        0xD000BF,  # 310000002333 310000013333
        0xD000BF,  # 310000002333 320100013333
        0xFF40BF,  # 332310002333 333310013333
        0xFF40BF,  # 333310002333 333310013333
        0xFF40BF,  # 333310002333 333310013333
        0xFF40BF,  # 333310002333 333310013333
        0xFF40BF,  # 333310002333 333310013333
        0xFA41BF,  # 332210002323 332210012333
        0xD00003,  # 310000000003 310000000013
        0xD00003,  # 310000000003 310000000013
    ]

    CLUB = [
        0xFF80BF,  # 333320002333
        0xFE002F,  # 333200000233
        0xF8000B,  # 332000000023
        0xFD001F,  # 333100000133
        0xCF407C,  # 303310001330
        0x03D1F0,  # 000331013300
        0x00F3C0,  # 000033033000
        0x001100,  # 000001010000
        0x001100,  # 000001010000
        0x00F3C0,  # 000033033000
        0x03F3F0,  # 000333033300
        0xDFD1FD,  # 313331013331
    ]

    DIAMOND = [
        0xFFE1FF,  # 333332013333
        0xFF807F,  # 333320001333
        0xFE001F,  # 333200000133
        0xF80007,  # 332000000013
        0xE00001,  # 320000000001
        0x800000,  # 200000000000
        0x000000,  # 000000000000
        0x000000,  # 000000000000
        0x000000,  # 000000000000
        0x000000,  # 000000000000
        0x800000,  # 200000000000
        0xE00003,  # 320000000001
    ]

    HEART = [
        0xFFFFFF,  # 333333333333
        0xFFBFFF,  # 333323333333
        0xFD2FFF,  # 333102333333
        0xF40BFD,  # 331000233331
        0xD002F4,  # 310000023310
        0x400090,  # 100000002100
        0x000000,  # 000000000000
        0x800000,  # 200000000000
        0xE00000,  # 320000000000
        0xF80000,  # 332000000000
        0xFE0000,  # 333200000000
        0xFF8000,  # 333320000000
    ]

    SPADE = [
        0xFFF02F,  # 333333000233
        0xFFD00B,  # 333331000023
        0xFF4002,  # 333310000002
        0xFD0000,  # 333100000000
        0xF40000,  # 331000000000
        0xD00000,  # 310000000000
        0x400000,  # 100000000000
        0x000000,  # 000000000000
        0x000000,  # 000000000000
        0x801890,  # 200000202100
        0xE03CA4,  # 320003302310
        0xF8B87D,  # 332023201331
    ]

    CARDS = [NUM6, NUM7, NUM8, NUM9, NUM10, CLUB, DIAMOND, HEART, SPADE]
    NAMES = ["6", "7", "8", "9", "10", "C", "D", "H", "S"]

    @staticmethod
    def to_bitmap(image: list[int], width: int, height: int):
        b = [0] * height
        ss = []
        amin = min(image)
        amax = max(image) + 1
        for row in range(height):
            s = ""
            for col in range(width):
                a = (image[row * height + col] - amin) / (amax - amin)  # normalize
                a = int(a * 4)
                b[row] = (b[row] << 2) | (a & 3)
                s += str(a)
            ss.append(s)
        print("to_bitmap()", ss)
        return b

    @staticmethod
    def to_grayscale(bitmap: list[int]):
        return [[(r >> (22 - i * 2) & 3) * 85 for i in range(12)] for r in bitmap]

    @staticmethod
    def to_bytes(bitmap: list[int]):
        gray = __class__.to_grayscale(bitmap)
        # print("to_bytes()", [x for row in gray for x in row])
        return bytes([x for row in gray for x in row])

    @staticmethod
    def compare(data: list[int], size: int, cards: list[list[int]] = CARDS):
        """Compare n*n data with cards, return argmin and diffs"""
        bitmap = __class__.to_bitmap(data, size, size)
        diffs = [__class__.difference(bitmap, c) for c in cards]
        argmin = 0
        for i in range(1, len(diffs)):
            if diffs[i] < diffs[argmin]:
                argmin = i
        return argmin, diffs

    @staticmethod
    def difference(bitmap: list[int], target: list[int]):
        N = len(bitmap)  # N*N pixels
        M = len(target)  # M*M, M <= N
        if N < M:
            raise Exception("bitmap should have larger dims than target")
        # 6/8/9, C/S are too close, use weighted diff
        WEIGHT = [1, 1, 1, 1.2, 2, 1.5, 1, 1.1, 2, 2, 1.5, 1.5]
        mask = (1 << (2 * M)) - 1
        min_diff = 4 * M * M
        for dx in range(0, N + 1 - M):
            for dy in range(0, N + 1 - M):
                diff = 0
                # ss = []
                for row in range(M):
                    a = bitmap[row + dy] >> (2 * dx) & mask
                    # print(f"mask {mask}={mask:x}, {bitmap[row + dy]:x} -> {a:x}")
                    b = target[row]
                    d = a ^ b
                    # ss.append(f"{a:06x}^{b:06x}={d:06x}")
                    s = 0
                    while d > 0:
                        s += d & 3
                        d >>= 2
                    diff += s * WEIGHT[row]
                # print(dx, dy, diff, ss)
                if diff < M:  # almost exact match
                    return diff
                elif diff < min_diff:
                    min_diff = diff
        return min_diff
