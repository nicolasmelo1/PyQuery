from setuptools import setup, find_packages

setup(
    name = 'PyQuery',         # How you named your package folder (MyLib)
    packages = find_packages(),   # Chose the same as "name"
    version = '0.1',      # Start with a small number and increase it with every change you make
    license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description = 'Easily make queries, specially the ones that need multiple joins',   # Give a short description about your library
    author = 'NICOLAS MELO',                   # Type in your name
    author_email = 'nicolasmelo12@gmail.com',      # Type in your E-Mail
    url = 'https://github.com/user/reponame',   # Provide either the link to your github or to your website
    download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
    keywords = ['Query', 'Django Like', 'SQL', 'Queries', 'Join'],   # Keywords that define your package best
    install_requires=[
        'psycopg2'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License', 
        'Operating System :: OS Independent', 
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    zip_safe=False
)