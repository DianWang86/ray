import os
import sys
from typing import List
from unittest import mock
from datetime import datetime

import pytest

from ci.ray_ci.container import _DOCKER_ECR_REPO
from ci.ray_ci.ray_docker_container import RayDockerContainer
from ci.ray_ci.test_base import RayCITestBase
from ci.ray_ci.utils import RAY_VERSION


class TestDockerContainer(RayCITestBase):
    cmds = []

    def test_run(self) -> None:
        def _mock_run_script(input: List[str]) -> None:
            self.cmds.append(input[0])

        with mock.patch(
            "ci.ray_ci.ray_docker_container.docker_pull", return_value=None
        ), mock.patch(
            "ci.ray_ci.docker_container.Container.run_script",
            side_effect=_mock_run_script,
        ):
            container = RayDockerContainer("py38", "cu118", "ray")
            container.run()
            cmd = self.cmds[-1]
            assert cmd == (
                "./ci/build/build-ray-docker.sh "
                f"ray-{RAY_VERSION}-cp38-cp38-manylinux2014_x86_64.whl "
                f"{_DOCKER_ECR_REPO}:123-raypy38cu118base "
                "requirements_compiled.txt "
                "rayproject/ray:123456-py38-cu118"
            )

            container = RayDockerContainer("py37", "cpu", "ray-ml")
            container.run()
            cmd = self.cmds[-1]
            assert cmd == (
                "./ci/build/build-ray-docker.sh "
                f"ray-{RAY_VERSION}-cp37-cp37m-manylinux2014_x86_64.whl "
                f"{_DOCKER_ECR_REPO}:123-ray-mlpy37cpubase "
                "requirements_compiled_py37.txt "
                "rayproject/ray-ml:123456-py37-cpu"
            )

    def test_get_image_name(self) -> None:
        container = RayDockerContainer("py38", "cpu", "ray")
        assert container._get_image_names() == [
            "rayproject/ray:123456-py38-cpu",
            "rayproject/ray:123456-py38",
            "rayproject/ray:nightly-py38-cpu",
            "rayproject/ray:nightly-py38",
        ]

        container = RayDockerContainer("py37", "cu118", "ray-ml")
        assert container._get_image_names() == [
            "rayproject/ray-ml:123456-py37-cu118",
            "rayproject/ray-ml:123456-py37-gpu",
            "rayproject/ray-ml:123456-py37",
            "rayproject/ray-ml:nightly-py37-cu118",
            "rayproject/ray-ml:nightly-py37-gpu",
            "rayproject/ray-ml:nightly-py37",
        ]

        with mock.patch.dict(
            os.environ, {"BUILDKITE_BRANCH": "releases/1.0.0"}
        ), mock.patch("ci.ray_ci.docker_container.datetime") as mock_date:
            mock_date.now.return_value = datetime(2021, 1, 1)
            container = RayDockerContainer("py38", "cpu", "ray")
            assert container._get_image_names() == [
                "rayproject/ray:1.0.0.123456-py38-cpu",
                "rayproject/ray:1.0.0.123456-py38",
                "rayproject/ray:1.0.0.2021-01-01-py38-cpu",
                "rayproject/ray:1.0.0.2021-01-01-py38",
            ]


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
