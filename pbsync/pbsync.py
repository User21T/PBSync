import subprocess
import os.path
import os
import sys
import argparse

from pbpy import *
from pbsync import pbsync_version

default_config_name = "PBSync.xml"

def sync_handler(sync_val, repository_val = None):
    if sync_val == "all" or sync_val == "force":
        # Do not progress further if we're in an error state
        if pbtools.check_error_state():
            pbtools.error_state("""Repository is currently in an error state. Please fix issues in your workspace before running PBSync
            If you have already fixed the problem, you may remove """ + pbtools.error_file + " from your project folder & run StartProject bat file again.", True)

        # Firstly, check our remote connection before doing anything
        remote_state, remote_url = pbtools.check_remote_connection()
        if not remote_state:
            pbtools.error_state("Remote connection was not successful. Please verify you have a valid git remote URL & internet connection. Current git remote URL: " + remote_url)
        else:
            pblog.info("Remote connection is up")

        pblog.info("------------------")

        pblog.info("Executing " + str(sync_val) + " sync command")
        pblog.info("PBpy Module Version: " + pbversion.ver)
        pblog.info("PBSync Executable Version: " + pbsync_version.ver)

        pblog.info("------------------")

        git_version_result = pbgit.compare_git_version(pbconfig.get('supported_git_version'))
        if git_version_result == -2:
            # Handle parse error first, in case of possibility of getting expection in following get_git_version() calls
            pblog.error("Git is not installed correctly on your system.")
            pblog.error("Please install latest Git from https://git-scm.com/download/win")
            pbtools.error_state()
        elif git_version_result == 0:
            pblog.info("Current Git version: " + str(pbgit.get_git_version()))
        elif git_version_result == -1:
            pblog.error("Git is not updated to the latest version in your system")
            pblog.error("Supported Git Version: " + pbconfig.get('supported_git_version'))
            pblog.error("Current Git Version: " + str(pbgit.get_git_version()))
            pblog.error("Please install latest Git from https://git-scm.com/download/win")
            pbtools.error_state()
        elif git_version_result == 1:
            pblog.warning("Current Git version is newer than supported one: " + str(pbgit.get_git_version()))
            pblog.warning("Supported Git version: " + pbconfig.get('supported_git_version'))
        else:
            pblog.error("Git is not installed correctly on your system.")
            pblog.error("Please install latest Git from https://git-scm.com/download/win")
            pbtools.error_state()
        lfs_version_result = pbgit.compare_lfs_version(pbconfig.get('supported_lfs_version'))
        if lfs_version_result == -2:
            # Handle parse error first, in case of possibility of getting expection in following get_git_version() calls
            pblog.error("Git LFS is not installed correctly on your system.")
            pblog.error("Please install latest Git LFS from https://git-lfs.github.com")
            pbtools.error_state()
        elif lfs_version_result == 0:
            pblog.info("Current Git LFS version: " + str(pbgit.get_lfs_version()))
        elif lfs_version_result == -1:
            pblog.error("Git LFS is not updated to the latest version in your system")
            pblog.error("Supported Git LFS Version: " + pbconfig.get('supported_lfs_version'))
            pblog.error("Current Git LFS Version: " + str(pbgit.get_lfs_version()))
            pblog.error("Please install latest Git LFS from https://git-lfs.github.com")
            pbtools.error_state()
        elif lfs_version_result == 1:
            pblog.warning("Current Git LFS version is newer than supported one: " + pbgit.get_lfs_version())
            pblog.warning("Supported Git LFS version: " + pbconfig.get('supported_lfs_version'))
        else:
            pblog.error("Git LFS is not installed correctly on your system")
            pblog.error("Please install latest Git LFS from https://git-lfs.github.com")
            pbtools.error_state()

        pblog.info("------------------")

        # Do not execute if Unreal Editor is running
        if pbtools.check_running_process("UE4Editor.exe"):
            pbtools.error_state("Unreal Editor is currently running. Please close it before running PBSync. If editor is not running, but you're somehow getting that error, please restart your system")

        pblog.info("Fetching recent changes on the repository...")
        subprocess.call(["git", "fetch", "origin"])

        # Do some housekeeping for git configuration
        pbgit.setup_config()

        # Check if we have correct credentials
        pbgit.check_credentials()

        pblog.info("------------------")

        # Execute synchronization part of script if we're on the expected branch, force sync is enabled
        if sync_val == "force" or pbgit.compare_with_currnent_branch_name(pbconfig.get('expected_branch_name')):
            pbtools.resolve_conflicts_and_pull() 
            pblog.info("------------------")
            
            if pbtools.pbget_pull() != 0:
                pbtools.error_state("An error occured while running PBGet. It's likely binary files for this release are not pushed yet. Please request help on #tech-support")
        else:
            pblog.warning("Current branch is not set as " + pbconfig.get('expected_branch_name') + ". Auto synchronization will be disabled")

        pblog.info("------------------")

        project_version = pbunreal.get_project_version()

        if project_version != None:
            pblog.info("Current project version: " + project_version)
        else:
            pbtools.error_state("Something went wrong while fetching project version. Please request help on #tech-support")
        
        pblog.info("------------------")

        pblog.info("Checking for engine updates...")
        if pbgit.sync_file("ProjectBorealis.uproject") != 0:
            pbtools.error_state("Something went wrong while updating .uproject file. Please request help on #tech-support")

        engine_version =  pbunreal.get_engine_version()

        pblog.info("Trying to register current engine build if it exists. Otherwise, required build will be downloaded...")
        if pbtools.run_ue4versionator() != 0:
            pbtools.error_state("Something went wrong while registering engine build " + engine_version + ". Please request help on #tech-support")
        else:
            pblog.info("Engine build " + engine_version + " successfully registered")
            
        # Clean old engine installations, do that only in expected branch
        if pbgit.compare_with_currnent_branch_name(pbconfig.get('expected_branch_name')):
            if pbtools.clean_old_engine_installations():
                pblog.info("Old engine installations are successfully cleaned")
            else:
                pblog.warning("Something went wrong while cleaning old engine installations. You may want to clean them manually.")

        pblog.info("------------------")

        if pbtools.check_ue4_file_association():
            os.startfile(os.getcwd() + "\\ProjectBorealis.uproject")
        else:
            pbtools.error_state(".uproject extension is not correctly set into Unreal Engine. Make sure you have Epic Games Launcher installed. If problem still persists, please get help from #tech-support.")

    elif sync_val == "engine":
        if repository_val is None:
            pblog.error("--repository <URL> argument should be provided with --sync engine command")
            sys.exit(1)
        engine_version = pbunreal.get_latest_available_engine_version(str(repository_val))
        if engine_version is None:
            pblog.error("Error while trying to fetch latest engine version")
            sys.exit(1)
        if not pbunreal.set_engine_version(engine_version):
            pblog.error("Error while trying to update engine version in .uproject file")
            sys.exit(1)
        pblog.info("Successfully changed engine version as " + str(engine_version))

    elif sync_val == "ddc" or sync_val == "DDC":
        pbunreal.generate_ddc_data()

    else:
        pblog.error("Incorrect value provided for sync command")
        sys.exit(1)

