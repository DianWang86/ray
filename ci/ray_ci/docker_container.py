import os
from typing import List
from datetime import datetime

from ci.ray_ci.container import Container


PLATFORM = ["cu118"]
GPU_PLATFORM = "cu118"


class DockerContainer(Container):
    """
    Container for building and publishing ray docker images
    """

    def __init__(self, python_version: str, platform: str, image_type: str) -> None:
        assert "RAYCI_CHECKOUT_DIR" in os.environ, "RAYCI_CHECKOUT_DIR not set"
        rayci_checkout_dir = os.environ["RAYCI_CHECKOUT_DIR"]
        self.python_version = python_version
        self.platform = platform
        self.image_type = image_type

        super().__init__(
            "forge",
            volumes=[
                f"{rayci_checkout_dir}:/rayci",
                "/var/run/docker.sock:/var/run/docker.sock",
            ],
        )

    def _get_image_version_tags(self) -> List[str]:
        branch = os.environ.get("BUILDKITE_BRANCH")
        sha_tag = os.environ["BUILDKITE_COMMIT"][:6]
        if branch == "master":
            return [sha_tag, "nightly"]

        if branch and branch.startswith("releases/"):
            release_name = branch[len("releases/") :]
            date_tag = datetime.now().strftime("%Y-%m-%d")
            return [f"{release_name}.{sha_tag}", f"{release_name}.{date_tag}"]

        return [sha_tag]

    def _get_canonical_tag(self) -> str:
        return self._get_image_tags()[0]

    def _get_image_tags(self) -> List[str]:
        # An image tag is composed by ray version tag, python version and platform.
        # See https://docs.ray.io/en/latest/ray-overview/installation.html for
        # more information on the image tags.
        versions = self._get_image_version_tags()

        platforms = [f"-{self.platform}"]
        if self.platform == "cpu" and self.image_type == "ray":
            # no tag is alias to cpu for ray image
            platforms.append("")
        elif self.platform == GPU_PLATFORM:
            # gpu is alias to cu118 for ray image
            platforms.append("-gpu")
            if self.image_type == "ray-ml":
                # no tag is alias to gpu for ray-ml image
                platforms.append("")

        tags = []
        for version in versions:
            for platform in platforms:
                tag = f"{version}-{self.python_version}{platform}"
                tags.append(tag)
        return tags
