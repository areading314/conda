# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from distutils.sysconfig import get_python_lib
from logging import getLogger
import ntpath
import os
from os.path import abspath, dirname, isfile, join, realpath
import sys
from unittest import TestCase

import pytest

from conda import CONDA_PACKAGE_ROOT
from conda._vendor.auxlib.ish import dals
from conda.base.context import context, reset_context
from conda.cli.common import stdout_json
from conda.common.compat import on_win, open
from conda.common.io import captured, env_var, env_vars
from conda.common.path import get_python_short_path, win_path_backout, win_path_ok
from conda.core.initialize import Result, _get_python_info, init_sh_system, init_sh_user, \
    initialize_dev, install, install_conda_csh, install_conda_fish, \
    install_conda_sh, install_conda_xsh, make_entry_point, make_entry_point_exe, \
    make_initialize_plan, make_install_plan, install_condacmd_conda_bat
from conda.exceptions import CondaValueError
from conda.gateways.disk.create import create_link, mkdir_p
from conda.models.enums import LinkType
from tests.helpers import tempdir

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


log = getLogger(__name__)


class InitializeTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orig_verbosity = os.environ.get('CONDA_VERBOSITY')
        os.environ['CONDA_VERBOSITY'] = '1'
        reset_context()

    @classmethod
    def tearDownClass(cls):
        if cls.orig_verbosity is None:
            del os.environ['CONDA_VERBOSITY']
        else:
            os.environ['CONDA_VERBOSITY'] = cls.orig_verbosity

    def test_get_python_info(self):
        python_exe, python_version, site_packages_dir = _get_python_info(sys.prefix)
        assert realpath(python_exe) == realpath(sys.executable)
        assert python_version == "%s.%s.%s" % sys.version_info[:3]
        assert site_packages_dir == get_python_lib()

    def test_make_install_plan(self):
        python_exe = "/darwin/bin/python"
        python_version = "2.6.10"
        site_packages_dir = "/darwin/lib/python2.6/site-packages"

        with patch("conda.core.initialize._get_python_info", return_value=(
                python_exe, python_version, site_packages_dir
        )):
            plan = make_install_plan("/darwin")
            stdout_json(plan)
            if on_win:
                assert plan == [
                    {
                        "function": "make_entry_point_exe",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\Scripts\\conda.exe"
                        }
                    },
                    {
                        "function": "make_entry_point_exe",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\Scripts\\conda-env.exe"
                        }
                    },
                    {
                        "function": "make_entry_point",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "func": "main",
                            "module": "conda.cli",
                            "target_path": "/darwin\\Scripts\\conda-script.py"
                        }
                    },
                    {
                        "function": "make_entry_point",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "func": "main",
                            "module": "conda_env.cli.main",
                            "target_path": "/darwin\\Scripts\\conda-env-script.py"
                        }
                    },
                    {
                        "function": "install_condacmd_conda_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\condacmd\\conda.bat"
                        }
                    },
                    {
                        "function": "install_condacmd_conda_activate_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\condacmd\\_conda_activate.bat"
                        }
                    },
                    {
                        "function": "install_condacmd_conda_auto_activate_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\condacmd\\conda_auto_activate.bat"
                        }
                    },
                    {
                        "function": "install_condacmd_hook_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\condacmd\\conda_hook.bat"
                        }
                    },
                    {
                        "function": "install_Scripts_activate_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\Scripts\\activate.bat"
                        }
                    },
                    {
                        "function": "install_activate_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\condacmd\\activate.bat"
                        }
                    },
                    {
                        "function": "install_deactivate_bat",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\condacmd\\deactivate.bat"
                        }
                    },
                    {
                        "function": "install_activate",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\Scripts\\activate"
                        }
                    },
                    {
                        "function": "install_deactivate",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\Scripts\\deactivate"
                        }
                    },
                    {
                        "function": "install_conda_sh",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\etc\\profile.d\\conda.sh"
                        }
                    },
                    {
                        "function": "install_conda_fish",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\etc\\fish\\conf.d\\conda.fish"
                        }
                    },
                    {
                        "function": "install_conda_xsh",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/lib/python2.6/site-packages\\xonsh\\conda.xsh"
                        }
                    },
                    {
                        "function": "install_conda_csh",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin\\etc\\profile.d\\conda.csh"
                        }
                    }
                ]
            else:
                assert plan == [
                    {
                        "function": "make_entry_point",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "func": "main",
                            "module": "conda.cli",
                            "target_path": "/darwin/bin/conda"
                        }
                    },
                    {
                        "function": "make_entry_point",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "func": "main",
                            "module": "conda_env.cli.main",
                            "target_path": "/darwin/bin/conda-env"
                        }
                    },
                    {
                        "function": "install_activate",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/bin/activate"
                        }
                    },
                    {
                        "function": "install_deactivate",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/bin/deactivate"
                        }
                    },
                    {
                        "function": "install_conda_sh",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/etc/profile.d/conda.sh"
                        }
                    },
                    {
                        "function": "install_conda_fish",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/etc/fish/conf.d/conda.fish"
                        }
                    },
                    {
                        "function": "install_conda_xsh",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/lib/python2.6/site-packages/xonsh/conda.xsh"
                        }
                    },
                    {
                        "function": "install_conda_csh",
                        "kwargs": {
                            "conda_prefix": "/darwin",
                            "target_path": "/darwin/etc/profile.d/conda.csh"
                        }
                    }
                ]

    def test_make_initialize_plan_bash_zsh(self):
        with tempdir() as conda_temp_prefix:
            plan = make_initialize_plan(conda_temp_prefix, ('bash', 'zsh'), for_user=True,
                                        for_system=True, anaconda_prompt=False)
            steps = tuple(step for step in plan if step['function'] == 'init_sh_user')
            assert len(steps) == 2
            steps = tuple(step for step in plan if step['function'] == 'init_sh_system')
            assert len(steps) == 1

    def test_make_initialize_plan_cmd_exe(self):
        with tempdir() as conda_temp_prefix:
            plan = make_initialize_plan(conda_temp_prefix, ('cmd.exe',), for_user=True,
                                        for_system=True, anaconda_prompt=True)
            steps = tuple(step for step in plan if step['function'] == 'init_cmd_exe_registry')
            assert len(steps) == 2
            steps = tuple(step for step in plan if step['function'] == 'install_anaconda_prompt')
            assert len(steps) == 2

    def test_make_entry_point(self):
        with tempdir() as conda_temp_prefix:
            conda_prefix = abspath(sys.prefix)
            if on_win:
                conda_exe_path = join(conda_temp_prefix, 'Scripts', 'conda-script.py')
            else:
                conda_exe_path = join(conda_temp_prefix, 'bin', 'conda')
            result = make_entry_point(conda_exe_path, conda_prefix, 'conda.entry.point', 'run')
            assert result == Result.MODIFIED

            with open(conda_exe_path) as fh:
                ep_contents = fh.read()

            if on_win:
                assert ep_contents == dals("""
                # -*- coding: utf-8 -*-
                import sys

                if __name__ == '__main__':
                    from conda.entry.point import run
                    sys.exit(run())
                """)
            else:
                assert ep_contents == dals("""
                #!%s/bin/python
                # -*- coding: utf-8 -*-
                import sys

                if __name__ == '__main__':
                    from conda.entry.point import run
                    sys.exit(run())
                """) % conda_prefix

            result = make_entry_point(conda_exe_path, conda_prefix, 'conda.entry.point', 'run')
            assert result == Result.NO_CHANGE

    def test_make_entry_point_exe(self):
        with tempdir() as conda_temp_prefix:
            conda_prefix = abspath(sys.prefix)
            target_path = join(conda_temp_prefix, 'Scripts', 'conda-env.exe')
            result = make_entry_point_exe(target_path, conda_prefix)
            assert result == Result.MODIFIED

            assert isfile(target_path)

            result = make_entry_point_exe(target_path, conda_prefix)
            assert result == Result.NO_CHANGE

    def test_install_conda_sh(self):
        with tempdir() as conda_prefix:
            target_path = join(conda_prefix, 'etc', 'profile.d', 'conda.sh')
            result = install_conda_sh(target_path, conda_prefix)
            assert result == Result.MODIFIED

            with open(target_path) as fh:
                created_file_contents = fh.read()

            if on_win:
                first_line, second_line, remainder = created_file_contents.split('\n', 2)
                assert first_line == "export CONDA_EXE=\"$(cygpath '%s')\"" % context.conda_exe
                assert second_line == "export CONDA_BAT=\"%s\"" % join(context.conda_prefix, 'condacmd', 'conda.bat')
            else:
                first_line, remainder = created_file_contents.split('\n', 1)
                assert first_line == 'export CONDA_EXE="%s"' % context.conda_exe

            with open(join(CONDA_PACKAGE_ROOT, 'shell', 'etc', 'profile.d', 'conda.sh')) as fh:
                original_contents = fh.read()
            assert remainder == original_contents

            result = install_conda_sh(target_path, conda_prefix)
            assert result == Result.NO_CHANGE

    def test_install_conda_fish(self):
        with tempdir() as conda_temp_prefix:
            conda_prefix = abspath(sys.prefix)
            target_path = join(conda_temp_prefix, 'etc', 'fish', 'conf.d', 'conda.fish')
            result = install_conda_fish(target_path, conda_prefix)
            assert result == Result.MODIFIED

            with open(target_path) as fh:
                created_file_contents = fh.read()

            first_line, second_line, third_line, remainder = created_file_contents.split('\n', 3)
            if on_win:
                win_conda_exe = join(conda_prefix, 'Scripts', 'conda.exe')
                assert first_line == 'set -gx CONDA_EXE (cygpath "%s")' % win_conda_exe
                assert second_line == 'set _CONDA_ROOT (cygpath "%s")' % conda_prefix
                assert third_line == 'set _CONDA_EXE (cygpath "%s")' % win_conda_exe
            else:
                assert first_line == 'set -gx CONDA_EXE "%s"' % join(conda_prefix, 'bin', 'conda')
                assert second_line == 'set _CONDA_ROOT "%s"' % conda_prefix
                assert third_line == 'set _CONDA_EXE "%s"' % join(conda_prefix, 'bin', 'conda')

            with open(join(CONDA_PACKAGE_ROOT, 'shell', 'etc', 'fish', 'conf.d', 'conda.fish')) as fh:
                original_contents = fh.read()
            assert remainder == original_contents

            result = install_conda_fish(target_path, conda_prefix)
            assert result == Result.NO_CHANGE

    def test_install_conda_xsh(self):
        with tempdir() as conda_temp_prefix:
            conda_prefix = abspath(sys.prefix)
            target_path = join(conda_temp_prefix, 'Lib', 'site-packages', 'conda.xsh')
            result = install_conda_xsh(target_path, conda_prefix)
            assert result == Result.MODIFIED

            with open(target_path) as fh:
                created_file_contents = fh.read()

            first_line, remainder = created_file_contents.split('\n', 1)
            if on_win:
                assert first_line == 'CONDA_EXE = "%s"' % join(conda_prefix, 'Scripts', 'conda.exe')
            else:
                assert first_line == 'CONDA_EXE = "%s"' % join(conda_prefix, 'bin', 'conda')

            with open(join(CONDA_PACKAGE_ROOT, 'shell', 'conda.xsh')) as fh:
                original_contents = fh.read()
            assert remainder == original_contents

            result = install_conda_xsh(target_path, conda_prefix)
            assert result == Result.NO_CHANGE

    def test_install_conda_csh(self):
        with tempdir() as conda_temp_prefix:
            conda_prefix = abspath(sys.prefix)
            target_path = join(conda_temp_prefix, 'etc', 'profile.d', 'conda.csh')
            result = install_conda_csh(target_path, conda_prefix)
            assert result == Result.MODIFIED

            with open(target_path) as fh:
                created_file_contents = fh.read()

            first_line, second_line, third_line, remainder = created_file_contents.split('\n', 3)
            if on_win:
                assert first_line == 'setenv CONDA_EXE `cygpath %s`' % join(conda_prefix, 'Scripts', 'conda.exe')
                assert second_line == 'setenv _CONDA_ROOT `cygpath %s`' % conda_prefix
                assert third_line == 'setenv _CONDA_EXE `cygpath %s`' % join(conda_prefix, 'Scripts', 'conda.exe')
            else:
                assert first_line == 'setenv CONDA_EXE "%s"' % join(conda_prefix, 'bin', 'conda')
                assert second_line == 'setenv _CONDA_ROOT "%s"' % conda_prefix
                assert third_line == 'setenv _CONDA_EXE "%s"' % join(conda_prefix, 'bin', 'conda')

            with open(join(CONDA_PACKAGE_ROOT, 'shell', 'etc', 'profile.d', 'conda.csh')) as fh:
                original_contents = fh.read()
            assert remainder == original_contents

            result = install_conda_csh(target_path, conda_prefix)
            assert result == Result.NO_CHANGE

    def test_install_condacmd_conda_bat(self):
        with tempdir() as conda_temp_prefix:
            conda_prefix = abspath(sys.prefix)
            target_path = join(conda_temp_prefix, 'condacmd', 'conda.bat')
            result = install_condacmd_conda_bat(target_path, conda_prefix)
            assert result == Result.MODIFIED

            with open(target_path) as fh:
                created_file_contents = fh.read()

            remainder = created_file_contents

            with open(join(CONDA_PACKAGE_ROOT, 'shell', 'condacmd', 'conda.bat')) as fh:
                original_contents = fh.read()
            assert remainder == original_contents

            result = install_condacmd_conda_bat(target_path, conda_prefix)
            assert result == Result.NO_CHANGE

    def test__get_python_info(self):
        python_exe, python_version, site_packages_dir = _get_python_info(sys.prefix)
        assert python_exe == sys.executable
        assert python_version == '%d.%d.%d' % sys.version_info[:3]
        assert site_packages_dir.endswith('site-packages')

    def test_install_1(self):
        with env_vars({'CONDA_DRY_RUN': 'true', 'CONDA_VERBOSITY': '0'}, reset_context):
            with tempdir() as conda_temp_prefix:
                with captured() as c:
                    install(conda_temp_prefix)

        assert "WARNING: Cannot install xonsh wrapper" in c.stderr
        if on_win:
            modified_files = (
                'conda.exe',
                'conda-env.exe',
                'conda-script.py',
                'conda-env-script.py',
                'conda.bat',
                '_conda_activate.bat',
                'conda_auto_activate.bat',
                'conda_hook.bat',
                'activate.bat',
                'activate.bat',
                'deactivate.bat',
                'activate',
                'deactivate',
                'conda.sh',
                'conda.fish',
                'conda.csh',
            )
        else:
            modified_files = (
                'conda',
                'conda-env',
                'activate',
                'deactivate',
                'conda.sh',
                'conda.fish',
                'conda.csh',
            )

        print(c.stdout)
        print(c.stderr, file=sys.stderr)

        assert c.stdout.count('modified') == len(modified_files)
        for fn in modified_files:
            line = next(line for line in c.stdout.splitlines() if line.strip().endswith(fn))
            assert line.strip().startswith('modified'), line

    def test_initialize_dev_bash(self):
        with pytest.raises(CondaValueError):
            initialize_dev('bash', conda_source_root=join('a', 'b', 'c'))

        with env_vars({'CONDA_DRY_RUN': 'true', 'CONDA_VERBOSITY': '0'}, reset_context):
            with tempdir() as conda_temp_prefix:
                new_py = abspath(join(conda_temp_prefix, get_python_short_path()))
                mkdir_p(dirname(new_py))
                create_link(abspath(sys.executable), new_py, LinkType.hardlink if on_win else LinkType.softlink)
                with captured() as c:
                    initialize_dev('bash', dev_env_prefix=conda_temp_prefix, conda_source_root=dirname(CONDA_PACKAGE_ROOT))

        print(c.stdout)
        print(c.stderr, file=sys.stderr)

        if on_win:
            modified_files = (
                'conda.exe',
                'conda-env.exe',
                'conda-script.py',
                'conda-env-script.py',
                'conda.bat',
                '_conda_activate.bat',
                'conda_auto_activate.bat',
                'conda_hook.bat',
                'activate.bat',
                'activate.bat',
                'deactivate.bat',
                'activate',
                'deactivate',
                'conda.sh',
                'conda.fish',
                'conda.xsh',
                'conda.csh',
                'site-packages',  # remove conda in site-packages dir
                'conda.egg-link',
                'easy-install.pth',
                'conda.egg-info',
            )
        else:
            modified_files = (
                'conda',
                'conda-env',
                'activate',
                'deactivate',
                'conda.sh',
                'conda.fish',
                'conda.xsh',
                'conda.csh',
                'site-packages',  # remove conda in site-packages dir
                'conda.egg-link',
                'easy-install.pth',
                'conda.egg-info',
            )

        stderr = c.stderr.replace('no change', 'modified')
        assert stderr.count('modified') == len(modified_files)

        for fn in modified_files:
            line = next(line for line in stderr.splitlines() if line.strip().endswith(fn))
            assert line.strip().startswith('modified'), line

        assert "unset CONDA_SHLVL" in c.stdout

    def test_initialize_dev_cmd_exe(self):
        with env_vars({'CONDA_DRY_RUN': 'true', 'CONDA_VERBOSITY': '0'}, reset_context):
            with tempdir() as conda_temp_prefix:
                new_py = abspath(join(conda_temp_prefix, get_python_short_path()))
                mkdir_p(dirname(new_py))
                create_link(abspath(sys.executable), new_py, LinkType.hardlink if on_win else LinkType.softlink)
                with captured() as c:
                    initialize_dev('cmd.exe', dev_env_prefix=conda_temp_prefix, conda_source_root=dirname(CONDA_PACKAGE_ROOT))

        print(c.stdout)
        print(c.stderr, file=sys.stderr)

        if on_win:
            modified_files = (
                'conda.exe',
                'conda-env.exe',
                'conda-script.py',
                'conda-env-script.py',
                'conda.bat',
                '_conda_activate.bat',
                'conda_auto_activate.bat',
                'conda_hook.bat',
                'activate.bat',
                'activate.bat',
                'deactivate.bat',
                'activate',
                'deactivate',
                'conda.sh',
                'conda.fish',
                'conda.xsh',
                'conda.csh',
                'site-packages',  # remove conda in site-packages dir
                'conda.egg-link',
                'easy-install.pth',
                'conda.egg-info',

            )
        else:
            modified_files = (
                'conda',
                'conda-env',
                'activate',
                'deactivate',
                'conda.sh',
                'conda.fish',
                'conda.xsh',
                'conda.csh',
                'site-packages',  # remove conda in site-packages dir
                'conda.egg-link',
                'easy-install.pth',
                'conda.egg-info',

            )

        stderr = c.stderr.replace('no change', 'modified')
        assert stderr.count('modified') == len(modified_files)

        for fn in modified_files:
            line = next(line for line in stderr.splitlines() if line.strip().endswith(fn))
            assert line.strip().startswith('modified'), line

    @pytest.mark.skipif(on_win, reason="unix-only test")
    def test_init_sh_user_unix(self):
        with tempdir() as conda_temp_prefix:
            target_path = join(conda_temp_prefix, '.bashrc')

            initial_content = dals("""
            export PATH="/some/other/conda/bin:$PATH"
            export PATH="%(prefix)s/bin:$PATH"
              export PATH="%(prefix)s/bin:$PATH"

            # >>> conda initialize >>>
            __conda_setup="$('%(prefix)s/bin/conda' shell.bash hook 2> /dev/null)"
            if [ $? -eq 0 ]; then
            fi
            unset __conda_setup
            # <<< conda initialize <<<

            . etc/profile.d/conda.sh
            . etc/profile.d/coda.sh
            . /somewhere/etc/profile.d/conda.sh
            source /etc/profile.d/conda.sh

            \t source %(prefix)s/etc/profile.d/conda.sh
            """) % {
                'prefix': win_path_backout(abspath(conda_temp_prefix)),
            }

            with open(target_path, 'w') as fh:
                fh.write(initial_content)

            init_sh_user(target_path, conda_temp_prefix, 'bash')

            with open(target_path) as fh:
                new_content = fh.read()

            expected_new_content = dals("""
            export PATH="/some/other/conda/bin:$PATH"
            # export PATH="%(prefix)s/bin:$PATH"  # commented out by conda initialize
            # export PATH="%(prefix)s/bin:$PATH"  # commented out by conda initialize

            # >>> conda initialize >>>
            # !! Contents within this block are managed by 'conda init' !!
            __conda_setup="$('%(prefix)s/bin/conda' shell.bash hook 2> /dev/null)"
            if [ $? -eq 0 ]; then
                eval "$__conda_setup"
            else
                if [ -f "%(prefix)s/etc/profile.d/conda.sh" ]; then
                    . "%(prefix)s/etc/profile.d/conda.sh"
                else
                    export PATH="%(prefix)s/bin:$PATH"
                fi
            fi
            unset __conda_setup
            # <<< conda initialize <<<

            # . etc/profile.d/conda.sh  # commented out by conda initialize
            . etc/profile.d/coda.sh
            # . /somewhere/etc/profile.d/conda.sh  # commented out by conda initialize
            # source /etc/profile.d/conda.sh  # commented out by conda initialize

            # source %(prefix)s/etc/profile.d/conda.sh  # commented out by conda initialize
            """) % {
                'prefix': win_path_backout(abspath(conda_temp_prefix)),
            }
            print(new_content)
            assert new_content == expected_new_content

    @pytest.mark.skipif(not on_win, reason="windows-only test")
    def test_init_sh_user_windows(self):
        with tempdir() as conda_temp_prefix:
            target_path = join(conda_temp_prefix, '.bashrc')
            conda_prefix = "c:\\Users\\Lars\\miniconda"
            cygpath_conda_prefix = "/c/Users/Lars/miniconda"

            initial_content = dals("""
            source /c/conda/Scripts/activate root
            . $(cygpath 'c:\\conda\\Scripts\\activate') root

            # >>> conda initialize >>>
            __conda_setup="$('%(prefix)s/bin/conda' shell.bash hook 2> /dev/null)"
            if [ $? -eq 0 ]; then
            fi
            unset __conda_setup
            # <<< conda initialize <<<

            . etc/profile.d/conda.sh
            . etc/profile.d/coda.sh
            . /somewhere/etc/profile.d/conda.sh
            source /etc/profile.d/conda.sh

            \t source %(prefix)s/etc/profile.d/conda.sh
            """) % {
                'prefix': win_path_ok(abspath(conda_prefix)),
            }

            with open(target_path, 'w') as fh:
                fh.write(initial_content)

            init_sh_user(target_path, conda_prefix, 'bash')

            with open(target_path) as fh:
                new_content = fh.read()

            print(new_content)

            expected_new_content = dals("""
            # source /c/conda/Scripts/activate root  # commented out by conda initialize
            # . $(cygpath 'c:\\conda\\Scripts\\activate') root  # commented out by conda initialize

            # >>> conda initialize >>>
            # !! Contents within this block are managed by 'conda init' !!
            eval "$('%(cygpath_conda_prefix)s/Scripts/conda.exe' shell.bash hook)"
            # <<< conda initialize <<<

            # . etc/profile.d/conda.sh  # commented out by conda initialize
            . etc/profile.d/coda.sh
            # . /somewhere/etc/profile.d/conda.sh  # commented out by conda initialize
            # source /etc/profile.d/conda.sh  # commented out by conda initialize

            # source %(prefix)s/etc/profile.d/conda.sh  # commented out by conda initialize
            """) % {
                'prefix': win_path_ok(abspath(conda_prefix)),
                'cygpath_conda_prefix': cygpath_conda_prefix,
            }

            assert new_content == expected_new_content

    def test_init_cmd_exe_registry(self):
        def _read_windows_registry_mock(target_path):
            return 'echo hello & "yada\\yada\\conda_hook.bat" & echo "world"', None

        from conda.core import initialize
        orig_read_windows_registry = initialize._read_windows_registry
        initialize._read_windows_registry = _read_windows_registry_mock
        orig_join = initialize.join
        initialize.join = ntpath.join

        try:
            target_path = r'HKEY_CURRENT_USER\Software\Microsoft\Command Processor\AutoRun'
            conda_prefix = "c:\\Users\\Lars\\miniconda"
            with env_var('CONDA_DRY_RUN', 'true', reset_context):
                with captured() as c:
                    initialize.init_cmd_exe_registry(target_path, conda_prefix)
        finally:
            initialize._read_windows_registry = orig_read_windows_registry
            initialize.join = orig_join

        expected = "echo hello & \"c:\\Users\\Lars\\miniconda\\condacmd\\conda_hook.bat\" & echo \"world\""
        assert c.stdout.strip().splitlines()[-1][1:] == expected

    def test_init_sh_system(self):
        with tempdir() as td:
            target_path = join(td, 'conda.sh')
            conda_prefix = join(td, 'b', 'c')
            init_sh_system(target_path, conda_prefix)
            with open(target_path) as fh:
                content = fh.read().strip().splitlines()
            assert content[0] == '# >>> conda initialize >>>'
            assert content[1] == "# !! Contents within this block are managed by 'conda init' !!"
            assert content[-1] == '# <<< conda initialize <<<'
