import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import load_only

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bot.common.service import Service
from bot.models.user import User


class UserService(Service[User]):
    model = User
    options = [load_only(User.id)]

def test_custom_option_list_uses_passed_options():
    service = UserService()
    custom = [load_only(User.username)]
    stmt = service._build_get_query(options=custom)
    assert stmt._with_options == tuple(custom)