def clean_handler(clean_val):
    if clean_val == "workspace":
        if pbtools.wipe_workspace():
            pblog.info("Workspace wipe successful")
            input("Press enter to quit...")
        else:
            pblog.error("Something went wrong while wiping the workspace")
            sys.exit(1)

    elif clean_val == "engine":
        if not pbtools.clean_old_engine_installations():
            pblog.error("Something went wrong on engine installation root folder clean process")
            sys.exit(1)
    else:
        pblog.error("Incorrect value provided for clean command")
        sys.exit(1)

def print_handler(print_val, repository_val = None):
    if print_val == "latest-engine":
        if repository_val is None:
            pblog.error("--repository <URL> argument should be provided with --print latest-engine command")
            sys.exit(1)
        engine_version = pbunreal.get_latest_available_engine_version(str(repository_val))
        if engine_version is None:
            sys.exit(1)
        pblog.info(engine_version, end ="")
    
    elif print_val == "current-engine":
        engine_version = pbunreal.get_engine_version()
        if engine_version is None:
            sys.exit(1)
        pblog.info(engine_version, end ="")
    
    elif print_val == "project":
        project_version = pbunreal.get_project_version()
        if project_version is None:
            sys.exit(1)
        pblog.info(project_version, end ="")

    else:
        pblog.error("Incorrect value provided for print command")
        sys.exit(1)

def autoversion_handler(autoversion_val):
    if pbunreal.project_version_increase(autoversion_val):
        pblog.info("Successfully increased project version")
    else:
        pblog.error("Error occured while trying to increase project version")
        sys.exit(1)

