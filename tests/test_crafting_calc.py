import pytest

from ffxivledger.models import Item, Transaction, Stock


def test_generate_queue(client, app):
    with app.app_context():
        from ffxivledger.crafting_calc import generate_queue
        for x in [1, 3, 5, 10]:
            craft_list = generate_queue(x)
            assert craft_list is not None
            assert 0 < len(craft_list) < x+1
