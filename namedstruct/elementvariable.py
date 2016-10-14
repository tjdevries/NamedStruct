"""
The variable NamedStruct element class.
Can be used in multiple ways ways:

1: Variable Lengths, in terms of namedstruct elements


    .. code-block:: python

        ExampleMessage = Message('VarTest', [('x', 'B'), ('y', 'B')])

        message_struct = [
            ('length_in_objects', 'H', 'vardata'),            # length field
            ('vardata', ExampleMessage, 'length_in_objects')  # variable length data
        ]

    The length is the string and you can think of it as "linking" to the
    length that is provided in the length field.

    .. note:: The length item is specified as a string, not as bytes

2: Variable lengths, in terms of byte size


    .. code-block:: python

        SomeMessage = namedstruct.Message(...)

        message_struct = [
            (b'length_in_bytes', 'B', 'vardata'),
            ('vardata', SomeMessage, b'length_in_bytes'),
        ]

    Now if our program specifies taht we should have a length in bytes field
    we can say 'length_in_bytes' = 8, while only have 2 SomeMessage, (assuming
    that the length of SomeMessge == 4).

    .. note:: The length item is specified as bytes, not as a string

3: Fixed length, in terms of namedstruct elements

    .. code-block:: python

        RepeatedMessage = Message('Repeated', [('x', 'B'), ('y', 'H')])

        message_struct = [
            ('repeated_data', RepeatedMessage, 3),
        ]

    Now we provide an integer that tells us that there will ALWAYS be that
    many messages in this message. You also no longer need to have another
    field that specifies the number of these messages.

4: Fixed length, in terms of bytes?

    TODO: write this

    Might have something that can only fit a certain number of bytes, like a
    CAN message, and this would break it up automatically?
"""


import struct

import namedstruct
from namedstruct.element import Element


class ElementVariable(Element):
    """
    Initialize a NamedStruct element object.

    :param field: The fields passed into the constructor of the element
    :param mode: The mode in which to pack the bytes
    """

    # pylint: disable=unused-argument
    def __init__(self, field: tuple, mode: namedstruct.modes.Mode):
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

        self.changemode(mode)

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
            and isinstance(field[1], namedstruct.message.Message) \
            and isinstance(field[2], (str, int, bytes))

    def changemode(self, mode: namedstruct.modes.Mode) -> None:
        """Change the mode of the message format

        :param mode: The mode that the bytes will now be packed in
        """
        self._mode = mode
        self.format.changemode(mode)

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

        return (ret, unused)

    def make(self, msg: dict):
        """Return the expected "made" value

        :param msg: The message containing the required values
        """
        ret = []
        for val in msg[self.name]:
            ret.append(self.format.make(val))
        return ret
