from setuptools import setup, find_packages

setup(
    name='mutation-core',
    version='0.6.0',
    install_requires=[],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mutation-core=src.mutation_core:main',
        ],
    },
    author='Bruno Garcia',
    author_email='brunoely.gc@gmail.com',
    description='Mutation testing tool for Bitcoin Core',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.8',  # Minimum Python version
)
