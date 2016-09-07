
import re
import struct

import decimal
from decimal import Decimal

from namedstruct.element import Element
from namedstruct.modes import Mode


bits_format = {
    ('c', 'b', 'B'): 1,
    ('h', 'H'): 2,
    ('i', 'I', 'l', 'L'): 4,
    ('q', 'Q'): 8
}


def get_bits_length(pack_format):
    if pack_format[0] in ['@', '=', '<', '>', '+']:
        pack_format = pack_format[1:]

    bits = -1
    for fmt in bits_format:
        match_str = r'|'.join(fmt)
        # match_str = r'(@|=|<|>|+)' + match_str
        # match_str = r'*' + match_str + r'*'

        if re.match(match_str, pack_format):
            bits = bits_format[fmt] * 4

    if bits == -1:
        raise ValueError('Pack format {0} was not a valid fixed point specifier'.format(
            pack_format)
        )

    return bits


def get_fixed_point(num, pack_format, precision):
    """
    Helper function to get the right bytes once we're done
    """
    if not isinstance(num, Decimal):
        try:
            num = Decimal(num)
        except:
            raise ValueError('Num {0} could not be converted to a Decimal'.format(num))

    bits = get_bits_length(pack_format)

    if bits < precision:
        raise ValueError('Specified a format {1} that was too small for the given precision of {0}'.format(
            pack_format,
            precision
        ))

    if num >= 2 ** (bits - precision):
        raise ValueError('num: {0} must fit in the specified number of available bits {1}'.format(num, 8 * (bits - precision)))

    num_shifted = int(num * (2 ** precision))
    return num_shifted


def get_fixed_bits(num, pack_format, precision):
    num_shifted = get_fixed_point(num, pack_format, precision)
    return struct.pack(pack_format, num_shifted)


class ElementFixedPoint(Element):
    """
    A NamedStruct element class for fixed point number fields.

    Uses the built in Decimal class

    Example Usage::

        from namedstruct.message import Message
        example_precision = 8
        example_struct = namedstruct.Message('example', [('my_fixed_point', 'F', 'I', example_precision)])

        my_data = {
            'my_fixed_point': '120.0'
        }
        packed_struct = example_struct.make(my_data)

    """

    def __init__(self, field, mode=Mode.Native):
        """Initialize a NamedStruct element object."""

        # TODO: Add checks in the class factory?
        self.name = field[0]
        self.pack_format = field[2]
        self.precision = field[3]

        if len(field) == 5:
            self.decimal_prec = field[4]
        else:
            self.decimal_prec = False

        # TODO: Do I need a ref here?
        self.ref = None

        self._mode = mode

        self.format = mode.value + self.pack_format
        self._struct = struct.Struct(self.format)

    @staticmethod
    def valid(field):
        """
        Validation function to determine if a field tuple represents a valid
        fixedpoint element type.

        The basics have already been validated by the Element factory class,
        validate the specific struct format now.
        """
        return len(field) >= 4 \
            and isinstance(field[1], str) \
            and re.match(r'\d*F', field[1]) \
            and isinstance(field[2], str) \
            and isinstance(field[3], (int, float, Decimal))

    def pack(self, msg):
        """Pack the provided values into the specified buffer."""
        packing_decimal = Decimal(msg[self.name])

        # integer = int(self.decimal // 1)
        # top_bits = integer.to_bytes(int((self.bits - self.precision) / 8), self._mode.to_byteorder())
        # top_bits = b'{0:%db}' % (self.bits - self.precision)
        # top_bits = top_bits.format(integer)

        # bot_bits = b'0' * self.precision

        # print('top_bits:', top_bits.bin)
        # print('bot_bits:', bot_bits)
        # print('all_bits:', top_bits + bot_bits)
        # self._struct.pack(top_bits + bot_bits)
        fixed_point = get_fixed_point(packing_decimal, self.format, self.precision)
        return self._struct.pack(fixed_point)

    def unpack(self, msg, buf):
        """Unpack data from the supplied buffer using the initialized format."""
        # ret = self._struct.unpack_from(buf, 0)
        ret = self._struct.unpack_from(buf, 0)[0]
        unused = buf[struct.calcsize(self.format):]

        if self.decimal_prec:
            decimal.getcontext().prec = self.decimal_prec
        else:
            decimal.getcontext().prec = 26

        ret_decimal = Decimal(ret) / Decimal(2 ** self.precision)
        return (ret_decimal, unused)

    def make(self, msg):
        """Return bytes of the expected format"""
        return self._struct.pack(msg[self.name])
