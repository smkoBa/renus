from setuptools import setup, find_packages

setup(
    name='renus',
    version='1.0.0',
python_requires=">=3.8",
    description='Renus Framework',
    url='https://github.com/smkoBa/renus',
    author='Smko Bayazidi',
    author_email='ba.smko@gmail.com',
    license='BSD',
    packages=find_packages(),

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)