from typing import Any

import pytest

from ckanext.syndicate.model import SyndicationLog

TEST_PROFILE = "test"


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestSyndicationLogModel:
    def test_create_syndication_log(self, package: dict[str, Any]):
        SyndicationLog.write(local_id=package["id"], profile_id=TEST_PROFILE)

        log = SyndicationLog.get(package["id"], TEST_PROFILE)

        assert log is not None
        assert log.local_id == package["id"]
        assert log.target_id == "-"
        assert log.profile_id == TEST_PROFILE
        assert log.state == SyndicationLog.State.SYNCED
        assert log.error is None

    def test_update_syndication_log(self, package: dict[str, Any]):
        SyndicationLog.write(local_id=package["id"], profile_id=TEST_PROFILE)

        SyndicationLog.write(
            local_id=package["id"],
            profile_id=TEST_PROFILE,
            target_id="remote-id-123",
            state=SyndicationLog.State.FAILED,
            error="Something went wrong",
        )

        log = SyndicationLog.get(package["id"], TEST_PROFILE)

        assert log is not None
        assert log.local_id == package["id"]
        assert log.target_id == "remote-id-123"
        assert log.profile_id == TEST_PROFILE
        assert log.state == SyndicationLog.State.FAILED
        assert log.error == "Something went wrong"

    def test_get_non_existing_log(self):
        log = SyndicationLog.get("non-existing-id", TEST_PROFILE)

        assert log is None

    def test_write_with_non_existing_local_id(self):
        with pytest.raises(Exception, match="violates foreign key constraint"):
            SyndicationLog.write(local_id="non-existing-id", profile_id=TEST_PROFILE)

    def test_package_relationship(self, package: dict[str, Any]):
        SyndicationLog.write(local_id=package["id"], profile_id=TEST_PROFILE)

        log = SyndicationLog.get(package["id"], TEST_PROFILE)

        assert log is not None
        assert log.local_package is not None
        assert log.local_package.id == package["id"]
