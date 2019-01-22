import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mozilla-bitbar-devicepool",
    version="0.0.0",
    author="Bob Clary",
    author_email="bclary@mozilla.com",
    description="Manage Mozilla Android Hardware testing at Bitbar.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bclary/mozilla-bitbar-devicepool",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
    ],
)
