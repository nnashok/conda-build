from collections import defaultdict
import os
import sys

import pytest

from conda_build.config import Config
from conda_build.metadata import MetaData
from conda_build.utils import check_call_env, prepend_bin_path


@pytest.fixture(scope='function')
def testing_workdir(tmpdir, request):
    """ Create a workdir in a safe temporary folder; cd into dir above before test, cd out after

    :param tmpdir: py.test fixture, will be injected
    :param request: py.test fixture-related, will be injected (see pytest docs)
    """

    saved_path = os.getcwd()

    tmpdir.chdir()
    # temporary folder for profiling output, if any
    tmpdir.mkdir('prof')

    def return_to_saved_path():
        if os.path.isdir(os.path.join(saved_path, 'prof')):
            profdir = tmpdir.join('prof')
            files = profdir.listdir('*.prof') if profdir.isdir() else []

            for f in files:
                f.rename(os.path.join(saved_path, 'prof', f.basename))
        os.chdir(saved_path)

    request.addfinalizer(return_to_saved_path)

    return str(tmpdir)


@pytest.fixture(scope='function')
def test_config(testing_workdir, request):
    return Config(croot=testing_workdir, anaconda_upload=False, verbose=True, activate=False)


@pytest.fixture(scope='function')
def test_metadata(request, test_config):
    d = defaultdict(dict)
    d['package']['name'] = request.function.__name__
    d['package']['version'] = '1.0'
    d['build']['number'] = '1'
    d['build']['entry_points'] = []
    d['requirements']['build'] = ['python']
    d['requirements']['run'] = ['python']
    d['test']['commands'] = ['echo "A-OK"', 'exit 0']
    d['about']['home'] = "sweet home"
    d['about']['license'] = "contract in blood"
    d['about']['summary'] = "a test package"

    return MetaData.fromdict(d, config=test_config)


@pytest.fixture(scope='function')
def testing_env(testing_workdir, request, monkeypatch):
    env_path = os.path.join(testing_workdir, 'env')

    check_call_env(['conda', 'create', '-yq', '-p', env_path,
                    'python={0}'.format(".".join(sys.version.split('.')[:2]))])
    monkeypatch.setenv('PATH', prepend_bin_path(os.environ.copy(), env_path, prepend_prefix=True)['PATH'])
    # cleanup is done by just cleaning up the testing_workdir
    return env_path
