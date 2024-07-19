from setuptools import find_namespace_packages, setup


def get_description():
    return "Publishing tools project family"


def get_long_description():
    with open("README.md") as f:
        text = f.read()

    # Long description is everything after README's initial heading
    idx = text.find("\n\n")
    return text[idx:]


def get_requirements():
    # Note: at time of writing, requirements.txt is empty.
    # It exists anyway for a consistent setup.
    with open("requirements.txt") as f:
        return f.read().splitlines()


setup(
    name="pubtools",
    version="1.4.1",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    url="https://github.com/release-engineering/pubtools",
    license="GNU General Public License",
    description=get_description(),
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=get_requirements(),
    python_requires=">=3.6",
    project_urls={
        "Documentation": "https://release-engineering.github.io/pubtools/",
        "Changelog": "https://github.com/release-engineering/pubtools/blob/master/CHANGELOG.md",
    },
    entry_points={
        "pubtools.hooks": [
            "mallopt = pubtools._impl.mallopt",
        ]
    },
)
