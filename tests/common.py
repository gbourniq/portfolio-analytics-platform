import base64
import datetime as dtm
import json
import os
from copy import deepcopy

from sigtech.dave.api.actions.common import PACKAGE_MEDIA_TYPE, UUID6Str
from sigtech.dave_tests.storage.common import _MOCK_TENANT_ID, _MOCK_USER_ID

SAMPLE_PACKAGES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "sample_packages"
)
SAMPLE_PATCHES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "sample_patches"
)
MOCK_API_RESPONSES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mock_api_responses"
)

MOCK_HEADERS = {
    "X-Dave-UserId": _MOCK_USER_ID,
    "X-Dave-TenantId": _MOCK_TENANT_ID,
    "X-Dave-SessionCredentials": json.dumps(
        {
            "AccessKeyId": "",
            "SecretAccessKey": "SecretAccessKey",
            "SessionToken": "SessionToken",
        }
    ),
    "X-Dave-s3RoleExternalId": _MOCK_TENANT_ID,
}


def sample_package(dir_name: str) -> bytes:
    from sigtech.dave.lib.package import build_package

    base_path = os.path.join(SAMPLE_PACKAGES_DIR, dir_name)
    return build_package(base_path)


def sample_patch(name) -> bytes:
    path = os.path.join(SAMPLE_PATCHES_DIR, name)
    assert os.path.isfile(path)
    with open(path, "rb") as f:
        return f.read()


def _sample_package_base64(dir_name: str) -> str:
    package_bytes = sample_package(dir_name)
    return base64.b64encode(package_bytes).decode("ascii")


def sample_package_data_uri(dir_name: str) -> str:
    package_base64 = _sample_package_base64(dir_name)
    return f"data:{PACKAGE_MEDIA_TYPE};base64,{package_base64}"


def any_timestamp():
    """Helper function that checks if the compared value is a valid iso timestamp"""

    class AnyTimestamp:
        value = None

        def __eq__(self, other):
            try:
                dtm.datetime.fromisoformat(other)
                self.value = other
                return True
            except ValueError:
                self.value = f"<Invalid timestamp: {other}>"
                return False

        def __repr__(self):
            return str(self.value) if self.value else super().__repr__()

    return AnyTimestamp()


def any_uuid6():
    """Helper function that checks if the compared value is a valid uuid6"""

    class AnyUUID6:
        value = None

        def __eq__(self, other):
            try:
                UUID6Str.validate(other)
                self.value = other
                return True
            except ValueError:
                self.value = f"<Invalid uuid6: {other}>"
                return False

        def __repr__(self):
            return str(self.value) if self.value else super().__repr__()

    return AnyUUID6()


def any_string():
    """Helper function that checks if the compared value is a string"""

    class AnyString:
        value = None

        def __eq__(self, other):
            try:
                assert isinstance(other, str)
                self.value = other
                return True
            except AssertionError:
                self.value = f"<Invalid string: {other}>"
                return False

        def __repr__(self):
            return str(self.value) if self.value else super().__repr__()

    return AnyString()


def any_number():
    """Helper function that checks if the compared value is a number (int or float)"""

    class AnyNumber:
        value = None

        def __eq__(self, other):
            try:
                assert isinstance(other, (int, float))
                self.value = other
                return True
            except AssertionError:
                self.value = f"<Invalid number: {other}>"
                return False

        def __repr__(self):
            return str(self.value) if self.value is not None else super().__repr__()

    return AnyNumber()


def mock_api_response(filename: str):
    with open(os.path.join(MOCK_API_RESPONSES_DIR, filename), "r") as f:
        # return a copy to avoid mutating the original data in unit-tests
        return deepcopy(json.load(f))