def publish_handler(publish_val):
    if not pbtools.push_build(publish_val):
        pblog.error("Something went wrong while pushing a new playable build.")
        sys.exit(1)

def push_handler(push_val):
    project_version = pbunreal.get_project_version()
    pblog.info("Initiating PBGet to push " + project_version + " binaries...")
    result = pbtools.pbget_push(str(push_val))
    if int(result) == 1:
        pblog.error("Error occured while pushing binaries for " + project_version)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="~~ Project Borealis Workspace Synchronization Tool ~~\nPBpy Module Version: " + pbversion.ver + "\nPBSync Executable Version: " + pbsync_version.ver)

    parser.add_argument("--sync", help="[force, all, engine, ddc] Main command for the PBSync, synchronizes the project with latest changes in repo, and does some housekeeping")
    parser.add_argument("--print", help="[current-engine, latest-engine, project] Prints requested version information into console. latest-engine command needs --repository parameter")
    parser.add_argument("--repository", help="<URL> Required repository url for --print latest-engine and --sync engine commands")
    parser.add_argument("--autoversion", help="[hotfix, stable, public] Automatic version update for project version")
    parser.add_argument("--wipe", help="[latest] Wipe the workspace and get latest changes from current branch (Not revertable)")
    parser.add_argument("--clean", help="[engine] Do cleanup according to specified argument")
    parser.add_argument("--config", help="Path of config XML file. If not provided, ./PBSync.xml is used as default")
    parser.add_argument("--push", help="[apikey] Push current binaries into NuGet repository with provided api key. If provided with --autoversion, push will be done after auto versioning.")
    parser.add_argument("--publish", help="[stable, public] Publishes a playable build with provided build type")
    args = parser.parse_args()

    # If config parameter is not passed, use default config
    if args.config == None:
        args.config = default_config_name

    def pbsync_config_parser_func (root): return {
        'engine_base_version': root.find('enginebaseversion').text,
        'supported_git_version': root.find('git/version').text,
        'supported_lfs_version': root.find('git/lfsversion').text,
        'expected_branch_name': root.find('git/expectedbranch').text,
        'git_hooks_path': root.find('git/hooksfoldername').text,
        'watchman_executable_name': root.find('git/watchmanexecname').text,
        'lfs_lock_url': root.find('git/lfslockurl').text,
        'git_url': root.find('git/url').text,
        'log_file_path': root.find('log/file').text,
        'max_log_size': int(root.find('log/maximumsize').text),
        'ddc_expected_min_size': int(root.find('ddc/expectedminsize').text),
        'uproject_path': root.find('project/uprojectname').text,
        'uproject_version_key': root.find('project/uprojectversionkey').text,
        'engine_version_prefix': root.find('project/engineversionprefix').text,
        'defaultgame_path': root.find('project/defaultgameinipath').text,
        'defaultgame_version_key': root.find('project/projectversionkey').text,
        'versionator_config_path': root.find('project/versionatorconfigpath').text,
        'pbget_url': root.find('pbget/url').text,
        'dispatch_executable_path': root.find('dispatch/executable').text,
        'dispatch_config': root.find('dispatch/config').text,
        'dispatch_drm': root.find('dispatch/drm').text,
        'dispatch_stagedir': root.find('dispatch/stagedir').text
    }

    if pbconfig.generate_config(args.config, pbsync_config_parser_func):
        # If log file is big enough, remove it
        if os.path.isfile(pbconfig.get('log_file_path')) and os.path.getsize(pbconfig.get('log_file_path')) >= pbconfig.get('max_log_size'):
            pbtools.remove_file(pbconfig.get('log_file_path'))

        # Setup logger
        pblog.setup_logger(pbconfig.get('log_file_path'))
    else:
        # Logger is not initialized yet, so use print instead
        print(str(args.config) + " config file is not valid or not found. Please check integrity of the file")
        pbtools.error_state()

    # Process arguments
    if not (args.sync is None):
        sync_handler(args.sync)

    if not (args.print is None):
        print_handler(args.print, args.repository)
    
    if not (args.autoversion is None):
        autoversion_handler(args.autoversion)

    if not (args.clean is None):
        clean_handler(args.clean)

    if not (args.publish is None):
        publish_handler(args.publish)

    if not (args.push is None):
        push_handler(args.push)

if __name__ == '__main__':
    if "Scripts" in os.getcwd():
        # Working directory fix for scripts calling PBSync from Scripts folder
        os.chdir("..")
    main()
