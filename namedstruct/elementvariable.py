import struct

from typing import Optional

from namedstruct.element import register, Element
from namedstruct.message import Message
from namedstruct.modes import Mode

print('ELEMENT VARIABLE')


@register
class ElementVariable(Element):
    """
    Initialize a NamedStruct element object.

    :param field: The fields passed into the constructor of the element
    :param mode: The mode in which to pack the bytes
    """

    # pylint: disable=unused-argument
    def __init__(self, field: tuple, mode: Optional[Mode]=Mode.Native, alignment: Optional[int]=1):
        # All of the type checks have already been performed by the class
        # factory
        self.name = field[0]
        self.ref = field[2]

        # Variable elements don't use the normal struct format, the format is
        # a NamedStruct.Message object, but change the mode to match the
        # current mode.
        self.format = field[1]

        # Set the packing style for the struct
        if isinstance(self.ref, (str, bytes)):
            self.variable_repeat = True

            # Determine whether bytes or objects are the measurement tool
            if isinstance(self.ref, str):
                self.object_length = True
            else:
                self.object_length = False

                # Change our ref to be a string, for NamedTuple
                self.ref = self.ref.decode('utf-8')
        else:
            self.variable_repeat = False

            # TODO: If we add #4, then we would have to have a check here
            self.object_length = True

        self.update(mode, alignment)

    @staticmethod
    def valid(field: tuple) -> bool:
        """
        Validation function to determine if a field tuple represents a valid
        enum element type.

        The basics have already been validated by the Element factory class,
        validate that the struct format is a valid numeric value.

        :param field: The fields passed in to construct the message
        """
        return len(field) == 3 \
            and isinstance(field[1], Message) \
            and isinstance(field[2], (str, int, bytes))

    def validate(self, msg):
        """
        Ensure that the supplied message contains the required information for
        this element object to operate.

        All elements that are Variable must reference valid Length elements.
        """
        from namedstruct.elementlength import ElementLength
        if self.variable_repeat:
            # Handle object length, not byte length
            if self.object_length:
                if not isinstance(msg[self.ref], ElementLength):
                    err = 'variable field {} reference {} invalid type'
                    raise TypeError(err.format(self.name, self.ref))
                elif not msg[self.ref].ref == self.name:
                    err = 'variable field {} reference {} mismatch'
                    raise TypeError(err.format(self.name, self.ref))
            # Handle byte length, not object length
            else:
                # TODO: Validate the object
                pass
        else:
            if not isinstance(self.ref, int):
                err = 'fixed repetition field {} reference {} not an integer'
                raise TypeError(err.format(self.name, self.ref))

    def update(self, mode: Optional[Mode]=None, alignment: Optional[int]=None) -> None:
        """change the mode of the struct format

        :param mode: The mode that the bytes will now be packed in
        """
        self._mode = mode
        self._alignment = alignment
        self.format.update(mode, alignment)

    def pack(self, msg: dict):
        """Pack the provided values into the supplied buffer.

        :param msg: The message with the values to pack
        """
        # When packing use the length of the current element to determine
        # how many elements to pack, not the length element of the message
        # (which should not be specified manually).
        if self.variable_repeat:
            if self.object_length:
                ret = [self.format.pack(dict(elem)) if elem else self.format.pack({})
                       for elem in msg[self.name]]
            else:
                ret = []
                length = 0

                for elem in msg[self.name]:
                    temp_elem = self.format.pack(dict(elem))

                    if length + len(temp_elem) <= msg[self.ref]:
                        ret.append(temp_elem)

        # Pack as many bytes as we have been given
        # and fill the rest of the byets with empty packing
        else:
            empty_byte = struct.pack('x')
            ret = [self.format.pack(msg[self.name][index]) if index < len(msg[self.name]) else empty_byte * len(self.format)
                   for index in range(self.ref)]

        # There is no need to make sure that the packed data is properly
        # aligned, because that should already be done by the individual
        # messages that have been packed.
        return b''.join(ret)

    def unpack(self, msg: dict, buf: bytes):
        """Unpack data from the supplied buffer using the initialized format.

        :param msg: The message with the values to unpack
        :param buf: The currently unused bytes from the message
        """
        # When unpacking a variable element, reference the already unpacked
        # length field to determine how many elements need unpacked.
        ret = []
        unused = buf
        if self.object_length:
            for _ in range(getattr(msg, self.ref)):
                (val, unused) = self.format.unpack_partial(unused)
                ret.append(val)
        else:
            length = 0
            while length < getattr(msg, self.ref):
                (val, unused) = self.format.unpack_partial(unused)
                length += len(val)
                ret.append(val)

        # There is no need to make sure that the unpacked data consumes a
        # properly aligned number of bytes because that should already be done
        # by the individual messages that have been unpacked.
        return (ret, unused)

    def make(self, msg: dict):
        """Return the expected "made" value

        :param msg: The message containing the required values
        """
        ret = []
        for val in msg[self.name]:
            ret.append(self.format.make(val))
        return ret
