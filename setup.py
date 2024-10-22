from setuptools import setup, find_packages

setup(
    name='mutation-core',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'mutation-core=src.mutation_core:main',
        ],
    },
    author='Bruno Garcia',
    author_email='brunoely.gc@gmail.com',
    description='A mutation testing tool for Bitcoin Core',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.8',  # Minimum Python version
)
