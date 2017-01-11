# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

# requirements
install_requires = [
    "pyev>=0.9.0",
]

dev_requires = [
    "thriftpy>=0.3.9",
] + install_requires


setup(name="dracula",
      description="a thrift server with high performance",
      keywords="thrift server",
      author="liuRoy",
      author_email="lrysjtu@gail.com",
      packages=find_packages(exclude=['docs', 'example']),
      url="https://github.com/LiuRoy/dracula",
      license="Apache License 2",
      zip_safe=False,
      install_requires=install_requires,
      extras_require={
          "dev": dev_requires,
      },
      classifiers=[
          "Topic :: Software Development",
          "Intended Audience :: Developers",
          "License :: Apache",
          "Programming Language :: Python :: 2.7",
      ])
