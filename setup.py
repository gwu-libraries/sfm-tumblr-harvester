from setuptools import setup

setup(
    name='sfmtumblrharvester',
    version='1.8.0',
    url='https://github.com/gwu-libraries/sfm-tumblr-harvester',
    author='Vict Tan',
    author_email='ychtan@email.gwu.edu',
    description="Social Feed Manager Tumblr Harvester",
    platforms=['POSIX'],
    test_suite='tests',
    scripts=['tumblr_harvester.py',
             'tumblr_warc_iter.py'],
    py_modules=['tumblr_harvester','tumblr_warc_iter'],
    install_requires=['sfmutils'],
    tests_require=['mock>=1.3.0'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 4 - Beta',
    ],
)
