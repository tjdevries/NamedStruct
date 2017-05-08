from enum import Enum
from jinja2 import Template

from starstruct.elementenum import ElementEnum

class TestGenerate():
    def test_1(self):
        t = Template("""
typedef enum {
{% for enum_name in enum %}
    {{ enum_name }} = {{ enum_name.value }},
{% endfor %}
} {{ enum.__name__ }}_t;""")

        class TestEnum(Enum):
            EXAMPLE = 1
            ANOTHER = 2
            FINAL = 3

        # print(t.render(enum=TestEnum))

        e = ElementEnum(['a', 'b', TestEnum])

        # for item in dir(TestEnum):
        #     print(item, getattr(TestEnum, item))

        assert e.generate('c') == t.render(enum=TestEnum)
