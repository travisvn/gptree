from setuptools import setup, find_packages

setup(
    name="gptree-cli",
    version="1.4.0",
    author="Travis Van Nimwegen",
    author_email="cli@travisvn.com",
    description="A CLI tool to provide LLM context for coding projects by combining project files into a single text file (or clipboard text) with directory tree structure",
    license="GPLv3",
    url="https://github.com/travisvn/gptree",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),  # Automatically find the package
    install_requires=[
        "pathspec",
        "pyperclip"
    ],
    entry_points={
        "console_scripts": [
            "gptree=cli_tool_gptree.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
