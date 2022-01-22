from argparse import ArgumentTypeError
from unittest.mock import patch, Mock, PropertyMock, MagicMock

from nose.tools import assert_equals
from nose.tools import assert_not_equals
from nose.tools import assert_raises

from vcsi.vcsi import Grid, mxn_type, Color, hex_color_type, manual_timestamps, timestamp_position_type, \
    TimestampPosition, comma_separated_string_type, metadata_position_type, cleanup, save_image,\
    compute_timestamp_position, max_line_length, draw_metadata
from vcsi import vcsi


def test_grid_default():
    test_grid = mxn_type('4x4')

    assert_equals(test_grid.x, 4)
    assert_equals(test_grid.y, 4)


def test_grid_equality():
    g1 = Grid(4, 4)
    g2 = Grid(4, 4)
    assert_equals(g1, g2)


def test_grid_inequality():
    g1 = Grid(4, 4)
    g2 = Grid(3, 4)
    assert_not_equals(g1, g2)


def test_grid_columns_integer():
    assert_raises(ArgumentTypeError, mxn_type, 'ax4')

    assert_raises(ArgumentTypeError, mxn_type, '4.1x4')


def test_grid_columns_positive():
    assert_raises(ArgumentTypeError, mxn_type, '-1x4')


def test_grid_rows_integer():
    assert_raises(ArgumentTypeError, mxn_type, '4xa')

    assert_raises(ArgumentTypeError, mxn_type, '4x4.1')


def test_grid_rows_positive():
    assert_raises(ArgumentTypeError, mxn_type, '4x-1')


def test_grid_format():
    assert_raises(ArgumentTypeError, mxn_type, '')

    assert_raises(ArgumentTypeError, mxn_type, '4xx4')

    assert_raises(ArgumentTypeError, mxn_type, '4x1x4')

    assert_raises(ArgumentTypeError, mxn_type, '4')


def test_hex_color_type():
    assert_equals(Color(*(0x10, 0x10, 0x10, 0xff)), hex_color_type("101010"))

    assert_equals(Color(*(0x10, 0x10, 0x10, 0x00)), hex_color_type("10101000"))

    assert_equals(Color(*(0xff, 0xff, 0xff, 0xff)), hex_color_type("ffffff"))

    assert_equals(Color(*(0xff, 0xff, 0xff, 0x00)), hex_color_type("ffffff00"))

    assert_raises(ArgumentTypeError, hex_color_type, "abcdeff")

    assert_raises(ArgumentTypeError, hex_color_type, "abcdfg")


def test_manual_timestamps():
    assert_equals(manual_timestamps("1:11:11.111,2:22:22.222"), ["1:11:11.111", "2:22:22.222"])

    assert_raises(ArgumentTypeError, manual_timestamps, "1:11:a1.111,2:22:b2.222")

    assert_raises(ArgumentTypeError, manual_timestamps, "1:1:1:1.111,2:2.222")

    assert_equals(manual_timestamps(""), [])


def test_timestamp_position_type():
    assert_equals(timestamp_position_type("north"), TimestampPosition.north)

    assert_not_equals(timestamp_position_type("south"), TimestampPosition.north)

    assert_raises(ArgumentTypeError, timestamp_position_type, "whatever")


@patch("vcsi.vcsi.parsedatetime")
def test_interval_type(mocked_parsedatatime):
    mocked_parsedatatime.return_value = 30
    assert_equals(mocked_parsedatatime("30 seconds"), 30)

    mocked_parsedatatime.assert_called_once_with("30 seconds")


def test_comma_separated_string_type():
    assert_equals(comma_separated_string_type("a, b, c"), ["a", "b", "c"])

    assert_equals(comma_separated_string_type("a b, c"), ["a b", "c"])


def test_metadata_position_type():
    assert_equals(metadata_position_type("top"), "top")

    assert_equals(metadata_position_type("TOP"), "top")

    assert_raises(ArgumentTypeError, metadata_position_type, "whatever")


@patch("vcsi.vcsi.os")
def test_cleanup(mocked_os):
    mocked_os.unlink.side_effect = lambda x: True
    args = Mock()
    args.is_verbose = False
    frames = [Mock()]
    frames[0].filename = "frame1"
    cleanup(frames, args)

    mocked_os.unlink.assert_called_once_with("frame1")


@patch("vcsi.vcsi.Image")
def test_save_image(mocked_Image):
    args = PropertyMock()
    output_path = "whatever"
    assert_equals(True, save_image(args, mocked_Image, None, output_path))

    mocked_Image.convert().save.assert_called_once()


def test_compute_timestamp_position():
    args = PropertyMock()
    args.timestamp_horizontal_margin = 10
    args.timestamp_vertical_margin = 10
    w, h = 1000, 500
    text_size = (10, 10)
    desired_size = (20, 20)
    rectangle_hpadding, rectangle_vpadding = 5, 5

    args.timestamp_position = TimestampPosition.west
    assert_equals(((1010, 500.0), (1030, 520.0)),
                  compute_timestamp_position(args, w, h, text_size, desired_size, rectangle_hpadding,
                                             rectangle_vpadding))

    args.timestamp_position = TimestampPosition.north
    assert_equals(((1000, 510.0), (1020, 530.0)),
                  compute_timestamp_position(args, w, h, text_size, desired_size, rectangle_hpadding,
                                             rectangle_vpadding))

    args.timestamp_position = None
    assert_equals(((990, 490), (1010, 510)),
                  compute_timestamp_position(args, w, h, text_size, desired_size, rectangle_hpadding,
                                             rectangle_vpadding))


def test_max_line_length():
    media_info = PropertyMock()
    metadata_font = PropertyMock()
    metadata_font.getsize.return_value = (40, 40)
    header_margin = 100
    width = 1000

    text = "A long line of text"
    assert_equals(19, max_line_length(media_info, metadata_font, header_margin, width, text))

    text = "A long line of text with a few more words"
    assert_equals(41, max_line_length(media_info, metadata_font, header_margin, width, text))

    text = "A really long line of text with a lots more words" * 100
    assert_equals(4900, max_line_length(media_info, metadata_font, header_margin, width, text))

    text = None
    filename = PropertyMock()
    type(media_info).filename = filename
    # media_info.filename = filename
    assert_equals(0, max_line_length(media_info, metadata_font, header_margin, width, text))
    filename.assert_called_once()


def test_draw_metadata():
    args = Mock()
    draw = Mock()
    header_lines = MagicMock()
    draw.text.return_value = 0
    args.metadata_vertical_margin = 0
    header_lines.__iter__ = Mock(return_value=iter(['text1', 'text2']))

    assert_equals(0, draw_metadata(draw, args,
                                   header_lines=header_lines,
                                   header_line_height=0,
                                   start_height=0))
    draw.text.assert_called()


def test_grid():
    assert_equals("2x2", Grid(2, 2).__str__())

    assert_equals("10x0", Grid(10, 0).__str__())

def test_color():
    assert_equals("FFFFFFFF", Color(255, 255, 255, 255).__str__())

