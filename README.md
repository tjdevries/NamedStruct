NamedStruct
======
A package that provides consistent packing and unpacking of binary data

Getting Started
===============

Requirements
------------

* Python 3.5+

Installation
------------

NamedStruct can be installed with pip:

```
$ pip install namedstruct
```

or directly from the source code:

```
$ git clone https://github.com/sprout42/NamedStruct.git
$ cd NamedStruct
$ python setup.py install
```

Basic Usage
===========

After installation, the package can imported:

```
$ python
>>> import namedstruct
>>> namedstruct.__version__
```

An example usage of the package:

```python
import enum

# Import the package
from namedstruct import Mode
from namedstruct.message import Message

# A custom Enum you might be using
class MyEnum(enum.Enum):
    my_custom_data_type = 0x0
    my_other_data_type = 0x1
    final_data_type = 0x2

SizeOfData = Message('Data', [('pad', '8x')], Mode.Big)
AnotherDataSize = Message('Data', [
    ('status', 'H'),
    ('pad', '6x'),
], Mode.Big)

# Create your Message
MyMessage = Message('message_name', [
    ('an_important_integer', 'i'),                    # Pack it into the size of a struct integer
    ('ten_long_string', '10s'),                       # Pack it like 10 consecutive characters
    ('a_fixed_point_number', 'F', 'i', 4),            # Pack it like an integer, but with four bits of precision
                                                      # as a floating point number
    ('union_identifier', 'B', MyEnum),
    ('like_a_c_union', {
        MyEnum.my_custom_data_type: SizeOfData,       # These sizes should usually all be the same,
        MyEnum.my_other_data_type: AnotherDataSize,   # but they can be of different styles!
        MyEnum.final_data_type: SizeOfData,
    }, 'union_identifier'),                           # Choose which type of thing based on union_identifier
], Mode.Big)                                          # Pack it with big endianess

# Now you can use a dictionary to make your messages
data_1 = {
    'an_important_integer': 42,
    'ten_long_string': 'wow! stuff',
    'a_fixed_point_number': '1.25',
    'union_identifier': MyEnum.my_other_data_type,
    'like_a_c_union': {'status': 1}
}

named_tuple_version = MyMessage.make(data_1)
print(named_tuple_version.an_important_integer)  # 42
print(named_tuple_version.a_fixed_point_number)  # b'\x00\x00\x00\x14'

packed_message = MyMessage.pack(data_1)
print(packed_message)  # b'\x00\x00\x00*wow! stuff\x00\x00\x00\x14\x01\x00\x01\x00\x00\x00\x00\x00\x00'

unpacked_message = MyMessage.unpack(packed_message)
print(unpacked_message.an_important_integer)  # 42
print(unpacked_message.a_fixed_point_number)  # 1.25
```
