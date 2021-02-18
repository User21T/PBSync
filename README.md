# PBSync

Advanced workspace synchronization tool for Unreal Engine projects hosted on git repositories.

## Setup

On Linux, this step can be skipped.

PyInstaller is required for executable generation, and it should be built from source to prevent false positive virus detections of generated PBSync executable.

You can run `install_pyinstaller.bat` to do this automatically.

## Distribution

### Windows

To generate a binary file from python source code, just run `build.bat` script. If generation was successful, the binary file will be put inside `dist` folder. To start using, generated executable should be put into root folder of the Unreal Engine project.

You must also install PyWin32 [system wide](https://github.com/mhammond/pywin32#installing-via-pip).

### Linux

On Linux systems, run the `build.sh` script to generate binary file.

But, since most Linux systems come with a version of Python already available, another option is to run it directly:

```
git clone https://github.com/ProjectBorealis/PBSync

PYTHONPATH=<path-to-local-PBSync> python <path-to-local-PBSync>/pbsync/pbsync.py --help
```

### Minor issues with gsutil

**Note:** PBSync requires [a modification](https://github.com/GoogleCloudPlatform/gsutil/pull/1174/files) to the gsutil dependency. You will have to do this every time gsutil updates and build again.

## Available Commands

List of available commands can be printed to console by passing `--help` to generated executable.

## Contribution

Everyone is welcomed to fork the repository, or open pull requests and new issues in this main repository.
