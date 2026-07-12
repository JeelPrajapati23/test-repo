from demo import get_last_n_items


def test_normal_case():
    assert get_last_n_items([1, 2, 3, 4, 5], 2) == [4, 5]


def test_full_list():
    assert get_last_n_items([1, 2, 3], 3) == [1, 2, 3]
