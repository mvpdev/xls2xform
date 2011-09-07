import os

from fabric.api import *
from fabric.contrib import files, console
from fabric import utils
from fabric.decorators import hosts

from datetime import datetime

env.home = '/home/wsgi/srv/'
env.project = 'xls2xform'

HOST_INFO = ["wsgi@nmis-linode.mvpafrica.org"]

DEPLOYMENTS = {
    'alpha': {
        'project': 'xls2xform',
        'branch': 'develop',
        'pyxform_branch': 'develop',
    },
    'prod': {
        'project': 'xls2xform_production',
        'branch': 'master',
        'pyxform_branch': 'develop',
    }
}

@hosts(HOST_INFO)
def deploy(deployment_name="alpha"):
    """
    TODO: figure out how to best use "@hosts" decorator.
    """
    setup_env(deployment_name)
    pull_from_origin()
    install_requirements()
    remove_old_pyxform()
    with cd(env.code_src):
#        run_in_virtualenv("pip install -e ")
        run_in_virtualenv("python manage.py migrate")
        run_in_virtualenv("python manage.py collectstatic --noinput")
    restart_wsgi()

@hosts(HOST_INFO)
def install_requirements():
    run_in_virtualenv("pip install -r %s" % env.pip_requirements_file)

def remove_old_pyxform():
    # remove the old pyxform from the virtualenvironment
    with cd(env.ve_src_dir):
        run("rm -rf pyxform")
    # replace with the branch specified in deployment settings
    run_in_virtualenv("pip install -e git://github.com/mvpdev/pyxform.git@%s#egg=pyxform" % env.pyxform_branch)

def setup_env(deployment_name):
    env.project_directory = os.path.join(env.home, DEPLOYMENTS[deployment_name]['project'])
    env.code_src = os.path.join(env.project_directory, env.project)
    env.branch = DEPLOYMENTS[deployment_name]['branch']
    env.pyxform_branch = DEPLOYMENTS[deployment_name]['pyxform_branch']
    env.virtualenv_activate_script = "source %s" % os.path.join(env.project_directory, 'project_env', 'bin', 'activate')
    env.ve_src_dir = os.path.join(env.project_directory, 'project_env', 'src')
    env.wsgi_config_file = os.path.join(env.project_directory, 'apache', 'environment.wsgi')
    env.pip_requirements_file = os.path.join(env.code_src, 'requirements.pip')

def pull_from_origin():
    with cd(env.code_src):
        run("git pull origin %(branch)s" % env)

def run_in_virtualenv(command):
    run(env.virtualenv_activate_script + ' && ' + command)

def migrate():
    with cd(env.code_src):
        run_in_virtualenv("python manage.py migrate")

def restart_wsgi():
    run('touch %s' % env.wsgi_config_file)
