from setuptools import setup, find_packages

setup(
    name="netbox-gpt",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "netbox-gpt=netbox_gpt.assistant:main",
        ],
    },
    python_requires=">=3.8",
)