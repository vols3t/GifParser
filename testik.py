import os
import pytest

from test import read_header_info  

HERE = os.path.dirname(__file__)

@pytest.mark.parametrize(
    "filename,expected_size",
    [
        ("big.gif", (2000, 2000)),
        ("smoll.gif", (1, 1)),
    ],
)
def test_gif_canvas_size(filename, expected_size):
    path = os.path.join(HERE, filename)
    assert os.path.exists(path), f"Файл {filename} не найден по пути {path}"
    with open(path, "rb") as f:
        data = f.read()

    header_info = read_header_info(data)
    assert "error" not in header_info, header_info.get("error")
    assert (header_info["width"], header_info["height"]) == expected_size