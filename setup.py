from setuptools import setup

setup(
    name='dp-search-app',
    version='',
    packages=['dp-search.server', 'dp-search.server.search', 'dp-search.server.tracking'],
    url='',
    license='',
    author='sullid',
    author_email='',
    description='', install_requires=['flask', 'elasticsearch', 'elasticsearch_dsl', 'gevent']
)
