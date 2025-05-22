from setuptools import setup, find_packages

setup(
    name="optimized_numerical",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
    ],
    author="PyToCpp",
    description="Optimized numerical operations using C++",
)