from setuptools import setup

setup(
    name='sfmtumblrharvester',
    version='2.2.0',
    url='https://github.com/gwu-libraries/sfm-tumblr-harvester',
    author='Social Feed Manager',
    author_email='sfm@gwu.edu',
    description="Social Feed Manager Tumblr Harvester",
    platforms=['POSIX'],
    test_suite='tests',
    scripts=['tumblr_harvester.py',
             'tumblr_warc_iter.py'],
    py_modules=['tumblr_harvester','tumblr_warc_iter'],
    install_requires=['sfmutils'],
    tests_require=['mock==2.0.0'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
    ],
)
